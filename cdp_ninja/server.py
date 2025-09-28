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
import math
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import psutil

# Import our CDP client
from cdp_ninja.core.cdp_client import CDPClient, CDPEvent
from cdp_ninja.core.cdp_pool import CDPConnectionPool, get_global_pool, initialize_global_pool, shutdown_global_pool
from cdp_ninja.core.domain_manager import DomainRiskLevel
from cdp_ninja.core.event_manager import initialize_event_manager
from cdp_ninja.config import config
from cdp_ninja.routes import browser_routes, debugging_routes, navigation_routes, dom_routes, dom_advanced_routes, network_intelligence_routes, js_debugging_routes, stress_testing_routes, system_routes, error_handling_routes, performance_routes, security_routes, accessibility_routes, stress_testing_advanced_routes

# Import deployment modules
from cdp_ninja.deployment.cli import (
    handle_usage, handle_install_agents, handle_install_deps,
    handle_tunnel, handle_kill_tunnels, handle_start_browser, handle_invoke_claude, handle_shell,
    configure_domain_manager, handle_list_domains, handle_domain_status, handle_health_check
)
from cdp_ninja.deployment.platforms import detect_local_platform, detect_remote_platform
from cdp_ninja.deployment.ssh_utils import verify_ssh_access_remote, check_remote_dependencies, setup_ssh_tunnel, start_claude_interface
from cdp_ninja.deployment.verification import verify_remote_installations, verify_local_installations
from cdp_ninja.deployment.installers import install_deps_local, install_deps_remote

# Import templates and constants
from cdp_ninja.templates.javascript import JSTemplates
from cdp_ninja.constants import CDPDefaults, HTTPStatus, ErrorMessages

# Import domain-specific modules
from cdp_ninja.utils.error_handling import handle_cdp_error
from cdp_ninja.interaction.coordinates import validate_drag_coordinates
from cdp_ninja.dom.coordinates import get_element_coordinates
from cdp_ninja.interaction.mouse import execute_mouse_drag

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shell execution flag will be checked dynamically


# Domain-specific functions moved to respective modules:
# - handle_cdp_error → utils.error_handling
# - validate_drag_coordinates → interaction.coordinates
# - get_element_coordinates → dom.coordinates
# - execute_mouse_drag → interaction.mouse


