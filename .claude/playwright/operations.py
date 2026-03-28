"""
Test execution operations for Playwright.

Handles running tests, parsing results, and capturing artifacts.
Adapted from AgenticTesting framework.
"""

import subprocess
import os
import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from datetime import datetime
from pathlib import Path

from .config import PlaywrightConfig, get_config
from .data_types import (
    TestResult,
    E2ETestResult,
    TestSuiteResult,
    FailureArtifacts,
    TestStatus,
    TestSuiteType,
)

if TYPE_CHECKING:
    from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def execute_playwright_tests(
    test_paths: List[str],
    config: Optional[PlaywrightConfig] = None,
    markers: Optional[List[str]] = None,
    parallel: bool = False,
    workers: int = 4,
    verbose: bool = True,
    json_report: bool = True,
    run_id: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> Tuple[bool, str, Optional[str]]:
    """
    Execute Playwright tests via pytest.

    Args:
        test_paths: List of test file paths or directories
        config: Playwright configuration
        markers: List of pytest markers to filter tests
        parallel: Run tests in parallel
        workers: Number of parallel workers
        verbose: Verbose output
        json_report: Generate JSON report
        run_id: Run ID for report naming
        working_dir: Working directory for test execution

    Returns:
        Tuple of (success, stdout, report_path)
    """
    config = config or get_config()
    working_dir = working_dir or os.getcwd()

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test paths
    cmd.extend(test_paths)

    # Add verbosity
    if verbose:
        cmd.append("-v")

    # Add markers
    if markers:
        marker_expr = " or ".join(markers)
        cmd.extend(["-m", marker_expr])

    # Add parallel execution
    if parallel:
        cmd.extend(["-n", str(workers)])

    # Add JSON report
    report_path = None
    if json_report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"test_report_{run_id}_{timestamp}" if run_id else f"test_report_{timestamp}"
        reports_dir = Path(working_dir) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = str(reports_dir / f"{report_name}.json")
        cmd.extend(["--json-report", f"--json-report-file={report_path}"])

    # Set environment variables for Playwright
    env = os.environ.copy()
    env["HEADLESS"] = str(config.headless).lower()
    env["SLOW_MO"] = str(config.slow_mo)
    env["PWDEBUG"] = "0"

    if run_id:
        env["RUN_ID"] = run_id

    logger.info(f"Executing pytest: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=working_dir,
            env=env,
            timeout=600,  # 10 minute timeout
        )

        success = result.returncode == 0
        output = result.stdout + result.stderr

        if not success:
            logger.warning(f"Tests failed with exit code {result.returncode}")

        return success, output, report_path

    except subprocess.TimeoutExpired:
        logger.error("Test execution timed out")
        return False, "Test execution timed out after 10 minutes", None
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return False, str(e), None


def parse_pytest_output(output: str) -> List[TestResult]:
    """
    Parse pytest console output to extract test results.

    Args:
        output: Raw pytest output

    Returns:
        List of TestResult objects
    """
    results = []

    # Pattern to match test results
    test_pattern = re.compile(
        r"([\w/\._]+)::(\w+)::(\w+)\s+(PASSED|FAILED|SKIPPED|ERROR)"
    )

    for match in test_pattern.finditer(output):
        file_path, class_name, test_name, status = match.groups()

        passed = status == "PASSED"
        error = None

        # Try to extract error message for failed tests
        if status == "FAILED":
            error_pattern = re.compile(
                rf"{re.escape(test_name)}.*?(?:AssertionError|Error|Exception):\s*(.+?)(?:\n\n|\Z)",
                re.DOTALL,
            )
            error_match = error_pattern.search(output)
            if error_match:
                error = error_match.group(1).strip()[:500]

        results.append(
            TestResult(
                test_name=f"{class_name}::{test_name}",
                test_file=file_path,
                passed=passed,
                error=error,
            )
        )

    return results


def parse_json_report(report_path: str) -> List[E2ETestResult]:
    """
    Parse pytest JSON report to extract detailed test results.

    Args:
        report_path: Path to JSON report file

    Returns:
        List of E2ETestResult objects
    """
    if not os.path.exists(report_path):
        logger.warning(f"Report file not found: {report_path}")
        return []

    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON report: {e}")
        return []

    results = []

    for test in report.get("tests", []):
        node_id = test.get("nodeid", "")
        outcome = test.get("outcome", "unknown")

        # Map outcome to status
        status_map: Dict[str, TestStatus] = {
            "passed": "passed",
            "failed": "failed",
            "skipped": "skipped",
            "error": "error",
        }
        status: TestStatus = status_map.get(outcome, "error")

        # Extract duration
        duration_ms = test.get("duration", 0) * 1000

        # Extract error info
        error = None
        if outcome in ("failed", "error"):
            call_info = test.get("call", {})
            if call_info:
                longrepr = call_info.get("longrepr", "")
                if longrepr:
                    error = str(longrepr)[:1000]

        # Parse node_id for file and test name
        parts = node_id.split("::")
        test_file = parts[0] if parts else ""
        test_name = "::".join(parts[1:]) if len(parts) > 1 else node_id

        results.append(
            E2ETestResult(
                test_name=test_name,
                test_file=test_file,
                status=status,
                duration_ms=duration_ms,
                error=error,
            )
        )

    return results


def create_test_suite_result(
    suite_name: str,
    suite_type: TestSuiteType,
    run_id: str,
    e2e_results: List[E2ETestResult],
    duration_seconds: float,
) -> TestSuiteResult:
    """
    Create a TestSuiteResult from E2E test results.

    Args:
        suite_name: Name of the test suite
        suite_type: Type of test suite
        run_id: Run ID
        e2e_results: List of E2E test results
        duration_seconds: Total duration

    Returns:
        TestSuiteResult object
    """
    passed = sum(1 for r in e2e_results if r.status == "passed")
    failed = sum(1 for r in e2e_results if r.status == "failed")
    skipped = sum(1 for r in e2e_results if r.status == "skipped")
    errors = sum(1 for r in e2e_results if r.status == "error")

    return TestSuiteResult(
        suite_name=suite_name,
        suite_type=suite_type,
        run_id=run_id,
        total_tests=len(e2e_results),
        passed=passed,
        failed=failed,
        skipped=skipped,
        error_count=errors,
        duration_seconds=duration_seconds,
        completed_at=datetime.now(),
        e2e_results=e2e_results,
    )


def run_smoke_tests(
    run_id: str,
    test_dir: str = "tests/e2e/smoke",
    config: Optional[PlaywrightConfig] = None,
) -> TestSuiteResult:
    """
    Run smoke test suite.

    Args:
        run_id: Run ID
        test_dir: Directory containing smoke tests
        config: Playwright configuration

    Returns:
        TestSuiteResult
    """
    start_time = datetime.now()

    success, output, report_path = execute_playwright_tests(
        test_paths=[test_dir],
        config=config,
        markers=["smoke"],
        run_id=run_id,
    )

    duration = (datetime.now() - start_time).total_seconds()

    # Parse results
    if report_path and os.path.exists(report_path):
        e2e_results = parse_json_report(report_path)
    else:
        test_results = parse_pytest_output(output)
        e2e_results = [
            E2ETestResult(
                test_name=r.test_name,
                test_file=r.test_file,
                status="passed" if r.passed else "failed",
                error=r.error,
            )
            for r in test_results
        ]

    return create_test_suite_result(
        suite_name="Smoke Tests",
        suite_type="smoke",
        run_id=run_id,
        e2e_results=e2e_results,
        duration_seconds=duration,
    )


def capture_page_artifacts(
    page: "Page",
    test_name: str,
    screenshot_dir: str = "screenshots",
) -> FailureArtifacts:
    """
    Capture all available artifacts from a page for debugging.

    Args:
        page: Playwright Page object
        test_name: Name of the test
        screenshot_dir: Directory for screenshots

    Returns:
        FailureArtifacts object
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(screenshot_dir, exist_ok=True)

    artifacts = FailureArtifacts()

    # Capture screenshot
    try:
        screenshot_path = os.path.join(
            screenshot_dir, f"{test_name}_{timestamp}_failure.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        artifacts.screenshot_path = screenshot_path
        logger.info(f"Screenshot saved: {screenshot_path}")
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")

    # Capture cookies
    try:
        artifacts.cookies = page.context.cookies()
    except Exception as e:
        logger.warning(f"Failed to capture cookies: {e}")

    # Capture local storage
    try:
        local_storage = page.evaluate("() => JSON.stringify(localStorage)")
        artifacts.local_storage = json.loads(local_storage) if local_storage else {}
    except Exception as e:
        logger.warning(f"Failed to capture localStorage: {e}")

    # Capture page HTML (truncated)
    try:
        artifacts.page_html = page.content()[:10000]
    except Exception as e:
        logger.warning(f"Failed to capture page HTML: {e}")

    # Capture map state if available
    try:
        map_state = page.evaluate("""
            (() => {
                if (window.map) {
                    return {
                        center: window.map.getCenter?.(),
                        zoom: window.map.getZoom?.(),
                        layers: window.map.getStyle?.()?.layers?.map(l => l.id),
                    };
                }
                return null;
            })()
        """)
        if map_state:
            artifacts.map_state = map_state
    except Exception:
        pass

    return artifacts


def install_playwright_browsers(browser: str = "chromium") -> bool:
    """
    Install Playwright browsers if not already installed.

    Args:
        browser: Browser to install (chromium, firefox, webkit)

    Returns:
        True if successful
    """
    try:
        result = subprocess.run(
            ["playwright", "install", browser],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            logger.info(f"Playwright {browser} installed successfully")
            return True
        else:
            logger.error(f"Failed to install {browser}: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Failed to install Playwright browsers: {e}")
        return False
