"""Claude API service — sends conversation to Claude and extracts OpenSCAD code."""

from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure the CADDEE project root is on sys.path so `shared` is importable.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import anthropic

from shared.messages import ConversationMessage

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODEL = "claude-sonnet-4-20250514"
_MAX_TOKENS = 4096

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.txt"

# Supported image MIME types (matches Anthropic API)
_SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


# ---------------------------------------------------------------------------
# Response container
# ---------------------------------------------------------------------------


@dataclass
class ClaudeResult:
    """Holds the raw assistant text and any extracted .scad code."""

    text: str
    scad_code: str | None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_system_prompt() -> str:
    """Read the system prompt from disk (cached after first call)."""
    return _PROMPT_PATH.read_text(encoding="utf-8")


def call_claude(
    conversation: list[ConversationMessage],
    current_scad: str | None = None,
    images: list[str] | None = None,
) -> ClaudeResult:
    """Send conversation history to Claude and return the result.

    Parameters
    ----------
    conversation:
        Full conversation history (user + assistant messages).
    current_scad:
        The current .scad source code, if any. Injected into the system
        prompt so Claude can modify existing designs.
    images:
        Optional list of data-URL-encoded images (``data:image/png;base64,…``)
        to attach to the latest user message for multimodal vision input.

    Returns
    -------
    ClaudeResult with the assistant text and extracted .scad code (if any).
    """
    client = anthropic.Anthropic()  # picks up ANTHROPIC_API_KEY from env

    system_prompt = load_system_prompt()
    if current_scad:
        system_prompt += (
            "\n\n<current_scad>\n" + current_scad + "\n</current_scad>"
        )

    # Build the messages list in the API format.
    messages = _build_messages(conversation, images)

    response = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=system_prompt,
        messages=messages,
    )

    # Extract text from the response.
    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text

    scad_code = _extract_scad(text)

    return ClaudeResult(text=text, scad_code=scad_code)


def call_claude_error_retry(
    conversation: list[ConversationMessage],
    scad_code: str,
    compile_error: str,
) -> ClaudeResult:
    """Ask Claude to fix a compile error in the generated .scad code.

    Appends a user message with the error and asks for a corrected file.
    """
    retry_message = (
        f"The OpenSCAD code you generated failed to compile with this error:\n\n"
        f"```\n{compile_error}\n```\n\n"
        f"Please fix the code and output the COMPLETE corrected .scad file."
    )

    extended_conversation = list(conversation) + [
        ConversationMessage(role="user", content=retry_message),
    ]

    return call_claude(extended_conversation, current_scad=scad_code)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Match ```openscad or ```scad code fences.
_SCAD_FENCE_RE = re.compile(
    r"```(?:openscad|scad)\s*\n(.*?)```",
    re.DOTALL,
)

# Match data URL format: data:<mediaType>;base64,<data>
_DATA_URL_RE = re.compile(r"^data:(image/[a-z+]+);base64,(.+)$", re.DOTALL)


def _extract_scad(text: str) -> str | None:
    """Pull the first OpenSCAD code block out of the assistant response."""
    match = _SCAD_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return None


def _parse_data_url(data_url: str) -> tuple[str, str] | None:
    """Parse a data URL into (media_type, base64_data). Returns None on failure."""
    match = _DATA_URL_RE.match(data_url)
    if not match:
        log.warning("Skipping image with invalid data URL format")
        return None
    media_type = match.group(1)
    if media_type not in _SUPPORTED_IMAGE_TYPES:
        log.warning("Skipping unsupported image type: %s", media_type)
        return None
    return media_type, match.group(2)


def _build_messages(
    conversation: list[ConversationMessage],
    images: list[str] | None = None,
) -> list[dict]:
    """Build the Anthropic API messages list, injecting images into the last user message."""
    if not images:
        return [{"role": msg.role, "content": msg.content} for msg in conversation]

    # Parse images into content blocks.
    image_blocks: list[dict] = []
    for data_url in images:
        parsed = _parse_data_url(data_url)
        if parsed is None:
            continue
        media_type, b64_data = parsed
        image_blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64_data,
            },
        })

    if not image_blocks:
        return [{"role": msg.role, "content": msg.content} for msg in conversation]

    # Build messages: all messages use plain text except the last user message
    # which gets multimodal content blocks (images + text).
    messages: list[dict] = []
    for i, msg in enumerate(conversation):
        is_last_user = (
            msg.role == "user"
            and i == len(conversation) - 1
        )
        if is_last_user:
            content: list[dict] = list(image_blocks)
            content.append({"type": "text", "text": msg.content})
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": msg.role, "content": msg.content})

    return messages
