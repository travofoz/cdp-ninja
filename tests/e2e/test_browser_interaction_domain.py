"""
E2E Tests for Browser Interaction Domain Endpoints

Tests click, type, scroll, hover, drag, and screenshot functionality
for browser automation and interaction testing.
"""

import requests
import time
import base64
from typing import Dict, Any
from .base_test import CDPNinjaE2ETest


class TestBrowserInteractionDomain(CDPNinjaE2ETest):
    """Test Browser Interaction domain endpoints for automation"""

    def test_click_interaction(self):
        """Test click interaction functionality"""
        # Navigate to click test page
        self.navigate_to(f"{self.demo_base}/browser-click-test.html")
        self.wait_for_events()

        # Test basic click
        response = requests.post(f"{self.cdp_base}/cdp/click",
                               json={"selector": "#click-target"})
        self.assertEqual(response.status_code, 200)

        click_data = response.json()
        self.assertIn('click_result', click_data)
        self.assertTrue(click_data['click_result']['success'])

        # Test click with coordinates
        coord_response = requests.post(f"{self.cdp_base}/cdp/click",
                                     json={"x": 100, "y": 200})
        self.assertEqual(coord_response.status_code, 200)

        # Test click with options
        options_response = requests.post(f"{self.cdp_base}/cdp/click",
                                       json={
                                           "selector": "#click-target",
                                           "button": "right",
                                           "clickCount": 2,
                                           "delay": 100
                                       })
        self.assertEqual(options_response.status_code, 200)

    def test_type_interaction(self):
        """Test typing interaction functionality"""
        # Navigate to typing test page
        self.navigate_to(f"{self.demo_base}/browser-type-test.html")
        self.wait_for_events()

        # Test basic typing
        response = requests.post(f"{self.cdp_base}/cdp/type",
                               json={
                                   "selector": "#type-input",
                                   "text": "Test typing text"
                               })
        self.assertEqual(response.status_code, 200)

        type_data = response.json()
        self.assertIn('type_result', type_data)
        self.assertTrue(type_data['type_result']['success'])

        # Test typing with options
        options_response = requests.post(f"{self.cdp_base}/cdp/type",
                                       json={
                                           "selector": "#type-input",
                                           "text": "Slow typing",
                                           "delay": 50,  # 50ms between characters
                                           "clear_first": True
                                       })
        self.assertEqual(options_response.status_code, 200)

        # Test special key combinations
        special_response = requests.post(f"{self.cdp_base}/cdp/type",
                                       json={
                                           "selector": "#type-input",
                                           "text": "Control+A",  # Select all
                                           "special_keys": True
                                       })
        self.assertEqual(special_response.status_code, 200)

    def test_scroll_interaction(self):
        """Test scroll interaction functionality"""
        # Navigate to scroll test page
        self.navigate_to(f"{self.demo_base}/browser-scroll-test.html")
        self.wait_for_events()

        # Test vertical scroll
        response = requests.post(f"{self.cdp_base}/cdp/scroll",
                               json={"y": 500})
        self.assertEqual(response.status_code, 200)

        scroll_data = response.json()
        self.assertIn('scroll_result', scroll_data)

        # Test horizontal scroll
        h_response = requests.post(f"{self.cdp_base}/cdp/scroll",
                                 json={"x": 300})
        self.assertEqual(h_response.status_code, 200)

        # Test scroll to element
        element_response = requests.post(f"{self.cdp_base}/cdp/scroll",
                                       json={
                                           "selector": "#scroll-target",
                                           "behavior": "smooth"
                                       })
        self.assertEqual(element_response.status_code, 200)

        # Test scroll with delta
        delta_response = requests.post(f"{self.cdp_base}/cdp/scroll",
                                     json={
                                         "deltaX": 100,
                                         "deltaY": 200,
                                         "relative": True
                                     })
        self.assertEqual(delta_response.status_code, 200)

    def test_hover_interaction(self):
        """Test hover interaction functionality"""
        # Navigate to hover test page
        self.navigate_to(f"{self.demo_base}/browser-hover-test.html")
        self.wait_for_events()

        # Test basic hover
        response = requests.post(f"{self.cdp_base}/cdp/hover",
                               json={"selector": "#hover-target"})
        self.assertEqual(response.status_code, 200)

        hover_data = response.json()
        self.assertIn('hover_result', hover_data)
        self.assertTrue(hover_data['hover_result']['success'])

        # Test hover with coordinates
        coord_response = requests.post(f"{self.cdp_base}/cdp/hover",
                                     json={"x": 150, "y": 250})
        self.assertEqual(coord_response.status_code, 200)

        # Test hover sequence
        sequence_response = requests.post(f"{self.cdp_base}/cdp/hover",
                                        json={
                                            "hover_sequence": [
                                                {"selector": "#hover-1"},
                                                {"selector": "#hover-2"},
                                                {"selector": "#hover-3"}
                                            ],
                                            "delay_between": 500
                                        })
        self.assertEqual(sequence_response.status_code, 200)

    def test_screenshot_capture(self):
        """Test screenshot capture functionality"""
        # Navigate to screenshot test page
        self.navigate_to(f"{self.demo_base}/browser-screenshot-test.html")
        self.wait_for_events()

        # Test full page screenshot
        response = requests.get(f"{self.cdp_base}/cdp/screenshot")
        self.assertEqual(response.status_code, 200)

        # Verify screenshot is valid image data
        screenshot_data = response.content
        self.assertGreater(len(screenshot_data), 1000, "Screenshot should contain image data")

        # Test screenshot with parameters
        params_response = requests.get(f"{self.cdp_base}/cdp/screenshot",
                                     params={
                                         "format": "jpeg",
                                         "quality": 80,
                                         "full_page": True
                                     })
        self.assertEqual(params_response.status_code, 200)

        # Test element screenshot
        element_response = requests.get(f"{self.cdp_base}/cdp/screenshot",
                                      params={"selector": "#screenshot-element"})
        self.assertEqual(element_response.status_code, 200)

        # Test viewport screenshot
        viewport_response = requests.get(f"{self.cdp_base}/cdp/screenshot",
                                       params={
                                           "clip": "true",
                                           "x": 0,
                                           "y": 0,
                                           "width": 800,
                                           "height": 600
                                       })
        self.assertEqual(viewport_response.status_code, 200)

    def test_drag_interaction(self):
        """Test drag and drop interaction functionality"""
        # Navigate to drag test page
        self.navigate_to(f"{self.demo_base}/browser-drag-test.html")
        self.wait_for_events()

        # Test basic drag and drop
        response = requests.post(f"{self.cdp_base}/cdp/drag",
                               json={
                                   "source_selector": "#drag-source",
                                   "target_selector": "#drop-target"
                               })
        self.assertEqual(response.status_code, 200)

        drag_data = response.json()
        self.assertIn('drag_result', drag_data)
        self.assertTrue(drag_data['drag_result']['success'])

        # Test drag with coordinates
        coord_response = requests.post(f"{self.cdp_base}/cdp/drag",
                                     json={
                                         "source": {"x": 100, "y": 100},
                                         "target": {"x": 300, "y": 200}
                                     })
        self.assertEqual(coord_response.status_code, 200)

        # Test drag with steps
        steps_response = requests.post(f"{self.cdp_base}/cdp/drag",
                                     json={
                                         "source_selector": "#drag-source-2",
                                         "target_selector": "#drop-target-2",
                                         "steps": 10,        # 10 intermediate steps
                                         "delay": 50         # 50ms between steps
                                     })
        self.assertEqual(steps_response.status_code, 200)

        # Test drag with hover validation
        hover_response = requests.post(f"{self.cdp_base}/cdp/drag",
                                     json={
                                         "source_selector": "#drag-source-3",
                                         "target_selector": "#drop-target-3",
                                         "validate_hover": True,
                                         "hold_duration": 1000  # Hold for 1 second
                                     })
        self.assertEqual(hover_response.status_code, 200)

    def test_interaction_combinations(self):
        """Test combinations of browser interactions"""
        # Navigate to interaction combination test page
        self.navigate_to(f"{self.demo_base}/browser-interaction-combo.html")
        self.wait_for_events()

        # Test click + type combination
        click_response = requests.post(f"{self.cdp_base}/cdp/click",
                                     json={"selector": "#combo-input"})
        self.assertEqual(click_response.status_code, 200)

        type_response = requests.post(f"{self.cdp_base}/cdp/type",
                                    json={
                                        "selector": "#combo-input",
                                        "text": "Combined interaction test"
                                    })
        self.assertEqual(type_response.status_code, 200)

        # Test hover + click combination
        hover_response = requests.post(f"{self.cdp_base}/cdp/hover",
                                     json={"selector": "#combo-button"})
        self.assertEqual(hover_response.status_code, 200)

        # Wait for hover effects
        self.wait_for_events(0.5)

        click_response = requests.post(f"{self.cdp_base}/cdp/click",
                                     json={"selector": "#combo-button"})
        self.assertEqual(click_response.status_code, 200)

        # Test scroll + screenshot combination
        scroll_response = requests.post(f"{self.cdp_base}/cdp/scroll",
                                      json={"y": 800})
        self.assertEqual(scroll_response.status_code, 200)

        screenshot_response = requests.get(f"{self.cdp_base}/cdp/screenshot")
        self.assertEqual(screenshot_response.status_code, 200)

    def test_interaction_error_handling(self):
        """Test error handling in browser interactions"""
        # Navigate to interaction error test page
        self.navigate_to(f"{self.demo_base}/browser-interaction-errors.html")
        self.wait_for_events()

        # Test click on non-existent element
        invalid_click = requests.post(f"{self.cdp_base}/cdp/click",
                                    json={"selector": "#non-existent-element"})
        # Should handle gracefully
        self.assertIn(invalid_click.status_code, [200, 400, 404])

        if invalid_click.status_code == 200:
            click_data = invalid_click.json()
            if 'click_result' in click_data:
                self.assertFalse(click_data['click_result']['success'])

        # Test type on non-input element
        invalid_type = requests.post(f"{self.cdp_base}/cdp/type",
                                   json={
                                       "selector": "#non-input-element",
                                       "text": "This should not work"
                                   })
        # Should handle gracefully
        self.assertIn(invalid_type.status_code, [200, 400])

        # Test drag with invalid coordinates
        invalid_drag = requests.post(f"{self.cdp_base}/cdp/drag",
                                   json={
                                       "source": {"x": -100, "y": -100},
                                       "target": {"x": 9999, "y": 9999}
                                   })
        # Should handle gracefully
        self.assertIn(invalid_drag.status_code, [200, 400])