#!/usr/bin/env python3
"""
CDP Thin Bridge - Next.js Debugging Examples
Specialized debugging scenarios for Next.js applications
"""

import requests
import time
import json
from datetime import datetime


class NextJSDebugger:
    """Specialized debugger for Next.js applications"""

    def __init__(self, bridge_url="http://localhost:8888", app_url="http://localhost:3000"):
        self.bridge_url = bridge_url.rstrip('/')
        self.app_url = app_url.rstrip('/')
        self.session = requests.Session()

    def log(self, message, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def api_call(self, endpoint, method="GET", **kwargs):
        """Make API call to bridge"""
        url = f"{self.bridge_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        return response

    def check_bridge_connection(self):
        """Verify bridge is accessible"""
        try:
            response = self.api_call("/health")
            if response.status_code == 200:
                self.log("✅ Bridge server connected")
                return True
        except:
            pass

        self.log("❌ Bridge server not responding", "ERROR")
        self.log(f"Make sure CDP bridge is running at {self.bridge_url}", "ERROR")
        return False

    def navigate_to_app(self, path="/"):
        """Navigate to Next.js app"""
        url = f"{self.app_url}{path}"
        self.log(f"Navigating to {url}")

        response = self.api_call("/cdp/page/navigate", "POST", json={"url": url})
        if response.status_code == 200:
            time.sleep(2)  # Wait for page load
            return True
        else:
            self.log(f"Navigation failed: {response.text}", "ERROR")
            return False

    def check_hydration_errors(self):
        """Check for Next.js hydration errors"""
        self.log("Checking for hydration errors...")

        # Get console logs
        response = self.api_call("/cdp/console/logs")
        if response.status_code != 200:
            self.log("Failed to get console logs", "ERROR")
            return []

        logs = response.json()
        hydration_errors = []

        # Look for common hydration error patterns
        error_patterns = [
            "hydration",
            "server did not match",
            "text content does not match",
            "prop `children` did not match",
            "Warning: Expected server HTML"
        ]

        for log in logs:
            if log.get('level') in ['error', 'warning']:
                message = str(log.get('args', [{}])[0].get('value', ''))
                if any(pattern.lower() in message.lower() for pattern in error_patterns):
                    hydration_errors.append({
                        'level': log['level'],
                        'message': message,
                        'timestamp': log.get('timestamp')
                    })

        if hydration_errors:
            self.log(f"⚠️ Found {len(hydration_errors)} hydration-related issues")
            for error in hydration_errors:
                self.log(f"  {error['level'].upper()}: {error['message']}")
        else:
            self.log("✅ No hydration errors detected")

        return hydration_errors

    def check_api_routes(self):
        """Monitor Next.js API route calls"""
        self.log("Monitoring API routes...")

        # Get network requests
        response = self.api_call("/cdp/network/requests")
        if response.status_code != 200:
            self.log("Failed to get network requests", "ERROR")
            return []

        requests_data = response.json()
        api_requests = []

        for req in requests_data:
            url = req.get('url', '')
            if '/api/' in url and url.startswith(self.app_url):
                api_requests.append({
                    'url': url,
                    'method': req.get('method', 'GET'),
                    'status': req.get('response', {}).get('status'),
                    'failed': req.get('failed', False)
                })

        if api_requests:
            self.log(f"Found {len(api_requests)} API route calls:")
            for req in api_requests:
                status_emoji = "❌" if req['failed'] or (req['status'] and req['status'] >= 400) else "✅"
                self.log(f"  {status_emoji} {req['method']} {req['url']} - {req['status']}")
        else:
            self.log("No API route calls detected")

        return api_requests

    def test_authentication_flow(self, login_url="/login"):
        """Test NextAuth.js authentication flow"""
        self.log("Testing authentication flow...")

        # Navigate to login page
        if not self.navigate_to_app(login_url):
            return False

        # Check for NextAuth.js elements
        self.log("Checking for NextAuth.js components...")

        checks = {
            "signin_form": "document.querySelector('form[action*=\"signin\"]')",
            "csrf_token": "document.querySelector('input[name=\"csrfToken\"]')",
            "provider_buttons": "document.querySelectorAll('[data-provider]').length",
            "nextauth_url": "window.location.href.includes('/api/auth/')"
        }

        results = {}
        for check_name, js_code in checks.items():
            response = self.api_call("/cdp/execute", "POST", json={"code": js_code})
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    results[check_name] = result['result'].get('value')

        self.log("Authentication check results:")
        for check, result in results.items():
            status = "✅" if result else "❌"
            self.log(f"  {status} {check.replace('_', ' ').title()}: {result}")

        return results

    def check_performance_issues(self):
        """Check for common Next.js performance issues"""
        self.log("Analyzing performance...")

        # Check for large bundle sizes via network requests
        response = self.api_call("/cdp/network/requests")
        if response.status_code != 200:
            return

        requests_data = response.json()
        large_files = []
        js_files = []

        for req in requests_data:
            url = req.get('url', '')
            response_data = req.get('response', {})
            headers = response_data.get('headers', {})

            # Check for JavaScript files
            if url.endswith('.js') or 'javascript' in headers.get('content-type', ''):
                size = headers.get('content-length')
                if size:
                    try:
                        size_kb = int(size) / 1024
                        js_files.append({'url': url, 'size_kb': size_kb})
                        if size_kb > 500:  # Large files > 500KB
                            large_files.append({'url': url, 'size_kb': size_kb})
                    except:
                        pass

        if large_files:
            self.log(f"⚠️ Found {len(large_files)} large JavaScript files:")
            for file in large_files:
                self.log(f"  📦 {file['url']} - {file['size_kb']:.1f}KB")
        else:
            self.log("✅ No unusually large JavaScript files detected")

        # Check for Next.js specific performance metrics
        perf_script = """
        (() => {
            const metrics = {};

            // Check for Next.js router
            if (window.__NEXT_DATA__) {
                metrics.nextjs_detected = true;
                metrics.page_props_size = JSON.stringify(window.__NEXT_DATA__.props || {}).length;
            }

            // Performance timing
            if (window.performance) {
                const timing = window.performance.timing;
                metrics.load_time = timing.loadEventEnd - timing.navigationStart;
                metrics.dom_ready = timing.domContentLoadedEventEnd - timing.navigationStart;
            }

            return metrics;
        })()
        """

        response = self.api_call("/cdp/execute", "POST", json={"code": perf_script})
        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                metrics = result['result'].get('value', {})
                self.log("Performance metrics:")
                for metric, value in metrics.items():
                    self.log(f"  {metric}: {value}")

    def test_dynamic_imports(self):
        """Test Next.js dynamic imports and code splitting"""
        self.log("Testing dynamic imports...")

        # Look for dynamic import chunks in network requests
        response = self.api_call("/cdp/network/requests")
        if response.status_code != 200:
            return

        requests_data = response.json()
        dynamic_chunks = []

        for req in requests_data:
            url = req.get('url', '')
            # Next.js chunk files typically have hash in filename
            if ('/_next/static/chunks/' in url and '.js' in url) or url.endswith('.chunk.js'):
                dynamic_chunks.append(url)

        if dynamic_chunks:
            self.log(f"✅ Found {len(dynamic_chunks)} dynamic chunks (code splitting working)")
            for chunk in dynamic_chunks[:3]:  # Show first 3
                self.log(f"  📦 {chunk.split('/')[-1]}")
        else:
            self.log("⚠️ No dynamic chunks detected - check code splitting configuration")

    def test_static_generation(self):
        """Check for Next.js static generation indicators"""
        self.log("Checking static generation...")

        # Check for static generation indicators
        static_check = """
        (() => {
            const indicators = {};

            // Check for static props
            if (window.__NEXT_DATA__ && window.__NEXT_DATA__.props) {
                indicators.has_static_props = true;
            }

            // Check for build ID
            if (window.__NEXT_DATA__ && window.__NEXT_DATA__.buildId) {
                indicators.build_id = window.__NEXT_DATA__.buildId;
            }

            // Check page rendering method
            if (window.__NEXT_DATA__ && window.__NEXT_DATA__.isFallback !== undefined) {
                indicators.is_fallback = window.__NEXT_DATA__.isFallback;
            }

            return indicators;
        })()
        """

        response = self.api_call("/cdp/execute", "POST", json={"code": static_check})
        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                indicators = result['result'].get('value', {})
                self.log("Static generation indicators:")
                for key, value in indicators.items():
                    self.log(f"  {key}: {value}")

    def debug_form_submission(self, form_selector="form"):
        """Debug form submission issues in Next.js"""
        self.log(f"Debugging form submission for: {form_selector}")

        # Take screenshot before interaction
        self.api_call("/cdp/screenshot")

        # Check if form exists
        form_check = f"document.querySelector('{form_selector}') !== null"
        response = self.api_call("/cdp/execute", "POST", json={"code": form_check})

        if response.status_code == 200:
            result = response.json()
            if result.get('result', {}).get('value'):
                self.log("✅ Form found on page")

                # Monitor form submission
                self.log("Setting up form submission monitoring...")

                # Add event listener to form
                monitor_script = f"""
                (() => {{
                    const form = document.querySelector('{form_selector}');
                    if (form) {{
                        form.addEventListener('submit', (e) => {{
                            console.log('FORM_SUBMIT: Form submission detected');
                            console.log('FORM_SUBMIT: Action:', form.action);
                            console.log('FORM_SUBMIT: Method:', form.method);
                        }});
                        return 'Form monitor added';
                    }}
                    return 'Form not found';
                }})()
                """

                self.api_call("/cdp/execute", "POST", json={"code": monitor_script})
                self.log("Form submission monitor added")

            else:
                self.log(f"❌ Form not found: {form_selector}")

    def run_comprehensive_debug(self):
        """Run comprehensive Next.js debugging session"""
        self.log("Starting comprehensive Next.js debugging session")
        self.log("=" * 50)

        if not self.check_bridge_connection():
            return False

        # Navigate to app
        if not self.navigate_to_app():
            return False

        # Run all checks
        checks = [
            ("Hydration Errors", self.check_hydration_errors),
            ("API Routes", self.check_api_routes),
            ("Performance Issues", self.check_performance_issues),
            ("Dynamic Imports", self.test_dynamic_imports),
            ("Static Generation", self.test_static_generation)
        ]

        results = {}
        for check_name, check_func in checks:
            self.log(f"\n--- {check_name} ---")
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.log(f"Error in {check_name}: {e}", "ERROR")
                results[check_name] = None

        # Summary
        self.log("\n" + "=" * 50)
        self.log("Debugging session completed")

        # Take final screenshot
        screenshot_response = self.api_call("/cdp/screenshot")
        if screenshot_response.status_code == 200:
            with open("nextjs_debug_final.png", "wb") as f:
                f.write(screenshot_response.content)
            self.log("Final screenshot saved: nextjs_debug_final.png")

        return results


def main():
    """Main debugging script"""
    import sys

    # Parse command line arguments
    app_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
    bridge_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8888"

    print(f"Next.js Debugging Tool")
    print(f"App URL: {app_url}")
    print(f"Bridge URL: {bridge_url}")
    print("=" * 50)

    debugger = NextJSDebugger(bridge_url=bridge_url, app_url=app_url)

    try:
        # Run comprehensive debugging
        results = debugger.run_comprehensive_debug()

        if results:
            print("\n✅ Debugging completed successfully!")
            print("Check the console output above for detailed findings.")
        else:
            print("\n❌ Debugging session failed")

    except KeyboardInterrupt:
        print("\n\nDebugging interrupted by user")
    except Exception as e:
        print(f"\n❌ Debugging failed: {e}")


if __name__ == "__main__":
    main()