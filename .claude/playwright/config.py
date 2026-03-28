"""
Configuration for Playwright testing module.

Supports environment variables for flexible configuration across environments.
"""

import os
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass, field


@dataclass
class PlaywrightConfig:
    """Playwright execution configuration."""

    # Browser settings
    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    headless: bool = field(default_factory=lambda: os.getenv("HEADLESS", "false").lower() == "true")
    slow_mo: int = field(default_factory=lambda: int(os.getenv("SLOW_MO", "0")))

    # Timeouts (milliseconds)
    default_timeout: int = field(default_factory=lambda: int(os.getenv("DEFAULT_TIMEOUT", "30000")))
    navigation_timeout: int = field(default_factory=lambda: int(os.getenv("NAVIGATION_TIMEOUT", "30000")))
    action_timeout: int = field(default_factory=lambda: int(os.getenv("ACTION_TIMEOUT", "10000")))

    # Viewport
    viewport_width: int = field(default_factory=lambda: int(os.getenv("VIEWPORT_WIDTH", "1920")))
    viewport_height: int = field(default_factory=lambda: int(os.getenv("VIEWPORT_HEIGHT", "1080")))

    # URLs
    base_url: str = field(default_factory=lambda: os.getenv("BASE_URL", "http://localhost:3000"))

    # Screenshots
    screenshot_on_failure: bool = True
    screenshot_dir: str = field(default_factory=lambda: os.getenv("SCREENSHOT_DIR", "screenshots"))

    # Video recording
    video_recording: bool = field(default_factory=lambda: os.getenv("RECORD_VIDEO", "false").lower() == "true")
    video_dir: str = field(default_factory=lambda: os.getenv("VIDEO_DIR", "videos"))

    # Trace recording
    trace_enabled: bool = field(default_factory=lambda: os.getenv("TRACE_ENABLED", "false").lower() == "true")
    trace_dir: str = field(default_factory=lambda: os.getenv("TRACE_DIR", "traces"))

    # HTTPS
    ignore_https_errors: bool = True

    # Test credentials (from environment only - never hardcode)
    test_user_email: Optional[str] = field(default_factory=lambda: os.getenv("TEST_USER_EMAIL"))
    test_user_password: Optional[str] = field(default_factory=lambda: os.getenv("TEST_USER_PASSWORD"))

    # Canvas/Map specific settings
    map_load_wait_ms: int = field(default_factory=lambda: int(os.getenv("MAP_LOAD_WAIT_MS", "2000")))

    @property
    def screenshot_path(self) -> Path:
        """Get full path to screenshot directory, creating if needed."""
        path = Path(self.screenshot_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def video_path(self) -> Path:
        """Get full path to video directory, creating if needed."""
        path = Path(self.video_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def trace_path(self) -> Path:
        """Get full path to trace directory, creating if needed."""
        path = Path(self.trace_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def has_credentials(self) -> bool:
        """Check if test credentials are configured."""
        return bool(self.test_user_email and self.test_user_password)

    def get_browser_launch_args(self) -> dict:
        """Get arguments for browser launch."""
        return {
            "headless": self.headless,
            "slow_mo": self.slow_mo,
            "args": [
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
        }

    def get_context_args(self) -> dict:
        """Get arguments for browser context."""
        args = {
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height,
            },
            "ignore_https_errors": self.ignore_https_errors,
        }

        if self.video_recording:
            args["record_video_dir"] = str(self.video_path)
            args["record_video_size"] = {
                "width": self.viewport_width,
                "height": self.viewport_height,
            }

        return args


# Global config instance
_config: Optional[PlaywrightConfig] = None


def get_config() -> PlaywrightConfig:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = PlaywrightConfig()
    return _config


def reset_config() -> None:
    """Reset config (useful for testing)."""
    global _config
    _config = None
