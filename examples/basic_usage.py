#!/usr/bin/env python3
"""
CDP Thin Bridge - Basic Usage Examples
Demonstrates core functionality of the browser debugging bridge
"""

import requests
import time
import json
from pathlib import Path

# Configuration
BRIDGE_URL = "http://localhost:8888"
TEST_PAGE = "http://example.com"


class CDPBridgeClient:
    """Simple client wrapper for CDP Bridge API"""

    def __init__(self, base_url=BRIDGE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def health_check(self):
        """Check if bridge is running"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False

    def cdp_status(self):
        """Get CDP connection status"""
        response = self.session.get(f"{self.base_url}/cdp/status")
        return response.json()

    def navigate(self, url):
        """Navigate to URL"""
        response = self.session.post(f"{self.base_url}/cdp/page/navigate",
                                   json={"url": url})
        return response.json()

    def execute_js(self, code):
        """Execute JavaScript in page context"""
        response = self.session.post(f"{self.base_url}/cdp/execute",
                                   json={"code": code})
        return response.json()

    def click_element(self, selector=None, x=None, y=None):
        """Click element by selector or coordinates"""
        if selector:
            payload = {"selector": selector}
        elif x is not None and y is not None:
            payload = {"x": x, "y": y}
        else:
            raise ValueError("Must provide selector or coordinates")

        response = self.session.post(f"{self.base_url}/cdp/click", json=payload)
        return response.json()

    def type_text(self, selector, text):
        """Type text into element"""
        response = self.session.post(f"{self.base_url}/cdp/type",
                                   json={"selector": selector, "text": text})
        return response.json()

    def screenshot(self, filename=None, full_page=False):
        """Take screenshot"""
        params = {"full_page": "true" if full_page else "false"}
        response = self.session.get(f"{self.base_url}/cdp/screenshot", params=params)

        if response.status_code == 200:
            if filename:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return f"Screenshot saved to {filename}"
            else:
                return response.content
        else:
            return response.json()

    def get_console_logs(self):
        """Get console output"""
        response = self.session.get(f"{self.base_url}/cdp/console/logs")
        return response.json()

    def get_network_requests(self):
        """Get network requests"""
        response = self.session.get(f"{self.base_url}/cdp/network/requests")
        return response.json()

    def fill_form(self, fields):
        """Fill form fields"""
        response = self.session.post(f"{self.base_url}/cdp/form/fill",
                                   json={"fields": fields})
        return response.json()


def example_basic_navigation():
    """Example: Basic page navigation and information gathering"""
    print("=== Basic Navigation Example ===")

    client = CDPBridgeClient()

    # Check connection
    if not client.health_check():
        print("❌ Bridge server not responding at", BRIDGE_URL)
        return

    print("✅ Bridge server is running")

    # Check CDP status
    status = client.cdp_status()
    print(f"CDP Connected: {status.get('connected')}")
    print(f"Port: {status.get('port')}")

    # Navigate to test page
    print(f"\nNavigating to {TEST_PAGE}...")
    result = client.navigate(TEST_PAGE)
    print(f"Navigation result: {result}")

    # Wait for page load
    time.sleep(2)

    # Get page title
    title_result = client.execute_js("document.title")
    if 'result' in title_result:
        title = title_result['result'].get('value', 'Unknown')
        print(f"Page title: {title}")

    # Get page URL
    url_result = client.execute_js("window.location.href")
    if 'result' in url_result:
        url = url_result['result'].get('value', 'Unknown')
        print(f"Current URL: {url}")

    # Take screenshot
    screenshot_path = "example_screenshot.png"
    result = client.screenshot(screenshot_path)
    print(f"Screenshot: {result}")


def example_form_interaction():
    """Example: Form filling and interaction"""
    print("\n=== Form Interaction Example ===")

    client = CDPBridgeClient()

    # Navigate to a page with forms (using httpbin for testing)
    form_page = "https://httpbin.org/forms/post"
    print(f"Navigating to form page: {form_page}")
    client.navigate(form_page)
    time.sleep(3)

    # Fill form fields
    form_data = {
        "input[name='custname']": "John Doe",
        "input[name='custtel']": "123-456-7890",
        "input[name='custemail']": "john@example.com",
        "textarea[name='comments']": "This is a test comment from CDP Bridge!"
    }

    print("Filling form fields...")
    result = client.fill_form(form_data)
    print(f"Form fill result: {result}")

    # Take screenshot of filled form
    client.screenshot("form_filled.png")
    print("Screenshot of filled form saved")

    # Submit form (optional - commented out to avoid actual submission)
    # print("Submitting form...")
    # client.click_element("input[type='submit']")


def example_network_monitoring():
    """Example: Network request monitoring"""
    print("\n=== Network Monitoring Example ===")

    client = CDPBridgeClient()

    # Navigate to a page that makes network requests
    print("Navigating to page with network activity...")
    client.navigate("https://jsonplaceholder.typicode.com/")
    time.sleep(3)

    # Get network requests
    requests_data = client.get_network_requests()
    print(f"Captured {len(requests_data)} network requests:")

    for req in requests_data[:5]:  # Show first 5 requests
        print(f"  {req.get('method', 'GET')} {req.get('url', 'Unknown URL')}")
        response = req.get('response', {})
        if response:
            print(f"    Status: {response.get('status', 'Unknown')}")


def example_console_monitoring():
    """Example: Console log monitoring"""
    print("\n=== Console Monitoring Example ===")

    client = CDPBridgeClient()

    # Execute some JavaScript that generates console output
    print("Generating console output...")

    js_commands = [
        "console.log('Hello from CDP Bridge!')",
        "console.warn('This is a warning message')",
        "console.error('This is an error message')",
        "console.info('Page loaded at:', new Date().toISOString())"
    ]

    for cmd in js_commands:
        client.execute_js(cmd)
        time.sleep(0.5)

    # Get console logs
    logs = client.get_console_logs()
    print(f"Console logs captured: {len(logs)}")

    for log in logs[-4:]:  # Show last 4 logs
        level = log.get('level', 'unknown')
        args = log.get('args', [])
        if args:
            message = ' '.join(str(arg.get('value', '')) for arg in args)
            print(f"  [{level.upper()}] {message}")


def example_debugging_workflow():
    """Example: Complete debugging workflow"""
    print("\n=== Complete Debugging Workflow ===")

    client = CDPBridgeClient()

    # 1. Navigate to test page
    test_url = "https://httpbin.org/html"
    print(f"1. Navigating to {test_url}")
    client.navigate(test_url)
    time.sleep(2)

    # 2. Take initial screenshot
    print("2. Taking initial screenshot...")
    client.screenshot("debug_initial.png")

    # 3. Execute diagnostic JavaScript
    print("3. Running diagnostics...")
    diagnostics = {
        "url": "window.location.href",
        "title": "document.title",
        "links": "document.querySelectorAll('a').length",
        "forms": "document.querySelectorAll('form').length",
        "scripts": "document.querySelectorAll('script').length"
    }

    results = {}
    for name, code in diagnostics.items():
        result = client.execute_js(code)
        if 'result' in result:
            results[name] = result['result'].get('value')

    print("Diagnostic results:")
    for name, value in results.items():
        print(f"  {name}: {value}")

    # 4. Check for JavaScript errors
    print("4. Checking console for errors...")
    logs = client.get_console_logs()
    errors = [log for log in logs if log.get('level') == 'error']
    if errors:
        print(f"Found {len(errors)} JavaScript errors:")
        for error in errors[-3:]:  # Show last 3 errors
            print(f"  ERROR: {error}")
    else:
        print("No JavaScript errors found")

    # 5. Network analysis
    print("5. Analyzing network requests...")
    network_requests = client.get_network_requests()
    failed_requests = [req for req in network_requests
                      if req.get('failed') or
                      (req.get('response', {}).get('status', 0) >= 400)]

    if failed_requests:
        print(f"Found {len(failed_requests)} failed requests:")
        for req in failed_requests:
            print(f"  {req.get('method')} {req.get('url')} - Status: {req.get('response', {}).get('status')}")
    else:
        print("All network requests successful")

    # 6. Final screenshot
    print("6. Taking final screenshot...")
    client.screenshot("debug_final.png")

    print("Debugging workflow complete!")


def main():
    """Run all examples"""
    print("CDP Thin Bridge - Usage Examples")
    print("=" * 40)

    try:
        example_basic_navigation()
        example_form_interaction()
        example_network_monitoring()
        example_console_monitoring()
        example_debugging_workflow()

        print("\n" + "=" * 40)
        print("✅ All examples completed successfully!")
        print("\nGenerated files:")
        print("  - example_screenshot.png")
        print("  - form_filled.png")
        print("  - debug_initial.png")
        print("  - debug_final.png")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to CDP Bridge server")
        print("Make sure the bridge is running at", BRIDGE_URL)
        print("Run: python -m api.server")

    except Exception as e:
        print(f"❌ Error running examples: {e}")


if __name__ == "__main__":
    main()