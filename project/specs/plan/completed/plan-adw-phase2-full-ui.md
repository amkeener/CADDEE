---
status: done
type: feature
complexity: major
adw_session: adw-build-20260328-phase2
expert: frontend
---

# Plan: Phase 2 — Full UI

## Task Description
Build the complete three-pane Electron UI with resizable panels, iteration history with thumbnails, parameter sliders from OpenSCAD customizer syntax, session save/restore, and export functionality.

## Objective
Transform the Phase 1 two-pane MVP into a full-featured design tool. Users should be able to browse iteration history, tweak parameters via sliders, save/restore sessions, and export their work.

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                    Electron Renderer                              │
│  ┌──────────────────┬─────────────────┬──────────────────────┐    │
│  │    3D Viewport   │   Chat Console  │    Tools Panel        │    │
│  │    (Three.js)    │   (React)       │                       │    │
│  │                  │                 │  ┌─ Iteration History─┐│    │
│  │   [captures      │   [threaded by  │  │ [thumb] prompt... ││    │
│  │    thumbnails]   │    iteration]   │  │ [thumb] prompt... ││    │
│  │                  │                 │  └────────────────────┘│    │
│  │                  │                 │  ┌─ Parameters ───────┐│    │
│  │                  │                 │  │ width  ═══●═══     ││    │
│  │                  │                 │  │ height ══●════     ││    │
│  │                  │                 │  └────────────────────┘│    │
│  │                  │                 │  ┌─ Export ───────────┐│    │
│  │                  │                 │  │ [Save STL] [.scad] ││    │
│  │                  │                 │  └────────────────────┘│    │
│  │  ◄── drag ──►   │  ◄── drag ──►   │                       │    │
│  └──────────────────┴─────────────────┴──────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘

Menu Bar:
  File > Save Session (Cmd+S)
  File > Open Session (Cmd+O)
```

## Relevant Files

### To Create
```
electron/src/renderer/components/
  ResizablePanes.tsx          # Three-pane layout with drag handles
  ToolsPanel.tsx              # Right panel: history, params, export
  IterationHistory.tsx        # Thumbnail list of past iterations
  ParameterSliders.tsx        # Auto-generated sliders from .scad
  ExportButtons.tsx           # STL and .scad export buttons

electron/src/renderer/hooks/
  useIterations.ts            # Iteration state + restore logic
  useParameters.ts            # Parameter parsing + slider state

electron/src/renderer/utils/
  scadParser.ts               # Parse OpenSCAD customizer variables
```

### To Modify
```
electron/src/renderer/App.tsx             # Three-pane layout
electron/src/renderer/components/
  Viewport.tsx                             # Add thumbnail capture API
  ChatConsole.tsx                          # Add iteration grouping
electron/src/renderer/hooks/useChat.ts    # Track iteration IDs, expose scadCode
electron/src/main/index.ts               # Add menu bar, export handlers
electron/src/main/ipc-handlers.ts        # New IPC channels
electron/src/preload/index.ts            # Expose new APIs
shared/messages.ts                        # New IPC message types
shared/messages.py                        # Mirror new types
sidecar/caddee/main.py                   # New request handlers
sidecar/caddee/services/session_manager.py  # Save/load/restore
```

## Implementation Phases

### Phase A: Resizable Three-Pane Layout
Replace the hardcoded two-pane flex layout with a resizable three-pane component.

1. **ResizablePanes component**: Three children separated by drag handles. Persists widths. Minimum pane sizes (200px viewport, 280px chat, 220px tools).
2. **ToolsPanel shell**: Empty component with section headers.
3. **Update App.tsx**: Wire three-pane layout.

### Phase B: Iteration History & Thumbnails
Surface the existing iteration data (already tracked by sidecar SessionManager) in the UI.

4. **Extend IPC protocol**: Add `get_iterations`, `iterations_list`, `restore_iteration` message types in shared/.
5. **Sidecar iteration endpoints**: Handle get_iterations and restore_iteration in main.py.
6. **Viewport thumbnail capture**: Expose a `captureThumb()` method via ref/callback that returns a small data URL from renderer.domElement.toDataURL().
7. **useIterations hook**: Manages iteration list state, fetches from sidecar, handles restore.
8. **IterationHistory component**: Shows thumbnails + truncated prompts. Click to restore (updates viewport + chat).
9. **Wire iteration flow**: After each successful compile, capture thumbnail, add to iteration list. On restore, load the .scad + STL and sync chat.

### Phase C: Export Functionality
Let users save STL and .scad files to disk.

10. **Export IPC handlers**: In main process, use `dialog.showSaveDialog` + `fs.writeFile` for STL (binary) and .scad (text).
11. **Preload API**: Expose `exportSTL(base64)` and `exportScad(code)` via contextBridge.
12. **ExportButtons component**: Two buttons in ToolsPanel. Disabled when no model exists.

### Phase D: Parameter Sliders
Parse OpenSCAD customizer syntax and render interactive sliders.

13. **scadParser utility**: Extract variables with customizer annotations. OpenSCAD format: `varname = value; // [min:max]` or `// [min:step:max]`. Also parse `/* [Section Name] */` headers. Returns structured param objects.
14. **Parameter update IPC**: New `update_parameters` request type. Sidecar receives variable overrides, patches the current .scad, recompiles (no Claude call), returns new STL.
15. **Sidecar parameter handler**: In main.py, handle `update_parameters` — regex-replace variable values in current_scad, compile, return result.
16. **ParameterSliders component**: Renders sliders grouped by section. Debounced onChange triggers recompile.
17. **useParameters hook**: Parses current .scad code, manages slider state, sends update_parameters.

