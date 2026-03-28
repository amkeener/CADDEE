"""
Base Page Object for Playwright testing.

All page objects should inherit from this base class.
Adapted from AgenticTesting framework.
"""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from pathlib import Path
import logging

if TYPE_CHECKING:
    from playwright.sync_api import Page, Locator

logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: "Page"):
        """
        Initialize the base page.

        Args:
            page: Playwright Page object
        """
        self.page = page

    # =========================================================================
    # Navigation
    # =========================================================================

    def navigate_to(self, url: str) -> None:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
        """
        logger.info(f"Navigating to: {url}")
        self.page.goto(url)

    def navigate_to_path(self, base_url: str, path: str) -> None:
        """
        Navigate to a path relative to base URL.

        Args:
            base_url: Base URL
            path: Path to append
        """
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        self.navigate_to(url)

    def reload(self) -> None:
        """Reload the current page."""
        logger.info("Reloading page")
        self.page.reload()

    def go_back(self) -> None:
        """Navigate back in browser history."""
        logger.info("Navigating back")
        self.page.go_back()

    def go_forward(self) -> None:
        """Navigate forward in browser history."""
        logger.info("Navigating forward")
        self.page.go_forward()

    # =========================================================================
    # Element Interactions
    # =========================================================================

    def click(self, selector: str, force: bool = False) -> None:
        """
        Click an element.

        Args:
            selector: CSS selector or locator string
            force: Force click even if element is not visible
        """
        logger.info(f"Clicking: {selector}")
        self.page.click(selector, force=force)

    def fill(self, selector: str, value: str) -> None:
        """
        Fill an input field.

        Args:
            selector: CSS selector for the input
            value: Value to fill
        """
        logger.info(f"Filling {selector}")
        self.page.fill(selector, value)

    def clear_and_fill(self, selector: str, value: str) -> None:
        """
        Clear an input field and fill with new value.

        Args:
            selector: CSS selector for the input
            value: Value to fill
        """
        logger.info(f"Clearing and filling {selector}")
        self.page.fill(selector, "")
        self.page.fill(selector, value)

    def type_text(self, selector: str, text: str, delay: int = 50) -> None:
        """
        Type text character by character.

        Args:
            selector: CSS selector for the input
            text: Text to type
            delay: Delay between keystrokes in ms
        """
        logger.info(f"Typing into {selector}")
        self.page.locator(selector).type(text, delay=delay)

    def select_option(self, selector: str, value: str) -> None:
        """
        Select an option from a dropdown.

        Args:
            selector: CSS selector for the select element
            value: Value to select
        """
        logger.info(f"Selecting {value} from {selector}")
        self.page.select_option(selector, value)

    def check(self, selector: str) -> None:
        """Check a checkbox."""
        logger.info(f"Checking: {selector}")
        self.page.check(selector)

    def uncheck(self, selector: str) -> None:
        """Uncheck a checkbox."""
        logger.info(f"Unchecking: {selector}")
        self.page.uncheck(selector)

    def hover(self, selector: str) -> None:
        """Hover over an element."""
        logger.info(f"Hovering: {selector}")
        self.page.hover(selector)

    def press_key(self, selector: str, key: str) -> None:
        """
        Press a key on an element.

        Args:
            selector: CSS selector
            key: Key to press (e.g., "Enter", "Tab")
        """
        logger.info(f"Pressing {key} on {selector}")
        self.page.press(selector, key)

    # =========================================================================
    # Element State
    # =========================================================================

    def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        return self.page.is_visible(selector)

    def is_enabled(self, selector: str) -> bool:
        """Check if element is enabled."""
        return self.page.is_enabled(selector)

    def is_checked(self, selector: str) -> bool:
        """Check if checkbox/radio is checked."""
        return self.page.is_checked(selector)

    def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        return self.page.text_content(selector) or ""

    def get_inner_text(self, selector: str) -> str:
        """Get inner text of an element."""
        return self.page.inner_text(selector)

    def get_input_value(self, selector: str) -> str:
        """Get value of an input element."""
        return self.page.input_value(selector)

    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get attribute value of an element."""
        return self.page.get_attribute(selector, attribute)

    def count_elements(self, selector: str) -> int:
        """Count elements matching selector."""
        return self.page.locator(selector).count()

    # =========================================================================
    # Waiting
    # =========================================================================

    def wait_for_selector(
        self, selector: str, state: str = "visible", timeout: int = 30000
    ) -> None:
        """
        Wait for element to be in specified state.

        Args:
            selector: CSS selector
            state: State to wait for (visible, hidden, attached, detached)
            timeout: Timeout in milliseconds
        """
        logger.info(f"Waiting for {selector} to be {state}")
        self.page.wait_for_selector(selector, state=state, timeout=timeout)

    def wait_for_load_state(self, state: str = "load", timeout: int = 30000) -> None:
        """
        Wait for page load state.

        Args:
            state: Load state (load, domcontentloaded, networkidle)
            timeout: Timeout in milliseconds
        """
        logger.info(f"Waiting for load state: {state}")
        self.page.wait_for_load_state(state, timeout=timeout)

    def wait_for_url(self, url_pattern: str, timeout: int = 30000) -> None:
        """
        Wait for URL to match pattern.

        Args:
            url_pattern: URL pattern (string or regex)
            timeout: Timeout in milliseconds
        """
        logger.info(f"Waiting for URL: {url_pattern}")
        self.page.wait_for_url(url_pattern, timeout=timeout)

    def wait_for_timeout(self, timeout: int) -> None:
        """
        Wait for specified time.

        Args:
            timeout: Time to wait in milliseconds
        """
        self.page.wait_for_timeout(timeout)

    # =========================================================================
    # Locators
    # =========================================================================

    def locator(self, selector: str) -> "Locator":
        """Get a locator for the selector."""
        return self.page.locator(selector)

    def get_by_role(self, role: str, **kwargs) -> "Locator":
        """Get element by ARIA role."""
        return self.page.get_by_role(role, **kwargs)

    def get_by_text(self, text: str, exact: bool = False) -> "Locator":
        """Get element by text content."""
        return self.page.get_by_text(text, exact=exact)

    def get_by_label(self, text: str) -> "Locator":
        """Get element by label text."""
        return self.page.get_by_label(text)

    def get_by_placeholder(self, text: str) -> "Locator":
        """Get element by placeholder text."""
        return self.page.get_by_placeholder(text)

    def get_by_test_id(self, test_id: str) -> "Locator":
        """Get element by data-testid attribute."""
        return self.page.get_by_test_id(test_id)

    # =========================================================================
    # Screenshots
    # =========================================================================

    def take_screenshot(
        self,
        name: str,
        full_page: bool = True,
        screenshot_dir: str = "screenshots"
    ) -> str:
        """
        Take a screenshot.

        Args:
            name: Screenshot name
            full_page: Capture full page
            screenshot_dir: Directory for screenshots

        Returns:
            Path to screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path(screenshot_dir)
        path.mkdir(parents=True, exist_ok=True)
        screenshot_path = path / f"{name}_{timestamp}.png"
        self.page.screenshot(path=str(screenshot_path), full_page=full_page)
        logger.info(f"Screenshot saved: {screenshot_path}")
        return str(screenshot_path)

    # =========================================================================
    # Page Properties
    # =========================================================================

    @property
    def url(self) -> str:
        """Get current page URL."""
        return self.page.url

    @property
    def title(self) -> str:
        """Get current page title."""
        return self.page.title()

    # =========================================================================
    # JavaScript Evaluation
    # =========================================================================

    def evaluate(self, expression: str) -> any:
        """
        Evaluate JavaScript expression.

        Args:
            expression: JavaScript expression

        Returns:
            Result of evaluation
        """
        return self.page.evaluate(expression)

    def evaluate_handle(self, expression: str):
        """
        Evaluate JavaScript and return handle.

        Args:
            expression: JavaScript expression

        Returns:
            JSHandle
        """
        return self.page.evaluate_handle(expression)
