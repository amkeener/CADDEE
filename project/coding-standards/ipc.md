# IPC Protocol Coding Standards

Applies to: `shared/messages.py`, `shared/messages.ts`, `electron/src/main/ipc-handlers.ts`, `electron/src/preload/index.ts`, `sidecar/caddee/main.py`

## Protocol

- **Transport:** stdio (JSON lines over stdin/stdout)
- **Format:** One JSON object per line, newline-delimited
- **Direction:** Electron main process ↔ Python sidecar (renderer never talks to sidecar directly)

## Message Structure

Every message (request and response) must have:
- **`id`**: `string` — unique per request, use `crypto.randomUUID()` on the Electron side
- **`type`**: `string` — discriminator field for routing

```
Request:  { id: "uuid", type: "chat", message: "..." }
Response: { id: "uuid", type: "chat_response", message: "...", scadCode: "...", stlBase64: "..." }
```

## Dual Definitions — Keep in Sync

Message types are defined in **two files** that must stay in sync:

| Language | File | Format |
|----------|------|--------|
| Python | `shared/messages.py` | `@dataclass` with `Literal["type"]` field |
| TypeScript | `shared/messages.ts` | `interface` with literal `type` field |

When adding a new message type:
1. Add the `@dataclass` in `messages.py`
2. Add it to the `SidecarRequest` or `SidecarResponse` union
3. Add the `interface` in `messages.ts`
4. Add it to the corresponding union type
5. Add the handler in `sidecar/caddee/main.py` `handle_request()`
6. Wire up through `electron/src/preload/index.ts` if needed from renderer

## Naming Conventions

| Concept | Python (`messages.py`) | TypeScript (`messages.ts`) |
|---------|----------------------|---------------------------|
| Field names | `snake_case` | `camelCase` |
| Type name | `PascalCase` | `PascalCase` |
| Type discriminator | `type: Literal["snake_type"]` | `type: 'snake_type'` |
| Union type | `SidecarRequest = A \| B \| C` | `type SidecarRequest = A \| B \| C` |

**Note:** The `type` discriminator values use `snake_case` in both languages (e.g., `"chat_response"`, `"export_step"`). Field names differ: Python uses `snake_case`, TypeScript uses `camelCase`. The sidecar reads raw JSON keys from Electron (camelCase), so handlers in `main.py` use `request.get("camelCaseKey")`.

## Binary Data

- STL files are passed as **base64-encoded strings** in the `stlBase64` / `stl_base64` field
- Encode: `base64.b64encode(data).decode("ascii")` (Python)
- Decode: `atob(base64String)` → `Uint8Array` (TypeScript)

## Error Responses

- Generic errors: `ErrorResponse` with `type: "error"`
- Domain-specific errors: e.g., `ChatErrorResponse` with `type: "chat_error"` and optional `compile_error`
- Services never raise — they return error result dataclasses that get serialized to JSON

## Adding a New Feature (Checklist)

- [ ] Define request dataclass/interface in both `shared/messages.py` and `shared/messages.ts`
- [ ] Define response dataclass/interface in both files
- [ ] Add to union types (`SidecarRequest`, `SidecarResponse`) in both files
- [ ] Add handler function `_handle_<type>()` in `sidecar/caddee/main.py`
- [ ] Add routing case in `handle_request()` in `main.py`
- [ ] If renderer needs access: add method to preload bridge and `CaddeeAPI` type
- [ ] If renderer needs access: add IPC handler in `electron/src/main/ipc-handlers.ts`
