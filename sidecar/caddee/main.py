"""CADDEE sidecar entry point — stdio JSON message loop."""

from __future__ import annotations

import base64
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

# Ensure the CADDEE project root is on sys.path so `shared` is importable.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from shared.messages import (
    ChatErrorResponse,
    ChatResponse,
    ErrorResponse,
    ParameterResponse,
    PongResponse,
)

from caddee.services.claude_service import call_claude, call_claude_error_retry
from caddee.services.openscad_service import compile_scad
from caddee.services.session_manager import Session

# ---------------------------------------------------------------------------
# Logging — write to stderr so stdout stays clean for IPC
# ---------------------------------------------------------------------------

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[sidecar] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global session (one per sidecar process lifetime)
# ---------------------------------------------------------------------------

_session = Session()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Read JSON requests from stdin, write JSON responses to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as exc:
            req_id = "unknown"
            if isinstance(request, dict):
                req_id = request.get("id", req_id)
            error_resp = asdict(ErrorResponse(id=req_id, error=str(exc)))
            sys.stdout.write(json.dumps(error_resp) + "\n")
            sys.stdout.flush()


# ---------------------------------------------------------------------------
# Request routing
# ---------------------------------------------------------------------------


def handle_request(request: dict) -> dict:
    """Route request to the appropriate handler based on the `type` field."""
    req_type = request.get("type")
    req_id = request.get("id", "unknown")

    if req_type == "ping":
        return asdict(PongResponse(id=req_id))

    if req_type == "chat":
        return _handle_chat(req_id, request.get("message", ""))

    if req_type == "update_parameters":
        return _handle_update_parameters(req_id, request.get("scadCode", ""))

    if req_type == "save_session":
        return _handle_save_session(req_id)

    if req_type == "load_session":
        return _handle_load_session(req_id, request.get("sessionData", {}))

    return asdict(ErrorResponse(id=req_id, error=f"Unknown request type: {req_type}"))


# ---------------------------------------------------------------------------
# Chat pipeline with error-recovery loop
# ---------------------------------------------------------------------------


def _handle_chat(req_id: str, user_message: str) -> dict:
    """Full chat pipeline: Claude -> OpenSCAD compile -> optional retry.

    Flow:
      1. User message -> Claude generates .scad
      2. OpenSCAD compiles .scad -> STL
      3. If compile fails -> feed error back to Claude for ONE retry
      4. If retry fails  -> return ChatErrorResponse
      5. If success      -> return ChatResponse with base64 STL
    """
    # Record the user message in the session.
    _session.add_user_message(user_message)

    # --- First attempt ---------------------------------------------------
    conversation, current_scad = _session.get_context_for_claude()

    try:
        result = call_claude(conversation, current_scad)
    except Exception as exc:
        log.error("Claude API call failed: %s", exc)
        return asdict(ChatErrorResponse(
            id=req_id,
            error=f"Claude API error: {exc}",
        ))

    if result.scad_code is None:
        # Claude responded but didn't produce .scad code — that's okay,
        # it might be answering a question. Return the text as a "no-code" response.
        _session.add_assistant_response(result.text)
        return asdict(ChatResponse(
            id=req_id,
            message=result.text,
            scad_code="",
            stl_base64="",
        ))

    # --- Compile first attempt -------------------------------------------
    compile_result = compile_scad(result.scad_code)

    if compile_result.success:
        stl_b64 = _read_stl_base64(compile_result.stl_path)
        _session.add_assistant_response(result.text, result.scad_code, stl_b64)
        return asdict(ChatResponse(
            id=req_id,
            message=result.text,
            scad_code=result.scad_code,
            stl_base64=stl_b64,
        ))

    # --- Retry: feed compile error back to Claude -------------------------
    log.info("First compile failed, retrying: %s", compile_result.error)

    try:
        retry_result = call_claude_error_retry(
            conversation, result.scad_code, compile_result.error or "Unknown error",
        )
    except Exception as exc:
        log.error("Claude retry call failed: %s", exc)
        return asdict(ChatErrorResponse(
            id=req_id,
            error=f"Claude API error on retry: {exc}",
            compile_error=compile_result.error,
        ))

    if retry_result.scad_code is None:
        _session.add_assistant_response(retry_result.text)
        return asdict(ChatErrorResponse(
            id=req_id,
            error="Claude could not produce corrected OpenSCAD code.",
            compile_error=compile_result.error,
        ))

    # --- Compile retry attempt --------------------------------------------
    retry_compile = compile_scad(retry_result.scad_code)

    if retry_compile.success:
        stl_b64 = _read_stl_base64(retry_compile.stl_path)
        _session.add_assistant_response(
            retry_result.text, retry_result.scad_code, stl_b64,
        )
        return asdict(ChatResponse(
            id=req_id,
            message=retry_result.text,
            scad_code=retry_result.scad_code,
            stl_base64=stl_b64,
            was_retry=True,
        ))

    # --- Both attempts failed ---------------------------------------------
    _session.add_assistant_response(retry_result.text, retry_result.scad_code)
    return asdict(ChatErrorResponse(
        id=req_id,
        error="OpenSCAD compilation failed after retry.",
        compile_error=retry_compile.error,
    ))


# ---------------------------------------------------------------------------
# Parameter update (recompile without Claude)
# ---------------------------------------------------------------------------


def _handle_update_parameters(req_id: str, scad_code: str) -> dict:
    """Compile updated .scad code directly (no Claude call)."""
    if not scad_code:
        return asdict(ErrorResponse(id=req_id, error="No scad code provided"))

    compile_result = compile_scad(scad_code)
    if not compile_result.success:
        return asdict(ErrorResponse(id=req_id, error=compile_result.error or "Compile failed"))

    stl_b64 = _read_stl_base64(compile_result.stl_path)
    _session.current_scad = scad_code
    return asdict(ParameterResponse(id=req_id, stl_base64=stl_b64, scad_code=scad_code))


# ---------------------------------------------------------------------------
# Session save/load
# ---------------------------------------------------------------------------


def _handle_save_session(req_id: str) -> dict:
    """Serialize current session state."""
    data = _session.to_dict()
    return {"id": req_id, "type": "session_data", "sessionData": data}


def _handle_load_session(req_id: str, session_data: dict) -> dict:
    """Restore session from serialized data."""
    global _session
    _session = Session.from_dict(session_data)
    return {"id": req_id, "type": "session_loaded", "message": "Session restored"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_stl_base64(stl_path: str | None) -> str:
    """Read an STL file and return its contents as a base64 string."""
    if stl_path is None:
        return ""
    try:
        data = Path(stl_path).read_bytes()
        return base64.b64encode(data).decode("ascii")
    except OSError as exc:
        log.error("Failed to read STL file %s: %s", stl_path, exc)
        return ""


if __name__ == "__main__":
    main()
