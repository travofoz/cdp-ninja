"""
CDP Ninja Route Modules
Raw pass-through routes with no validation or sanitization
Each module handles a specific aspect of browser debugging
"""

from .browser import browser_routes
from .debugging import debugging_routes
from .navigation import navigation_routes
from .dom import dom_routes
from .dom_advanced import dom_advanced_routes
from .network_intelligence import network_intelligence_routes
from .js_debugging import js_debugging_routes
from .stress_testing import stress_testing_routes
from .system import system_routes
from .error_handling import error_handling_routes
from .cloud_hiding import cloud_hiding_routes
from .righteous import righteous_routes
from .high_tree import high_tree_routes
from .tiger_knockdown import tiger_knockdown_routes

__all__ = [
    'browser_routes',
    'debugging_routes',
    'navigation_routes',
    'dom_routes',
    'dom_advanced_routes',
    'network_intelligence_routes',
    'js_debugging_routes',
    'stress_testing_routes',
    'system_routes',
    'error_handling_routes',
    'cloud_hiding_routes',
    'righteous_routes',
    'high_tree_routes',
    'tiger_knockdown_routes'
]