class CDPBridgeServer:
    """Main API server for CDP Bridge"""

    def __init__(self, cdp_port: int = 9222, bridge_port: int = 8888, debug: bool = False, timeout: int = 900,
                 max_risk_level=None, max_connections: int = 5):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for remote access

        self.cdp = CDPClient(port=cdp_port, timeout=timeout)
        self.bridge_port = bridge_port
        self.debug = debug
        self.timeout = timeout
        self.max_risk_level = max_risk_level
        self.max_connections = max_connections

        # Initialize centralized event manager
        initialize_event_manager(max_events_per_domain=200, max_total_events=self.max_connections * 1000)

        # Server state
        self.start_time = datetime.now()
        self.request_count = 0

        self._setup_routes()
        self._setup_error_handlers()

    def _setup_routes(self):
        """Register all API routes"""

        # Register blueprints
        self.app.register_blueprint(debugging_routes)
        self.app.register_blueprint(browser_routes)
        self.app.register_blueprint(navigation_routes)
        self.app.register_blueprint(dom_routes)
        self.app.register_blueprint(dom_advanced_routes)
        self.app.register_blueprint(network_intelligence_routes)
        self.app.register_blueprint(js_debugging_routes)
        self.app.register_blueprint(stress_testing_routes)
        self.app.register_blueprint(system_routes)
        self.app.register_blueprint(error_handling_routes)
        self.app.register_blueprint(performance_routes)
        self.app.register_blueprint(security_routes)
        self.app.register_blueprint(accessibility_routes)
        self.app.register_blueprint(stress_testing_advanced_routes)

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
        self.app.route('/cdp/drag', methods=['POST'])(self.drag_element)
        self.app.route('/cdp/screenshot')(self.capture_screenshot)
        self.app.route('/cdp/execute', methods=['POST'])(self.execute_javascript)

        # Network Operations
        self.app.route('/cdp/network/requests')(self.get_network_requests)
        self.app.route('/cdp/network/block', methods=['POST'])(self.block_urls)
        self.app.route('/cdp/network/throttle', methods=['POST'])(self.throttle_network)
        self.app.route('/cdp/network/clear')(self.clear_network_cache)

        # Console & Debugging
        self.app.route('/cdp/console/logs')(self.get_console_logs)

        # DOM Operations
        self.app.route('/cdp/dom/snapshot')(self.get_dom_snapshot)
        self.app.route('/cdp/dom/query', methods=['POST'])(self.query_selector)
        self.app.route('/cdp/dom/set_attribute', methods=['POST'])(self.set_element_attribute)
        self.app.route('/cdp/dom/set_html', methods=['POST'])(self.set_element_html)

        # Form Operations
        self.app.route('/cdp/form/fill', methods=['POST'])(self.fill_form)
        self.app.route('/cdp/form/submit', methods=['POST'])(self.submit_form)
        self.app.route('/cdp/form/values')(self.get_form_values)

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
            code = JSTemplates.click_element(selector)
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

            error_response = handle_cdp_error(press_result, "Mouse press failed")
            if error_response:
                return error_response

            # Mouse release
            release_result = self.cdp.send_command('Input.dispatchMouseEvent', {
                'type': 'mouseReleased',
                'x': x,
                'y': y,
                'button': 'left'
            })

            error_response = handle_cdp_error(release_result, "Mouse release failed")
            if error_response:
                return error_response

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
            focus_code = JSTemplates.focus_element(selector)
            self.cdp.send_command('Runtime.evaluate', {'expression': focus_code})

        # Type each character
        for char in text:
            result = self.cdp.send_command('Input.dispatchKeyEvent', {
                'type': 'char',
                'text': char
            })
            error_response = handle_cdp_error(result, f"Failed to type character: {char}")
            if error_response:
                return error_response

        return jsonify({"success": True, "typed": text})

    def scroll_page(self):
        """Scroll the page"""
        data = request.get_json() or {}
        direction = data.get('direction', 'down')
        amount = data.get('amount', CDPDefaults.DEFAULT_SCROLL_AMOUNT)

        delta_y = amount if direction == 'down' else -amount if direction == 'up' else 0

        result = self.cdp.send_command('Input.dispatchMouseEvent', {
            'type': 'mouseWheel',
            'x': CDPDefaults.MOUSE_WHEEL_X,
            'y': CDPDefaults.MOUSE_WHEEL_Y,
            'deltaX': 0,
            'deltaY': delta_y
        })

        error_response = handle_cdp_error(result, "Type text operation failed")
        if error_response:
            return error_response

        return jsonify({"success": True, "scrolled": direction, "amount": amount})

    def hover_element(self):
        """Hover over element"""
        data = request.get_json()
        if not data or 'selector' not in data:
            return jsonify({"error": "Selector required"}), 400

        selector = data['selector']

        # Get element coordinates using template
        code = JSTemplates.get_element_center_coordinates(selector)
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

                error_response = handle_cdp_error(hover_result, "Hover operation failed")
                if error_response:
                    return error_response

                return jsonify({"success": True, "hovered": selector, "at": [x, y]})

        return jsonify({"error": "Element not found"}), 404

    def drag_element(self):
        """Drag from start coordinates to end coordinates"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), HTTPStatus.BAD_REQUEST

        # NO EXCEPTION HANDLING - Let malformed input reach browser for security testing
        # Determine drag mode and get coordinates
        if all(key in data for key in ['startX', 'startY', 'endX', 'endY']):
            # Direct coordinate drag
            start_x, start_y, end_x, end_y = validate_drag_coordinates(data)
        elif all(key in data for key in ['startSelector', 'endSelector']):
            # Selector-based drag - get element coordinates
            start_x, start_y = get_element_coordinates(self.cdp, data['startSelector'], "start element")
            end_x, end_y = get_element_coordinates(self.cdp, data['endSelector'], "end element")
        else:
            return jsonify({
                "error": "Either startX/startY/endX/endY or startSelector/endSelector required"
            }), HTTPStatus.BAD_REQUEST

        # Execute the drag operation
        error_response = execute_mouse_drag(self.cdp, start_x, start_y, end_x, end_y)
        if error_response:
            return error_response

        return jsonify({
            "success": True,
            "dragged": {
                "from": [start_x, start_y],
                "to": [end_x, end_y]
            }
        })

    def capture_screenshot(self):
        """Capture screenshot of current page"""
        format_type = request.args.get('format', 'png')
        quality = int(request.args.get('quality', CDPDefaults.DEFAULT_SCREENSHOT_QUALITY))
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
        """Get recent network requests and WebSocket frames"""
        events = self.cdp.get_recent_events('Network', 200)

        # Group by request ID for HTTP requests
        requests = {}
        websocket_frames = []

        for event in events:
            # Handle WebSocket frames separately
            if event.method in ['Network.webSocketFrameReceived', 'Network.webSocketFrameSent']:
                websocket_frames.append({
                    'type': 'websocket_frame',
                    'direction': 'received' if 'Received' in event.method else 'sent',
                    'timestamp': event.timestamp,
                    'requestId': event.params.get('requestId', ''),
                    'frame': event.params.get('response', {}),
                    'payload': event.params.get('response', {}).get('payloadData', '')
                })
            elif 'requestId' in event.params:
                req_id = event.params['requestId']
                if req_id not in requests:
                    requests[req_id] = {}

                event_type = event.method.replace('Network.', '')
                requests[req_id][event_type] = event.params

        # Format HTTP requests
        formatted = []
        for req_id, data in requests.items():
            if 'requestWillBeSent' in data:
                req = data['requestWillBeSent']
                formatted.append({
                    'type': 'http_request',
                    'id': req_id,
                    'url': req['request']['url'],
                    'method': req['request']['method'],
                    'timestamp': req['timestamp'],
                    'response': data.get('responseReceived', {}).get('response', {}),
                    'failed': 'loadingFailed' in data
                })

        # Combine and sort by timestamp
        all_requests = formatted + websocket_frames
        all_requests.sort(key=lambda x: x['timestamp'], reverse=True)

        return jsonify({
            'requests': all_requests,
            'http_count': len(formatted),
            'websocket_count': len(websocket_frames),
            'total': len(all_requests)
        })

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
            'downloadThroughput': data.get('download', CDPDefaults.DEFAULT_DOWNLOAD_THROUGHPUT),
            'uploadThroughput': data.get('upload', CDPDefaults.DEFAULT_UPLOAD_THROUGHPUT),
            'latency': data.get('latency', CDPDefaults.DEFAULT_NETWORK_LATENCY)
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

    def get_dom_snapshot(self):
        """Get current DOM tree"""
        result = self.cdp.send_command('DOM.getDocument', {'depth': -1})
        if 'result' in result and 'root' in result['result'] and 'nodeId' in result['result']['root']:
            root_id = result['result']['root']['nodeId']
            html_result = self.cdp.send_command('DOM.getOuterHTML', {'nodeId': root_id})
            return jsonify(html_result)

        return jsonify({"error": "Failed to get DOM document"}), 500

    def query_selector(self):
        """Query DOM selector"""
        data = request.get_json()
        if not data or 'selector' not in data:
            return jsonify({"error": "Selector required"}), 400

        selector = data['selector']
        code = f"""
            (() => {{
                const selector = '{selector}';
                return Array.from(document.querySelectorAll(selector)).map(el => ({{
                    tagName: el.tagName,
                    textContent: el.textContent.substring(0, 100),
                    innerHTML: el.innerHTML.substring(0, 200),
                    attributes: Array.from(el.attributes).reduce((acc, attr) => {{
                        acc[attr.name] = attr.value;
                        return acc;
                    }}, {{}})
                }}));
            }})()
        """

        result = self.cdp.send_command('Runtime.evaluate', {
            'expression': code,
            'returnByValue': True
        })

        return jsonify(result)

    def set_element_attribute(self):
        """Set attribute on DOM element"""
        data = request.get_json()
        if not data or 'selector' not in data or 'name' not in data or 'value' not in data:
            return jsonify({"error": "Selector, name, and value required"}), 400

        selector = data['selector']
        attr_name = data['name']
        attr_value = data['value']

        code = JSTemplates.set_element_attribute(selector, attr_name, attr_value)

        result = self.cdp.send_command('Runtime.evaluate', {
            'expression': code,
            'returnByValue': True
        })

        if 'result' in result and 'result' in result['result']:
            return jsonify(result['result']['result'])

        return jsonify({"error": "Failed to set attribute"}), 500

    def set_element_html(self):
        """Set innerHTML of DOM element"""
        data = request.get_json()
        if not data or 'selector' not in data or 'html' not in data:
            return jsonify({"error": "Selector and html required"}), 400

        selector = data['selector']
        html_content = data['html']

        # Use template for safe HTML content setting
        code = JSTemplates.set_element_html(selector, html_content)

        result = self.cdp.send_command('Runtime.evaluate', {
            'expression': code,
            'returnByValue': True
        })

        if 'result' in result and 'result' in result['result']:
            return jsonify(result['result']['result'])

        return jsonify({"error": "Failed to set HTML"}), 500

    def get_form_values(self):
        """Get all form field values"""
        selector = request.args.get('selector', 'form')

        code = JSTemplates.get_form_data(selector)

        result = self.cdp.send_command('Runtime.evaluate', {
            'expression': code,
            'returnByValue': True
        })

        if 'result' in result and 'result' in result['result']:
            return jsonify(result['result']['result'])

        return jsonify({"error": "Failed to get form values"}), 500

    def fill_form(self):
        """Fill form fields"""
        data = request.get_json()
        if not data or 'fields' not in data:
            return jsonify({"error": "Fields required"}), 400

        fields = data['fields']
        results = []

        for selector, value in fields.items():
            code = JSTemplates.fill_form_field(selector, value)
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

        # Initialize global pool for blueprints
        pool_risk_level = self.max_risk_level if self.max_risk_level else DomainRiskLevel.MEDIUM
        initialize_global_pool(max_connections=self.max_connections, port=self.cdp.connection.port, max_risk_level=pool_risk_level)

        try:
            # Run Flask server
            self.app.run(
                host='127.0.0.1',  # IPv4 localhost for SSH tunnel compatibility
                port=self.bridge_port,
                debug=self.debug,
                use_reloader=False
            )
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        finally:
            self.cdp.stop()

        return True



# Phase 4 Deployment Action Handlers - Moved to deployment/cli.py
# Functions handle_usage, handle_install_agents, handle_install_deps,
# handle_tunnel, handle_invoke_claude, handle_shell and all helper functions
# have been extracted to deployment/cli.py for better modularization

def main():
    """Main entry point"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='CDP Ninja - Browser debugging bridge and deployment toolkit')

    # Server configuration arguments
    parser.add_argument('--cdp-port', type=int, default=9222,
                       help='Chrome DevTools Protocol port')
    parser.add_argument('--bridge-port', type=int, default=8888,
                       help='HTTP API bridge port')
    parser.add_argument('--debug', action='store_true',
                       help='Enable Flask debug mode')
    parser.add_argument('--timeout', type=int, default=900,
                       help='Chrome command timeout in seconds (default: 900)')

    # Domain loading and risk control
    parser.add_argument('--max-risk-level', choices=['safe', 'low', 'medium', 'high', 'very_high'], default='medium',
                       help='Maximum risk level for domain loading (default: medium)')
    parser.add_argument('--eager-load-domains', action='store_true',
                       help='Enable all allowed domains immediately on startup')
    parser.add_argument('--lazy-load-domains', action='store_true',
                       help='Enable domains only when needed (default behavior)')
    parser.add_argument('--enable-domains', type=str, metavar='DOMAIN,DOMAIN',
                       help='Comma-separated list of specific domains to enable')
    parser.add_argument('--disable-auto-unload', action='store_true',
                       help='Disable automatic domain unloading after timeout')
    parser.add_argument('--domain-timeout', type=int, metavar='MINUTES',
                       help='Timeout in minutes for domain auto-unloading')

    # Server control
    parser.add_argument('--bind-host', type=str, default='127.0.0.1',
                       help='Host address to bind the server (default: 127.0.0.1)')
    parser.add_argument('--max-connections', type=int, default=5,
                       help='Maximum number of CDP connections (default: 5)')
    parser.add_argument('--enable-cors', action='store_true',
                       help='Enable CORS for remote access')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'], default='info',
                       help='Set logging level (default: info)')
    parser.add_argument('--version', action='store_true',
                       help='Show version information and exit')

    # Diagnostic and monitoring
    parser.add_argument('--list-domains', action='store_true',
                       help='List all available domains with risk levels')
    parser.add_argument('--domain-status', action='store_true',
                       help='Show current domain status and exit')
    parser.add_argument('--health-check', action='store_true',
                       help='Perform health check on CDP bridge')

    # Phase 4 deployment action arguments
    parser.add_argument('--usage', action='store_true',
                       help='Output complete API documentation')
    parser.add_argument('--install-agents', type=str, metavar='[user@host:]/path',
                       help='Install agents locally or remotely with conflict resolution')
    parser.add_argument('--install-deps', type=str, metavar='[user@host]', nargs='?', const='localhost',
                       help='Install dependencies (Claude CLI, tmux, gotty/ttyd)')
    parser.add_argument('--web-backend', choices=['gotty', 'ttyd'], default='ttyd',
                       help='Web terminal backend for --install-deps and --invoke-claude (default: ttyd)')
    parser.add_argument('--tunnel', type=str, metavar='user@host',
                       help='Setup SSH tunnels for remote access')
    parser.add_argument('--kill-tunnels', action='store_true',
                       help='Kill all active SSH tunnels')
    parser.add_argument('--start-browser', action='store_true',
                       help='Start Chromium browser with CDP debugging enabled')
    parser.add_argument('--invoke-claude', type=str, metavar='user@host',
                       help='Start Claude interface in tmux with web terminal')
    parser.add_argument('--shell', action='store_true',
                       help='Enable shell execution capabilities')
    parser.add_argument('--instruct-only', action='store_true',
                       help='Show manual instructions instead of executing deployment actions')

    args = parser.parse_args()

    # Handle version flag first
    if args.version:
        from ._version import __version__
        print(f"CDP Ninja v{__version__}")
        sys.exit(0)

    # Handle diagnostic flags
    if args.list_domains:
        handle_list_domains(args)
        sys.exit(0)

    if args.domain_status:
        handle_domain_status(args)
        sys.exit(0)

    if args.health_check:
        result = handle_health_check(args)
        sys.exit(0 if result else 1)

    # Handle action flags first - execute action and exit
    if args.usage:
        handle_usage()
        sys.exit(0)

    if args.install_agents:
        handle_install_agents(args.install_agents, args.instruct_only)
        sys.exit(0)

    if args.install_deps:
        handle_install_deps(args.install_deps, args.web_backend, args.instruct_only)
        sys.exit(0)

    if args.tunnel:
        handle_tunnel(args.tunnel, args.instruct_only)
        sys.exit(0)

    if args.kill_tunnels:
        handle_kill_tunnels()
        sys.exit(0)

    if args.start_browser:
        handle_start_browser()
        sys.exit(0)

    if args.invoke_claude:
        handle_invoke_claude(args.invoke_claude, args.web_backend, args.instruct_only)
        sys.exit(0)

    if args.shell:
        result = handle_shell()
        if result == 'start_server_with_shell':
            # Continue to start server with shell enabled
            pass
        else:
            sys.exit(0)

    # Configure domain manager based on CLI arguments
    domain_manager = configure_domain_manager(args)

    # No action flags provided - start server (backward compatible)
    print("🥷 CDP Ninja Server")
    print("=" * 40)
    print(f"Chrome DevTools Port: {args.cdp_port}")
    print(f"Bridge API Port: {args.bridge_port}")
    print(f"Debug Mode: {args.debug}")

    # Shell execution status (set by --shell flag via handle_shell())
    if config.enable_shell_execution:
        print(f"Shell Execution: ENABLED (POST /system/execute)")
    else:
        print(f"Shell Execution: DISABLED")

    print("⚠️  DANGEROUS: No input validation")
    print("=" * 40)

    server = CDPBridgeServer(
        cdp_port=args.cdp_port,
        bridge_port=args.bridge_port,
        debug=args.debug,
        timeout=args.timeout,
        max_risk_level=domain_manager.max_risk_level,
        max_connections=getattr(args, 'max_connections', 5)
    )

    server.run()


if __name__ == "__main__":
    main()