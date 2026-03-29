# Python Coding Standards

Applies to: `sidecar/**/*.py`, `shared/*.py`

## Language & Tooling

- **Python** >= 3.11
- **`from __future__ import annotations`** at the top of every file (enables PEP 604 `X | Y` syntax everywhere)
- **Package manager:** `uv` — use `uv add`, `uv lock`, `uv sync`, `uv run`
- **Build backend:** hatchling
- **Type-check:** type hints on all public functions (private `_helper` functions encouraged but not required)

## Data Modeling

- **`dataclasses`** for all structured data — results, messages, configs
- **No Pydantic, no TypedDict, no NamedTuple** for domain types
- Use `field(default_factory=list)` for mutable defaults
- Use `Literal["value"]` for discriminated union fields (e.g., `type: Literal["chat"] = "chat"`)

## Service Pattern

- Services are **stateless modules** with pure functions: take data in, return result dataclass out
- **Services never raise exceptions to callers** — return error result dataclasses instead
- Global state lives in `Session` object in `main.py` — one session per process lifetime
- New services: create `sidecar/caddee/services/{name}.py`, import in `main.py`

## IPC Protocol

- **stdout is reserved for IPC JSON** — never `print()` to stdout
- **Logging goes to stderr** via `logging.basicConfig(stream=sys.stderr, ...)`
- Use `log = logging.getLogger(__name__)` per module
- New request types: add handler in `main.py`, add message type in `shared/messages.py`

## File I/O

- **`pathlib.Path`** for all file operations — no `os.path`
- Temp files: `tempfile.NamedTemporaryFile(delete=False)` when consumed downstream
- Clean up temp files: `Path.unlink(missing_ok=True)`
- Base64 encoding: `base64.b64encode(data).decode("ascii")`

## Naming

- **Files/modules:** snake_case (`claude_service.py`, `session_manager.py`)
- **Classes:** PascalCase (`Session`, `ChatRequest`)
- **Functions:** snake_case (`call_claude`, `compile_scad`)
- **Private functions:** leading underscore (`_handle_chat`, `_read_stl_base64`)
- **Constants:** UPPER_SNAKE_CASE (`_PROJECT_ROOT` for module-level)

## Imports

- Standard library first, then third-party, then local — separated by blank lines
- `from __future__ import annotations` always first
- Prefer explicit imports over wildcard: `from shared.messages import ChatResponse`

## Error Handling

- Top-level `main()` loop catches all exceptions and returns `ErrorResponse`
- Services return error states in result dataclasses (e.g., `success=False, error="msg"`)
- Log errors with `log.error(...)` — include relevant context
- Optional features (FreeCAD): guard imports with availability checks, degrade gracefully

## Dependencies

- **Tier 1** (always required): `anthropic`, `trimesh`, `numpy`
- **Tier 2** (optional, runtime-detected): FreeCAD Python modules
- Add deps via `uv add <package>` — keep `pyproject.toml` and `uv.lock` in sync
- Dev deps go in `[project.optional-dependencies] dev`

## Validation (enforced during build/review)

```bash
cd sidecar && uv run python -m py_compile caddee/main.py
cd sidecar && uv run python -m py_compile caddee/services/claude_service.py
cd sidecar && uv run python -m py_compile caddee/services/openscad_service.py
cd sidecar && uv run python -m py_compile caddee/services/freecad_service.py
cd sidecar && uv run python -m py_compile caddee/services/session_manager.py
```