### Phase E: Session Save/Restore
Persist full design sessions to disk.

18. **Session file format**: `.cad-session` JSON containing: version, conversation, iterations (without STL blobs — reference temp files or re-embed), current_scad, parameter overrides.
19. **Sidecar session serialization**: Add `to_dict()` and `from_dict()` to Session class. Handle save_session and load_session IPC messages.
20. **Electron menu + IPC**: File > Save Session (Cmd+S), File > Open Session (Cmd+O). Main process handles dialog + file I/O, forwards data to/from sidecar.
21. **Wire to UI**: On load, restore viewport + chat + iteration history from session data.

### Phase F: Chat Threading & Polish
Visual refinements to the chat experience.

22. **Iteration grouping in chat**: Add visual separators between design iterations. Show iteration number badge. Group user prompt + assistant response + compile result.
23. **Final integration**: Ensure all panes sync correctly. Test edge cases (empty session, failed compiles, parameter changes during compile).

## Step by Step Tasks

1. Create ResizablePanes component with drag handles
2. Create ToolsPanel shell component
3. Update App.tsx to three-pane layout with ResizablePanes
4. Add new IPC message types to shared/messages.ts and shared/messages.py
5. Add iteration endpoints to sidecar (get_iterations, restore_iteration)
6. Add thumbnail capture to Viewport component
7. Create useIterations hook
8. Create IterationHistory component
9. Wire iteration flow end-to-end
10. Add export IPC handlers in main process
11. Extend preload API with export methods
12. Create ExportButtons component in ToolsPanel
13. Create scadParser utility for OpenSCAD customizer syntax
14. Add update_parameters IPC message type and sidecar handler
15. Create ParameterSliders component
16. Create useParameters hook and wire sliders to recompile
17. Add session save/load to sidecar SessionManager
18. Add Electron menu bar with File > Save/Open Session
19. Wire session save/restore end-to-end
20. Add iteration grouping to ChatConsole
21. Final integration testing and polish

## Acceptance Criteria
- [ ] Three-pane layout with resizable dividers (viewport, chat, tools)
- [ ] Iteration history shows thumbnails and prompts; click restores that version
- [ ] Parameter sliders auto-generated from OpenSCAD customizer syntax
- [ ] Slider changes trigger recompile without Claude call
- [ ] Export STL and .scad to user-chosen file location
- [ ] Session save/restore via File menu (Cmd+S / Cmd+O)
- [ ] Chat shows visual iteration grouping
- [ ] All Phase 1 functionality preserved

## Validation Commands
```bash
cd electron && npx tsc --noEmit        # TypeScript compiles
cd electron && npm run build            # Electron builds
cd sidecar && uv run python -c "from caddee.services.session_manager import Session; print('OK')"
```
