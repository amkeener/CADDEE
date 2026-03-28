"""
Page Object Models for Playwright testing.

Provides base classes and specialized page objects for canvas/map testing.
"""

from .base_page import BasePage
from .map_page import MapPage

__all__ = ["BasePage", "MapPage"]
