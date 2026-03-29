"""CADDEE sidecar entry point — stdio JSON message loop."""

from __future__ import annotations

import base64
import json
import logging
import logging.handlers
import sys
import time
from dataclasses import asdict
from pathlib import Path

# Ensure the CADDEE project root is on sys.path so `shared` is importable.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from shared.messages import (
    ChatErrorResponse,
    ChatResponse,
    CompatibilityResponse,
    CapabilitiesResponse,
    ErrorResponse,
    ExportResponse,
    ImportResponse,
    LiveSyncResponse,
    ParameterResponse,
    PongResponse,
    SetApiKeyResponse,
)

from caddee.services.claude_service import call_claude, call_claude_error_retry, set_api_key, validate_api_key
from caddee.services.openscad_service import compile_scad
from caddee.services.session_manager import Session
from caddee.services import freecad_service

# ---------------------------------------------------------------------------
# Logging — stderr for console + rotating file for persistent debug logs
# ---------------------------------------------------------------------------

_LOG_DIR = Path.home() / ".caddee" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_LOG_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# Root logger config — DEBUG to capture everything
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format=_LOG_FORMAT,
    datefmt=_LOG_DATE_FMT,
)

# Rotating file handler: 5 MB per file, keep 3 backups
_file_handler = logging.handlers.RotatingFileHandler(
    _LOG_DIR / "sidecar.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FMT))
logging.getLogger().addHandler(_file_handler)

# Quiet noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("trimesh").setLevel(logging.WARNING)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global session (one per sidecar process lifetime)
# ---------------------------------------------------------------------------

_session = Session()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase: 'stl_base64' -> 'stlBase64'."""
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _camelize(obj: object) -> object:
    """Recursively convert dict keys from snake_case to camelCase."""
    if isinstance(obj, dict):
        return {_snake_to_camel(k): _camelize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_camelize(item) for item in obj]
    return obj


def main() -> None:
    """Read JSON requests from stdin, write JSON responses to stdout."""
    log.info("Sidecar process started (pid=%d)", __import__("os").getpid())
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            t0 = time.monotonic()
            response = handle_request(request)
            elapsed = (time.monotonic() - t0) * 1000
            log.debug(
                "Request %s (%s) completed in %.1fms",
                request.get("id", "?")[:8],
                request.get("type", "?"),
                elapsed,
            )
            sys.stdout.write(json.dumps(_camelize(response)) + "\n")
            sys.stdout.flush()
        except Exception as exc:
            log.exception("Unhandled exception processing request")
            req_id = "unknown"
            if isinstance(request, dict):
                req_id = request.get("id", req_id)
            error_resp = asdict(ErrorResponse(id=req_id, error=str(exc)))
            sys.stdout.write(json.dumps(_camelize(error_resp)) + "\n")
            sys.stdout.flush()


# ---------------------------------------------------------------------------
# Request routing
# ---------------------------------------------------------------------------


def handle_request(request: dict) -> dict:
    """Route request to the appropriate handler based on the `type` field."""
    req_type = request.get("type")
    req_id = request.get("id", "unknown")
    log.debug("Handling request id=%s type=%s", req_id[:8], req_type)

    if req_type == "ping":
        return asdict(PongResponse(id=req_id))

    if req_type == "chat":
        return _handle_chat(req_id, request.get("message", ""), request.get("images"), request.get("stlBase64"))

    if req_type == "update_parameters":
        return _handle_update_parameters(req_id, request.get("scadCode", ""))

    if req_type == "save_session":
        return _handle_save_session(req_id)

    if req_type == "load_session":
        return _handle_load_session(req_id, request.get("sessionData", {}))

    if req_type == "check_compatibility":
        return _handle_check_compatibility(req_id, request.get("stlBase64", ""))

    if req_type == "get_capabilities":
        return _handle_get_capabilities(req_id)

    if req_type == "export_step":
        return _handle_export_step(req_id, request.get("stlBase64", ""), request.get("outputPath", ""))

    if req_type == "export_fcstd":
        return _handle_export_fcstd(req_id, request.get("stlBase64", ""), request.get("outputPath", ""))

    if req_type == "import_file":
        return _handle_import_file(req_id, request.get("filePath", ""))

    if req_type == "live_sync":
        return _handle_live_sync(req_id, request.get("stlBase64", ""), request.get("action", "push"))

    if req_type == "set_api_key":
        return _handle_set_api_key(req_id, request.get("apiKey", ""))

    return asdict(ErrorResponse(id=req_id, error=f"Unknown request type: {req_type}"))


# ---------------------------------------------------------------------------
# Chat pipeline with error-recovery loop
# ---------------------------------------------------------------------------


def _handle_chat(req_id: str, user_message: str, images: list[str] | None = None, stl_base64: str | None = None) -> dict:
    """Full chat pipeline: Claude -> OpenSCAD compile -> optional retry.

    Flow:
      1. User message (+ optional images) -> Claude generates .scad
      2. OpenSCAD compiles .scad -> STL
      3. If compile fails -> feed error back to Claude for ONE retry
      4. If retry fails  -> return ChatErrorResponse
      5. If success      -> return ChatResponse with base64 STL
    """
    # Record the user message in the session.
    _session.add_user_message(user_message)
    log.info("Chat request: %d chars, %d images, stl=%s, %d conversation msgs",
             len(user_message), len(images or []), "yes" if stl_base64 else "no", len(_session.conversation))

    # --- Build model context from current STL (if any) --------------------
    model_context: str | None = None
    if stl_base64:
        try:
            analysis = freecad_service.analyze_mesh(stl_base64)
            result_dict = analysis.to_dict()
            lines = [f"Overall: {analysis.overall}"]
            for check in result_dict["checks"]:
                status = "PASS" if check["passed"] else check["severity"].upper()
                lines.append(f"  [{status}] {check['name']}: {check['message']}")
            stats = result_dict["stats"]
            lines.append(f"  Mesh stats: {stats.get('vertices', '?')} vertices, {stats.get('faces', '?')} faces")
            if "volume" in stats:
                lines.append(f"  Volume: {stats['volume']} cubic units")
            if "boundingBox" in stats:
                lines.append(f"  Bounding box: {stats['boundingBox']}")
            model_context = "\n".join(lines)
            log.debug("Model context: %d chars, overall=%s", len(model_context), analysis.overall)
        except Exception as exc:
            log.warning("Failed to analyze mesh for context: %s", exc)

    # --- First attempt ---------------------------------------------------
    conversation, current_scad = _session.get_context_for_claude()
    log.debug("Context: %d messages, scad=%s, model_context=%s",
              len(conversation), "yes" if current_scad else "no", "yes" if model_context else "no")

    try:
        t0 = time.monotonic()
        result = call_claude(conversation, current_scad, images=images, model_context=model_context)
        log.info("Claude responded in %.1fs, scad=%s, text=%d chars",
                 time.monotonic() - t0, "yes" if result.scad_code else "no", len(result.text))
    except Exception as exc:
        log.error("Claude API call failed: %s", exc, exc_info=True)
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
    log.debug("Compiling first attempt (%d chars of scad)", len(result.scad_code))
    compile_result = compile_scad(result.scad_code)
    log.debug("First compile: success=%s", compile_result.success)

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
# FreeCAD integration handlers (Phase 3)
# ---------------------------------------------------------------------------


def _handle_check_compatibility(req_id: str, stl_base64: str) -> dict:
    """Run mesh compatibility checks via trimesh."""
    if not stl_base64:
        return asdict(ErrorResponse(id=req_id, error="No STL data provided"))
    result = freecad_service.analyze_mesh(stl_base64)
    return asdict(CompatibilityResponse(
        id=req_id,
        checks=result.to_dict()["checks"],
        stats=result.to_dict()["stats"],
        overall=result.overall,
    ))


def _handle_get_capabilities(req_id: str) -> dict:
    """Report available capabilities."""
    caps = freecad_service.get_capabilities()
    return asdict(CapabilitiesResponse(id=req_id, capabilities=caps.to_dict()))


def _handle_export_step(req_id: str, stl_base64: str, output_path: str) -> dict:
    """Export current model as STEP file."""
    if not stl_base64:
        return asdict(ErrorResponse(id=req_id, error="No STL data provided"))
    result = freecad_service.export_step(stl_base64, output_path)
    return asdict(ExportResponse(
        id=req_id,
        success=result.success,
        output_path=result.output_path,
        error=result.error,
    ))


def _handle_export_fcstd(req_id: str, stl_base64: str, output_path: str) -> dict:
    """Export current model as FreeCAD document."""
    if not stl_base64:
        return asdict(ErrorResponse(id=req_id, error="No STL data provided"))
    result = freecad_service.export_fcstd(stl_base64, output_path)
    return asdict(ExportResponse(
        id=req_id,
        success=result.success,
        output_path=result.output_path,
        error=result.error,
    ))


def _handle_import_file(req_id: str, file_path: str) -> dict:
    """Import a CAD file."""
    if not file_path:
        return asdict(ErrorResponse(id=req_id, error="No file path provided"))
    result = freecad_service.import_file(file_path)
    d = result.to_dict()

    # Store imported scad code in session so Claude can see/modify it
    if d.get("scadCode"):
        _session.current_scad = d["scadCode"]
        log.info("Imported %s — set current_scad (%d chars)", d["fileType"], len(d["scadCode"]))

    return asdict(ImportResponse(
        id=req_id,
        success=d["success"],
        file_type=d["fileType"],
        scad_code=d.get("scadCode"),
        stl_base64=d.get("stlBase64"),
        metadata=d.get("metadata", {}),
        error=d.get("error"),
    ))


def _handle_live_sync(req_id: str, stl_base64: str, action: str) -> dict:
    """Push model to running FreeCAD instance or check connection."""
    if action == "check":
        connected = freecad_service.check_freecad_running()
        return asdict(LiveSyncResponse(id=req_id, success=True, connected=connected))
    if not stl_base64:
        return asdict(ErrorResponse(id=req_id, error="No STL data provided"))
    result = freecad_service.live_sync_push(stl_base64)
    return asdict(LiveSyncResponse(
        id=req_id,
        success=result.success,
        connected=result.success,
        error=result.error,
    ))


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------


def _handle_set_api_key(req_id: str, api_key: str) -> dict:
    """Set and optionally validate the Anthropic API key."""
    if not api_key:
        set_api_key("")
        return asdict(SetApiKeyResponse(id=req_id, success=True))

    error = validate_api_key(api_key)
    if error:
        log.error("API key validation failed: %s", error)
        return asdict(SetApiKeyResponse(id=req_id, success=False, error=error))

    set_api_key(api_key)
    log.info("API key set successfully")
    return asdict(SetApiKeyResponse(id=req_id, success=True))


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
