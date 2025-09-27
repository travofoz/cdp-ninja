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
from cdp_ninja.config import config
from cdp_ninja.routes import browser_routes, debugging_routes, navigation_routes, dom_routes, dom_advanced_routes, network_intelligence_routes, js_debugging_routes, stress_testing_routes, system_routes, error_handling_routes, performance_routes, security_routes, accessibility_routes, stress_testing_advanced_routes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global flag for shell execution
SHELL_ENABLED = False


class CDPBridgeServer:
    """Main API server for CDP Bridge"""

    def __init__(self, cdp_port: int = 9222, bridge_port: int = 8888, debug: bool = False, timeout: int = 900):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for remote access

        self.cdp = CDPClient(port=cdp_port, timeout=timeout)
        self.bridge_port = bridge_port
        self.debug = debug
        self.timeout = timeout

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
            code = f"""
                (() => {{
                    const selector = {json.dumps(selector)};
                    const el = document.querySelector(selector);
                    if (el) {{
                        el.click();
                        return {{success: true, selector: selector}};
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
            focus_code = f"""
                (() => {{
                    const selector = {json.dumps(selector)};
                    const el = document.querySelector(selector);
                    if (el) el.focus();
                }})()
            """
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
                const selector = {json.dumps(selector)};
                const el = document.querySelector(selector);
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

    def drag_element(self):
        """Drag from start coordinates to end coordinates"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        # Support both coordinate-based and selector-based dragging
        if 'startX' in data and 'startY' in data and 'endX' in data and 'endY' in data:
            # Direct coordinate drag
            try:
                start_x, start_y = float(data['startX']), float(data['startY'])
                end_x, end_y = float(data['endX']), float(data['endY'])
                # Check for NaN or infinite values
                if not all(math.isfinite(coord) for coord in [start_x, start_y, end_x, end_y]):
                    return jsonify({"error": "Coordinates must be finite numbers"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Coordinates must be numeric"}), 400
        elif 'startSelector' in data and 'endSelector' in data:
            # Selector-based drag - get coordinates of elements
            start_code = f"""
                (() => {{
                    const selector = {json.dumps(data['startSelector'])};
                    const el = document.querySelector(selector);
                    if (el) {{
                        const rect = el.getBoundingClientRect();
                        return {{x: rect.x + rect.width/2, y: rect.y + rect.height/2}};
                    }}
                    return null;
                }})()
            """
            start_result = self.cdp.send_command('Runtime.evaluate', {
                'expression': start_code,
                'returnByValue': True
            })

            end_code = f"""
                (() => {{
                    const selector = {json.dumps(data['endSelector'])};
                    const el = document.querySelector(selector);
                    if (el) {{
                        const rect = el.getBoundingClientRect();
                        return {{x: rect.x + rect.width/2, y: rect.y + rect.height/2}};
                    }}
                    return null;
                }})()
            """
            end_result = self.cdp.send_command('Runtime.evaluate', {
                'expression': end_code,
                'returnByValue': True
            })

            # Extract coordinates safely
            try:
                if 'result' not in start_result or 'result' not in start_result['result']:
                    return jsonify({"error": "Failed to evaluate start selector"}), 500
                if 'result' not in end_result or 'result' not in end_result['result']:
                    return jsonify({"error": "Failed to evaluate end selector"}), 500

                start_coords = start_result['result']['result']
                end_coords = end_result['result']['result']
                if not start_coords or not end_coords:
                    return jsonify({"error": "One or both elements not found"}), 404
                start_x, start_y = start_coords['x'], start_coords['y']
                end_x, end_y = end_coords['x'], end_coords['y']
            except (KeyError, TypeError):
                return jsonify({"error": "Failed to get element coordinates"}), 500
        else:
            return jsonify({"error": "Either startX/startY/endX/endY or startSelector/endSelector required"}), 400

        # Perform drag operation
        # 1. Mouse down at start position
        mouse_down = self.cdp.send_command('Input.dispatchMouseEvent', {
            'type': 'mousePressed',
            'x': start_x,
            'y': start_y,
            'button': 'left',
            'clickCount': 1
        })

        if 'error' in mouse_down:
            return jsonify(mouse_down), 500

        # 2. Mouse move to end position (dragging)
        mouse_move = self.cdp.send_command('Input.dispatchMouseEvent', {
            'type': 'mouseMoved',
            'x': end_x,
            'y': end_y
        })

        if 'error' in mouse_move:
            return jsonify(mouse_move), 500

        # 3. Mouse up at end position
        mouse_up = self.cdp.send_command('Input.dispatchMouseEvent', {
            'type': 'mouseReleased',
            'x': end_x,
            'y': end_y,
            'button': 'left'
        })

        if 'error' in mouse_up:
            return jsonify(mouse_up), 500

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
                const selector = {json.dumps(selector)};
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

        code = f"""
            (() => {{
                const selector = {json.dumps(selector)};
                const attrName = {json.dumps(attr_name)};
                const attrValue = {json.dumps(attr_value)};
                const el = document.querySelector(selector);
                if (el) {{
                    el.setAttribute(attrName, attrValue);
                    return {{success: true, selector: selector, attribute: attrName, value: attrValue}};
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

        return jsonify({"error": "Failed to set attribute"}), 500

    def set_element_html(self):
        """Set innerHTML of DOM element"""
        data = request.get_json()
        if not data or 'selector' not in data or 'html' not in data:
            return jsonify({"error": "Selector and html required"}), 400

        selector = data['selector']
        html_content = data['html']

        # Use JSON encoding to safely pass HTML content
        code = f"""
            (() => {{
                const selector = {json.dumps(selector)};
                const htmlContent = {json.dumps(html_content)};
                const el = document.querySelector(selector);
                if (el) {{
                    el.innerHTML = htmlContent;
                    return {{success: true, selector: selector, html_length: el.innerHTML.length}};
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

        return jsonify({"error": "Failed to set HTML"}), 500

    def get_form_values(self):
        """Get all form field values"""
        selector = request.args.get('selector', 'form')

        code = f"""
            (() => {{
                const selector = {json.dumps(selector)};
                const form = document.querySelector(selector);
                if (!form) return {{error: 'Form not found'}};

                const values = {{}};
                const inputs = form.querySelectorAll('input, textarea, select');

                inputs.forEach(input => {{
                    const name = input.name || input.id;
                    if (name) {{
                        if (input.type === 'checkbox' || input.type === 'radio') {{
                            values[name] = input.checked;
                        }} else if (input.type === 'file') {{
                            values[name] = input.files.length > 0 ? input.files[0].name : null;
                        }} else {{
                            values[name] = input.value;
                        }}
                    }}
                }});

                return {{
                    selector: selector,
                    values: values,
                    fieldCount: inputs.length
                }};
            }})()
        """

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

        # Initialize global pool for blueprints
        initialize_global_pool(max_connections=5, port=self.cdp.connection.port)

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


# Phase 4 Deployment Action Handlers
def handle_usage():
    """Output complete API documentation from USAGE.md"""
    try:
        usage_path = Path(__file__).parent.parent / "USAGE.md"
        if not usage_path.exists():
            print("❌ USAGE.md not found at expected location")
            return

        print("🥷 CDP Ninja API Documentation")
        print("=" * 50)
        print()

        with open(usage_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse and format the markdown content for CLI display
        lines = content.split('\n')
        in_code_block = False

        for line in lines:
            # Handle code blocks
            if line.startswith('```'):
                in_code_block = not in_code_block
                print("─" * 40)
                continue

            # Format headers
            if line.startswith('# '):
                print(f"\n🔥 {line[2:]}")
                print("=" * len(line))
            elif line.startswith('## '):
                print(f"\n💠 {line[3:]}")
                print("─" * len(line))
            elif line.startswith('### '):
                print(f"\n⚡ {line[4:]}")
            # Format code blocks with indentation
            elif in_code_block:
                print(f"   {line}")
            # Format list items
            elif line.startswith('- '):
                print(f"  • {line[2:]}")
            # Regular lines
            elif line.strip():
                print(line)
            else:
                print()

    except Exception as e:
        print(f"❌ Error reading API documentation: {e}")
        return 1

    return 0


def handle_install_agents(target_path):
    """Install agents locally or remotely with conflict resolution"""
    print(f"🥷 Installing CDP Ninja agents to: {target_path}")

    try:
        agents_dir = Path(__file__).parent.parent / "agents"
        if not agents_dir.exists():
            print(f"❌ Agents directory not found: {agents_dir}")
            print("💡 Expected location: /agents (relative to cdp_ninja package)")
            return False

        agent_files = list(agents_dir.glob("*.md"))
        if not agent_files:
            print(f"❌ No agent files found in: {agents_dir}")
            return False

        print(f"📁 Found {len(agent_files)} agent files")

        # Parse target (local vs remote)
        if ':' in target_path:
            # Remote installation via SCP
            print("🌐 Remote installation detected")
            host, remote_path = target_path.split(':', 1)
            success = install_agents_remote(host, remote_path, agents_dir)
        else:
            # Local installation
            print("💻 Local installation detected")
            success = install_agents_local(target_path, agents_dir)

        if success:
            print("\n🎉 Agent installation completed successfully!")
            print("💡 Next steps:")
            print("   1. Verify agents are accessible in your Claude Code environment")
            print("   2. Test with: Task(subagent_type='cdp-ninja-hidden-door', ...)")
        else:
            print("\n❌ Agent installation failed or no files were installed")

        return success

    except Exception as e:
        print(f"❌ Agent installation failed: {e}")
        return False


def handle_install_deps(target_host, web_backend):
    """Install dependencies (Claude CLI, tmux, gotty/ttyd) on target system"""
    print(f"🛠️  Installing dependencies on: {target_host}")
    print(f"📺 Web backend: {web_backend}")

    if target_host == 'localhost':
        print("💻 Installing locally...")
        install_deps_local(web_backend)
    else:
        print(f"🌐 Installing remotely on {target_host}...")
        install_deps_remote(target_host, web_backend)


def handle_tunnel(target_host):
    """Setup SSH tunnels for remote access"""
    print(f"🚇 Setting up SSH tunnel to: {target_host}")

    # Auto-detect required ports from bridge configuration
    cdp_port = 9222
    bridge_port = 8888
    web_port = 8080

    setup_ssh_tunnel(target_host, cdp_port, bridge_port, web_port)


def handle_invoke_claude(target_host, web_backend):
    """Start Claude interface in tmux with web terminal"""
    print(f"🤖 Starting Claude interface on: {target_host}")
    print(f"📺 Web backend: {web_backend}")

    start_remote_claude(target_host, web_backend)


def handle_shell():
    """Enable shell execution capabilities on the bridge"""
    print("🐚 Enabling shell execution endpoint...")
    print("⚠️  Warning: Remote shell execution will be enabled")
    print("📡 Shell endpoint: POST /system/execute")

    # Set global flag to enable shell routes
    global SHELL_ENABLED
    SHELL_ENABLED = True

    print("✅ Shell execution enabled - starting server")
    return 'start_server_with_shell'  # Signal to start server with shell enabled


# Helper functions for agent installation
def install_agents_local(target_path, agents_dir):
    """Install agents to local path with conflict resolution"""
    import shutil

    target = Path(target_path).expanduser().resolve()

    try:
        target.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"❌ Permission denied creating directory: {target}")
        return False

    installed_count = 0
    skipped_count = 0

    for agent_file in agents_dir.glob("*.md"):
        target_file = target / agent_file.name

        if target_file.exists() and not getattr(install_agents_local, 'overwrite_all', False):
            choice = prompt_file_conflict(agent_file, target_file)
            if choice == 'skip':
                print(f"⏭️  Skipped: {agent_file.name}")
                skipped_count += 1
                continue
            elif choice == 'all':
                # Set flag to overwrite all remaining files
                install_agents_local.overwrite_all = True

        try:
            shutil.copy2(agent_file, target_file)
            print(f"✅ Installed: {agent_file.name}")
            installed_count += 1
        except Exception as e:
            print(f"❌ Failed to install {agent_file.name}: {e}")

    print(f"\n📊 Installation complete: {installed_count} installed, {skipped_count} skipped")
    return installed_count > 0


def install_agents_remote(host, remote_path, agents_dir):
    """Install agents to remote path via SCP (SSH key authentication required)"""
    import subprocess

    print(f"🔑 Using SSH key authentication (passwords not supported)")
    print(f"📁 Target directory: {host}:{remote_path}")

    # Test SSH connection first
    try:
        result = subprocess.run(
            ['ssh', '-o', 'PasswordAuthentication=no', '-o', 'ConnectTimeout=10',
             host, 'echo "SSH connection test"'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print("❌ SSH key authentication failed")
            print("🔧 Setup required:")
            print(f"   1. Generate SSH key: ssh-keygen -t ed25519")
            print(f"   2. Copy to remote: ssh-copy-id {host}")
            print(f"   3. Test connection: ssh {host}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ SSH connection timeout to {host}")
        return False
    except FileNotFoundError:
        print("❌ SSH client not found")
        return False

    print("✅ SSH connection verified")

    # Create remote directory
    try:
        result = subprocess.run(
            ['ssh', host, f'mkdir -p {remote_path}'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print(f"❌ Failed to create remote directory: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Timeout creating remote directory")
        return False

    # Copy agents with SCP
    installed_count = 0
    failed_count = 0

    for agent_file in agents_dir.glob("*.md"):
        remote_file = f"{host}:{remote_path}/{agent_file.name}"
        try:
            result = subprocess.run(
                ['scp', '-o', 'PasswordAuthentication=no',
                 str(agent_file), remote_file],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print(f"✅ Installed: {agent_file.name}")
                installed_count += 1
            else:
                print(f"❌ Failed to copy {agent_file.name}: {result.stderr}")
                failed_count += 1
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout copying {agent_file.name}")
            failed_count += 1

    print(f"\n📊 Remote installation complete: {installed_count} installed, {failed_count} failed")
    return installed_count > 0


def prompt_file_conflict(source_file, target_file):
    """Prompt user for file conflict resolution"""
    from datetime import datetime

    source_time = datetime.fromtimestamp(source_file.stat().st_mtime)
    target_time = datetime.fromtimestamp(target_file.stat().st_mtime)
    source_size = source_file.stat().st_size
    target_size = target_file.stat().st_size

    print(f"\n⚠️  File conflict: {target_file.name}")
    print("─" * 50)
    print(f"📄 Source: {source_time.strftime('%Y-%m-%d %H:%M:%S')} ({source_size:,} bytes)")
    print(f"📄 Target: {target_time.strftime('%Y-%m-%d %H:%M:%S')} ({target_size:,} bytes)")

    if source_time > target_time:
        print("📅 Source is newer")
    elif target_time > source_time:
        print("📅 Target is newer")
    else:
        print("📅 Same modification time")

    if source_size != target_size:
        print(f"📏 Size difference: {source_size - target_size:+,} bytes")

    while True:
        choice = input("\n[O]verwrite, [S]kip, [D]iff, [A]ll overwrite? ").lower().strip()

        if choice in ['o', 'overwrite']:
            return 'overwrite'
        elif choice in ['s', 'skip']:
            return 'skip'
        elif choice in ['a', 'all']:
            return 'all'
        elif choice in ['d', 'diff']:
            show_file_diff(source_file, target_file)
            continue
        else:
            print("❌ Invalid choice. Use O/S/D/A")


def show_file_diff(source_file, target_file):
    """Show basic diff between files"""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_lines = f.readlines()
        with open(target_file, 'r', encoding='utf-8') as f:
            target_lines = f.readlines()

        print("\n📊 Quick diff (first 10 differences):")
        print("─" * 30)

        diff_count = 0
        max_lines = min(len(source_lines), len(target_lines), 50)

        for i in range(max_lines):
            if i < len(source_lines) and i < len(target_lines):
                if source_lines[i] != target_lines[i]:
                    print(f"Line {i+1}:")
                    print(f"- {target_lines[i].rstrip()}")
                    print(f"+ {source_lines[i].rstrip()}")
                    diff_count += 1
                    if diff_count >= 5:
                        print("... (showing first 5 differences)")
                        break

        if len(source_lines) != len(target_lines):
            print(f"📏 Line count: source={len(source_lines)}, target={len(target_lines)}")

    except Exception as e:
        print(f"❌ Could not show diff: {e}")


def install_deps_local(web_backend):
    """Install dependencies locally"""
    import subprocess

    try:
        # Install Claude CLI
        print("📦 Installing Claude CLI...")
        subprocess.run(['pip', 'install', 'claude-cli'], check=True)

        # Install tmux (platform-specific)
        if platform.system() == 'Darwin':
            subprocess.run(['brew', 'install', 'tmux'], check=True)
        elif platform.system() == 'Linux':
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tmux'], check=True)

        # Install web backend
        install_web_backend_local(web_backend)

        print("✅ Local dependencies installed successfully")

    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")


def install_deps_remote(target_host, web_backend):
    """Install dependencies on remote host"""
    import subprocess

    commands = [
        'pip install claude-cli',
        'sudo apt-get update && sudo apt-get install -y tmux',
    ]

    if web_backend == 'gotty':
        commands.append('wget -O /tmp/gotty.tar.gz https://github.com/yudai/gotty/releases/latest/download/gotty_linux_amd64.tar.gz && tar -xzf /tmp/gotty.tar.gz -C /usr/local/bin/')
    else:  # ttyd
        commands.append('sudo apt-get install -y ttyd')

    for cmd in commands:
        try:
            subprocess.run(['ssh', target_host, cmd], check=True)
            print(f"✅ Executed: {cmd}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed: {cmd} - {e}")


def install_web_backend_local(web_backend):
    """Install web backend locally"""
    import subprocess

    if web_backend == 'gotty':
        print("📺 Installing gotty...")
        # Platform-specific gotty installation
        if platform.system() == 'Darwin':
            subprocess.run(['brew', 'install', 'gotty'], check=True)
        else:
            print("⚠️  Manual gotty installation required on this platform")
    else:  # ttyd
        print("📺 Installing ttyd...")
        if platform.system() == 'Darwin':
            subprocess.run(['brew', 'install', 'ttyd'], check=True)
        elif platform.system() == 'Linux':
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ttyd'], check=True)


def setup_ssh_tunnel(target_host, cdp_port, bridge_port, web_port):
    """Setup SSH tunnels for remote access"""
    import subprocess

    tunnels = [
        f'{cdp_port}:localhost:{cdp_port}',
        f'{bridge_port}:localhost:{bridge_port}',
        f'{web_port}:localhost:{web_port}'
    ]

    cmd = ['ssh', '-L'] + ['-L'.join(tunnels)] + [target_host, '-N']

    print(f"🚇 Tunnel command: {' '.join(cmd)}")
    print("⚠️  Run this command in a separate terminal:")
    print(f"ssh -L {':'.join(tunnels)} {target_host} -N")


def start_remote_claude(target_host, web_backend):
    """Start Claude interface on remote host with web terminal"""
    import subprocess

    if web_backend == 'ttyd':
        remote_cmd = '''
        tmux new-session -d -s claude 'claude' 2>/dev/null || true;
        ttyd -p 8080 -t titleFixed='Claude CLI' -t disableLeaveAlert=true -W tmux attach -t claude
        '''
    else:  # gotty
        remote_cmd = '''
        tmux new-session -d -s claude 'claude' 2>/dev/null || true;
        gotty -p 8080 --permit-write --reconnect --reconnect-time 10 --max-connection 5 --title-format 'Claude CLI - {{.hostname}}' tmux attach -t claude
        '''

    try:
        subprocess.run(['ssh', target_host, remote_cmd], check=True)
        print(f"✅ Claude interface started on {target_host}:8080")
        print(f"🌐 Access via: http://{target_host}:8080")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Claude interface: {e}")


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
    parser.add_argument('--invoke-claude', type=str, metavar='user@host',
                       help='Start Claude interface in tmux with web terminal')
    parser.add_argument('--shell', action='store_true',
                       help='Enable shell execution capabilities')

    args = parser.parse_args()

    # Handle action flags first - execute action and exit
    if args.usage:
        handle_usage()
        sys.exit(0)

    if args.install_agents:
        handle_install_agents(args.install_agents)
        sys.exit(0)

    if args.install_deps:
        handle_install_deps(args.install_deps, args.web_backend)
        sys.exit(0)

    if args.tunnel:
        handle_tunnel(args.tunnel)
        sys.exit(0)

    if args.invoke_claude:
        handle_invoke_claude(args.invoke_claude, args.web_backend)
        sys.exit(0)

    if args.shell:
        result = handle_shell()
        if result == 'start_server_with_shell':
            # Continue to start server with shell enabled
            pass
        else:
            sys.exit(0)

    # No action flags provided - start server (backward compatible)
    print("🥷 CDP Ninja Server")
    print("=" * 40)
    print(f"Chrome DevTools Port: {args.cdp_port}")
    print(f"Bridge API Port: {args.bridge_port}")
    print(f"Debug Mode: {args.debug}")

    # Enable shell execution if --shell flag was used
    if SHELL_ENABLED:
        config.enable_shell_execution = True
        print(f"Shell Execution: ENABLED (POST /system/execute)")
    else:
        print(f"Shell Execution: DISABLED")

    print("⚠️  DANGEROUS: No input validation")
    print("=" * 40)

    server = CDPBridgeServer(
        cdp_port=args.cdp_port,
        bridge_port=args.bridge_port,
        debug=args.debug,
        timeout=args.timeout
    )

    server.run()


if __name__ == "__main__":
    main()