"""
Data types for Playwright testing module.

Defines models for test results, artifacts, and failure analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal


# Type aliases
TestStatus = Literal["passed", "failed", "skipped", "error"]
TestSuiteType = Literal["smoke", "regression", "feature", "e2e", "acceptance"]
FailureType = Literal[
    "assertion",
    "timeout",
    "element_not_found",
    "canvas_interaction",
    "api_error",
    "network_error",
    "authentication",
    "unknown",
]


@dataclass
class TestResult:
    """Individual test result from test suite execution."""

    test_name: str
    test_file: str
    passed: bool
    duration_ms: float = 0.0
    error: Optional[str] = None
    error_line: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


@dataclass
class E2ETestResult:
    """Individual E2E test result from Playwright browser automation."""

    test_name: str
    test_file: str
    status: TestStatus
    duration_ms: float = 0.0
    screenshots: List[str] = field(default_factory=list)
    video_path: Optional[str] = None
    trace_path: Optional[str] = None
    console_logs: List[str] = field(default_factory=list)
    network_errors: List[str] = field(default_factory=list)
    error: Optional[str] = None
    error_line: Optional[int] = None

    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == "passed"


@dataclass
class FailureArtifacts:
    """Artifacts captured on test failure."""

    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    trace_path: Optional[str] = None
    console_logs: List[str] = field(default_factory=list)
    network_requests: List[Dict[str, Any]] = field(default_factory=list)
    network_errors: List[str] = field(default_factory=list)
    page_html: Optional[str] = None
    local_storage: Dict[str, str] = field(default_factory=dict)
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    map_state: Optional[Dict[str, Any]] = None  # For canvas/map debugging


@dataclass
class FailureAnalysis:
    """Analysis of a test failure with suggested fixes."""

    test_name: str
    test_file: str
    failure_type: FailureType
    root_cause: str
    suggested_fix: str
    confidence: Literal["high", "medium", "low"]
    code_snippet: Optional[str] = None
    related_files: List[str] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    steps_to_reproduce: List[str] = field(default_factory=list)


@dataclass
class TestSuiteResult:
    """Results from a complete test suite run."""

    suite_name: str
    suite_type: TestSuiteType
    run_id: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    error_count: int = 0
    duration_seconds: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    test_results: List[TestResult] = field(default_factory=list)
    e2e_results: List[E2ETestResult] = field(default_factory=list)
    failure_analyses: List[FailureAnalysis] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    @property
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0 and self.error_count == 0


@dataclass
class MapTestContext:
    """Context for map/canvas testing."""

    map_container_selector: str = "canvas"
    map_ready_indicator: Optional[str] = None  # CSS selector that appears when map is ready
    default_zoom_level: int = 15
    tile_load_wait_ms: int = 2000
    layer_names: List[str] = field(default_factory=list)

    # Coordinate system info
    uses_geographic_coords: bool = True  # vs pixel coords
    default_center: Optional[tuple] = None  # (lng, lat) or (x, y)
