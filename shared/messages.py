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


SidecarRequest = ChatRequest | PingRequest


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


SidecarResponse = ChatResponse | ChatErrorResponse | PongResponse | ErrorResponse


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
