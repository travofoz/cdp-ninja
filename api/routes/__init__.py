"""
CDP Ninja Route Modules
Raw pass-through routes with no validation or sanitization
Each module handles a specific aspect of browser debugging
"""

from .browser import browser_routes
from .debugging import debugging_routes
from .navigation import navigation_routes
from .dom import dom_routes
from .system import system_routes

__all__ = [
    'browser_routes',
    'debugging_routes',
    'navigation_routes',
    'dom_routes',
    'system_routes'
]