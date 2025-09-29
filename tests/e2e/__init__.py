"""
CDP Ninja E2E Test Suite

Domain-based testing to prevent architectural regressions like
the console logging issue that was fixed in v2.0.8.

Complete test coverage for all 90 endpoints across 10 domains.
"""

from .base_test import CDPNinjaE2ETest
from .test_console_domain import TestConsoleDomain
from .test_network_domain import TestNetworkDomain
from .test_performance_domain import TestPerformanceDomain
from .test_dom_domain import TestDOMDomain
from .test_security_domain import TestSecurityDomain
from .test_accessibility_domain import TestAccessibilityDomain
from .test_error_handling_domain import TestErrorHandlingDomain
from .test_stress_testing_domain import TestStressTestingDomain
from .test_browser_interaction_domain import TestBrowserInteractionDomain
from .test_navigation_domain import TestNavigationDomain
from .test_js_debugging_domain import TestJSDebuggingDomain
from .test_system_domain import TestSystemDomain

__all__ = [
    'CDPNinjaE2ETest',
    'TestConsoleDomain',
    'TestNetworkDomain',
    'TestPerformanceDomain',
    'TestDOMDomain',
    'TestSecurityDomain',
    'TestAccessibilityDomain',
    'TestErrorHandlingDomain',
    'TestStressTestingDomain',
    'TestBrowserInteractionDomain',
    'TestNavigationDomain',
    'TestJSDebuggingDomain',
    'TestSystemDomain'
]