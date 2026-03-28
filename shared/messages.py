"""
IPC message types shared between Electron and Python sidecar.
Mirrored in shared/messages.ts — keep in sync.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# --- Requests (Electron -> Sidecar) ---


@dataclass
class ChatRequest:
    id: str
    type: Literal["chat"] = "chat"
    message: str = ""
    images: list[str] = field(default_factory=list)  # base64-encoded (Phase 4)


@dataclass
class PingRequest:
    id: str
    type: Literal["ping"] = "ping"


@dataclass
class UpdateParametersRequest:
    id: str
    scad_code: str
    type: Literal["update_parameters"] = "update_parameters"


@dataclass
class SaveSessionRequest:
    id: str
    type: Literal["save_session"] = "save_session"


@dataclass
class LoadSessionRequest:
    id: str
    session_data: dict = field(default_factory=dict)
    type: Literal["load_session"] = "load_session"


@dataclass
class CompatibilityCheckRequest:
    id: str
    stl_base64: str = ""
    type: Literal["check_compatibility"] = "check_compatibility"


@dataclass
class ExportStepRequest:
    id: str
    stl_base64: str = ""
    output_path: str = ""
    type: Literal["export_step"] = "export_step"


@dataclass
class ExportFcstdRequest:
    id: str
    stl_base64: str = ""
    output_path: str = ""
    type: Literal["export_fcstd"] = "export_fcstd"


@dataclass
class ImportFileRequest:
    id: str
    file_path: str = ""
    type: Literal["import_file"] = "import_file"


@dataclass
class LiveSyncRequest:
    id: str
    stl_base64: str = ""
    action: Literal["push", "check"] = "push"
    type: Literal["live_sync"] = "live_sync"


@dataclass
class CapabilitiesRequest:
    id: str
    type: Literal["get_capabilities"] = "get_capabilities"


SidecarRequest = (
    ChatRequest
    | PingRequest
    | UpdateParametersRequest
    | SaveSessionRequest
    | LoadSessionRequest
    | CompatibilityCheckRequest
    | ExportStepRequest
    | ExportFcstdRequest
    | ImportFileRequest
    | LiveSyncRequest
    | CapabilitiesRequest
)


# --- Responses (Sidecar -> Electron) ---


@dataclass
class ChatResponse:
    id: str
    message: str
    scad_code: str
    stl_base64: str
    was_retry: bool = False
    type: Literal["chat_response"] = "chat_response"


@dataclass
class ChatErrorResponse:
    id: str
    error: str
    compile_error: str | None = None
    type: Literal["chat_error"] = "chat_error"


@dataclass
class PongResponse:
    id: str
    message: str = "sidecar is running"
    type: Literal["pong"] = "pong"


@dataclass
class ErrorResponse:
    id: str
    error: str
    type: Literal["error"] = "error"


@dataclass
class ParameterResponse:
    id: str
    stl_base64: str
    scad_code: str
    type: Literal["parameter_response"] = "parameter_response"


@dataclass
class SessionDataResponse:
    id: str
    session_data: dict = field(default_factory=dict)
    type: Literal["session_data"] = "session_data"


@dataclass
class SessionLoadedResponse:
    id: str
    message: str = "Session loaded"
    type: Literal["session_loaded"] = "session_loaded"


@dataclass
class CompatibilityResponse:
    id: str
    checks: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    overall: str = "unknown"
    type: Literal["compatibility_result"] = "compatibility_result"


@dataclass
class ExportResponse:
    id: str
    success: bool = False
    output_path: str | None = None
    error: str | None = None
    type: Literal["export_result"] = "export_result"


@dataclass
class ImportResponse:
    id: str
    success: bool = False
    file_type: str = "unknown"
    scad_code: str | None = None
    stl_base64: str | None = None
    metadata: dict = field(default_factory=dict)
    error: str | None = None
    type: Literal["import_result"] = "import_result"


@dataclass
class LiveSyncResponse:
    id: str
    success: bool = False
    connected: bool = False
    error: str | None = None
    type: Literal["live_sync_result"] = "live_sync_result"


@dataclass
class CapabilitiesResponse:
    id: str
    capabilities: dict = field(default_factory=dict)
    type: Literal["capabilities"] = "capabilities"


SidecarResponse = (
    ChatResponse
    | ChatErrorResponse
    | PongResponse
    | ErrorResponse
    | ParameterResponse
    | SessionDataResponse
    | SessionLoadedResponse
    | CompatibilityResponse
    | ExportResponse
    | ImportResponse
    | LiveSyncResponse
    | CapabilitiesResponse
)


# --- Shared Types ---


@dataclass
class ConversationMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class DesignIteration:
    prompt: str
    scad_code: str
    stl_base64: str
    timestamp: float
