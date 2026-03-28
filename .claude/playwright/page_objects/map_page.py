"""
Map Page Object for canvas-based map testing.

Specialized page object for ArcGIS and MapLibre map interactions.
Handles canvas coordinate clicks, layer management, and map-specific waits.
"""

from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
from datetime import datetime
from pathlib import Path
import logging
import json

from .base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class MapPage(BasePage):
    """
    Page object for canvas-based map interactions.

    Handles ArcGIS and MapLibre maps with canvas rendering.
    """

    # Default selectors - override in subclasses as needed
    MAP_CONTAINER = "[data-testid='map-container'], .map-container, .esri-view, .maplibregl-map"
    MAP_CANVAS = "canvas"
    ZOOM_IN = "button:has-text('+'), [data-testid='zoom-in'], .esri-widget--button[title='Zoom in']"
    ZOOM_OUT = "button:has-text('-'), [data-testid='zoom-out'], .esri-widget--button[title='Zoom out']"
    POPUP = ".esri-popup, .maplibregl-popup, [data-testid='popup']"
    TOOLTIP = ".esri-tooltip, .maplibregl-popup, [data-testid='tooltip']"

    def __init__(
        self,
        page: "Page",
        tile_load_wait_ms: int = 2000,
        map_container_selector: Optional[str] = None,
    ):
        """
        Initialize the map page.

        Args:
            page: Playwright Page object
            tile_load_wait_ms: Time to wait for tiles after map load
            map_container_selector: Override default map container selector
        """
        super().__init__(page)
        self.tile_load_wait_ms = tile_load_wait_ms
        if map_container_selector:
            self.MAP_CONTAINER = map_container_selector

    # =========================================================================
    # Map Loading & Ready State
    # =========================================================================

    def wait_for_map_ready(self, timeout: int = 30000) -> None:
        """
        Wait for map to be fully loaded and rendered.

        Waits for canvas element, then additional time for tile rendering.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Waiting for map to be ready")
        try:
            # Wait for canvas to appear
            self.wait_for_selector(self.MAP_CANVAS, timeout=timeout)

            # Wait for network to settle (tiles loading)
            try:
                self.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                logger.warning("Network idle timeout, continuing anyway")

            # Additional wait for tile rendering
            self.wait_for_timeout(self.tile_load_wait_ms)
            logger.info("Map ready")

        except Exception as e:
            logger.error(f"Map load timeout: {e}")
            raise

    def is_map_visible(self) -> bool:
        """Check if map canvas is visible."""
        return self.is_visible(self.MAP_CANVAS)

    def wait_for_layer_load(
        self,
        layer_name: str,
        timeout: int = 10000,
        check_interval: int = 500
    ) -> bool:
        """
        Wait for a specific layer to be loaded and visible.

        Uses JavaScript evaluation to check layer state.

        Args:
            layer_name: Name/ID of the layer
            timeout: Maximum wait time in ms
            check_interval: How often to check in ms

        Returns:
            True if layer loaded, False if timeout
        """
        logger.info(f"Waiting for layer: {layer_name}")
        elapsed = 0

        while elapsed < timeout:
            try:
                # Try MapLibre API first
                result = self.evaluate(f"""
                    (() => {{
                        if (window.map && window.map.getLayer) {{
                            const layer = window.map.getLayer('{layer_name}');
                            return layer && layer.visibility !== 'none';
                        }}
                        return false;
                    }})()
                """)
                if result:
                    logger.info(f"Layer {layer_name} loaded")
                    return True
            except Exception:
                pass

            self.wait_for_timeout(check_interval)
            elapsed += check_interval

        logger.warning(f"Layer {layer_name} load timeout")
        return False

    # =========================================================================
    # Canvas Coordinate Interactions
    # =========================================================================

    def click_at_coordinates(self, x: int, y: int) -> None:
        """
        Click at specific pixel coordinates on the map canvas.

        Args:
            x: X coordinate (pixels from left)
            y: Y coordinate (pixels from top)
        """
        logger.info(f"Clicking map at ({x}, {y})")
        canvas = self.page.locator(self.MAP_CANVAS).first
        canvas.click(position={"x": x, "y": y})

    def double_click_at_coordinates(self, x: int, y: int) -> None:
        """
        Double-click at coordinates (often triggers zoom).

        Args:
            x: X coordinate
            y: Y coordinate
        """
        logger.info(f"Double-clicking map at ({x}, {y})")
        canvas = self.page.locator(self.MAP_CANVAS).first
        canvas.dblclick(position={"x": x, "y": y})

    def hover_at_coordinates(self, x: int, y: int) -> None:
        """
        Hover at coordinates to trigger tooltips/popups.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        logger.info(f"Hovering map at ({x}, {y})")
        canvas = self.page.locator(self.MAP_CANVAS).first
        canvas.hover(position={"x": x, "y": y})

    def drag_map(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int
    ) -> None:
        """
        Drag/pan the map from one point to another.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
        """
        logger.info(f"Dragging map from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        canvas = self.page.locator(self.MAP_CANVAS).first
        canvas.drag_to(
            canvas,
            source_position={"x": start_x, "y": start_y},
            target_position={"x": end_x, "y": end_y}
        )

    def get_canvas_center(self) -> Tuple[int, int]:
        """
        Get the center coordinates of the map canvas.

        Returns:
            Tuple of (x, y) center coordinates
        """
        canvas = self.page.locator(self.MAP_CANVAS).first
        box = canvas.bounding_box()
        if box:
            return (int(box["width"] / 2), int(box["height"] / 2))
        return (0, 0)

    # =========================================================================
    # Zoom Controls
    # =========================================================================

    def zoom_in(self, clicks: int = 1) -> None:
        """
        Zoom in on the map.

        Args:
            clicks: Number of zoom steps
        """
        for i in range(clicks):
            logger.info(f"Zooming in ({i + 1}/{clicks})")
            self.click(self.ZOOM_IN)
            self.wait_for_timeout(500)  # Wait for zoom animation

    def zoom_out(self, clicks: int = 1) -> None:
        """
        Zoom out on the map.

        Args:
            clicks: Number of zoom steps
        """
        for i in range(clicks):
            logger.info(f"Zooming out ({i + 1}/{clicks})")
            self.click(self.ZOOM_OUT)
            self.wait_for_timeout(500)  # Wait for zoom animation

    def zoom_to_level(self, level: int) -> None:
        """
        Set map to specific zoom level via JavaScript.

        Args:
            level: Target zoom level
        """
        logger.info(f"Setting zoom level to {level}")
        try:
            self.evaluate(f"""
                (() => {{
                    if (window.map && window.map.setZoom) {{
                        window.map.setZoom({level});
                    }}
                }})()
            """)
            self.wait_for_timeout(1000)  # Wait for zoom
        except Exception as e:
            logger.warning(f"Failed to set zoom via JS: {e}")

    # =========================================================================
    # Popups & Tooltips
    # =========================================================================

    def is_popup_visible(self) -> bool:
        """Check if a popup is currently visible."""
        return self.is_visible(self.POPUP)

    def get_popup_content(self) -> Optional[str]:
        """Get text content of visible popup."""
        try:
            if self.is_popup_visible():
                return self.get_text(self.POPUP)
        except Exception:
            pass
        return None

    def close_popup(self) -> None:
        """Close any open popup."""
        try:
            close_btn = f"{self.POPUP} button[aria-label='Close'], {self.POPUP} .esri-popup__button--close"
            if self.is_visible(close_btn):
                self.click(close_btn)
        except Exception as e:
            logger.warning(f"Failed to close popup: {e}")

    def wait_for_popup(self, timeout: int = 5000) -> bool:
        """
        Wait for popup to appear.

        Args:
            timeout: Maximum wait time in ms

        Returns:
            True if popup appeared
        """
        try:
            self.wait_for_selector(self.POPUP, state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    # =========================================================================
    # Layer Management
    # =========================================================================

    def get_visible_layers(self) -> List[str]:
        """
        Get list of currently visible layer names.

        Returns:
            List of layer names/IDs
        """
        try:
            result = self.evaluate("""
                (() => {
                    if (window.map && window.map.getStyle) {
                        const style = window.map.getStyle();
                        if (style && style.layers) {
                            return style.layers
                                .filter(l => l.layout?.visibility !== 'none')
                                .map(l => l.id);
                        }
                    }
                    return [];
                })()
            """)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.warning(f"Failed to get visible layers: {e}")
            return []

    def toggle_layer_visibility(self, layer_name: str, visible: bool) -> None:
        """
        Toggle a layer's visibility.

        Args:
            layer_name: Layer ID/name
            visible: True to show, False to hide
        """
        visibility = "visible" if visible else "none"
        logger.info(f"Setting layer {layer_name} visibility to {visibility}")
        try:
            self.evaluate(f"""
                (() => {{
                    if (window.map && window.map.setLayoutProperty) {{
                        window.map.setLayoutProperty('{layer_name}', 'visibility', '{visibility}');
                    }}
                }})()
            """)
        except Exception as e:
            logger.warning(f"Failed to toggle layer visibility: {e}")

    # =========================================================================
    # Map State
    # =========================================================================

    def get_map_center(self) -> Optional[Tuple[float, float]]:
        """
        Get current map center coordinates.

        Returns:
            Tuple of (longitude, latitude) or None
        """
        try:
            result = self.evaluate("""
                (() => {
                    if (window.map && window.map.getCenter) {
                        const center = window.map.getCenter();
                        return [center.lng, center.lat];
                    }
                    return null;
                })()
            """)
            if result and len(result) == 2:
                return (result[0], result[1])
        except Exception as e:
            logger.warning(f"Failed to get map center: {e}")
        return None

    def get_map_zoom(self) -> Optional[float]:
        """
        Get current map zoom level.

        Returns:
            Zoom level or None
        """
        try:
            return self.evaluate("""
                (() => {
                    if (window.map && window.map.getZoom) {
                        return window.map.getZoom();
                    }
                    return null;
                })()
            """)
        except Exception as e:
            logger.warning(f"Failed to get map zoom: {e}")
        return None

    def get_map_state(self) -> Dict[str, Any]:
        """
        Get complete map state for debugging.

        Returns:
            Dictionary with center, zoom, visible layers, etc.
        """
        return {
            "center": self.get_map_center(),
            "zoom": self.get_map_zoom(),
            "visible_layers": self.get_visible_layers(),
            "canvas_center": self.get_canvas_center(),
        }

    # =========================================================================
    # Screenshots
    # =========================================================================

    def capture_map_screenshot(
        self,
        name: str,
        screenshot_dir: str = "screenshots"
    ) -> str:
        """
        Capture screenshot of just the map area.

        Args:
            name: Screenshot name
            screenshot_dir: Directory for screenshots

        Returns:
            Path to screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path(screenshot_dir)
        path.mkdir(parents=True, exist_ok=True)
        screenshot_path = path / f"map_{name}_{timestamp}.png"

        canvas = self.page.locator(self.MAP_CANVAS).first
        canvas.screenshot(path=str(screenshot_path))

        logger.info(f"Map screenshot saved: {screenshot_path}")
        return str(screenshot_path)

    def capture_before_after(
        self,
        action_name: str,
        action_callable,
        screenshot_dir: str = "screenshots"
    ) -> Tuple[str, str]:
        """
        Capture screenshots before and after an action.

        Args:
            action_name: Name for the screenshots
            action_callable: Function to execute between screenshots
            screenshot_dir: Directory for screenshots

        Returns:
            Tuple of (before_path, after_path)
        """
        before_path = self.capture_map_screenshot(f"{action_name}_before", screenshot_dir)
        action_callable()
        self.wait_for_timeout(1000)  # Wait for map to update
        after_path = self.capture_map_screenshot(f"{action_name}_after", screenshot_dir)
        return (before_path, after_path)
