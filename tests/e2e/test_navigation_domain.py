"""
E2E Tests for Navigation Domain Endpoints

Tests page navigation, reload, history management,
viewport control, and cookie management.
"""

import requests
import time
from typing import Dict, Any
from .base_test import CDPNinjaE2ETest


class TestNavigationDomain(CDPNinjaE2ETest):
    """Test Navigation domain endpoints for page control"""

    def test_page_navigation(self):
        """Test page navigation functionality"""
        # Test basic navigation
        response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                               json={"url": f"{self.demo_base}/navigation-test-page"})
        self.assertEqual(response.status_code, 200)

        nav_data = response.json()
        self.assertIn('navigation_result', nav_data)
        self.assertTrue(nav_data['navigation_result']['success'])

        # Wait for page load
        self.wait_for_events()

        # Test navigation with options
        options_response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                                       json={
                                           "url": f"{self.demo_base}/navigation-with-options",
                                           "wait_for_load": True,
                                           "timeout": 10000
                                       })
        self.assertEqual(options_response.status_code, 200)

        # Test navigation to invalid URL
        invalid_response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                                       json={"url": "https://invalid-url-that-does-not-exist.com"})
        # Should handle gracefully
        self.assertIn(invalid_response.status_code, [200, 400])

    def test_page_reload(self):
        """Test page reload functionality"""
        # Navigate to a page first
        self.navigate_to(f"{self.demo_base}/navigation-reload-test.html")
        self.wait_for_events()

        # Test basic reload
        response = requests.post(f"{self.cdp_base}/cdp/page/reload")
        self.assertEqual(response.status_code, 200)

        reload_data = response.json()
        self.assertIn('reload_result', reload_data)

        # Test reload with cache bypass
        cache_bypass_response = requests.post(f"{self.cdp_base}/cdp/page/reload",
                                            json={"ignore_cache": True})
        self.assertEqual(cache_bypass_response.status_code, 200)

        # Test reload with script evaluation
        script_response = requests.post(f"{self.cdp_base}/cdp/page/reload",
                                      json={
                                          "ignore_cache": False,
                                          "script_to_evaluate": "console.log('Page reloaded');"
                                      })
        self.assertEqual(script_response.status_code, 200)

    def test_page_history_navigation(self):
        """Test browser history navigation (back/forward)"""
        # Navigate to multiple pages to build history
        self.navigate_to(f"{self.demo_base}/navigation-page-1.html")
        self.wait_for_events()

        self.navigate_to(f"{self.demo_base}/navigation-page-2.html")
        self.wait_for_events()

        self.navigate_to(f"{self.demo_base}/navigation-page-3.html")
        self.wait_for_events()

        # Test back navigation
        back_response = requests.post(f"{self.cdp_base}/cdp/page/back")
        self.assertEqual(back_response.status_code, 200)

        back_data = back_response.json()
        self.assertIn('navigation_result', back_data)

        self.wait_for_events()

        # Test forward navigation
        forward_response = requests.post(f"{self.cdp_base}/cdp/page/forward")
        self.assertEqual(forward_response.status_code, 200)

        forward_data = forward_response.json()
        self.assertIn('navigation_result', forward_data)

        # Test back when no history available
        # Navigate to fresh page first
        self.navigate_to("about:blank")
        self.wait_for_events()

        no_history_response = requests.post(f"{self.cdp_base}/cdp/page/back")
        # Should handle gracefully
        self.assertIn(no_history_response.status_code, [200, 400])

    def test_page_stop(self):
        """Test page loading stop functionality"""
        # Start navigation to slow-loading page
        slow_nav_response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                                        json={"url": f"{self.demo_base}/navigation-slow-page"})
        self.assertEqual(slow_nav_response.status_code, 200)

        # Immediately stop the loading
        stop_response = requests.post(f"{self.cdp_base}/cdp/page/stop")
        self.assertEqual(stop_response.status_code, 200)

        stop_data = stop_response.json()
        self.assertIn('stop_result', stop_data)

    def test_page_info_retrieval(self):
        """Test page information retrieval"""
        # Navigate to info test page
        self.navigate_to(f"{self.demo_base}/navigation-info-test.html")
        self.wait_for_events()

        # Get page info
        response = requests.get(f"{self.cdp_base}/cdp/page/info")
        self.assertEqual(response.status_code, 200)

        info_data = response.json()
        self.assertIn('page_info', info_data)

        page_info = info_data['page_info']
        expected_fields = ['url', 'title', 'ready_state']

        for field in expected_fields:
            self.assertIn(field, page_info)

        # Verify URL matches expected
        self.assertIn('navigation-info-test', page_info['url'])

    def test_viewport_control(self):
        """Test viewport size and device emulation"""
        # Navigate to viewport test page
        self.navigate_to(f"{self.demo_base}/navigation-viewport-test.html")
        self.wait_for_events()

        # Test viewport resize
        viewport_sizes = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 768, "height": 1024},   # Tablet
            {"width": 375, "height": 667},    # Mobile
        ]

        for viewport in viewport_sizes:
            with self.subTest(viewport=viewport):
                response = requests.post(f"{self.cdp_base}/cdp/page/viewport",
                                       json=viewport)
                self.assertEqual(response.status_code, 200)

                viewport_data = response.json()
                self.assertIn('viewport_result', viewport_data)

                self.wait_for_events(0.5)  # Wait for resize

        # Test device emulation
        device_response = requests.post(f"{self.cdp_base}/cdp/page/viewport",
                                      json={
                                          "width": 375,
                                          "height": 667,
                                          "device_scale_factor": 2,
                                          "mobile": True,
                                          "touch_enabled": True
                                      })
        self.assertEqual(device_response.status_code, 200)

    def test_cookie_management(self):
        """Test cookie getting and setting"""
        # Navigate to cookie test page
        self.navigate_to(f"{self.demo_base}/navigation-cookie-test.html")
        self.wait_for_events()

        # Test cookie setting
        set_response = requests.post(f"{self.cdp_base}/cdp/page/cookies",
                                   json={
                                       "action": "set",
                                       "cookies": [
                                           {
                                               "name": "test_cookie",
                                               "value": "test_value",
                                               "domain": "cdp-ninja-test.meatspace.lol",
                                               "path": "/",
                                               "httpOnly": False,
                                               "secure": False
                                           }
                                       ]
                                   })
        self.assertEqual(set_response.status_code, 200)

        # Test cookie retrieval
        get_response = requests.get(f"{self.cdp_base}/cdp/page/cookies")
        self.assertEqual(get_response.status_code, 200)

        cookie_data = get_response.json()
        self.assertIn('cookies', cookie_data)

        cookies = cookie_data['cookies']
        self.assertIsInstance(cookies, list)

        # Verify our test cookie exists
        test_cookie_found = False
        for cookie in cookies:
            if cookie.get('name') == 'test_cookie':
                test_cookie_found = True
                self.assertEqual(cookie['value'], 'test_value')
                break

        self.assertTrue(test_cookie_found, "Test cookie should be found")

        # Test cookie deletion
        delete_response = requests.post(f"{self.cdp_base}/cdp/page/cookies",
                                      json={
                                          "action": "delete",
                                          "name": "test_cookie"
                                      })
        self.assertEqual(delete_response.status_code, 200)

    def test_navigation_error_handling(self):
        """Test navigation error handling"""
        # Test navigation to malformed URL
        malformed_response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                                         json={"url": "not-a-valid-url"})
        self.assertIn(malformed_response.status_code, [200, 400])

        # Test navigation to blocked/unreachable URL
        blocked_response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                                       json={"url": "https://blocked-site.example.com"})
        self.assertIn(blocked_response.status_code, [200, 400])

        # Test viewport with invalid dimensions
        invalid_viewport = requests.post(f"{self.cdp_base}/cdp/page/viewport",
                                       json={"width": -100, "height": -100})
        self.assertIn(invalid_viewport.status_code, [200, 400])

    def test_navigation_timing(self):
        """Test navigation timing and performance"""
        # Navigate with timing measurement
        start_time = time.time()

        response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                               json={
                                   "url": f"{self.demo_base}/navigation-timing-test",
                                   "wait_for_load": True
                               })
        self.assertEqual(response.status_code, 200)

        end_time = time.time()
        navigation_duration = end_time - start_time

        # Verify navigation completed in reasonable time
        self.assertLess(navigation_duration, 30, "Navigation should complete within 30 seconds")

        # Get page info to verify load completion
        info_response = requests.get(f"{self.cdp_base}/cdp/page/info")
        self.assertEqual(info_response.status_code, 200)

        info_data = info_response.json()
        if 'page_info' in info_data and 'ready_state' in info_data['page_info']:
            ready_state = info_data['page_info']['ready_state']
            self.assertIn(ready_state, ['interactive', 'complete'])

    def test_page_lifecycle_events(self):
        """Test page lifecycle event monitoring during navigation"""
        # Navigate to lifecycle test page
        response = requests.post(f"{self.cdp_base}/cdp/page/navigate",
                               json={"url": f"{self.demo_base}/navigation-lifecycle-test"})
        self.assertEqual(response.status_code, 200)

        # Wait for page lifecycle events
        self.wait_for_events(2)

        # Check debug events for page lifecycle
        events_response = requests.get(f"{self.cdp_base}/cdp/debug/events",
                                     params={"domain": "Page"})
        self.assertEqual(events_response.status_code, 200)

        events_data = events_response.json()
        if 'events' in events_data:
            events = events_data['events']
            lifecycle_events = [e for e in events if 'lifecycle' in e.get('method', '').lower()]

            # Should have captured some page lifecycle events
            self.assertGreater(len(lifecycle_events), 0, "Should capture page lifecycle events")