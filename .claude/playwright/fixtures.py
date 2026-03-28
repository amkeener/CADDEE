"""
Pytest fixtures for Playwright testing.

Provides browser context, page, and failure handling fixtures.
Adapted from AgenticTesting framework.
"""

from typing import Generator, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
import logging
import os

if TYPE_CHECKING:
    import pytest
    from playwright.sync_api import Page, BrowserContext

from .config import get_config

logger = logging.getLogger(__name__)


# =============================================================================
# Browser Configuration Fixtures
# =============================================================================


def browser_type_launch_args() -> Dict[str, Any]:
    """
    Define browser launch arguments.

    Use as a pytest fixture:
        @pytest.fixture(scope="session")
        def browser_type_launch_args():
            return browser_type_launch_args()

    Returns:
        Dictionary of browser launch arguments
    """
    config = get_config()
    return config.get_browser_launch_args()


def browser_context_args() -> Dict[str, Any]:
    """
    Define browser context arguments.

    Use as a pytest fixture:
        @pytest.fixture(scope="session")
        def browser_context_args():
            return browser_context_args()

    Returns:
        Dictionary of browser context arguments
    """
    config = get_config()
    return config.get_context_args()


# =============================================================================
# Page Fixture Helpers
# =============================================================================


def create_page_fixture(context: "BrowserContext") -> Generator["Page", None, None]:
    """
    Create a new page for each test.

    Use in conftest.py:
        @pytest.fixture(scope="function")
        def page(context):
            yield from create_page_fixture(context)

    Args:
        context: Browser context fixture

    Yields:
        Playwright Page object
    """
    config = get_config()
    page = context.new_page()
    page.set_default_timeout(config.default_timeout)
    page.set_default_navigation_timeout(config.navigation_timeout)

    yield page

    page.close()


def create_authenticated_page_fixture(
    page: "Page",
    login_url: str,
    email_selector: str = "input[name='email'], input[type='email']",
    password_selector: str = "input[name='password'], input[type='password']",
    submit_selector: str = "button[type='submit']",
) -> Generator["Page", None, None]:
    """
    Create a page with authenticated user session.

    Use in conftest.py:
        @pytest.fixture(scope="function")
        def authenticated_page(page):
            yield from create_authenticated_page_fixture(
                page,
                login_url="/login",
            )

    Args:
        page: Playwright page fixture
        login_url: URL for login page
        email_selector: Selector for email input
        password_selector: Selector for password input
        submit_selector: Selector for submit button

    Yields:
        Authenticated Playwright Page object
    """
    config = get_config()

    if not config.has_credentials:
        logger.warning("Test credentials not configured, skipping authentication")
        yield page
        return

    # Navigate to login page
    page.goto(f"{config.base_url}{login_url}")

    # Fill credentials
    page.fill(email_selector, config.test_user_email or "")
    page.fill(password_selector, config.test_user_password or "")
    page.click(submit_selector)

    # Wait for navigation after login
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        logger.warning("Network idle timeout after login, continuing anyway")

    yield page


# =============================================================================
# Failure Handling
# =============================================================================


def handle_test_failure(
    request: "pytest.FixtureRequest",
    page: "Page"
) -> Generator[None, None, None]:
    """
    Automatically capture artifacts on test failure.

    Use in conftest.py:
        @pytest.fixture(scope="function", autouse=True)
        def handle_test_failure(request, page):
            yield from handle_test_failure(request, page)

    Args:
        request: Pytest request fixture
        page: Playwright page fixture

    Yields:
        None
    """
    yield

    # Check if test failed
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        config = get_config()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name = request.node.name

        # Capture screenshot
        if config.screenshot_on_failure:
            screenshot_name = f"{test_name}_{timestamp}_failure"
            screenshot_path = config.screenshot_path / f"{screenshot_name}.png"

            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Failure screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.error(f"Failed to take screenshot: {e}")

        # Log page URL and title for context
        try:
            logger.info(f"Failed on URL: {page.url}")
            logger.info(f"Page title: {page.title()}")
        except Exception:
            pass


def pytest_runtest_makereport_hook(item, call):
    """
    Make test results available to fixtures.

    Add to conftest.py:
        @pytest.hookimpl(tryfirst=True, hookwrapper=True)
        def pytest_runtest_makereport(item, call):
            outcome = yield
            rep = outcome.get_result()
            setattr(item, f"rep_{rep.when}", rep)
    """
    pass  # Placeholder - actual implementation goes in conftest.py


# =============================================================================
# Example conftest.py Template
# =============================================================================

CONFTEST_TEMPLATE = '''
"""
Pytest configuration for Playwright tests.

Copy this to your tests/conftest.py and customize as needed.
"""

import pytest
from playwright.sync_api import Page, BrowserContext

# Import from ADW playwright module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude"))

from playwright.config import get_config
from playwright.fixtures import (
    browser_type_launch_args as get_browser_launch_args,
    browser_context_args as get_browser_context_args,
    create_page_fixture,
    create_authenticated_page_fixture,
    handle_test_failure as handle_failure,
)


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Browser launch arguments."""
    return get_browser_launch_args()


@pytest.fixture(scope="session")
def browser_context_args():
    """Browser context arguments."""
    return get_browser_context_args()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """Fresh page for each test."""
    yield from create_page_fixture(context)


@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    """Page with authenticated user session."""
    yield from create_authenticated_page_fixture(page, login_url="/login")


@pytest.fixture(scope="function", autouse=True)
def handle_test_failure(request, page: Page):
    """Auto-capture artifacts on test failure."""
    yield from handle_failure(request, page)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Make test results available to fixtures."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "smoke: Quick smoke tests")
    config.addinivalue_line("markers", "regression: Full regression suite")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "map: Tests involving map/canvas")
'''


def generate_conftest(output_path: str) -> str:
    """
    Generate a conftest.py file from template.

    Args:
        output_path: Where to write the file

    Returns:
        Path to generated file
    """
    with open(output_path, "w") as f:
        f.write(CONFTEST_TEMPLATE)
    return output_path
