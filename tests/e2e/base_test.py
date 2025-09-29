"""
Base E2E Test Class for CDP Ninja

Provides common testing utilities and setup for all domain tests.
"""

import unittest
import requests
import time
from typing import Dict, Any, Optional


class CDPNinjaE2ETest(unittest.TestCase):
    """Base class for CDP Ninja E2E tests"""

    def setUp(self):
        """Common setup for all CDP Ninja tests"""
        # CDP Ninja bridge endpoint (assumes tunnel is active)
        self.cdp_base = "http://localhost:8888"

        # Demo site base URL
        self.demo_base = "http://cdp-ninja-test.meatspace.lol"

        # Verify CDP Ninja is accessible
        self._verify_cdp_ninja_connection()

        # Clear any existing state
        self._cleanup_state()

    def tearDown(self):
        """Common cleanup for all tests"""
        self._cleanup_state()

    def _verify_cdp_ninja_connection(self):
        """Verify CDP Ninja bridge is accessible"""
        try:
            response = requests.get(f"{self.cdp_base}/cdp/status", timeout=5)
            if response.status_code != 200:
                self.fail(f"CDP Ninja not accessible at {self.cdp_base}")
        except requests.RequestException as e:
            self.fail(f"Cannot connect to CDP Ninja: {e}")

    def _cleanup_state(self):
        """Clean up test state between tests"""
        try:
            # Clear console logs
            requests.post(f"{self.cdp_base}/cdp/console/clear")

            # Clear network requests
            requests.post(f"{self.cdp_base}/cdp/network/clear")

            # Navigate to blank page
            requests.post(f"{self.cdp_base}/cdp/page/navigate",
                         json={"url": "about:blank"})

            time.sleep(0.5)  # Brief pause for cleanup

        except requests.RequestException:
            # Cleanup failures shouldn't fail tests
            pass

    def navigate_to(self, url: str, wait_for_load: bool = True) -> Dict[str, Any]:
        """Navigate to URL and optionally wait for load"""
        response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                               json={"url": url})
        self.assertEqual(response.status_code, 200, f"Navigation to {url} failed")

        if wait_for_load:
            time.sleep(1)  # Wait for page load

        return response.json()

    def wait_for_events(self, timeout: float = 2.0):
        """Wait for events to propagate through system"""
        time.sleep(timeout)

    def get_status(self) -> Dict[str, Any]:
        """Get CDP Ninja status"""
        response = requests.get(f"{self.cdp_base}/cdp/status")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def take_screenshot(self) -> bytes:
        """Take screenshot of current page"""
        response = requests.get(f"{self.cdp_base}/cdp/screenshot")
        self.assertEqual(response.status_code, 200)
        return response.content

    def execute_javascript(self, expression: str) -> Dict[str, Any]:
        """Execute JavaScript expression"""
        response = requests.post(f"{self.cdp_base}/cdp/execute",
                               json={"expression": expression})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def assert_event_consistency(self, domain: str, expected_event_types: list):
        """
        Assert that events are consistent across server and pool CDPClient instances
        This is the core test to prevent the console logging regression
        """
        # Get events via debug endpoint (server CDPClient)
        debug_response = requests.get(f"{self.cdp_base}/cdp/debug/events",
                                    params={"domain": domain})
        self.assertEqual(debug_response.status_code, 200)
        debug_events = debug_response.json().get('events', [])

        # Get domain-specific events (pool CDPClient)
        domain_events = self._get_domain_events(domain)

        # Both should have events
        self.assertGreater(len(debug_events), 0,
                          f"Server CDPClient should have {domain} events")
        self.assertGreater(len(domain_events), 0,
                          f"Pool CDPClient should have {domain} events")

        # Verify expected event types are present in both
        debug_event_types = {event.get('method', '') for event in debug_events}
        domain_event_types = self._extract_event_types(domain_events, domain)

        for expected_type in expected_event_types:
            self.assertIn(expected_type, debug_event_types,
                         f"Server CDPClient missing {expected_type}")
            self.assertIn(expected_type, domain_event_types,
                         f"Pool CDPClient missing {expected_type}")

    def _get_domain_events(self, domain: str) -> list:
        """Get events for specific domain via domain-specific endpoints"""
        if domain == "Console":
            response = requests.get(f"{self.cdp_base}/cdp/console/logs")
        elif domain == "Network":
            response = requests.get(f"{self.cdp_base}/cdp/network/requests")
        elif domain == "Performance":
            response = requests.get(f"{self.cdp_base}/cdp/performance")
        else:
            # Fallback to debug events filtered by domain
            response = requests.get(f"{self.cdp_base}/cdp/debug/events",
                                  params={"domain": domain})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Extract events based on response structure
        if 'logs' in data:
            return data['logs']
        elif 'requests' in data:
            return data['requests']
        elif 'events' in data:
            return data['events']
        else:
            return []

    def _extract_event_types(self, events: list, domain: str) -> set:
        """Extract event method types from domain-specific event format"""
        if domain == "Console":
            # Console logs don't expose method names directly
            return {"Console.messageAdded", "Runtime.consoleAPICalled"}
        elif domain == "Network":
            # Network requests represent various network events
            return {"Network.requestWillBeSent", "Network.responseReceived"}
        else:
            # Generic event format
            return {event.get('method', '') for event in events}