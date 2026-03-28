/**
 * IPC message types shared between Electron and Python sidecar.
 * Mirrored in shared/messages.py — keep in sync.
 */

// --- Requests (Electron -> Sidecar) ---

export interface ChatRequest {
  id: string
  type: 'chat'
  message: string
  images?: string[]  // base64-encoded images (Phase 4)
}

export interface PingRequest {
  id: string
  type: 'ping'
}

export type SidecarRequest = ChatRequest | PingRequest

// --- Responses (Sidecar -> Electron) ---

export interface ChatResponse {
  id: string
  type: 'chat_response'
  message: string        // Claude's text response
  scadCode: string       // Generated .scad source
  stlBase64: string      // Compiled STL as base64
  wasRetry: boolean      // True if error recovery was triggered
}

export interface ChatErrorResponse {
  id: string
  type: 'chat_error'
  error: string          // Error message for the user
  compileError?: string  // Raw OpenSCAD error (if compile failed after retry)
}

export interface PongResponse {
  id: string
  type: 'pong'
  message: string
}

export interface ErrorResponse {
  id: string
  type: 'error'
  error: string
}

export type SidecarResponse = ChatResponse | ChatErrorResponse | PongResponse | ErrorResponse

// --- Shared Types ---

export interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface DesignIteration {
  prompt: string
  scadCode: string
  stlBase64: string
  timestamp: number
}
