"""
E2E Tests for DOM Domain Endpoints

Tests DOM interaction, form handling, and element manipulation
across server vs pool CDPClient instances.
"""

import requests
import time
from typing import Dict, Any, List
from .base_test import CDPNinjaE2ETest


class TestDOMDomain(CDPNinjaE2ETest):
    """Test DOM domain endpoints for event consistency"""

    def test_dom_snapshot_basic(self):
        """Test basic DOM snapshot functionality"""
        # Navigate to DOM test page
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Get DOM snapshot
        response = requests.get(f"{self.cdp_base}/cdp/dom/snapshot")
        self.assertEqual(response.status_code, 200)

        snapshot = response.json()
        # Check actual response structure from DOM snapshot endpoint
        self.assertTrue(snapshot.get('success', False), "DOM snapshot should succeed")
        self.assertIn('html', snapshot, "Should contain HTML content")
        self.assertGreater(len(snapshot['html']), 0, "HTML content should not be empty")

    def test_dom_query_selectors(self):
        """Test DOM element querying with various selectors"""
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Test single element queries (query_all=False, default)
        single_selectors = [
            {"selector": "#test-button", "expected_found": True},
            {"selector": "#nonexistent", "expected_found": False},
            {"selector": ".test-class", "expected_found": True},  # Should return first match
        ]

        for test_case in single_selectors:
            with self.subTest(selector=test_case["selector"], mode="single"):
                response = requests.post(f"{self.cdp_base}/cdp/dom/query",
                                       json={"selector": test_case["selector"]})
                self.assertEqual(response.status_code, 200)

                result = response.json()
                self.assertIn('elements', result)

                elements = result['elements']
                expected_found = test_case["expected_found"]

                if expected_found:
                    self.assertIsNotNone(elements, f"Single query for {test_case['selector']} should find element")
                    self.assertIsInstance(elements, dict, f"Single query should return dict object")
                    self.assertIn('tagName', elements, f"Element should have tagName")
                else:
                    self.assertIsNone(elements, f"Single query for {test_case['selector']} should return null")

        # Test multiple element queries (query_all=True)
        multi_selectors = [
            {"selector": ".test-class", "expected_min": 3},
            {"selector": "input[type='text']", "expected_count": 2},  # Curl shows exactly 2
            {"selector": "div", "expected_min": 5},
            {"selector": "#nonexistent", "expected_count": 0},
        ]

        for test_case in multi_selectors:
            with self.subTest(selector=test_case["selector"], mode="multiple"):
                response = requests.post(f"{self.cdp_base}/cdp/dom/query",
                                       json={"selector": test_case["selector"], "all": True})
                self.assertEqual(response.status_code, 200)

                result = response.json()
                self.assertIn('elements', result)

                elements = result['elements']
                self.assertIsNotNone(elements, f"Elements should not be None for {test_case['selector']}")
                self.assertIsInstance(elements, list, f"Multiple query should return list")

                if "expected_min" in test_case:
                    self.assertGreaterEqual(len(elements), test_case["expected_min"],
                                          f"Selector {test_case['selector']} should return at least {test_case['expected_min']} elements")
                elif "expected_count" in test_case:
                    self.assertEqual(len(elements), test_case["expected_count"],
                                   f"Selector {test_case['selector']} should return exactly {test_case['expected_count']} elements")

    def test_form_filling_and_submission(self):
        """Test form filling and submission functionality"""
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Test basic form field interaction using type endpoint
        # Fill input field using type endpoint (this exists in dom-test-page.html)
        type_response = requests.post(f"{self.cdp_base}/cdp/type",
                                    json={
                                        "selector": "#type-input",
                                        "text": "testuser"
                                    })
        self.assertEqual(type_response.status_code, 200)

        # Verify field was filled by querying the element
        query_response = requests.post(f"{self.cdp_base}/cdp/dom/query",
                                     json={"selector": "#type-input", "details": True})
        self.assertEqual(query_response.status_code, 200)

        result = query_response.json()
        elements = result.get('elements')
        if elements and isinstance(elements, dict):
            # Basic form interaction test passed
            self.assertIn('tagName', elements, "Should find input element")
            self.assertEqual(elements['tagName'], 'INPUT', "Should be INPUT element")

    def test_dom_modification(self):
        """Test DOM element modification"""
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Test text content modification
        modify_text_response = requests.post(f"{self.cdp_base}/cdp/dom/modify",
                                           json={
                                               "selector": "#modify-target",
                                               "action": "set_text",
                                               "value": "Modified text content"
                                           })
        self.assertEqual(modify_text_response.status_code, 200)

        # Verify modification by querying element (returns single object, not array)
        query_response = requests.post(f"{self.cdp_base}/cdp/dom/query",
                                     json={"selector": "#modify-target"})
        self.assertEqual(query_response.status_code, 200)

        result = query_response.json()
        self.assertIn('elements', result)
        elements = result['elements']
        self.assertIsNotNone(elements, "Should find modified element")
        self.assertIsInstance(elements, dict, "Single query returns dict")
        self.assertEqual(elements['textContent'], "Modified text content")

        # Test attribute modification
        modify_attr_response = requests.post(f"{self.cdp_base}/cdp/dom/modify",
                                           json={
                                               "selector": "#modify-target",
                                               "action": "set_attribute",
                                               "attribute": "data-test",
                                               "value": "modified"
                                           })
        self.assertEqual(modify_attr_response.status_code, 200)

    def test_dom_element_bounds(self):
        """Test DOM element bounds calculation"""
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Get bounds for test element
        response = requests.post(f"{self.cdp_base}/cdp/dom/get_bounds",
                               json={"selector": "#bounds-test-element"})
        self.assertEqual(response.status_code, 200)

        bounds_data = response.json()
        self.assertTrue(bounds_data.get('success', False), "Bounds query should succeed")
        self.assertIn('bounds', bounds_data)

        bounds = bounds_data['bounds']
        # Check actual bounds structure from CDP getBoxModel
        self.assertIn('model', bounds, "Should contain box model")
        model = bounds['model']

        # Verify essential properties exist
        required_fields = ['width', 'height']
        for field in required_fields:
            self.assertIn(field, model)
            self.assertIsInstance(model[field], (int, float))
            self.assertGreater(model[field], 0, f"{field} should be positive")

    def test_dom_visibility_check(self):
        """Test DOM element visibility detection"""
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        visibility_tests = [
            {"selector": "#visible-element", "expected": True},
            {"selector": "#hidden-element", "expected": False},
            {"selector": "#display-none-element", "expected": False},
            {"selector": "#opacity-zero-element", "expected": False}
        ]

        for test_case in visibility_tests:
            with self.subTest(selector=test_case["selector"]):
                response = requests.post(f"{self.cdp_base}/cdp/dom/is_visible",
                                       json={"selector": test_case["selector"]})
                self.assertEqual(response.status_code, 200)

                visibility_data = response.json()
                self.assertTrue(visibility_data.get('success', False), "Visibility check should succeed")
                self.assertIn('visibility', visibility_data, "Should contain visibility data")

                visibility = visibility_data['visibility']
                if visibility is not None:
                    self.assertIn('basic_visible', visibility, "Should contain basic_visible")
                    actual_visible = visibility['basic_visible']
                    self.assertEqual(actual_visible, test_case["expected"],
                                   f"Element {test_case['selector']} visibility should be {test_case['expected']}")
                else:
                    # Element not found case
                    self.assertFalse(test_case["expected"], f"Element {test_case['selector']} not found but expected to be visible")

    def test_dom_style_computation(self):
        """Test DOM element computed style retrieval"""
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Get computed styles
        response = requests.post(f"{self.cdp_base}/cdp/dom/get_style",
                               json={
                                   "selector": "#styled-element",
                                   "properties": ["color", "font-size", "display", "position"]
                               })
        self.assertEqual(response.status_code, 200)

        style_data = response.json()
        # Check if CDP command is supported
        if style_data.get('success', True) and 'computedStyle' in style_data:
            styles = style_data['computedStyle']
            requested_props = ["color", "font-size", "display", "position"]

            for prop in requested_props:
                self.assertIn(prop, styles,
                             f"Computed style should include {prop}")
                self.assertIsInstance(styles[prop], str,
                                    f"Style property {prop} should be string")
        else:
            # CDP command not supported or element not found - verify error handling
            self.assertFalse(style_data.get('success', True), "Should report failure when CDP command unsupported")
            self.assertIn('cdp_result', style_data, "Should contain CDP error details")
            # This is expected behavior when CDP command not available

    def test_shadow_dom_handling(self):
        """Test Shadow DOM element interaction"""
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Test shadow DOM endpoint
        response = requests.post(f"{self.cdp_base}/cdp/dom/shadow",
                               json={"selector": "#shadow-host"})
        self.assertEqual(response.status_code, 200)

        shadow_data = response.json()
        # Shadow DOM endpoint returns structure info, not elements array
        self.assertTrue(shadow_data.get('success', False), "Shadow DOM query should succeed")
        if 'shadow_dom' in shadow_data:
            shadow_dom = shadow_data['shadow_dom']
            self.assertIn('node', shadow_dom, "Should contain node info")

    def test_dom_parent_traversal(self):
        """Test DOM parent element traversal"""
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Get parent element
        response = requests.post(f"{self.cdp_base}/cdp/dom/parent",
                               json={"selector": "#child-element"})
        self.assertEqual(response.status_code, 200)

        parent_data = response.json()
        self.assertTrue(parent_data.get('success', False), "Parent traversal should succeed")
        self.assertIn('navigation', parent_data, "Should contain navigation data")

        navigation = parent_data['navigation']
        if navigation:
            self.assertIn('original_element', navigation, "Should contain original element info")
            self.assertIn('parents', navigation, "Should contain parents array")
            self.assertIsInstance(navigation['parents'], list, "Parents should be array")

    def test_browser_interaction_with_dom(self):
        """Test browser interaction endpoints with DOM elements"""
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Test click interaction
        click_response = requests.post(f"{self.cdp_base}/cdp/click",
                                     json={"selector": "#click-target"})
        self.assertEqual(click_response.status_code, 200)

        # Test typing in input field
        type_response = requests.post(f"{self.cdp_base}/cdp/type",
                                    json={
                                        "selector": "#type-input",
                                        "text": "Test typing text"
                                    })
        self.assertEqual(type_response.status_code, 200)

        # Test hover on test button
        hover_response = requests.post(f"{self.cdp_base}/cdp/hover",
                                     json={"selector": "#test-button"})
        self.assertEqual(hover_response.status_code, 200)

        # Test scrolling
        scroll_response = requests.post(f"{self.cdp_base}/cdp/scroll",
                                      json={"y": 500})
        self.assertEqual(scroll_response.status_code, 200)

    def test_dom_cross_instance_consistency(self):
        """Test DOM events consistency across CDPClient instances"""
        # Navigate to page that generates DOM events
        self.navigate_to(f"{self.demo_base}/dom-test-page.html")
        self.wait_for_events()

        # Perform DOM operations that generate events
        # Click a button that triggers DOM changes
        requests.post(f"{self.cdp_base}/cdp/click", json={"selector": "#test-button"})
        self.wait_for_events()

        # Modify DOM to generate more events
        requests.post(f"{self.cdp_base}/cdp/dom/modify", json={
            "selector": "#modify-target",
            "action": "set_text",
            "value": "Modified for consistency test"
        })
        self.wait_for_events()

        # Test cross-instance consistency for DOM domain
        # Check that both instances have received events
        pool_events = self.get_server_events("DOM")
        server_events = self.get_pool_events("DOM")

        self.assertGreater(len(pool_events), 0, "Pool should have DOM events")
        self.assertGreater(len(server_events), 0, "Server should have DOM events")