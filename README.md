# CADDEE — CAD-AI Collaborative Design Environment

CADDEE is a desktop tool that turns natural language into 3D models. Type what you want to build, and Claude generates OpenSCAD code, compiles it to STL, and renders it in a Three.js viewport — all in real time.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Electron Shell                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │  Viewport   │  │    Chat    │  │  Tools Panel   │  │
│  │  (Three.js) │  │  Console   │  │  Params/Export │  │
│  └──────┬─────┘  └─────┬──────┘  └───────┬────────┘  │
│         └──────────────┼─────────────────┘            │
│                   preload bridge                      │
│                        │  IPC (stdio JSON)            │
├────────────────────────┼─────────────────────────────┤
│                  Python Sidecar                       │
│  ┌──────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Claude API   │  │ OpenSCAD │  │ FreeCAD/trimesh│  │
│  │ (Anthropic)  │  │ CLI      │  │ (mesh/export)  │  │
│  └──────────────┘  └──────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**Electron frontend** (`electron/`) — React + Three.js renderer with three-pane layout (viewport, chat, tools).

**Python sidecar** (`sidecar/`) — Long-lived process handling Claude API calls, OpenSCAD compilation, mesh analysis (trimesh), and optional FreeCAD integration.

**Shared types** (`shared/`) — IPC message definitions mirrored in Python and TypeScript. Keep `messages.py` and `messages.ts` in sync.

## Prerequisites

- **Node.js** >= 18
- **Python** >= 3.11
- **uv** (Python package manager) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **OpenSCAD** — `brew install openscad` (macOS)
- **FreeCAD** >= 1.0 (optional, Phase 3) — `brew install --cask freecad`
- **Anthropic API key** — set `ANTHROPIC_API_KEY` env var

## Setup

```bash
# Clone and enter the project
git clone <repo-url> && cd CADDEE

# Install Electron dependencies
cd electron && npm install && cd ..

# Install Python sidecar dependencies
cd sidecar && uv sync && cd ..
```

## Development

```bash
# Start the Electron app (launches sidecar automatically)
cd electron && npm run dev

# Type-check the Electron app
cd electron && npm run typecheck

# Run sidecar standalone (for debugging)
cd sidecar && echo '{"id":"1","type":"ping"}' | uv run python -m caddee.main

# Compile-check a sidecar module
cd sidecar && uv run python -m py_compile caddee/main.py
```

## Project Structure

```
CADDEE/
├── electron/                  # Electron + React + Three.js frontend
│   ├── src/main/              # Main process (window, IPC, sidecar spawn)
│   ├── src/preload/           # Preload bridge (contextBridge API)
│   └── src/renderer/          # React renderer
│       ├── components/        # UI components (Viewport, Chat, Tools, etc.)
│       ├── hooks/             # Custom React hooks
│       ├── types/             # TypeScript type definitions
│       └── utils/             # Utilities (scadParser, etc.)
├── sidecar/                   # Python sidecar
│   └── caddee/
│       ├── services/          # Business logic (claude, openscad, freecad, session)
│       └── prompts/           # Claude system prompts
├── shared/                    # IPC message types (Python + TypeScript)
├── project/                   # Backlog, plans, specs, coding standards
│   └── coding-standards/      # Language-specific coding standards
└── .claude/                   # ADW framework, experts, commands
    └── commands/experts/      # Domain expert definitions
```

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Core Loop — text → Claude → .scad → STL → Three.js | Done |
| 2 | Full UI — three-pane layout, sliders, history, sessions, export | Done |
| 3 | FreeCAD Integration — mesh checks, STEP/FCStd export, live sync, import | Done |
| 4 | Image Input — sketch/photo upload → Claude vision → .scad | Not Started |

## Coding Standards

Language-specific coding standards are enforced during `/build_adw` and `/code_review_adw`:

- [TypeScript/React](project/coding-standards/typescript.md)
- [Python](project/coding-standards/python.md)
- [IPC Protocol](project/coding-standards/ipc.md)
