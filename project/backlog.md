# CADDEE Backlog

## Architecture Decisions
- **OpenSCAD**: CLI (shell out to binary) for Phase 1
- **IPC**: stdio (JSON over stdin/stdout) for Phase 1
- **Structure**: Monorepo (electron/, sidecar/, shared/)
- **Error recovery**: 1 auto-retry on OpenSCAD compile failure; configurable iterations later
- **FreeCAD**: Target 1.0+ (any 1.x release)

## FreeCAD Version Guide
CADDEE targets **FreeCAD 1.0+** (any 1.x release). The Python API surface (`FreeCAD`, `Part`, `Mesh` modules) is stable across 1.x.

**Install (macOS):** `brew install --cask freecad`

FreeCAD is only needed starting in Phase 3. Key APIs used:
- `FreeCAD.newDocument()` / `FreeCAD.openDocument()` — headless document ops
- `Part.Shape` / `Part.read()` — STEP/BREP import/export
- `Mesh.Mesh` — STL import, mesh analysis (non-manifold, open shells)
- `importSVG`, `importDXF` — 2D import (future)

Socket connection for live sync uses FreeCAD's built-in Python interpreter.

---

## Phase 1 — Core Loop (MVP)
> Text -> Claude -> .scad -> OpenSCAD CLI -> STL -> Three.js viewer

**Status:** Done

### Features
- [x] Python sidecar with Claude API integration (Anthropic SDK)
- [x] OpenSCAD code generation via system prompt + conversation context
- [x] OpenSCAD CLI compilation (.scad -> STL)
- [x] Error recovery: feed compile errors back to Claude (1 retry)
- [x] Electron shell with single-window layout
- [x] Three.js viewport rendering STL output (OrbitControls)
- [x] Hot-swap STL on each iteration
- [x] Basic chat console (text input, conversation display)
- [x] IPC bridge: Electron <-> Python sidecar via stdio (JSON)
- [x] Color-coded render feedback (grey = stable, yellow = in-progress)

### Out of Scope for Phase 1
- Tools panel
- Parameter sliders
- Session save/restore
- FreeCAD integration
- Image/sketch input

---

## Phase 2 — Full UI
> Three-pane Electron shell with full feature set

**Status:** Done

### Features
- [x] Three-pane layout (viewport, chat, tools panel)
- [x] Chat history with conversation threading
- [x] Parameter sliders auto-generated from OpenSCAD `/* [Section] */` customizer syntax
- [x] Iteration history with thumbnails (click to restore)
- [x] Session save/restore (.cad-session files)
- [x] Export: STL, .scad download
- [x] Resizable panes

---

## Phase 3 — FreeCAD Integration
> Headless checks, STEP export, live sync, import wizard

**Status:** Done

**Requires:** FreeCAD 1.0+ installed separately

### Features
- [x] Headless compatibility checks (non-manifold, self-intersecting, open shells, thin walls)
- [x] STEP export via FreeCAD/CadQuery conversion pipeline
- [x] Live sync: push .step to open FreeCAD instance via socket
- [x] Import wizard: load .FCStd, .step, .stl, .scad files as starting points
- [x] Compatibility results surfaced in Tools panel with plain-English explanations
- [x] Export to .FCStd format

---

## Phase 4 — Image Input
> Sketch/photo upload -> Claude vision -> .scad starting point

**Status:** Done

### Features
- [x] Image/sketch upload in chat console (paperclip button, drag-and-drop, clipboard paste)
- [x] Claude vision (multimodal) extracts dimensional intent
- [x] Generates initial .scad as conversation starting point
- [x] Support for photos of physical objects, hand-drawn sketches, technical drawings
- [x] Image thumbnails shown in chat message bubbles
- [x] Up to 5 images per message, with preview strip and remove buttons

---

## Chores

- [x] **CADDEE ADW Experts**: Created all three domain experts — caddee-electron, caddee-sidecar, caddee-ipc. Each references coding standards and is registered in the orchestrator's verified_experts list.
- [x] **README.md**: Project README with architecture overview, setup instructions, and dev workflow.
- [x] **Coding Standards**: Created language-specific standards (TypeScript, Python, IPC) in `project/coding-standards/`. Enforced during `/build_adw` (step 5.1) and `/code_review_adw` (step 5.1) via expert `coding_standards` field.

---

## Future Work / Backlog
> Items identified during planning for future consideration

- [ ] **WASM OpenSCAD**: Replace CLI with openscad-wasm for in-browser compilation (no external dependency). Reference: github.com/DSchroer/openscad-wasm
- [ ] **WebSocket IPC**: Migrate from stdio to WebSocket for reconnection support and independent sidecar lifecycle
- [ ] **HTTP/FastAPI IPC**: Full HTTP API for sidecar, enabling independent development/testing and potential remote sidecar
- [ ] **Configurable retry count**: Allow N retries on OpenSCAD compile failure (programmatic or user-set based on task complexity)
- [ ] **CadQuery as alternative backend**: Python-native CAD scripting, more concise for complex objects, better STEP I/O
- [ ] **OpenSCAD MCP server integration**: Connect to existing MCP servers for validation/best-practice checks
- [ ] **Multi-LLM parallel generation**: Run multiple models and present best outputs (DesignBench pattern)
- [ ] **RAG for OpenSCAD examples**: Example retrieval to improve generation quality for complex geometries
- [ ] **OAuth auth mode**: Browser-based OAuth login with Anthropic account instead of requiring API key. Sidecar detects missing `ANTHROPIC_API_KEY`, launches OAuth flow, stores tokens in `~/.caddee/auth.json`, uses them for API calls. Enables users to use their Claude subscription directly.
