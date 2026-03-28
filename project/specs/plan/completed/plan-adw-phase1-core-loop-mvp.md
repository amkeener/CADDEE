---
status: done
type: feature
complexity: major
adw_session: adw-plan-20260328-phase1
expert: pending (CADDEE experts not yet created)
---

# Plan: Phase 1 — Core Loop MVP

## Task Description
Build the core design loop: user types text -> Claude generates OpenSCAD code -> OpenSCAD CLI compiles to STL -> Three.js renders in Electron window. Includes error recovery (1 auto-retry on compile failure). Single window layout, no tools panel.

## Objective
Prove the end-to-end iteration loop works: a user can describe a 3D object in natural language, see it rendered, and refine it through conversation. This is the foundational infrastructure that all subsequent phases build on.

## Architecture

```
┌─────────────────────────────────────────────┐
│           Electron Main Process             │
│  - Spawns Python sidecar (stdio)            │
│  - IPC bridge (main <-> renderer)           │
└──────────────┬──────────────────────────────┘
               │ JSON over stdin/stdout
┌──────────────▼──────────────────────────────┐
│           Python Sidecar                    │
│  - Anthropic SDK (Claude API)               │
│  - OpenSCAD CLI subprocess                  │
│  - Session state (conversation + .scad)     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           Electron Renderer                 │
│  ┌──────────────┐  ┌────────────────────┐   │
│  │  3D Viewport │  │   Chat Console     │   │
│  │  (Three.js)  │  │   (React)          │   │
│  │  STLLoader   │  │   Text input       │   │
│  │  OrbitCtrl   │  │   Message history   │   │
│  └──────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Relevant Files

### To Create
```
electron/
  package.json                    # Electron + React + Three.js deps
  src/
    main/
      index.ts                    # Electron main process
      sidecar.ts                  # Spawn & manage Python sidecar
      ipc-handlers.ts             # IPC bridge (renderer <-> sidecar)
    renderer/
      index.html                  # Entry HTML
      App.tsx                     # Root React component
      components/
        Viewport.tsx              # Three.js STL viewer
        ChatConsole.tsx           # Chat input + message display
        StatusIndicator.tsx       # Render status (grey/yellow/red)
      hooks/
        useChat.ts                # Chat state management
        useSidecar.ts             # Sidecar communication hook
      types/
        messages.ts               # IPC message types
  tsconfig.json
  vite.config.ts                  # Vite for renderer bundling

sidecar/
  pyproject.toml                  # Python deps (anthropic, fastapi for future)
  caddee/
    __init__.py
    main.py                       # Entry point (stdio message loop)
    services/
      __init__.py
      claude_service.py           # Anthropic SDK integration
      openscad_service.py         # OpenSCAD CLI wrapper
      session_manager.py          # Conversation + .scad state
    models/
      __init__.py
      messages.py                 # IPC message dataclasses
    prompts/
      system_prompt.txt           # OpenSCAD system prompt for Claude

shared/
  messages.ts                     # TypeScript IPC message types
  messages.py                     # Python IPC message types (mirrored)
```

## Implementation Phases

### Phase A: Project Scaffolding
Set up monorepo structure, package managers, and dev tooling.

1. **Initialize Electron project** with Vite + React + TypeScript
2. **Initialize Python project** with pyproject.toml (uv or pip)
3. **Define IPC message protocol** in shared/ (TypeScript + Python types)
4. **Verify dev workflow**: `npm run dev` starts Electron + hot reload

### Phase B: Python Sidecar — Core Services
Build the Python backend that does the heavy lifting.

5. **stdio message loop** (`main.py`): Read JSON from stdin, write JSON to stdout. Simple request/response protocol.
6. **Claude service** (`claude_service.py`): Anthropic SDK integration with system prompt. Send conversation history + current .scad, receive updated .scad code.
7. **OpenSCAD service** (`openscad_service.py`): Shell out to `openscad` CLI. Compile .scad -> STL. Capture stdout/stderr for error handling.
8. **Session manager** (`session_manager.py`): Track conversation history and current .scad source. Feed full context to Claude on each turn.
9. **Error recovery loop**: If OpenSCAD fails to compile, automatically feed the error back to Claude for one retry before surfacing to user.

### Phase C: Electron Shell + IPC Bridge
Connect the Electron frontend to the Python backend.

10. **Sidecar manager** (`sidecar.ts`): Spawn Python process, handle stdio streams, parse JSON messages, manage lifecycle (start/stop/restart).
11. **IPC handlers** (`ipc-handlers.ts`): Bridge between renderer (via Electron IPC) and sidecar (via stdio). Route messages bidirectionally.
12. **Verify round-trip**: Send a test message from renderer -> main -> sidecar -> main -> renderer.

### Phase D: Three.js Viewport
Render STL files in the browser.

13. **STL viewer component** (`Viewport.tsx`): Three.js scene with STLLoader, PerspectiveCamera, OrbitControls, ambient + directional lighting.
14. **Hot-swap STL**: When new STL data arrives, dispose old mesh, load new one, auto-fit camera.
15. **Color feedback**: Grey material for stable render, yellow while compilation is in progress.

### Phase E: Chat Console
Build the conversation UI.

16. **Chat component** (`ChatConsole.tsx`): Text input, message history (user/assistant bubbles), auto-scroll.
17. **Wire to sidecar**: Send user message -> receive Claude response + STL update -> display both.
18. **Status indicators**: Show "thinking...", "compiling...", "render error" states.

### Phase F: Integration & Polish

19. **End-to-end flow**: Type "make a cube" -> see a cube rendered. Refine: "make it a rounded cube" -> see updated render.
20. **Error UX**: If compile fails after retry, show error message in chat with Claude's explanation.
21. **OpenSCAD system prompt tuning**: Craft the system prompt that instructs Claude on OpenSCAD best practices, output format, and error handling.
22. **Window layout**: Side-by-side viewport + chat, reasonable default sizes.

## Step by Step Tasks

1. Initialize Electron + Vite + React + TypeScript project in `electron/`
2. Initialize Python project with uv in `sidecar/`
3. Define IPC message types in `shared/` (TypeScript + Python)
4. Implement Python stdio message loop (`sidecar/caddee/main.py`)
5. Implement Claude service with Anthropic SDK (`claude_service.py`)
6. Write OpenSCAD system prompt (`system_prompt.txt`)
7. Implement OpenSCAD CLI wrapper (`openscad_service.py`)
8. Implement session manager (`session_manager.py`)
9. Implement error recovery loop (compile fail -> Claude retry)
10. Implement Electron sidecar manager (`sidecar.ts`)
11. Implement IPC bridge (`ipc-handlers.ts`)
12. Build Three.js viewport component (`Viewport.tsx`)
13. Implement STL hot-swap and color feedback
14. Build chat console component (`ChatConsole.tsx`)
15. Wire chat to sidecar (send message, receive response + STL)
16. Implement status indicators (thinking, compiling, error)
17. End-to-end integration testing and prompt tuning
18. Window layout and basic styling

## Testing Strategy

- **Python sidecar**: Unit tests for each service (mock OpenSCAD CLI, mock Claude API)
- **IPC protocol**: Test message serialization/deserialization both sides
- **Integration**: Manual end-to-end testing (type prompt, verify render)
- **OpenSCAD**: Test with known .scad inputs that should compile/fail

## Acceptance Criteria
- [ ] User can type a natural language description and see a 3D model rendered
- [ ] User can refine the model through follow-up messages
- [ ] OpenSCAD compile errors trigger one automatic retry via Claude
- [ ] If retry fails, error is shown to user with explanation
- [ ] 3D viewport supports orbit/pan/zoom
- [ ] STL hot-swaps on each successful iteration
- [ ] Visual feedback during compilation (color change)
- [ ] App launches as a native desktop window

## Prerequisites
- Node.js 20+
- Python 3.11+
- OpenSCAD CLI installed (`brew install openscad` on macOS)
- Anthropic API key (set as env var `ANTHROPIC_API_KEY`)

## Validation Commands
```bash
# Verify OpenSCAD is installed
openscad --version

