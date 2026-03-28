# Batch Plan Context: Health Data Improvements

## Project
WakeCap anchor-planner (frontend-2.0-anchor-planner/) - a Single-SPA micro-frontend for construction RTLS monitoring.

## Architecture
- React 18 + TypeScript, ArcGIS Maps SDK, shadcn/ui with `twap-` prefix
- Main page: `ConstructionMonitor.tsx`
- Services: `services/data/anchorDataQueries.ts` (SQL queries), `services/monitoring/statusClassifier.ts` (health classification)
- Panels: `pages/ConstructionMonitor/panels/DashboardPanel.tsx`, `ZoneHealthPanel.tsx`, `GatewayHealthPanel.tsx`
- Config: `types/config.ts` (DEFAULT_ANOMALY_THRESHOLDS), `services/config/configManager.ts`

## Key Data Findings (from production analysis, Feb 2026)
- **Project**: Apex Manhattanville, 175 anchors, 2 active gateways (of 9 configured)
- **Latency**: Median 9.5s, P95 30s, max 846s (extreme outlier). GW ...8796 has 2x worse P95 than GW ...8772
- **Gateway**: IDs in anchor_scans don't match node.id — need mapping resolution
- **Thresholds**: SQL (10/20/50m error) vs Runtime (50/100/200m error) — 5x divergence but only affects 2 anchors
- **Health scores**: Runtime formula (10/40/30/20) drops zone scores -20 points vs SQL (30/40/30) due to latency weight

## Two Threshold Sets
1. **SQL thresholds** (anchorDataQueries.ts): IQ 178/127/64 (0-255), Error 10/20/50m, Battery 2.8/2.5/2.2V
2. **Runtime thresholds** (config.ts): IQ 70/50/25%, Error 50/100/200m, Latency 5s/15s/60s, Battery 2.5/2.2/2.0V

## Health Score Formulas
- **SQL** (anchorDataQueries.ts line 333): `online*0.30 + iq*0.40 + error*0.30`
- **Runtime** (statusClassifier.ts line 370): `iq*0.40 + error*0.30 + latency*0.20 + online*0.10`

## Current Latency UI Status
- DashboardPanel: "Coming Soon" placeholder
- ZoneHealthPanel: Shows P50 only in detail view
- GatewayHealthPanel: Per-anchor latency with color-coded badges (green ≤5s, amber 5-15s, red >15s)
- `formatLatency()` helper exists in statusClassifier.ts but is unused in components
