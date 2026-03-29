---
status: done
type: feature
complexity: major
adw_session: adw-build-20260328-phase3
expert: python_tooling
---

# Plan: Phase 3 — FreeCAD Integration

## Task Description
Add headless compatibility checks, STEP/FCStd export, import wizard, and live FreeCAD sync. Mesh analysis via trimesh (always available); STEP/FCStd export and live sync require FreeCAD 1.0+ installed separately.

## Objective
Bridge CADDEE's generative workflow to professional CAD tools. Users get immediate geometry feedback (manifold checks, thin walls) and can export to industry-standard formats (STEP, FCStd) for downstream use in FreeCAD, Fusion 360, SolidWorks, etc.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Electron Renderer                                              │
│  ┌───────────┐ ┌────────────┐ ┌──────────────────────────────┐  │
│  │ Viewport  │ │  Chat      │ │  Tools Panel                 │  │
│  │           │ │  Console   │ │  ├─ Compatibility [NEW]      │  │
│  │           │ │            │ │  ├─ Iteration History         │  │
│  │           │ │            │ │  ├─ Parameters                │  │
│  │           │ │            │ │  └─ Export (STL/SCAD/STEP/    │  │
│  │           │ │            │ │       FCStd) [EXTENDED]       │  │
│  └───────────┘ └────────────┘ └──────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Import Wizard Dialog [NEW]                              │    │
│  │  Load .FCStd / .step / .stl / .scad as starting point   │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
        ↕ IPC
┌─────────────────────────────────────────────────────────────────┐
│  Python Sidecar                                                 │
│  ├─ freecad_service.py [NEW]                                    │
│  │   ├─ trimesh: mesh analysis (always available)               │
│  │   ├─ FreeCAD: STEP/FCStd export (optional)                  │
│  │   └─ FreeCAD: live sync via socket (optional)                │
│  ├─ claude_service.py (existing)                                │
│  ├─ openscad_service.py (existing)                              │
│  └─ session_manager.py (existing)                               │
└─────────────────────────────────────────────────────────────────┘
```

## Dependency Strategy

**Tier 1 — Always available (pip install):**
- `trimesh` — mesh analysis (non-manifold, open shells, watertight, thin walls)
- `numpy` — required by trimesh

**Tier 2 — Optional (FreeCAD 1.0+ installed separately):**
- `FreeCAD`, `Part`, `Mesh` modules — STEP/FCStd export, live sync
- Detected at runtime, graceful fallback with helpful messages

## Relevant Files

### To Create
```
sidecar/caddee/services/freecad_service.py    # FreeCAD + trimesh service
electron/src/renderer/components/CompatibilityPanel.tsx  # Mesh analysis UI
electron/src/renderer/components/ImportWizard.tsx         # Import dialog
```

### To Modify
```
shared/messages.py          # New message types
shared/messages.ts          # New message types (mirror)
sidecar/caddee/main.py     # New request handlers
sidecar/pyproject.toml     # Add trimesh dependency
electron/src/main/index.ts           # Import menu item
electron/src/main/ipc-handlers.ts    # STEP/FCStd export handlers
electron/src/preload/index.ts        # New API methods
electron/src/renderer/App.tsx        # Wire new components
electron/src/renderer/components/ToolsPanel.tsx    # Add compatibility section
electron/src/renderer/components/ExportButtons.tsx # Add STEP/FCStd buttons
```

## Step by Step Tasks

1. **Add trimesh dependency and create freecad_service.py scaffold** — Detection logic for FreeCAD availability, trimesh import, result dataclasses.

2. **Implement mesh compatibility checks via trimesh** — analyze_mesh() that checks: watertight, manifold edges, degenerate faces, thin walls (via face normals), volume/surface area stats. Returns structured CompatibilityResult.

3. **Add Phase 3 message types to shared/** — CompatibilityCheckRequest/Response, ExportStepRequest/Response, ExportFcstdRequest/Response, ImportFileRequest/Response, LiveSyncRequest/Response, CapabilitiesRequest/Response.

4. **Add compatibility check handler to sidecar main.py** — Route check_compatibility requests to freecad_service.analyze_mesh(). Add capabilities handler to report what's available (trimesh always, FreeCAD if detected).

5. **Create CompatibilityPanel UI component** — Shows check results with green/yellow/red indicators and plain-English explanations. "Check" button triggers analysis. Shows "FreeCAD not installed" for STEP-specific checks.

6. **Wire CompatibilityPanel into App.tsx and ToolsPanel** — Add to ToolsPanel as new section. Auto-check on each new STL. Pass current STL base64 data.

7. **Implement STEP and FCStd export in freecad_service** — export_step() and export_fcstd() using FreeCAD Python API. Graceful error if FreeCAD not available.

8. **Add STEP/FCStd export IPC handlers and UI** — Electron IPC handlers with save dialogs. New buttons in ExportButtons component. Preload API methods.

9. **Implement import wizard backend** — import_file() in freecad_service handles .stl, .scad, .step, .FCStd. For mesh formats: load and analyze. For .scad: load source. Returns file contents + metadata.

10. **Create ImportWizard UI and wire to File menu** — Dialog component for file selection and preview. "Import" menu item in File menu. Loads file into current session as starting point.

11. **Implement live FreeCAD sync** — Detect running FreeCAD, connect via socket, push STEP on each iteration. Toggle in Tools panel. Graceful when FreeCAD not running.

12. **Integration testing and validation** — End-to-end flow verification, error handling edge cases, backlog update.

## Acceptance Criteria
- [ ] Compatibility panel shows mesh analysis results after each iteration
- [ ] Analysis covers: watertight, manifold, degenerate faces, volume/area stats
- [ ] Results use plain-English explanations (not just pass/fail)
- [ ] STEP export works when FreeCAD is installed
- [ ] FCStd export works when FreeCAD is installed
- [ ] Export buttons show helpful message when FreeCAD not available
- [ ] Import wizard can load .stl, .scad, .step, .FCStd files
- [ ] Imported files become the starting point for conversation
- [ ] Live sync pushes to running FreeCAD instance
- [ ] All features degrade gracefully when FreeCAD is not installed
- [ ] Capabilities endpoint reports what's available

## Validation Commands
```bash
# Verify trimesh is installed
cd sidecar && uv run python -c "import trimesh; print('trimesh OK')"

# Verify sidecar starts
cd sidecar && echo '{"id":"1","type":"ping"}' | uv run python -m caddee.main

# Check capabilities
cd sidecar && echo '{"id":"1","type":"get_capabilities"}' | uv run python -m caddee.main

# TypeScript compilation
cd electron && npx tsc --noEmit

# Verify Electron dev server
cd electron && npm run dev
```
