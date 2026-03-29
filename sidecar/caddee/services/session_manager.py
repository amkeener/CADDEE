"""Session manager — tracks conversation history, .scad source, and design iterations."""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

# Ensure the CADDEE project root is on sys.path so `shared` is importable.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from shared.messages import ConversationMessage, DesignIteration


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


@dataclass
class Session:
    """Holds all state for a single CADDEE design session."""

    conversation: list[ConversationMessage] = field(default_factory=list)
    current_scad: str | None = None
    iterations: list[DesignIteration] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_user_message(self, text: str) -> None:
        """Append a user message to the conversation history."""
        self.conversation.append(
            ConversationMessage(role="user", content=text),
        )
        log.debug("Session: added user message (%d chars), total=%d msgs",
                   len(text), len(self.conversation))

    def add_assistant_response(
        self,
        text: str,
        scad_code: str | None = None,
        stl_base64: str | None = None,
    ) -> None:
        """Record an assistant response and optionally a new design iteration.

        Parameters
        ----------
        text:
            The full assistant message text.
        scad_code:
            The extracted .scad source code (if any).
        stl_base64:
            Base64-encoded STL file data (if compile succeeded).
        """
        self.conversation.append(
            ConversationMessage(role="assistant", content=text),
        )

        if scad_code is not None:
            self.current_scad = scad_code

        if scad_code and stl_base64:
            self.iterations.append(
                DesignIteration(
                    prompt=self._last_user_message(),
                    scad_code=scad_code,
                    stl_base64=stl_base64,
                    timestamp=time.time(),
                ),
            )
            log.info("Session: new iteration #%d (scad=%d chars, stl=%d chars b64)",
                     len(self.iterations), len(scad_code), len(stl_base64))

    def get_context_for_claude(
        self,
    ) -> tuple[list[ConversationMessage], str | None]:
        """Return the data needed for a Claude API call.

        Returns
        -------
        A tuple of (conversation_history, current_scad_code).
        """
        return list(self.conversation), self.current_scad

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize session state for save/restore."""
        log.debug("Session: serializing (%d msgs, %d iterations)",
                   len(self.conversation), len(self.iterations))
        return {
            "version": 1,
            "conversation": [
                {"role": m.role, "content": m.content} for m in self.conversation
            ],
            "current_scad": self.current_scad,
            "iterations": [
                {
                    "prompt": it.prompt,
                    "scad_code": it.scad_code,
                    "stl_base64": it.stl_base64,
                    "timestamp": it.timestamp,
                }
                for it in self.iterations
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Restore session from serialized data."""
        log.info("Session: restoring from dict (version=%s)", data.get("version", "?"))
        session = cls()
        for msg in data.get("conversation", []):
            session.conversation.append(
                ConversationMessage(role=msg["role"], content=msg["content"])
            )
        session.current_scad = data.get("current_scad")
        for it in data.get("iterations", []):
            session.iterations.append(
                DesignIteration(
                    prompt=it["prompt"],
                    scad_code=it["scad_code"],
                    stl_base64=it.get("stl_base64", ""),
                    timestamp=it.get("timestamp", 0.0),
                )
            )
        return session

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _last_user_message(self) -> str:
        """Return the most recent user message, or empty string."""
        for msg in reversed(self.conversation):
            if msg.role == "user":
                return msg.content
        return ""
