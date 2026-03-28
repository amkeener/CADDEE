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

export interface UpdateParametersRequest {
  id: string
  type: 'update_parameters'
  scadCode: string
}

export interface SaveSessionRequest {
  id: string
  type: 'save_session'
}

export interface LoadSessionRequest {
  id: string
  type: 'load_session'
  sessionData: Record<string, unknown>
}

export interface CompatibilityCheckRequest {
  id: string
  type: 'check_compatibility'
  stlBase64: string
}

export interface ExportStepRequest {
  id: string
  type: 'export_step'
  stlBase64: string
  outputPath: string
}

export interface ExportFcstdRequest {
  id: string
  type: 'export_fcstd'
  stlBase64: string
  outputPath: string
}

export interface ImportFileRequest {
  id: string
  type: 'import_file'
  filePath: string
}

export interface LiveSyncRequest {
  id: string
  type: 'live_sync'
  stlBase64: string
  action: 'push' | 'check'
}

export interface CapabilitiesRequest {
  id: string
  type: 'get_capabilities'
}

export type SidecarRequest =
  | ChatRequest
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

export interface ParameterResponse {
  id: string
  type: 'parameter_response'
  stlBase64: string
  scadCode: string
}

export interface SessionDataResponse {
  id: string
  type: 'session_data'
  sessionData: Record<string, unknown>
}

export interface SessionLoadedResponse {
  id: string
  type: 'session_loaded'
  message: string
}

export interface CompatibilityCheck {
  name: string
  passed: boolean
  severity: 'info' | 'warning' | 'error'
  message: string
}

export interface CompatibilityResponse {
  id: string
  type: 'compatibility_result'
  checks: CompatibilityCheck[]
  stats: Record<string, number | string>
  overall: 'pass' | 'warning' | 'fail' | 'unknown'
}

export interface ExportResultResponse {
  id: string
  type: 'export_result'
  success: boolean
  outputPath?: string
  error?: string
}

export interface ImportResultResponse {
  id: string
  type: 'import_result'
  success: boolean
  fileType: 'stl' | 'scad' | 'step' | 'fcstd' | 'unknown'
  scadCode?: string
  stlBase64?: string
  metadata: Record<string, unknown>
  error?: string
}

export interface LiveSyncResponse {
  id: string
  type: 'live_sync_result'
  success: boolean
  connected: boolean
  error?: string
}

export interface CapabilitiesResponse {
  id: string
  type: 'capabilities'
  capabilities: {
    trimeshAvailable: boolean
    freecadAvailable: boolean
    meshAnalysis: boolean
    stepExport: boolean
    fcstdExport: boolean
    liveSync: boolean
  }
}

export type SidecarResponse =
  | ChatResponse
  | ChatErrorResponse
  | PongResponse
  | ErrorResponse
  | ParameterResponse
  | SessionDataResponse
  | SessionLoadedResponse
  | CompatibilityResponse
  | ExportResultResponse
  | ImportResultResponse
  | LiveSyncResponse
  | CapabilitiesResponse

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
