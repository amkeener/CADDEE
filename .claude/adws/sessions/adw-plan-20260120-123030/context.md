# Context: Playwright Implementation for ADW

## Session
- **ID**: adw-plan-20260120-123030
- **Expert**: python_tooling (with new playwright expert to be created)
- **Type**: Feature implementation

## Reference Implementation: AgenticTesting

The `../AgenticTesting` project provides a mature Playwright implementation with:

### Key Components
1. **atf_modules/playwright_ops.py** - Test execution, result parsing, artifact capture
2. **atf_modules/data_types.py** - Pydantic models for config, results, failures
3. **tests/conftest.py** - Pytest fixtures for browser context, auth, failure handling
4. **tests/core/pages/base_page.py** - Base page object with navigation, interactions, waiting
5. **tests/core/pages/wakecap/project_page.py** - Domain page with map/canvas handling

### Canvas/Map Handling Patterns
```python
# From project_page.py
MAP_CANVAS = "canvas"

def wait_for_map_load(self, timeout: int = 30000) -> None:
    self.wait_for_selector(self.MAP_CANVAS, timeout=timeout)
    self.wait_for_timeout(2000)  # Additional wait for tiles/data

def click_on_map(self, x: int, y: int) -> None:
    canvas = self.page.locator(self.MAP_CANVAS).first
    canvas.click(position={"x": x, "y": y})
```

### Configuration Pattern
Uses pydantic-settings with env vars:
- HEADLESS, SLOW_MO, DEFAULT_TIMEOUT
- BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD
- SCREENSHOT_ON_FAILURE, VIDEO_RECORDING

## Target: anchor-planner Frontend

The frontend uses:
- ArcGIS JS API for existing map functionality
- MapLibre GL JS for new hybrid layer approach
- Canvas-based rendering for both libraries
- React components

### Canvas Testing Challenges
1. No DOM elements for map features - must use coordinate clicks
2. Tile loading delays - need wait strategies
3. Floor plan overlays - complex layer stacking
4. Popups/tooltips appear on hover/click

## Files to Create

### In AdwProject (.claude/)
- `commands/experts/playwright/expertise.yaml` - Expert definition
- `playwright/` module directory with adapted patterns

### In anchor-planner submodule (optional phase 2)
- `tests/e2e/` - E2E test structure
- `tests/core/pages/` - Page objects
