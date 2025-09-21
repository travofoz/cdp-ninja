"""
Error Reporter - Captures crashes for debugging telemetry
Doesn't prevent anything, just reports what broke
This is valuable debugging data!
"""

import logging
import traceback
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque

logger = logging.getLogger(__name__)


class ErrorReporter:
    """
    Capture all errors for debugging telemetry
    The goal is to collect data about what breaks, not prevent breaking

    @class ErrorReporter
    @property {deque} crash_log - Recent crashes and errors
    @property {int} max_entries - Maximum entries to keep in memory
    """

    def __init__(self, max_entries: int = 1000):
        """
        Initialize error reporter

        @param {int} max_entries - Max crash entries to keep in memory
        """
        self.crash_log: deque = deque(maxlen=max_entries)
        self.stats = {
            'total_crashes': 0,
            'chrome_deaths': 0,
            'injection_attempts': 0,
            'malformed_requests': 0
        }

    def report_crash(self,
                    operation: str,
                    error: Exception,
                    context: Optional[Dict[str, Any]] = None,
                    request_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log a crash - this is valuable debugging data!

        @param {str} operation - What we were trying to do
        @param {Exception} error - What went wrong
        @param {dict} context - Additional context
        @param {dict} request_data - Raw request data that caused the crash
        @returns {dict} Crash data for immediate analysis
        """
        crash_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'request_data': request_data or {}
        }

        # Analyze the crash for patterns
        self._analyze_crash(crash_data, error)

        self.crash_log.append(crash_data)
        self.stats['total_crashes'] += 1

        logger.error(f"CRASH in {operation}: {error}")

        return crash_data

    def _analyze_crash(self, crash_data: Dict[str, Any], error: Exception):
        """
        Analyze crash patterns for debugging insights

        @param {dict} crash_data - Crash information
        @param {Exception} error - The exception that occurred
        """
        error_str = str(error).lower()

        # Chrome connection died
        if any(keyword in error_str for keyword in
               ['disconnected', 'connection closed', 'websocket', 'connection refused']):
            crash_data['chrome_died'] = True
            self.stats['chrome_deaths'] += 1
            logger.error("🔥 Chrome process appears to be dead!")

        # Potential injection attempt
        request_data = crash_data.get('request_data', {})
        if self._looks_like_injection(request_data):
            crash_data['potential_injection'] = True
            self.stats['injection_attempts'] += 1
            logger.info("💉 Potential injection attempt detected (this is good data!)")

        # Malformed request
        if any(keyword in error_str for keyword in
               ['invalid', 'malformed', 'parse error', 'syntax error']):
            crash_data['malformed_request'] = True
            self.stats['malformed_requests'] += 1
            logger.info("🗂️  Malformed request detected (good for fuzzing!)")

    def _looks_like_injection(self, request_data: Dict[str, Any]) -> bool:
        """
        Detect potential injection attempts in request data
        This is GOOD - we want to test these!

        @param {dict} request_data - Request data to analyze
        @returns {bool} True if looks like injection attempt
        """
        if not request_data:
            return False

        # Convert all values to strings for analysis
        all_text = json.dumps(request_data).lower()

        # Common injection patterns (we WANT to test these)
        injection_patterns = [
            '<script', 'javascript:', 'alert(', 'document.cookie',
            'drop table', 'union select', '\'; --', '$(', 'eval(',
            'system(', 'exec(', 'shell_exec', 'passthru'
        ]

        return any(pattern in all_text for pattern in injection_patterns)

    def report_success(self, operation: str, context: Optional[Dict[str, Any]] = None):
        """
        Report successful operations (for baseline comparison)

        @param {str} operation - What succeeded
        @param {dict} context - Success context
        """
        logger.debug(f"✅ SUCCESS: {operation}")

    def get_crash_summary(self) -> Dict[str, Any]:
        """
        Get summary of recent crashes

        @returns {dict} Crash statistics and recent entries
        """
        recent_crashes = list(self.crash_log)[-10:]  # Last 10 crashes

        return {
            'stats': self.stats.copy(),
            'recent_crashes': recent_crashes,
            'total_logged': len(self.crash_log),
            'chrome_health': 'DEAD' if self.stats['chrome_deaths'] > 0 else 'ALIVE'
        }

    def get_crash_by_operation(self, operation: str) -> List[Dict[str, Any]]:
        """
        Get all crashes for a specific operation

        @param {str} operation - Operation to filter by
        @returns {list} List of crashes for this operation
        """
        return [crash for crash in self.crash_log if crash['operation'] == operation]

    def clear_crashes(self):
        """
        Clear crash log (for testing or after analysis)
        """
        self.crash_log.clear()
        self.stats = {
            'total_crashes': 0,
            'chrome_deaths': 0,
            'injection_attempts': 0,
            'malformed_requests': 0
        }
        logger.info("🗑️  Crash log cleared")


# Global error reporter instance
crash_reporter = ErrorReporter()


def handle_crash(operation: str, request_data: Optional[Dict[str, Any]] = None):
    """
    Decorator to automatically report crashes from route handlers

    @param {str} operation - Name of the operation
    @param {dict} request_data - Request data that might have caused crash
    @returns {function} Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                crash_reporter.report_success(operation)
                return result
            except Exception as e:
                crash_data = crash_reporter.report_crash(
                    operation=operation,
                    error=e,
                    context={'function': func.__name__},
                    request_data=request_data
                )

                # Return the crash data as JSON - this is useful debugging info!
                from flask import jsonify
                return jsonify({
                    'crash': True,
                    'operation': operation,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'timestamp': crash_data['timestamp'],
                    'details': 'Check logs for full traceback'
                }), 500

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def get_global_crash_stats():
    """
    Get global crash statistics

    @returns {dict} Global crash summary
    """
    return crash_reporter.get_crash_summary()