# Verify Python deps
cd sidecar && uv run python -c "import anthropic; print('OK')"

# Verify Electron dev server
cd electron && npm run dev

# End-to-end smoke test
# Type "create a simple cube" in chat -> cube should render
```

---

# Broad Strokes: Phases 2–4

These are high-level outlines to inform Phase 1 decisions. Detailed plans will be created as each phase begins.

## Phase 2 — Full UI (builds on Phase 1)

**Goal:** Three-pane layout with full design workflow features.

**Key additions to Phase 1 infrastructure:**
- **Tools panel** (third pane): Export buttons, history list, settings
- **Parameter sliders**: Parse OpenSCAD `/* [Section] */` customizer comments from generated .scad, render as React slider components. Changes update .scad variables and re-compile.
- **Iteration history**: Store each (prompt, .scad, STL thumbnail) tuple. Thumbnail via Three.js `renderer.domElement.toDataURL()`. Click to restore any version.
- **Session save/restore**: Serialize full state (conversation, .scad source, iteration history) to `.cad-session` JSON file. File > Save / File > Open.
- **Chat threading**: Visual grouping of refinement cycles.

**Phase 1 considerations:** Session manager should store full history from the start (not just current state) to make Phase 2 easier. IPC messages should be extensible.

## Phase 3 — FreeCAD Integration (builds on Phases 1-2)

**Goal:** Bridge to professional CAD workflow via FreeCAD.

**Requires:** FreeCAD 1.0+ installed separately.

**Key work:**
- **Headless geometry checks**: Python sidecar imports FreeCAD modules, loads STL/STEP, runs mesh analysis (non-manifold, open shells, thin walls, self-intersecting). Results shown in Tools panel.
- **STEP export pipeline**: .scad -> OpenSCAD -> STL -> FreeCAD `Part.read()` -> STEP. Or direct CadQuery path for cleaner B-rep.
- **Live sync**: Detect running FreeCAD instance, connect to its Python interpreter via socket, push .step into active document on each iteration. FreeCAD viewport refreshes automatically.
- **Import wizard**: Load external .FCStd/.step/.stl/.scad files. For .scad: direct load. For mesh formats: load as reference in viewport, Claude describes and offers to rebuild parametrically.

**Phase 1 considerations:** OpenSCAD service should output STL to a temp file (not just memory) so FreeCAD can read it later. Service architecture should allow adding FreeCAD as another service alongside Claude and OpenSCAD.

## Phase 4 — Image Input (builds on Phases 1-3)

**Goal:** Sketch or photo as conversation input.

**Key work:**
- **Image upload UI**: Drag-and-drop or file picker in chat console. Display image inline in conversation.
- **Claude vision integration**: Send image as multimodal content block alongside text. Claude extracts dimensional intent (shape, proportions, features).
- **Initial .scad generation**: Claude generates starting .scad from image analysis. Enters normal refinement loop from there.
- **Input types**: Hand-drawn sketches, photos of physical objects, technical drawings, screenshots of other CAD tools.

**Phase 1 considerations:** Claude service should accept multimodal content blocks (text + images) even if Phase 1 only uses text. The Anthropic SDK supports this natively. Message types in shared/ should include an optional `images` field.
