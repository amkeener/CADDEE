# ADW Session Context

Session ID: batch-build-adw-20260121-102710
Batch: project/specs/batch-adw-20260121-102710/

## Project Overview

ADW Template Project with frontend-2.0-anchor-planner submodule. The submodule is a React micro-frontend using:
- Single-SPA architecture
- ArcGIS JavaScript API for primary map
- MapLibre GL JS as alternative map provider
- Calcite Design System
- Tailwind CSS with `twap-` prefix

## Working Directory

All implementation work happens in `frontend-2.0-anchor-planner/` submodule.

## Key Files

### Map Components
- `src/app/components/Map/MapLibreMap.tsx` - MapLibre component (modify)
- `src/app/components/Map/MapLibreDemo.tsx` - Toggle UI (modify)
- `src/app/components/Map/ArcGISMap.tsx` - ArcGIS map (reference)
- `src/app/components/Map/index.ts` - Exports

### Pages
- `src/app/pages/ConstructionMonitor.tsx` - Main page with map toggle

### Layer Services
- `src/app/services/layers/*.ts` - Layer factory functions
- `src/app/services/layers/interfaces/*.ts` - Layer interfaces

## Expert Guidelines

### react_frontend
- All Tailwind classes MUST use `twap-` prefix
- Use `cn()` from `@/lib/utils` for conditional classnames
- Path aliases: @/components, @/lib, @/services, etc.

### arcgis
- Follow ArcGIS Indoors Information Model
- Use layer factory pattern
- Provider-agnostic adapters for both ArcGIS and MapLibre

## Validation Commands

```bash
cd frontend-2.0-anchor-planner
pnpm lint:check
pnpm build
```

## Important Notes

1. The MapLibre integration already has provider-agnostic layer adapters (ML-001 to ML-006)
2. Blueprint API returns NO orientation metadata - only space polygon bounds
3. Current floor plan alignment is inaccurate (uses space bounds instead of image bounds)
4. All three plans can be implemented independently
