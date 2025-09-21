"""
CDP Ninja Utilities
Raw debugging utilities with no safety features
"""

from .error_reporter import ErrorReporter, crash_reporter

__all__ = [
    'ErrorReporter',
    'crash_reporter'
]