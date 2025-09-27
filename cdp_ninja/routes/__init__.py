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
from .performance import performance_routes
from .security import security_routes
from .accessibility import accessibility_routes
from .stress_testing_advanced import stress_testing_advanced_routes

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
    'performance_routes',
    'security_routes',
    'accessibility_routes',
    'stress_testing_advanced_routes'
]