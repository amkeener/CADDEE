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

**Status:** Not Started

### Features
- [ ] Python sidecar with Claude API integration (Anthropic SDK)
- [ ] OpenSCAD code generation via system prompt + conversation context
- [ ] OpenSCAD CLI compilation (.scad -> STL)
- [ ] Error recovery: feed compile errors back to Claude (1 retry)
- [ ] Electron shell with single-window layout
- [ ] Three.js viewport rendering STL output (OrbitControls)
- [ ] Hot-swap STL on each iteration
- [ ] Basic chat console (text input, conversation display)
- [ ] IPC bridge: Electron <-> Python sidecar via stdio (JSON)
- [ ] Color-coded render feedback (grey = stable, yellow = in-progress)

### Out of Scope for Phase 1
- Tools panel
- Parameter sliders
- Session save/restore
- FreeCAD integration
- Image/sketch input

---

## Phase 2 — Full UI
> Three-pane Electron shell with full feature set

**Status:** Not Started

### Features
- [ ] Three-pane layout (viewport, chat, tools panel)
- [ ] Chat history with conversation threading
- [ ] Parameter sliders auto-generated from OpenSCAD `/* [Section] */` customizer syntax
- [ ] Iteration history with thumbnails (click to restore)
- [ ] Session save/restore (.cad-session files)
- [ ] Export: STL, .scad download
- [ ] Resizable panes

---

## Phase 3 — FreeCAD Integration
> Headless checks, STEP export, live sync, import wizard

**Status:** Not Started

**Requires:** FreeCAD 1.0+ installed separately

### Features
- [ ] Headless compatibility checks (non-manifold, self-intersecting, open shells, thin walls)
- [ ] STEP export via FreeCAD/CadQuery conversion pipeline
- [ ] Live sync: push .step to open FreeCAD instance via socket
- [ ] Import wizard: load .FCStd, .step, .stl, .scad files as starting points
- [ ] Compatibility results surfaced in Tools panel with plain-English explanations
- [ ] Export to .FCStd format

---

## Phase 4 — Image Input
> Sketch/photo upload -> Claude vision -> .scad starting point

**Status:** Not Started

### Features
- [ ] Image/sketch upload in chat console
- [ ] Claude vision (multimodal) extracts dimensional intent
- [ ] Generates initial .scad as conversation starting point
- [ ] Support for photos of physical objects, hand-drawn sketches, technical drawings

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
