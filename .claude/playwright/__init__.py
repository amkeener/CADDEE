"""
Playwright Testing Module for ADW.

Provides E2E testing infrastructure with specialized support for
canvas-based applications like ArcGIS and MapLibre maps.
"""

from .config import PlaywrightConfig, get_config
from .data_types import (
    TestResult,
    E2ETestResult,
    TestSuiteResult,
    FailureArtifacts,
    TestStatus,
)

__all__ = [
    "PlaywrightConfig",
    "get_config",
    "TestResult",
    "E2ETestResult",
    "TestSuiteResult",
    "FailureArtifacts",
    "TestStatus",
]

__version__ = "1.0.0"
