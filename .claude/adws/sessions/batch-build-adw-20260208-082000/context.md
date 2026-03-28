# Build Context: Plan-01 Latency Formula & Display

## Project
WakeCap anchor-planner (`frontend-2.0-anchor-planner/`) — a Single-SPA micro-frontend for construction RTLS monitoring.

## Architecture
- React 18 + TypeScript, ArcGIS Maps SDK, shadcn/ui with `twap-` prefix
- Main page: `ConstructionMonitor.tsx`
- Services: `services/data/anchorDataQueries.ts` (SQL queries), `services/monitoring/statusClassifier.ts` (health classification)
- Panels: `pages/ConstructionMonitor/panels/DashboardPanel.tsx`, `ZoneHealthPanel.tsx`, `GatewayHealthPanel.tsx`
- Config: `types/config.ts` (DEFAULT_ANOMALY_THRESHOLDS), `services/config/configManager.ts`

## Expert: frontend-2.0
- Monorepo: Lerna/pnpm, React 18, TypeScript 5.2, Single-SPA
- Anchor-planner is a sub-app within the monorepo
- All CSS classes use `twap-` prefix (Tailwind with anchor-planner prefix)
- Validation: `pnpm lint:check`, `pnpm format:check`, `npx tsc --noEmit`, `pnpm build`

## Key Data Context (from production analysis)
- Median latency: 9.5s, P95: 30s, max: 846s (extreme outlier)
- Current 5s/15s/60s thresholds put ~61% in warning territory (correct behavior)
- SQL formula: `online*0.30 + iq*0.40 + error*0.30` (missing latency)
- Runtime formula: `online*0.10 + iq*0.40 + error*0.30 + latency*0.20` (target)
- `formatLatency()` exists in statusClassifier.ts but is unused in components
- DashboardPanel latency shows "Coming Soon" placeholder
