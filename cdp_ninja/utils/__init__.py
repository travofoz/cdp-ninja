"""
CDP Ninja Utilities
Raw debugging utilities with no safety features
"""

from .error_reporter import ErrorReporter, crash_reporter
from .error_handling import handle_cdp_error

__all__ = [
    'ErrorReporter',
    'crash_reporter',
    'handle_cdp_error'
]