---
status: done
type: feature
complexity: moderate
adw_session: adw-plan-20260328-byok
expert: caddee-ipc (primary), caddee-electron, caddee-sidecar
---

# Plan: In-App API Key Setup (BYOK)

## Task Description
Add a settings UI for entering/storing an Anthropic API key securely, eliminating the need for shell env vars. Users paste their key, it's validated against the API, stored encrypted via Electron safeStorage, and sent to the sidecar at startup.

## Expert Context
- **caddee-ipc**: New `set_api_key` message type, dual-language sync
- **caddee-electron**: Settings modal, safeStorage integration, startup flow
- **caddee-sidecar**: Receive key via IPC, pass to Anthropic SDK

## Objective
Replace the `export ANTHROPIC_API_KEY` shell requirement with an in-app settings flow. Env var still works as a fallback.

## Relevant Files

### To Read (for context)
- `project/coding-standards/typescript.md`
- `project/coding-standards/python.md`
- `project/coding-standards/ipc.md`

### To Modify
- `shared/messages.py` — add SetApiKeyRequest/Response
- `shared/messages.ts` — add matching TS types
- `sidecar/caddee/services/claude_service.py` — accept api_key param
- `sidecar/caddee/main.py` — add set_api_key handler
- `electron/src/main/index.ts` — credential loading at startup, send key to sidecar
- `electron/src/main/sidecar.ts` — expose sendApiKey() convenience method
- `electron/src/main/ipc-handlers.ts` — add api-key IPC handlers
- `electron/src/preload/index.ts` — expose api key methods to renderer
- `electron/src/renderer/App.tsx` — modal state, startup check
- `electron/src/renderer/components/ToolsPanel.tsx` — gear icon

### To Create
- `electron/src/main/credentials.ts` — safeStorage credential store
- `electron/src/renderer/components/ApiKeyModal.tsx` — settings modal

## Implementation Phases

### Phase 1: IPC + Sidecar (backend)
Add the `set_api_key` message type and sidecar handling so the key can be injected at runtime.

### Phase 2: Electron Main Process (credential storage)
Add encrypted credential storage and startup key-loading logic.

### Phase 3: UI (settings modal + integration)
Build the modal, wire it into the app, add gear icon to ToolsPanel.

## Step by Step Tasks

### Step 1: Add IPC message types
Add `SetApiKeyRequest` and `SetApiKeyResponse` to both `shared/messages.py` and `shared/messages.ts`.

**messages.py:**
```python
@dataclass
class SetApiKeyRequest:
    id: str
    api_key: str = ""
    type: Literal["set_api_key"] = "set_api_key"

@dataclass
class SetApiKeyResponse:
    id: str
    success: bool = False
    error: str | None = None
    type: Literal["api_key_set"] = "api_key_set"
```

**messages.ts:**
```typescript
export interface SetApiKeyRequest {
  id: string
  type: 'set_api_key'
  apiKey: string
}

export interface SetApiKeyResponse {
  id: string
  type: 'api_key_set'
  success: boolean
  error?: string
}
```

Add to union types in both files.

### Step 2: Sidecar API key handling
- Add `_api_key: str | None = None` module-level in `claude_service.py`
- Add `set_api_key(key: str)` function that sets the module-level var
- Modify `call_claude()`: pass `api_key=_api_key` to `anthropic.Anthropic(api_key=_api_key)` — the SDK uses env var when api_key is None
- Add `_handle_set_api_key()` in `main.py`:
  - Calls `set_api_key(key)`
  - Does a lightweight validation: `anthropic.Anthropic(api_key=key).messages.create(model="claude-haiku-4-5-20251001", max_tokens=1, messages=[{"role":"user","content":"hi"}])`
  - Returns `SetApiKeyResponse(success=True)` or error

### Step 3: Create credentials module
New file `electron/src/main/credentials.ts`:
- Uses `safeStorage.encryptString()` / `safeStorage.decryptString()`
- Stores encrypted key at `~/.caddee/credentials`
- Exports: `saveApiKey(key)`, `loadApiKey() -> string | null`, `clearApiKey()`, `hasApiKey() -> boolean`
- Creates `~/.caddee/` directory if needed

### Step 4: Electron main process startup flow
Modify `electron/src/main/index.ts`:
- After sidecar starts, check for API key:
  1. `process.env.ANTHROPIC_API_KEY` — if set, send to sidecar via `set_api_key`
  2. Else `loadApiKey()` from credentials — if found, send to sidecar
  3. Else — send `api-key:missing` event to renderer after window loads
- Add IPC handler for `api-key:status` so renderer can check on demand

### Step 5: Add IPC handlers for API key management
In `electron/src/main/ipc-handlers.ts`:
- `api-key:save` — validate via sidecar `set_api_key`, if success store with `saveApiKey()`
- `api-key:status` — return `{ configured: boolean, source: 'env' | 'stored' | 'none' }`
- `api-key:clear` — call `clearApiKey()`, send empty `set_api_key` to sidecar

### Step 6: Update preload bridge
In `electron/src/preload/index.ts`:
- `getApiKeyStatus()` — invoke `api-key:status`
- `saveApiKey(key: string)` — invoke `api-key:save`
- `clearApiKey()` — invoke `api-key:clear`
- `onApiKeyMissing(callback)` — listen for `api-key:missing` event

Update `CaddeeAPI` type.

### Step 7: Build ApiKeyModal component
New file `electron/src/renderer/components/ApiKeyModal.tsx`:
- Overlay modal with dark theme matching existing UI
- Masked text input for API key (with show/hide toggle)
- "Get API Key" link button → opens `https://console.anthropic.com/settings/keys` in external browser
- Save button — calls `window.caddee.saveApiKey(key)`, shows success/error
- Clear button — calls `window.caddee.clearApiKey()`
- Close button (only if key already configured)
- Status indicator: key source (env var / stored / none)

### Step 8: Integrate into App.tsx and ToolsPanel
- App.tsx:
  - Add `apiKeyConfigured` state (boolean)
  - Add `showApiKeyModal` state
  - On mount: check `window.caddee.getApiKeyStatus()`
  - Listen for `onApiKeyMissing` → show modal
  - Pass `onOpenSettings` callback to ToolsPanel
- ToolsPanel.tsx:
  - Add gear icon button in header
  - Accept `onOpenSettings` prop, wire to click handler

## Testing Strategy
1. **No env var, no stored key** → modal shows on startup
2. **Enter valid key** → sidecar validates, stores, modal closes, chat works
3. **Enter invalid key** → error message shown, not stored
4. **Env var set** → key used from env, no modal, status shows "env"
5. **Clear stored key** → next launch shows modal
6. **Gear icon** → opens modal with current status

## Acceptance Criteria
- [ ] App launches and works without `ANTHROPIC_API_KEY` env var
- [ ] API key input modal appears on first launch (no key configured)
- [ ] Key is validated against Anthropic API before storing
- [ ] Key is encrypted via safeStorage and stored at `~/.caddee/credentials`
- [ ] Env var takes precedence over stored key
- [ ] Gear icon in ToolsPanel opens settings modal
- [ ] Clear button removes stored key
- [ ] Sidecar receives key via IPC and uses it for Claude calls

## Validation Commands
- `cd electron && npx tsc --noEmit`
- `cd sidecar && uv run python -m py_compile caddee/main.py`
- `cd sidecar && uv run python -m py_compile caddee/services/claude_service.py`
- `cd sidecar && echo '{"id":"1","type":"ping"}' | uv run python -m caddee.main 2>/dev/null`
