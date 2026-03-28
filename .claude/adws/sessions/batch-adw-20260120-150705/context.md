# Batch Planning Context

Session: batch-adw-20260120-150705
Tasks: MapLibre layer migrations (ML-001 through ML-006)

## Project Overview

This is the **anchor-planner** frontend (frontend-2.0-anchor-planner), a micro-frontend for WakeCap's indoor positioning system. It uses ArcGIS for map visualization and is piloting MapLibre as an alternative.

## Expert: arcgis (GIS/Maps)

**Expertise**: ArcGIS JavaScript API and Indoors Information Model expert for map layers, spatial queries, and GIS visualization.

### Guidelines
- Follow ArcGIS Indoors Information Model for all features
- Use layer factory pattern - pure functions returning FeatureLayer/FeatureCollectionLayer
- All new map features must align with Indoors data model
- Use LevelManager.ts for floor management, DetailsManager.ts for POI layers

### Validation Commands
```bash
pnpm lint:check
pnpm build
```

## Existing MapLibre Architecture

A hybrid MapLibre + ArcGIS architecture was implemented as a pilot (see `project/specs/plan/completed/plan-adw-maplibre-arcgis-hybrid.md`).

### Interface Pattern
```
src/app/services/layers/
├── interfaces/
│   ├── types.ts              # MapProvider, LayerHandle, BaseLayerOptions
│   └── IFacilityLayer.ts     # Facility layer interface
├── arcgis/
│   └── facilityLayerAdapter.ts   # ArcGIS adapter
├── maplibre/
│   └── facilityLayerAdapter.ts   # MapLibre adapter
└── facilityLayer.ts          # Unified factory with provider selection
```

### Key Types (from interfaces/types.ts)
```typescript
export type MapProvider = 'arcgis' | 'maplibre';
export type MapInstance = unknown;

export interface LayerHandle {
  id: string;
  remove: () => void;
  setVisible: (visible: boolean) => void;
}
```

### MapLibre Adapter Pattern Example
```typescript
// maplibre/facilityLayerAdapter.ts
export const maplibreFacilityAdapter: IFacilityLayerAdapter = {
  addLayer(map: unknown, options: FacilityLayerOptions): LayerHandle {
    const mapInstance = map as MapLibreMap;
    // Add source
    mapInstance.addSource(sourceId, { type: 'geojson', data: {...} });
    // Add layers
    mapInstance.addLayer({ id: fillLayerId, type: 'fill', ... });
    mapInstance.addLayer({ id: outlineLayerId, type: 'line', ... });
    // Return handle
    return {
      id: `facility-${facilityId}`,
      remove: () => { /* cleanup */ },
      setVisible: (vis) => { /* toggle visibility */ }
    };
  }
};
```

## Existing ArcGIS Layers to Migrate

| Layer | Complexity | Key Features |
|-------|------------|--------------|
| `createProposedAnchorsLayer` | Low | Points with diamond markers, text labels, popups |
| `createDroneDeployLayer` | Low | WMTS raster tiles |
| `createGatewayLayer` | Medium | Points with diamond markers, popups, field filtering |
| `createZonesLayer` | Medium | Polygons with health-based color renderers, popups |
| `createBeaconLayer` | Medium | Points with status renderer, floor filtering via definitionExpression |
| `createRSSIHeatmapLayer` | High | Canvas-based MediaLayer, needs evaluation |

## MapLibre Capabilities Reference

### Point Layers
- `type: 'circle'` - Simple points
- `type: 'symbol'` - Points with icons/text
- Clustering: `cluster: true` on source

### Polygon Layers
- `type: 'fill'` - Filled polygons
- `type: 'line'` - Polygon outlines
- Data-driven styling: `['get', 'propertyName']`

### Raster/Tile Layers
- `type: 'raster'` with raster source
- WMTS: Add as `raster` source with tiles array

### Heatmap
- `type: 'heatmap'` - Native WebGL heatmap
- Properties: heatmap-weight, heatmap-intensity, heatmap-color, heatmap-radius

### Popups
```typescript
map.on('click', layerId, (e) => {
  new maplibregl.Popup()
    .setLngLat(e.lngLat)
    .setHTML(htmlContent)
    .addTo(map);
});
```

### Floor Filtering
```typescript
// Filter by property
map.setFilter(layerId, ['==', ['get', 'LEVEL_ID'], `Level_${floor}`]);
```

## File Locations

- ArcGIS layers: `frontend-2.0-anchor-planner/src/app/services/layers/create*.ts`
- Interfaces: `frontend-2.0-anchor-planner/src/app/services/layers/interfaces/`
- MapLibre adapters: `frontend-2.0-anchor-planner/src/app/services/layers/maplibre/`
- ArcGIS adapters: `frontend-2.0-anchor-planner/src/app/services/layers/arcgis/`
- Types: `frontend-2.0-anchor-planner/src/app/types/`

## Styling Requirements

- All Tailwind classes must use `twap-` prefix
- Use `cn()` utility from `@/lib/utils` for conditional classnames
