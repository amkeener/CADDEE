# Build Context: Plan-02 Gateway Health & Imbalance Detection

## Project
WakeCap anchor-planner (`frontend-2.0-anchor-planner/`) — a Single-SPA micro-frontend for construction RTLS monitoring.

## Architecture
- React 18 + TypeScript, ArcGIS Maps SDK, shadcn/ui with `twap-` prefix
- Main page: `ConstructionMonitor.tsx`
- Services: `services/data/anchorDataQueries.ts` (SQL queries), `services/monitoring/statusClassifier.ts` (health classification)
- Panels: `pages/ConstructionMonitor/panels/DashboardPanel.tsx`, `ZoneHealthPanel.tsx`, `GatewayHealthPanel.tsx`
- Config: `types/config.ts` (DEFAULT_ANOMALY_THRESHOLDS, DEFAULT_DIAGNOSTICS_CONFIG), `services/config/configManager.ts`
- Data loading: `utils/data/loadLiveData.ts` (LiveAnchorDataFile, loadLiveDataForSpace)

## Expert: frontend-2.0
- Monorepo: Lerna/pnpm, React 18, TypeScript 5.2, Single-SPA
- Anchor-planner is a sub-app within the monorepo
- All CSS classes use `twap-` prefix (Tailwind with anchor-planner prefix)
- Validation: `pnpm lint:check`, `pnpm format:check`, `npx tsc --noEmit`, `pnpm build`

## Key Data Context (from production analysis)
- 9 gateways configured but only 2 are active (receiving scans)
- Gateway IDs in anchor_scans (1127758796, 1127758772) don't match node.id - need serial_no mapping
- Active gateways have load imbalance (102 vs 73 anchors) and latency imbalance (P95: 34.5s vs 24.6s)
- 4 gateways are approved (G1, G2, G4, G11), 5 are not - yet none show in scan data
- Plan-01 (latency formula) was already implemented - uses formatLatency(), calculateP95(), filterOutlierLatency()

## Recent Changes from Plan-01
Plan-01 was implemented in a prior build session. Key files that were modified:
- `types/monitoring.ts` - Added p95Latency fields to SiteHealthMetrics and ZoneHealthSummary
- `types/config.ts` - Added latencyOutlierCap to AnomalyThresholds
- `services/data/anchorDataQueries.ts` - Updated health score formula to 10/40/30/20, added P95 column
- `services/monitoring/statusClassifier.ts` - Added calculateP95(), filterOutlierLatency()
- `components/panels/GatewayHealthPanel.tsx` - Added formatLatency usage, P50/P95 summary
- `components/construction/DashboardPanel.tsx` - Real latency KPI
- `components/panels/ZoneHealthPanel.tsx` - P95 column, latency badge

These changes are already in the working tree and should be built upon, not conflicted with.
