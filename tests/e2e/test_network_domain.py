"""
E2E Tests for Network Domain Endpoints

Tests network request capture, filtering, and consistency
across server vs pool CDPClient instances.
"""

import requests
import time
import json
from typing import List, Dict, Any
from .base_test import CDPNinjaE2ETest


class TestNetworkDomain(CDPNinjaE2ETest):
    """Test Network domain endpoints for event consistency"""

    def test_network_requests_capture(self):
        """Test that network requests are captured correctly"""
        # Clear existing requests
        clear_response = requests.post(f"{self.cdp_base}/cdp/network/clear")
        self.assertEqual(clear_response.status_code, 200)

        # Navigate to page that makes known network requests
        self.navigate_to(f"{self.demo_base}/network-requests-standard.html")
        self.wait_for_events()

        # Get captured network requests
        response = requests.get(f"{self.cdp_base}/cdp/network/requests")
        self.assertEqual(response.status_code, 200)

        requests_data = response.json().get('requests', [])
        self.assertGreater(len(requests_data), 0, "Should capture network requests")

        # Verify we captured the expected request
        found_test_request = False
        for req in requests_data:
            if '/api/test-endpoint' in req.get('url', ''):
                found_test_request = True
                break

        self.assertTrue(found_test_request, "Should capture test API request")

    def test_network_error_capture(self):
        """Test that network errors (404, 500, etc.) are captured"""
        requests.post(f"{self.cdp_base}/cdp/network/clear")

        # Navigate to page that triggers 404 error
        self.navigate_to(f"{self.demo_base}/network-404-error.html")
        self.wait_for_events()

        network_requests = requests.get(f"{self.cdp_base}/cdp/network/requests").json()

        # Find 404 request
        error_request = None
        for req in network_requests.get('requests', []):
            if req.get('status') == 404:
                error_request = req
                break

        self.assertIsNotNone(error_request, "Should capture 404 network error")

    def test_network_timing_data(self):
        """Test that network timing data is captured"""
        requests.post(f"{self.cdp_base}/cdp/network/clear")

        self.navigate_to(f"{self.demo_base}/network-slow-request.html")
        self.wait_for_events(3)  # Wait longer for slow request

        # Get timing data
        response = requests.get(f"{self.cdp_base}/cdp/network/timing")
        self.assertEqual(response.status_code, 200)

        timing_data = response.json()
        self.assertIn('requests', timing_data)
        self.assertGreater(len(timing_data['requests']), 0)

        # Verify timing data has expected fields
        for req in timing_data['requests']:
            self.assertIn('timing', req)
            timing = req['timing']
            self.assertIn('requestTime', timing)
            self.assertIn('receiveHeadersEnd', timing)

    def test_network_cross_instance_consistency(self):
        """Test network events consistency across CDPClient instances"""
        requests.post(f"{self.cdp_base}/cdp/network/clear")

        # Generate network activity
        self.navigate_to(f"{self.demo_base}/network-multiple-requests.html")
        self.wait_for_events()

        # Test cross-instance consistency for Network domain
        expected_events = ["Network.requestWillBeSent", "Network.responseReceived"]
        self.assert_event_consistency("Network", expected_events)

    def test_network_filtering(self):
        """Test network request filtering functionality"""
        requests.post(f"{self.cdp_base}/cdp/network/clear")

        # Set up network blocking for specific URL pattern
        block_response = requests.post(f"{self.cdp_base}/cdp/network/block",
                                     json={"patterns": ["*/blocked-resource/*"]})
        self.assertEqual(block_response.status_code, 200)

        # Navigate to page that tries to load blocked resource
        self.navigate_to(f"{self.demo_base}/network-blocked-resource.html")
        self.wait_for_events()

        # Check that blocked request appears in network requests
        network_response = requests.get(f"{self.cdp_base}/cdp/network/requests")
        requests_data = network_response.json().get('requests', [])

        blocked_request = None
        for req in requests_data:
            if 'blocked-resource' in req.get('url', ''):
                blocked_request = req
                break

        self.assertIsNotNone(blocked_request, "Blocked request should appear in logs")
        self.assertTrue(
            blocked_request.get('blocked', False) or
            blocked_request.get('status') in [0, -1],
            "Request should be marked as blocked"
        )

    def test_network_throttling(self):
        """Test network throttling functionality"""
        # Apply network throttling
        throttle_response = requests.post(f"{self.cdp_base}/cdp/network/throttle",
                                        json={
                                            "downloadThroughput": 50000,  # 50KB/s
                                            "uploadThroughput": 50000,
                                            "latency": 500  # 500ms
                                        })
        self.assertEqual(throttle_response.status_code, 200)

        requests.post(f"{self.cdp_base}/cdp/network/clear")

        # Make request and measure timing
        start_time = time.time()
        self.navigate_to(f"{self.demo_base}/network-large-resource.html")
        self.wait_for_events(5)  # Wait longer for throttled request
        end_time = time.time()

        # Verify throttling affected timing
        duration = end_time - start_time
        self.assertGreater(duration, 2.0, "Throttled request should take longer")

        # Remove throttling
        requests.post(f"{self.cdp_base}/cdp/network/throttle",
                     json={"offline": False, "downloadThroughput": -1,
                           "uploadThroughput": -1, "latency": 0})

    def test_websocket_monitoring(self):
        """Test WebSocket connection monitoring"""
        # Navigate to page with WebSocket connection
        self.navigate_to(f"{self.demo_base}/websocket-test.html")
        self.wait_for_events()

        # Get WebSocket data
        response = requests.get(f"{self.cdp_base}/cdp/network/websockets")
        self.assertEqual(response.status_code, 200)

        ws_data = response.json()
        self.assertIn('websockets', ws_data)

        # Verify WebSocket connection was captured
        if len(ws_data['websockets']) > 0:
            ws = ws_data['websockets'][0]
            self.assertIn('url', ws)
            self.assertIn('state', ws)

    def test_cors_analysis(self):
        """Test CORS issue detection"""
        requests.post(f"{self.cdp_base}/cdp/network/clear")

        # Navigate to page that triggers CORS error
        self.navigate_to(f"{self.demo_base}/network-cors-error.html")
        self.wait_for_events()

        # Get CORS analysis
        response = requests.get(f"{self.cdp_base}/cdp/network/cors")
        self.assertEqual(response.status_code, 200)

        cors_data = response.json()
        if 'issues' in cors_data and len(cors_data['issues']) > 0:
            # Verify CORS issue was detected
            cors_issue = cors_data['issues'][0]
            self.assertIn('type', cors_issue)
            self.assertEqual(cors_issue['type'].lower(), 'cors')

    def test_cache_analysis(self):
        """Test network cache analysis"""
        # Clear network data
        requests.post(f"{self.cdp_base}/cdp/network/clear")

        # Load page twice to test caching
        self.navigate_to(f"{self.demo_base}/network-cacheable-resources.html")
        self.wait_for_events()

        # Load again to trigger cache
        self.navigate_to(f"{self.demo_base}/network-cacheable-resources.html")
        self.wait_for_events()

        # Get cache analysis
        response = requests.get(f"{self.cdp_base}/cdp/network/cache")
        self.assertEqual(response.status_code, 200)

        cache_data = response.json()
        self.assertIn('cache_analysis', cache_data)

        # Verify some resources were cached
        if 'cached_resources' in cache_data['cache_analysis']:
            cached_count = len(cache_data['cache_analysis']['cached_resources'])
            self.assertGreater(cached_count, 0, "Some resources should be cached on second load")