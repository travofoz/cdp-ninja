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
        self.assertIn('dom_snapshot', snapshot)
        self.assertIn('nodes', snapshot['dom_snapshot'])
        self.assertGreater(len(snapshot['dom_snapshot']['nodes']), 0,
                          "DOM snapshot should contain nodes")

    def test_dom_query_selectors(self):
        """Test DOM element querying with various selectors"""
        self.navigate_to(f"{self.demo_base}/dom-query-test.html")
        self.wait_for_events()

        test_selectors = [
            {"selector": "#test-button", "expected_count": 1},
            {"selector": ".test-class", "expected_count": 3},
            {"selector": "input[type='text']", "expected_count": 2},
            {"selector": "div", "expected_count": ">= 5"}
        ]

        for test_case in test_selectors:
            with self.subTest(selector=test_case["selector"]):
                response = requests.post(f"{self.cdp_base}/cdp/dom/query",
                                       json={"selector": test_case["selector"]})
                self.assertEqual(response.status_code, 200)

                result = response.json()
                self.assertIn('elements', result)

                elements = result['elements']
                expected = test_case["expected_count"]

                if isinstance(expected, int):
                    self.assertEqual(len(elements), expected,
                                   f"Selector {test_case['selector']} should return {expected} elements")
                elif expected.startswith(">="):
                    min_count = int(expected.split()[1])
                    self.assertGreaterEqual(len(elements), min_count,
                                          f"Selector {test_case['selector']} should return at least {min_count} elements")

    def test_form_filling_and_submission(self):
        """Test form filling and submission functionality"""
        self.navigate_to(f"{self.demo_base}/form-test-page.html")
        self.wait_for_events()

        # Fill form fields
        form_data = {
            "fields": {
                "#username": "testuser",
                "#email": "test@example.com",
                "#password": "testpass123",
                "#checkbox-agree": True,
                "#dropdown-country": "US"
            }
        }

        fill_response = requests.post(f"{self.cdp_base}/cdp/form/fill",
                                    json=form_data)
        self.assertEqual(fill_response.status_code, 200)

        # Get form values to verify filling worked
        values_response = requests.post(f"{self.cdp_base}/cdp/form/values",
                                      json={"selectors": list(form_data["fields"].keys())})
        self.assertEqual(values_response.status_code, 200)

        values = values_response.json()
        self.assertIn('values', values)

        # Verify form was filled correctly
        for selector, expected_value in form_data["fields"].items():
            if selector in values['values']:
                actual_value = values['values'][selector]
                if isinstance(expected_value, bool):
                    self.assertEqual(actual_value, expected_value,
                                   f"Checkbox {selector} should be {expected_value}")
                else:
                    self.assertEqual(actual_value, expected_value,
                                   f"Field {selector} should contain '{expected_value}'")

        # Submit form
        submit_response = requests.post(f"{self.cdp_base}/cdp/form/submit",
                                      json={"selector": "#test-form"})
        self.assertEqual(submit_response.status_code, 200)

    def test_dom_modification(self):
        """Test DOM element modification"""
        self.navigate_to(f"{self.demo_base}/dom-modify-test.html")
        self.wait_for_events()

        # Test text content modification
        modify_text_response = requests.post(f"{self.cdp_base}/cdp/dom/modify",
                                           json={
                                               "selector": "#modify-target",
                                               "action": "set_text",
                                               "value": "Modified text content"
                                           })
        self.assertEqual(modify_text_response.status_code, 200)

        # Verify modification by querying element
        query_response = requests.post(f"{self.cdp_base}/cdp/dom/query",
                                     json={"selector": "#modify-target"})
        self.assertEqual(query_response.status_code, 200)

        elements = query_response.json()['elements']
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0]['textContent'], "Modified text content")

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
        self.navigate_to(f"{self.demo_base}/dom-bounds-test.html")
        self.wait_for_events()

        # Get bounds for test element
        response = requests.post(f"{self.cdp_base}/cdp/dom/get_bounds",
                               json={"selector": "#bounds-test-element"})
        self.assertEqual(response.status_code, 200)

        bounds_data = response.json()
        self.assertIn('bounds', bounds_data)

        bounds = bounds_data['bounds']
        required_fields = ['x', 'y', 'width', 'height']

        for field in required_fields:
            self.assertIn(field, bounds)
            self.assertIsInstance(bounds[field], (int, float))
            self.assertGreaterEqual(bounds[field], 0)

    def test_dom_visibility_check(self):
        """Test DOM element visibility detection"""
        self.navigate_to(f"{self.demo_base}/dom-visibility-test.html")
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
                self.assertIn('visible', visibility_data)
                self.assertEqual(visibility_data['visible'], test_case["expected"],
                               f"Element {test_case['selector']} visibility should be {test_case['expected']}")

    def test_dom_style_computation(self):
        """Test DOM element computed style retrieval"""
        self.navigate_to(f"{self.demo_base}/dom-style-test.html")
        self.wait_for_events()

        # Get computed styles
        response = requests.post(f"{self.cdp_base}/cdp/dom/get_style",
                               json={
                                   "selector": "#styled-element",
                                   "properties": ["color", "font-size", "display", "position"]
                               })
        self.assertEqual(response.status_code, 200)

        style_data = response.json()
        self.assertIn('computed_style', style_data)

        styles = style_data['computed_style']
        requested_props = ["color", "font-size", "display", "position"]

        for prop in requested_props:
            self.assertIn(prop, styles,
                         f"Computed style should include {prop}")

    def test_shadow_dom_handling(self):
        """Test Shadow DOM element interaction"""
        self.navigate_to(f"{self.demo_base}/shadow-dom-test.html")
        self.wait_for_events()

        # Query shadow DOM elements
        response = requests.post(f"{self.cdp_base}/cdp/dom/shadow",
                               json={
                                   "action": "query",
                                   "host_selector": "#shadow-host",
                                   "shadow_selector": "#shadow-content"
                               })
        self.assertEqual(response.status_code, 200)

        shadow_data = response.json()
        if 'elements' in shadow_data:
            self.assertGreater(len(shadow_data['elements']), 0,
                             "Should find elements in shadow DOM")

    def test_dom_parent_traversal(self):
        """Test DOM parent element traversal"""
        self.navigate_to(f"{self.demo_base}/dom-traversal-test.html")
        self.wait_for_events()

        # Get parent element
        response = requests.post(f"{self.cdp_base}/cdp/dom/parent",
                               json={"selector": "#child-element"})
        self.assertEqual(response.status_code, 200)

        parent_data = response.json()
        self.assertIn('parent', parent_data)

        parent = parent_data['parent']
        self.assertIn('tagName', parent)
        self.assertIn('id', parent)

    def test_browser_interaction_with_dom(self):
        """Test browser interaction endpoints with DOM elements"""
        self.navigate_to(f"{self.demo_base}/interaction-test.html")
        self.wait_for_events()

        # Test click interaction
        click_response = requests.post(f"{self.cdp_base}/cdp/click",
                                     json={"selector": "#click-test-button"})
        self.assertEqual(click_response.status_code, 200)

        # Test typing
        type_response = requests.post(f"{self.cdp_base}/cdp/type",
                                    json={
                                        "selector": "#type-test-input",
                                        "text": "Test typing text"
                                    })
        self.assertEqual(type_response.status_code, 200)

        # Test hover
        hover_response = requests.post(f"{self.cdp_base}/cdp/hover",
                                     json={"selector": "#hover-test-element"})
        self.assertEqual(hover_response.status_code, 200)

        # Test scrolling
        scroll_response = requests.post(f"{self.cdp_base}/cdp/scroll",
                                      json={"y": 500})
        self.assertEqual(scroll_response.status_code, 200)

    def test_dom_cross_instance_consistency(self):
        """Test DOM events consistency across CDPClient instances"""
        # Navigate to page that generates DOM events
        self.navigate_to(f"{self.demo_base}/dom-events-test.html")
        self.wait_for_events()

        # Perform DOM operations that generate events
        requests.post(f"{self.cdp_base}/cdp/click", json={"selector": "#event-trigger"})
        self.wait_for_events()

        # Test cross-instance consistency for DOM domain
        expected_events = ["DOM.documentUpdated", "DOM.childNodeInserted"]
        self.assert_event_consistency("DOM", expected_events)