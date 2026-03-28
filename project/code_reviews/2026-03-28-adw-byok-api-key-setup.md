## Summary
Adds in-app API key setup (BYOK) — settings modal for entering/storing an Anthropic API key via Electron safeStorage, eliminating the shell env var requirement. New IPC message type `set_api_key`, credential storage module, startup flow, and gear icon in ToolsPanel.

## Verdict: REQUEST CHANGES

2 issues found that should be fixed before merge.

## ADW Review Metadata
- Session: adw-review-20260328-byok
- Experts: security_audit, caddee-ipc, caddee-electron, caddee-sidecar
- Scope: 1 commit (b8d993e)

## Static Analysis

| Check | Status | Issues |
|-------|--------|--------|
| TypeScript (`tsc --noEmit`) | PASS | 0 |
| Python (`py_compile`) | PASS | 0 |
| Sidecar ping | PASS | 0 |

## Test Coverage

No test suite configured for this project. Manual testing strategy documented in plan.

## Security Review (security_audit)

### Critical Issues
None

### High Risk
None

### Medium Risk
1. **Credential file permissions** — `credentials.ts:18`: `writeFileSync(CREDENTIALS_PATH, encrypted)` does not set file permissions. On Linux, the default umask could leave `~/.caddee/credentials` world-readable. Should use `{ mode: 0o600 }` to restrict to owner-only. On macOS this is less critical (home dirs are private by default) but still best practice. `[simple]`

### Low Risk
1. **Broad exception in validation** — `claude_service.py:74`: `except Exception as exc: return str(exc)` could expose internal error details. Acceptable for a local desktop app but worth noting.
2. **No rate limiting on key validation** — A user could spam the Save button and trigger many API calls. Low risk since this is local-only UI with a disabled state during save.

## Coding Standards Compliance

| Standard | Files Checked | Violations | Status |
|----------|--------------|------------|--------|
| python.md | 2 (claude_service.py, main.py) | 0 | PASS |
| typescript.md | 6 (credentials.ts, index.ts, ipc-handlers.ts, preload, ApiKeyModal, ToolsPanel) | 1 | WARN |
| ipc.md | 4 (messages.py, messages.ts, main.py, preload) | 0 | PASS |

### Violations
1. `electron/src/main/ipc-handlers.ts:4` — **Unused import**: `loadApiKey` is imported but never used in this file. It's used in `index.ts` instead. **[trivial]** `warning`

## Domain Review (caddee-ipc)

### Validation Commands
All passed (tsc, py_compile, sidecar ping).

### Critical Issues (must fix)
None

### Concerns (should fix)
1. **Unused import** in `ipc-handlers.ts` — remove `loadApiKey` from the import. `[trivial]`
2. **Credential file permissions** — add `{ mode: 0o600 }` to `writeFileSync` in `credentials.ts`. `[simple]`

### Suggestions (nice to have)
None

## Domain Review (caddee-electron)

### Critical Issues
None

### Concerns
None — component follows all patterns: functional component, inline CSS-in-JS, dark theme palette, `useCallback` for handlers, proper state management.

### Architecture Notes
- Startup race between `api-key:missing` event and React `useEffect` registration is handled correctly — `App.tsx` does a proactive `getApiKeyStatus()` check as a fallback.
- Modal correctly prevents close when no key is configured (`canClose` prop).

## Domain Review (caddee-sidecar)

### Critical Issues
None

### Concerns
None — follows service pattern (returns results, doesn't raise), logging to stderr, type hints on public functions, `from __future__ import annotations` present.

## Edge Cases Not Covered
1. What happens if `safeStorage.isEncryptionAvailable()` returns false (e.g., headless Linux without a keyring)? Currently would throw on `encryptString()`.
2. Sidecar restart after key is set — the in-memory `_api_key` is lost. The startup flow in `index.ts` re-sends the key, so this is handled.

## What's Good
1. Clean separation of concerns: credential storage is isolated in its own module, IPC types properly mirrored, sidecar changes are minimal and backwards-compatible.
2. Env var fallback preserved — existing users are unaffected. The precedence logic (env > stored > prompt) is sound.
3. Key validation before storage prevents saving invalid keys.
