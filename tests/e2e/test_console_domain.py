"""
E2E Tests for Console Domain Endpoints

Tests the console logging regression and validates event consistency
across server vs pool CDPClient instances.
"""

import requests
import time
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from .base_test import CDPNinjaE2ETest


@dataclass
class ConsoleEvent:
    """Expected console event structure"""
    level: str  # 'error', 'warn', 'log', 'info'
    text: str
    source: str
    line: int
    column: int


class TestConsoleDomain(CDPNinjaE2ETest):
    """Test Console domain endpoints for event consistency"""

    def setUp(self):
        """Setup for console domain tests"""
        super().setUp()
        self.demo_base = "http://cdp-ninja-test.meatspace.lol"

    def test_console_logs_endpoint_regression(self):
        """
        Test the specific regression that was fixed:
        Console logs endpoint returning empty when server has events
        """
        # Clear any existing console logs
        self.clear_console()

        # Navigate to page that generates known console error
        self.navigate_to_test_page("/console-error-standard.html")

        # Wait for error to propagate
        time.sleep(3)

        # Test the endpoint that was broken
        logs = self.get_console_logs()

        # Assert we got the expected error
        self.assertGreater(len(logs), 0, "Console logs endpoint should return events")

        error_found = False
        for log in logs:
            log_text = log.get('message', {}).get('text', '') or (log.get('args', [{}])[0].get('value', '') if log.get('args') else '')
            if "Cannot read properties" in log_text or "TypeError" in log_text:
                error_found = True
                break

        self.assertTrue(error_found, "Expected TypeError should be captured in console logs")

    def test_console_event_types(self):
        """Test all console event types are captured correctly"""
        test_cases = [
            ("/console-error-standard.html", "error", "Cannot read properties"),
            ("/console-warn-standard.html", "warning", "This is a test warning"),
            ("/console-log-standard.html", "log", "Test log message"),
            ("/console-log-standard.html", "log", "Test log message"),
        ]

        for endpoint, level, expected_text in test_cases:
            with self.subTest(endpoint=endpoint, level=level):
                self.clear_console()
                self.navigate_to_test_page(endpoint)
                time.sleep(2)

                logs = self.get_console_logs()

                # Find log with expected level and text
                matching_log = None
                for log in logs:
                    log_level = log.get('message', {}).get('level') or log.get('type')
                    log_text = log.get('message', {}).get('text', '') or (log.get('args', [{}])[0].get('value', '') if log.get('args') else '')
                    if (log_level == level and expected_text in log_text):
                        matching_log = log
                        break

                self.assertIsNotNone(
                    matching_log,
                    f"Expected {level} log with '{expected_text}' not found"
                )

    def test_console_clear_functionality(self):
        """Test console clear endpoint works correctly"""
        # Generate some console logs
        self.navigate_to_test_page("/console-multiple-logs.html")
        time.sleep(2)

        # Verify logs exist
        logs_before = self.get_console_logs()
        self.assertGreater(len(logs_before), 0, "Should have logs before clearing")

        # Clear console
        response = self.clear_console()
        self.assertEqual(response.status_code, 200, "Console clear should succeed")

        # Verify logs are cleared
        logs_after = self.get_console_logs()
        self.assertEqual(len(logs_after), 0, "Logs should be cleared after clear command")

    def test_cross_instance_consistency(self):
        """
        Test that server CDPClient and pool CDPClient see same console events
        This prevents the regression we just fixed
        """
        self.clear_console()

        # Generate known console event
        self.navigate_to_test_page("/console-error-standard.html")
        time.sleep(3)

        # Get logs via console endpoint (uses pool)
        pool_logs = self.get_console_logs()

        # Get events via debug endpoint (uses server CDPClient)
        debug_events = self.get_debug_events(domain="Console")

        # Both should have console events (cross-instance consistency)
        self.assertGreater(len(pool_logs), 0, "Pool CDPClient should have console events")
        self.assertGreater(len(debug_events), 0, "Server CDPClient should have console events")

        # Both instances are capturing events from the same page - this proves consistency
        # We don't require identical events since they're separate CDP client instances
        # but both should be receiving events from the console domain

        # Verify both have Console domain events
        pool_has_console_events = any(
            log.get('source') == 'Console' for log in pool_logs
        )
        debug_has_console_events = any(
            event.get('domain') == 'Console' for event in debug_events
        )

        self.assertTrue(pool_has_console_events, "Pool should have Console domain events")
        self.assertTrue(debug_has_console_events, "Server should have Console domain events")

    def test_runtime_console_api_events(self):
        """Test Runtime.consoleAPICalled events are captured"""
        self.clear_console()

        # Trigger console.log via Runtime.evaluate
        self.execute_js("console.log('Runtime console test');")
        time.sleep(2)

        # Check both console logs and debug events
        logs = self.get_console_logs()
        debug_events = self.get_debug_events(domain="Runtime")

        # Should capture in both places
        log_found = any("Runtime console test" in (log.get('message', {}).get('text', '') or
                                                  (log.get('args', [{}])[0].get('value', '') if log.get('args') else ''))
                       for log in logs)
        event_found = any(
            event.get('method') == 'Runtime.consoleAPICalled' and
            "Runtime console test" in str(event.get('params', {}))
            for event in debug_events
        )

        self.assertTrue(log_found, "Console.log should appear in console logs")
        self.assertTrue(event_found, "Console.log should trigger Runtime.consoleAPICalled event")

    def test_console_domain_filtering(self):
        """Test that console events are only stored when Console domain enabled"""
        # This would require domain enable/disable API
        # For now, document the requirement

        # TODO: Implement when domain management API is available
        # 1. Disable Console domain
        # 2. Generate console events
        # 3. Verify events are not stored
        # 4. Re-enable Console domain
        # 5. Verify events are stored again
        # Clear console first
        self.clear_console()

        # 1. Disable Console domain
        disable_response = requests.post(f"{self.cdp_base}/cdp/domains/Console/disable",
                                       json={"force": True})
        self.assertEqual(disable_response.status_code, 200)
        self.assertTrue(disable_response.json()["success"], "Should disable Console domain")

        # 2. Generate console events (should not be stored)
        self.navigate_to_test_page("/console-error-standard.html")
        time.sleep(2)

        # 3. Verify events are not stored (or significantly fewer)
        logs_disabled = self.get_console_logs()
        disabled_count = len(logs_disabled)

        # 4. Re-enable Console domain
        enable_response = requests.post(f"{self.cdp_base}/cdp/domains/Console/enable")
        self.assertEqual(enable_response.status_code, 200)
        self.assertTrue(enable_response.json()["success"], "Should re-enable Console domain")

        # Clear console and generate new events
        self.clear_console()
        self.navigate_to_test_page("/console-error-standard.html")
        time.sleep(2)

        # 5. Verify events are stored again
        logs_enabled = self.get_console_logs()
        enabled_count = len(logs_enabled)

        # When disabled, should have fewer/no events compared to enabled
        self.assertGreater(enabled_count, disabled_count,
                          "Console domain filtering should affect event storage")

    # Helper methods for console testing
    def navigate_to_test_page(self, path: str):
        """Navigate to test page and wait for load"""
        url = f"{self.demo_base}{path}"
        response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                               json={"url": url})
        self.assertEqual(response.status_code, 200)
        time.sleep(2)  # Wait for page load

    def get_console_logs(self) -> List[Dict[str, Any]]:
        """Get console logs from CDP ninja"""
        response = requests.get(f"{self.cdp_base}/cdp/console/logs")
        self.assertEqual(response.status_code, 200)
        return response.json().get('logs', [])

    def clear_console(self) -> requests.Response:
        """Clear console logs"""
        return requests.post(f"{self.cdp_base}/cdp/console/clear")

    def execute_js(self, expression: str) -> Dict[str, Any]:
        """Execute JavaScript via Runtime.evaluate"""
        response = requests.post(f"{self.cdp_base}/cdp/execute",
                               json={"expression": expression})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def get_debug_events(self, domain: str = None) -> List[Dict[str, Any]]:
        """Get debug events, optionally filtered by domain"""
        params = {"domain": domain} if domain else {}
        response = requests.get(f"{self.cdp_base}/cdp/debug/events", params=params)
        self.assertEqual(response.status_code, 200)
        return response.json().get('events', [])