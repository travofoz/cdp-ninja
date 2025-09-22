"""
HTTP API Server for CDP Bridge
Exposes CDP functionality via REST endpoints
"""

import base64
import json
import logging
import os
import subprocess
import time
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import psutil

# Import our CDP client
from cdp_ninja.core.cdp_client import CDPClient, CDPEvent
from cdp_ninja.core.cdp_pool import CDPConnectionPool, get_global_pool, initialize_global_pool, shutdown_global_pool
from cdp_ninja.config import config
from cdp_ninja.routes import browser_routes, debugging_routes, navigation_routes, dom_routes, system_routes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CDPBridgeServer:
    """Main API server for CDP Bridge"""

    def __init__(self, cdp_port: int = 9222, bridge_port: int = 8888, debug: bool = False):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for remote access

        self.cdp = CDPClient(port=cdp_port)
        self.bridge_port = bridge_port
        self.debug = debug

        # Server state
        self.start_time = datetime.now()
        self.request_count = 0

        self._setup_routes()
        self._setup_error_handlers()

    def _setup_routes(self):
        """Register all API routes"""

        # Health & Status
        self.app.route('/')(self.index)
        self.app.route('/health')(self.health_check)
        self.app.route('/cdp/status')(self.cdp_status)

        # CDP Core Operations
        self.app.route('/cdp/command', methods=['POST'])(self.execute_command)
        self.app.route('/cdp/events/<domain>')(self.get_domain_events)
        self.app.route('/cdp/events')(self.get_all_events)

        # Browser Interaction
        self.app.route('/cdp/click', methods=['POST'])(self.click_element)
        self.app.route('/cdp/type', methods=['POST'])(self.type_text)
        self.app.route('/cdp/scroll', methods=['POST'])(self.scroll_page)
        self.app.route('/cdp/hover', methods=['POST'])(self.hover_element)
        self.app.route('/cdp/screenshot')(self.capture_screenshot)
        self.app.route('/cdp/execute', methods=['POST'])(self.execute_javascript)

        # Network Operations
        self.app.route('/cdp/network/requests')(self.get_network_requests)
        self.app.route('/cdp/network/block', methods=['POST'])(self.block_urls)
        self.app.route('/cdp/network/throttle', methods=['POST'])(self.throttle_network)
        self.app.route('/cdp/network/clear')(self.clear_network_cache)

        # Console & Debugging
        self.app.route('/cdp/console/logs')(self.get_console_logs)
        self.app.route('/cdp/console/clear')(self.clear_console)

        # DOM Operations
        self.app.route('/cdp/dom/snapshot')(self.get_dom_snapshot)
        self.app.route('/cdp/dom/query', methods=['POST'])(self.query_selector)

        # Form Operations
        self.app.route('/cdp/form/fill', methods=['POST'])(self.fill_form)
        self.app.route('/cdp/form/submit', methods=['POST'])(self.submit_form)

        # Page Operations
        self.app.route('/cdp/page/navigate', methods=['POST'])(self.navigate)
        self.app.route('/cdp/page/reload')(self.reload_page)
        self.app.route('/cdp/page/back')(self.go_back)
        self.app.route('/cdp/page/forward')(self.go_forward)

        # System Operations (Windows)
        self.app.route('/system/powershell', methods=['POST'])(self.run_powershell)
        self.app.route('/system/processes')(self.list_processes)
        self.app.route('/system/chrome/profiles')(self.chrome_profiles)

        # Advanced Debugging
        self.app.route('/debug/reproduce', methods=['POST'])(self.reproduce_bug)

    def _setup_error_handlers(self):
        """Setup global error handlers"""

        @self.app.errorhandler(404)
        def not_found(e):
            return jsonify({"error": "Endpoint not found"}), 404

        @self.app.errorhandler(500)
        def server_error(e):
            logger.error(f"Server error: {e}")
            return jsonify({"error": "Internal server error"}), 500

        @self.app.before_request
        def before_request():
            self.request_count += 1

    # ========== Route Implementations ==========

    def index(self):
        """API documentation page"""
        return f"""
        <h1>CDP Thin Bridge API</h1>
        <p>Status: Running</p>
        <p>CDP Port: {self.cdp.connection.port}</p>
        <p>Uptime: {datetime.now() - self.start_time}</p>
        <p>Requests: {self.request_count}</p>
        <h2>Quick Links:</h2>
        <ul>
            <li><a href="/health">Health Check</a></li>
            <li><a href="/cdp/status">CDP Status</a></li>
            <li><a href="/cdp/console/logs">Console Logs</a></li>
            <li><a href="/cdp/network/requests">Network Requests</a></li>
        </ul>
        <h2>Example Usage:</h2>
        <pre>
# Take screenshot
curl {request.host_url}cdp/screenshot > screenshot.png

# Execute JavaScript
curl -X POST {request.host_url}cdp/execute \\
  -H "Content-Type: application/json" \\
  -d '{{"code":"document.title"}}'

# Click element
curl -X POST {request.host_url}cdp/click \\
  -H "Content-Type: application/json" \\
  -d '{{"selector":"#my-button"}}'
        </pre>
        """

    def health_check(self):
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "cdp_connected": self.cdp.is_connected(),
            "uptime": str(datetime.now() - self.start_time),
            "requests": self.request_count,
            "timestamp": datetime.now().isoformat()
        })

    def cdp_status(self):
        """Get CDP connection status"""
        info = self.cdp.get_connection_info()
        return jsonify(info)

    def execute_command(self):
        """Execute arbitrary CDP command"""
        data = request.get_json()
        if not data or 'method' not in data:
            return jsonify({"error": "Method required"}), 400

        method = data['method']
        params = data.get('params', {})

        result = self.cdp.send_command(method, params)
        return jsonify(result)

    def get_domain_events(self, domain):
        """Get recent events for specific domain"""
        events = self.cdp.get_recent_events(domain, limit=100)
        return jsonify([event.to_dict() for event in events])

    def get_all_events(self):
        """Get all recent events"""
        events = self.cdp.get_recent_events(limit=200)
        return jsonify([event.to_dict() for event in events])

    def click_element(self):
        """Click on element by selector or coordinates"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        if 'selector' in data:
            # Click by selector
            selector = data['selector']
            code = f"""
                (() => {{
                    const el = document.querySelector('{selector}');
                    if (el) {{
                        el.click();
                        return {{success: true, selector: '{selector}'}};
                    }}
                    return {{success: false, error: 'Element not found'}};
                }})()
            """
            result = self.cdp.send_command('Runtime.evaluate', {
                'expression': code,
                'returnByValue': True
            })

            if 'result' in result and 'result' in result['result']:
                return jsonify(result['result']['result'])

        elif 'x' in data and 'y' in data:
            # Click by coordinates
            x, y = data['x'], data['y']

            # Mouse press
            press_result = self.cdp.send_command('Input.dispatchMouseEvent', {
                'type': 'mousePressed',
                'x': x,
                'y': y,
                'button': 'left',
                'clickCount': 1
            })

            if 'error' in press_result:
                return jsonify(press_result), 500

            # Mouse release
            release_result = self.cdp.send_command('Input.dispatchMouseEvent', {
                'type': 'mouseReleased',
                'x': x,
                'y': y,
                'button': 'left'
            })

            if 'error' in release_result:
                return jsonify(release_result), 500

            return jsonify({"success": True, "clicked": [x, y]})

        else:
            return jsonify({"error": "Selector or coordinates required"}), 400

        return jsonify(result)

    def type_text(self):
        """Type text into element or focused input"""
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Text required"}), 400

        text = data['text']
        selector = data.get('selector')

        if selector:
            # Focus element first
            focus_code = f"document.querySelector('{selector}').focus()"
            self.cdp.send_command('Runtime.evaluate', {'expression': focus_code})

        # Type each character
        for char in text:
            result = self.cdp.send_command('Input.dispatchKeyEvent', {
                'type': 'char',
                'text': char
            })
            if 'error' in result:
                return jsonify(result), 500

        return jsonify({"success": True, "typed": text})

    def scroll_page(self):
        """Scroll the page"""
        data = request.get_json() or {}
        direction = data.get('direction', 'down')
        amount = data.get('amount', 100)

        delta_y = amount if direction == 'down' else -amount if direction == 'up' else 0

        result = self.cdp.send_command('Input.dispatchMouseEvent', {
            'type': 'mouseWheel',
            'x': 100,
            'y': 100,
            'deltaX': 0,
            'deltaY': delta_y
        })

        if 'error' in result:
            return jsonify(result), 500

        return jsonify({"success": True, "scrolled": direction, "amount": amount})

    def hover_element(self):
        """Hover over element"""
        data = request.get_json()
        if not data or 'selector' not in data:
            return jsonify({"error": "Selector required"}), 400

        selector = data['selector']

        # Get element coordinates
        code = f"""
            (() => {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    const rect = el.getBoundingClientRect();
                    return {{x: rect.x + rect.width/2, y: rect.y + rect.height/2}};
                }}
                return null;
            }})()
        """
        result = self.cdp.send_command('Runtime.evaluate', {
            'expression': code,
            'returnByValue': True
        })

        if 'result' in result and 'result' in result['result']:
            coords = result['result']['result']
            if coords:
                x, y = coords['x'], coords['y']

                hover_result = self.cdp.send_command('Input.dispatchMouseEvent', {
                    'type': 'mouseMoved',
                    'x': x,
                    'y': y
                })

                if 'error' in hover_result:
                    return jsonify(hover_result), 500

                return jsonify({"success": True, "hovered": selector, "at": [x, y]})

        return jsonify({"error": "Element not found"}), 404

    def capture_screenshot(self):
        """Capture screenshot of current page"""
        format_type = request.args.get('format', 'png')
        quality = int(request.args.get('quality', 80))
        full_page = request.args.get('full_page', 'false').lower() == 'true'

        params = {
            'format': format_type,
            'quality': quality
        }

        if full_page:
            params['captureBeyondViewport'] = True

        result = self.cdp.send_command('Page.captureScreenshot', params)

        if 'result' in result and 'data' in result['result']:
            img_data = base64.b64decode(result['result']['data'])
            return Response(img_data, mimetype=f'image/{format_type}')

        return jsonify(result), 500

    def execute_javascript(self):
        """Execute JavaScript in page context"""
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({"error": "Code required"}), 400

        code = data['code']
        result = self.cdp.send_command('Runtime.evaluate', {
            'expression': code,
            'returnByValue': True
        })

        return jsonify(result)

    def get_network_requests(self):
        """Get recent network requests with details"""
        events = self.cdp.get_recent_events('Network', 200)

        # Group by request ID
        requests = {}
        for event in events:
            if 'requestId' in event.params:
                req_id = event.params['requestId']
                if req_id not in requests:
                    requests[req_id] = {}

                event_type = event.method.replace('Network.', '')
                requests[req_id][event_type] = event.params

        # Format for response
        formatted = []
        for req_id, data in requests.items():
            if 'requestWillBeSent' in data:
                req = data['requestWillBeSent']
                formatted.append({
                    'id': req_id,
                    'url': req['request']['url'],
                    'method': req['request']['method'],
                    'timestamp': req['timestamp'],
                    'response': data.get('responseReceived', {}).get('response', {}),
                    'failed': 'loadingFailed' in data
                })

        return jsonify(formatted)

    def block_urls(self):
        """Block URLs matching patterns"""
        data = request.get_json()
        if not data or 'patterns' not in data:
            return jsonify({"error": "Patterns required"}), 400

        patterns = data['patterns']
        result = self.cdp.send_command('Network.setBlockedURLs', {'urls': patterns})
        return jsonify(result)

    def throttle_network(self):
        """Simulate slow network conditions"""
        data = request.get_json() or {}

        result = self.cdp.send_command('Network.emulateNetworkConditions', {
            'offline': data.get('offline', False),
            'downloadThroughput': data.get('download', 100000),
            'uploadThroughput': data.get('upload', 50000),
            'latency': data.get('latency', 100)
        })

        return jsonify(result)

    def clear_network_cache(self):
        """Clear network cache"""
        result = self.cdp.send_command('Network.clearBrowserCache')
        return jsonify(result)

    def get_console_logs(self):
        """Get console output from page"""
        console_events = self.cdp.get_recent_events('Console', 100)
        runtime_events = self.cdp.get_recent_events('Runtime', 100)

        logs = []
        for event in console_events + runtime_events:
            if event.method in ['Console.messageAdded', 'Runtime.consoleAPICalled']:
                logs.append(event.params)

        return jsonify(logs)

    def clear_console(self):
        """Clear console output"""
        result = self.cdp.send_command('Runtime.evaluate', {
            'expression': 'console.clear()'
        })
        return jsonify(result)

    def get_dom_snapshot(self):
        """Get current DOM tree"""
        result = self.cdp.send_command('DOM.getDocument', {'depth': -1})
        if 'result' in result:
            root_id = result['result']['root']['nodeId']
            html_result = self.cdp.send_command('DOM.getOuterHTML', {'nodeId': root_id})
            return jsonify(html_result)

        return jsonify(result)

    def query_selector(self):
        """Query DOM selector"""
        data = request.get_json()
        if not data or 'selector' not in data:
            return jsonify({"error": "Selector required"}), 400

        selector = data['selector']
        code = f"""
            Array.from(document.querySelectorAll('{selector}')).map(el => ({{
                tagName: el.tagName,
                textContent: el.textContent.substring(0, 100),
                innerHTML: el.innerHTML.substring(0, 200),
                attributes: Array.from(el.attributes).reduce((acc, attr) => {{
                    acc[attr.name] = attr.value;
                    return acc;
                }}, {{}})
            }}))
        """

        result = self.cdp.send_command('Runtime.evaluate', {
            'expression': code,
            'returnByValue': True
        })

        return jsonify(result)

    def fill_form(self):
        """Fill form fields"""
        data = request.get_json()
        if not data or 'fields' not in data:
            return jsonify({"error": "Fields required"}), 400

        fields = data['fields']
        results = []

        for selector, value in fields.items():
            code = f"""
                (() => {{
                    const el = document.querySelector('{selector}');
                    if (el) {{
                        el.value = '{value}';
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                        el.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return true;
                    }}
                    return false;
                }})()
            """
            result = self.cdp.send_command('Runtime.evaluate', {
                'expression': code,
                'returnByValue': True
            })

            success = False
            if 'result' in result and 'result' in result['result']:
                success = result['result']['result']

            results.append({
                "field": selector,
                "value": value,
                "success": success
            })

        return jsonify({"filled": results})

    def submit_form(self):
        """Submit form"""
        data = request.get_json()
        if not data or 'selector' not in data:
            return jsonify({"error": "Form selector required"}), 400

        selector = data['selector']
        code = f"document.querySelector('{selector}').submit()"

        result = self.cdp.send_command('Runtime.evaluate', {'expression': code})
        return jsonify(result)

    def navigate(self):
        """Navigate to URL"""
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "URL required"}), 400

        url = data['url']
        result = self.cdp.send_command('Page.navigate', {'url': url})
        return jsonify(result)

    def reload_page(self):
        """Reload current page"""
        result = self.cdp.send_command('Page.reload')
        return jsonify(result)

    def go_back(self):
        """Go back in browser history"""
        code = "window.history.back()"
        result = self.cdp.send_command('Runtime.evaluate', {'expression': code})
        return jsonify(result)

    def go_forward(self):
        """Go forward in browser history"""
        code = "window.history.forward()"
        result = self.cdp.send_command('Runtime.evaluate', {'expression': code})
        return jsonify(result)

    def run_powershell(self):
        """Execute PowerShell command (Windows only)"""
        if platform.system() != 'Windows':
            return jsonify({"error": "PowerShell only available on Windows"}), 400

        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({"error": "Command required"}), 400

        command = data['command']

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=10
            )

            return jsonify({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            })

        except subprocess.TimeoutExpired:
            return jsonify({"error": "Command timeout"}), 408
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def list_processes(self):
        """List running processes with Chrome highlighted"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                info = proc.info
                if 'chrome' in info['name'].lower():
                    info['chrome_process'] = True
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return jsonify(processes)

    def chrome_profiles(self):
        """List Chrome profiles and active sessions"""
        if platform.system() == 'Windows':
            profiles_path = Path.home() / "AppData/Local/Google/Chrome/User Data"
        elif platform.system() == 'Darwin':
            profiles_path = Path.home() / "Library/Application Support/Google/Chrome"
        else:
            profiles_path = Path.home() / ".config/google-chrome"

        profiles = []

        if profiles_path.exists():
            for item in profiles_path.iterdir():
                if item.is_dir() and (item.name == "Default" or item.name.startswith("Profile")):
                    profiles.append({
                        "name": item.name,
                        "path": str(item),
                        "bookmarks": (item / "Bookmarks").exists(),
                        "history": (item / "History").exists()
                    })

        return jsonify(profiles)

    def reproduce_bug(self):
        """Automated bug reproduction workflow"""
        data = request.get_json()
        if not data or 'steps' not in data:
            return jsonify({"error": "Steps required"}), 400

        steps = data['steps']
        capture_screenshots = data.get('screenshots', False)

        results = []

        for i, step in enumerate(steps):
            step_result = {
                "step": i + 1,
                "description": step.get('description', f'Step {i+1}'),
                "timestamp": time.time()
            }

            try:
                # Execute step action
                action = step.get('action')
                success = False

                if action == 'click':
                    if 'selector' in step:
                        response = self.click_element.__wrapped__(self)
                        with self.app.test_request_context(json={'selector': step['selector']}):
                            request.json = {'selector': step['selector']}
                            response = self.click_element()
                        success = True
                    elif 'x' in step and 'y' in step:
                        with self.app.test_request_context(json={'x': step['x'], 'y': step['y']}):
                            request.json = {'x': step['x'], 'y': step['y']}
                            response = self.click_element()
                        success = True

                elif action == 'type':
                    with self.app.test_request_context(json={'text': step['text'], 'selector': step.get('selector')}):
                        request.json = {'text': step['text'], 'selector': step.get('selector')}
                        response = self.type_text()
                    success = True

                elif action == 'wait':
                    time.sleep(step.get('duration', 1))
                    success = True

                elif action == 'navigate':
                    with self.app.test_request_context(json={'url': step['url']}):
                        request.json = {'url': step['url']}
                        response = self.navigate()
                    success = True

                # Capture state after step
                if capture_screenshots:
                    screenshot_result = self.cdp.send_command('Page.captureScreenshot', {
                        'format': 'jpeg',
                        'quality': 50
                    })
                    if 'result' in screenshot_result:
                        step_result['screenshot'] = screenshot_result['result']['data']

                # Get console errors
                console_events = self.cdp.get_recent_events('Console', 10)
                errors = [e.params for e in console_events
                         if e.params.get('level') == 'error']
                step_result['console_errors'] = errors

                step_result['success'] = success

            except Exception as e:
                step_result['success'] = False
                step_result['error'] = str(e)

            results.append(step_result)

            # Stop if step failed
            if not step_result['success']:
                break

        return jsonify({
            "completed": all(r['success'] for r in results),
            "steps_executed": len(results),
            "results": results
        })

    def run(self):
        """Start the bridge server"""
        logger.info(f"Starting CDP Bridge Server on port {self.bridge_port}")

        # Start CDP client
        if not self.cdp.start():
            logger.error("Failed to connect to Chrome DevTools")
            return False

        try:
            # Run Flask server
            self.app.run(
                host='127.0.0.1',  # Bind to localhost for SSH tunnel compatibility
                port=self.bridge_port,
                debug=self.debug,
                use_reloader=False
            )
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        finally:
            self.cdp.stop()

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='CDP Thin Bridge Server')
    parser.add_argument('--cdp-port', type=int, default=9222,
                       help='Chrome DevTools Protocol port')
    parser.add_argument('--bridge-port', type=int, default=8888,
                       help='HTTP API bridge port')
    parser.add_argument('--debug', action='store_true',
                       help='Enable Flask debug mode')

    args = parser.parse_args()

    print("🥷 CDP Ninja Server")
    print("=" * 40)
    print(f"Chrome DevTools Port: {args.cdp_port}")
    print(f"Bridge API Port: {args.bridge_port}")
    print(f"Debug Mode: {args.debug}")
    print("⚠️  DANGEROUS: No input validation")
    print("=" * 40)

    server = CDPBridgeServer(
        cdp_port=args.cdp_port,
        bridge_port=args.bridge_port,
        debug=args.debug
    )

    server.run()


if __name__ == "__main__":
    main()