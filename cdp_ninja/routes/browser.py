"""
Browser Interaction Routes - RAW pass-through to CDP
No validation, no sanitization, no limits
If it crashes Chrome, that's debugging data!
"""

import base64
import logging
from flask import Blueprint, jsonify, request, Response, current_app
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter

logger = logging.getLogger(__name__)
browser_routes = Blueprint('browser', __name__)


@browser_routes.route('/cdp/click', methods=['POST'])
def click_element():
    """
    Click on element by selector or coordinates - RAW mode

    @route POST /cdp/click
    @param {string} [selector] - ANY selector, malformed or not
    @param {number} [x] - ANY x coordinate, can be negative/huge
    @param {number} [y] - ANY y coordinate, can be negative/huge
    @param {string} [button] - Mouse button (left/right/middle)
    @param {number} [clickCount] - Number of clicks
    @returns {object} Whatever Chrome returns (or crashes)

    @example
    // Normal click
    {"selector": "#submit-button"}

    // Injection attempt - we WANT to test this
    {"selector": "';alert('xss')//"}

    // Malformed selector - see if Chrome handles it
    {"selector": ">>>>invalid>>>>"}

    // Extreme coordinates - test bounds
    {"x": 999999999, "y": -999999999}

    // Rapid multi-click
    {"selector": "#button", "clickCount": 10}
    """
    try:
        data = request.get_json() or {}
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not initialized"}), 500

        cdp = pool.acquire(timeout=30)
        if not cdp:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            if 'selector' in data:
                # RAW selector, no escaping, no validation
                selector = data['selector']  # Could be anything!
                button = data.get('button', 'left')
                click_count = data.get('clickCount', 1)

                # Send EXACTLY what user provided - no safety checks
                code = f"""
                    (() => {{
                        const el = document.querySelector('{selector}');
                        if (el) {{
                            el.click();
                            return {{success: true, selector: '{selector}'}};
                        }}
                        return {{success: false, error: 'Element not found', selector: '{selector}'}};
                    }})()
                """

                result = cdp.send_command('Runtime.evaluate', {
                    'expression': code,
                    'returnByValue': True
                })

            elif 'x' in data and 'y' in data:
                # RAW coordinates, could be negative, huge, non-numeric
                x = data['x']  # Whatever they sent, no validation
                y = data['y']  # Could be string, negative, huge
                button = data.get('button', 'left')
                click_count = data.get('clickCount', 1)

                # Mouse press
                result = cdp.send_command('Input.dispatchMouseEvent', {
                    'type': 'mousePressed',
                    'x': x,
                    'y': y,
                    'button': button,
                    'clickCount': click_count
                })

                if 'error' not in result:
                    # Mouse release
                    release_result = cdp.send_command('Input.dispatchMouseEvent', {
                        'type': 'mouseReleased',
                        'x': x,
                        'y': y,
                        'button': button
                    })

                    if 'error' not in release_result:
                        result = {"success": True, "clicked": [x, y], "button": button}

            else:
                result = {"error": "Need selector or x,y coordinates"}

            return jsonify(result)

        finally:
            pool.release(cdp)

    except Exception as e:
        # Log the crash but return the error - this is debugging data!
        crash_data = crash_reporter.report_crash(
            operation="click",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "error_type": type(e).__name__,
            "details": "Check logs for full traceback",
            "crash_id": crash_data.get('timestamp')
        }), 500


@browser_routes.route('/cdp/type', methods=['POST'])
def type_text():
    """
    Type text into element or focused input - RAW mode

    @route POST /cdp/type
    @param {string} text - ANY text, including control characters
    @param {string} [selector] - Element to focus first (optional)
    @param {number} [delay] - Delay between characters in ms
    @returns {object} Success status or crash data

    @example
    // Normal typing
    {"text": "hello world", "selector": "#input"}

    // Special characters - test edge cases
    {"text": "\\n\\t\\r\\0"}

    // Huge text - test limits
    {"text": "A".repeat(100000)}

    // Control characters
    {"text": "\\u0000\\u0001\\u0002"}
    """
    try:
        data = request.get_json() or {}
        text = data.get('text', '')  # Could be empty, huge, contain anything
        selector = data.get('selector')
        delay = data.get('delay', 0)  # User-controlled delay

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Focus element if selector provided (no validation)
            if selector:
                focus_code = f"document.querySelector('{selector}').focus()"
                cdp.send_command('Runtime.evaluate', {'expression': focus_code})

            # Type each character with optional delay
            for char in text:
                result = cdp.send_command('Input.dispatchKeyEvent', {
                    'type': 'char',
                    'text': char  # RAW character, no filtering
                })

                if 'error' in result:
                    break

                if delay > 0:
                    import time
                    time.sleep(delay / 1000.0)

            return jsonify({
                "success": True,
                "typed": text,
                "length": len(text),
                "selector": selector
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="type",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "typed_so_far": data.get('text', '')[:100],  # First 100 chars
            "crash_id": crash_data.get('timestamp')
        }), 500


@browser_routes.route('/cdp/scroll', methods=['POST'])
def scroll_page():
    """
    Scroll the page - ANY direction, ANY amount

    @route POST /cdp/scroll
    @param {string} [direction] - Direction (up/down/left/right)
    @param {number} [amount] - Scroll amount in pixels
    @param {number} [x] - X coordinate for scroll origin
    @param {number} [y] - Y coordinate for scroll origin
    @returns {object} Scroll result or crash data

    @example
    // Normal scroll
    {"direction": "down", "amount": 100}

    // Extreme scroll - test limits
    {"direction": "down", "amount": 999999999}

    // Negative scroll
    {"direction": "up", "amount": -1000}

    // Invalid direction - see what happens
    {"direction": "diagonal", "amount": 50}
    """
    try:
        data = request.get_json() or {}
        direction = data.get('direction', 'down')  # No validation
        amount = data.get('amount', 100)  # Could be negative, huge
        x = data.get('x', 100)  # Raw coordinates
        y = data.get('y', 100)

        # Convert direction to delta (no validation of direction string)
        delta_x = 0
        delta_y = 0

        if direction == 'down':
            delta_y = amount
        elif direction == 'up':
            delta_y = -amount
        elif direction == 'left':
            delta_x = -amount
        elif direction == 'right':
            delta_x = amount
        else:
            # Invalid direction? Send it anyway and see what happens
            delta_y = amount

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            result = cdp.send_command('Input.dispatchMouseEvent', {
                'type': 'mouseWheel',
                'x': x,
                'y': y,
                'deltaX': delta_x,
                'deltaY': delta_y
            })

            if 'error' not in result:
                result = {
                    "success": True,
                    "scrolled": direction,
                    "amount": amount,
                    "delta": [delta_x, delta_y]
                }

            return jsonify(result)

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="scroll",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "scroll_params": data,
            "crash_id": crash_data.get('timestamp')
        }), 500


@browser_routes.route('/cdp/hover', methods=['POST'])
def hover_element():
    """
    Hover over element - RAW selector, no validation

    @route POST /cdp/hover
    @param {string} selector - ANY selector string
    @param {number} [x] - Override X coordinate
    @param {number} [y] - Override Y coordinate
    @returns {object} Hover result or crash data

    @example
    // Normal hover
    {"selector": "#menu-item"}

    // Malformed selector
    {"selector": ">><<invalid>><<"}

    // Direct coordinates
    {"x": 200, "y": 300}
    """
    try:
        data = request.get_json() or {}
        selector = data.get('selector')
        override_x = data.get('x')
        override_y = data.get('y')

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            if override_x is not None and override_y is not None:
                # Use provided coordinates directly
                x, y = override_x, override_y

                result = cdp.send_command('Input.dispatchMouseEvent', {
                    'type': 'mouseMoved',
                    'x': x,
                    'y': y
                })

                return jsonify({
                    "success": True,
                    "hovered_at": [x, y],
                    "method": "coordinates"
                })

            elif selector:
                # Get element coordinates using RAW selector
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

                coord_result = cdp.send_command('Runtime.evaluate', {
                    'expression': code,
                    'returnByValue': True
                })

                if 'result' in coord_result and 'result' in coord_result['result']:
                    coords = coord_result['result']['result']
                    if coords:
                        x, y = coords['x'], coords['y']

                        hover_result = cdp.send_command('Input.dispatchMouseEvent', {
                            'type': 'mouseMoved',
                            'x': x,
                            'y': y
                        })

                        return jsonify({
                            "success": True,
                            "hovered": selector,
                            "at": [x, y],
                            "method": "selector"
                        })

                return jsonify({
                    "success": False,
                    "error": "Element not found or coordinates unavailable",
                    "selector": selector
                })

            else:
                return jsonify({"error": "Need selector or x,y coordinates"})

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="hover",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "selector": data.get('selector'),
            "crash_id": crash_data.get('timestamp')
        }), 500


@browser_routes.route('/cdp/screenshot', methods=['GET'])
def capture_screenshot():
    """
    Capture screenshot of current page - ANY format, ANY quality

    @route GET /cdp/screenshot
    @param {string} [format] - Image format (png/jpeg/webp) - no validation
    @param {number} [quality] - Image quality (0-100) - no limits
    @param {boolean} [full_page] - Capture beyond viewport
    @param {number} [width] - Custom viewport width
    @param {number} [height] - Custom viewport height
    @returns {binary} Image data or error JSON

    @example
    // Normal screenshot
    GET /cdp/screenshot

    // Custom format/quality - no validation
    GET /cdp/screenshot?format=webp&quality=999

    // Extreme dimensions
    GET /cdp/screenshot?width=99999&height=99999&full_page=true
    """
    try:
        # Get parameters with NO validation
        format_type = request.args.get('format', 'png')  # Could be anything
        quality = request.args.get('quality', 80)  # Could be > 100, negative
        full_page = request.args.get('full_page', 'false').lower() == 'true'
        width = request.args.get('width')
        height = request.args.get('height')

        # Convert quality to int if possible, otherwise send as-is
        try:
            quality = int(quality)
        except (ValueError, TypeError) as e:
            logger.debug(f"Quality parameter '{quality}' not convertible to int: {e} - sending raw value")
            pass  # Send whatever they provided

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Build screenshot parameters - no validation
            params = {
                'format': format_type,  # png, jpeg, webp, or whatever
                'quality': quality      # Could be > 100, negative, string
            }

            if full_page:
                params['captureBeyondViewport'] = True

            # Custom viewport if specified
            if width or height:
                try:
                    viewport_params = {}
                    if width:
                        viewport_params['width'] = int(width)
                    if height:
                        viewport_params['height'] = int(height)

                    # Set viewport - might fail with extreme values
                    cdp.send_command('Emulation.setDeviceMetricsOverride', {
                        **viewport_params,
                        'deviceScaleFactor': 1,
                        'mobile': False
                    })
                except Exception as e:
                    logger.debug(f"Failed to set viewport for screenshot: {e} - continuing with current viewport")
                    pass  # Continue with current viewport

            result = cdp.send_command('Page.captureScreenshot', params)

            if 'result' in result and 'data' in result['result']:
                img_data = base64.b64decode(result['result']['data'])

                # Try to determine MIME type, fallback to png
                mime_type = f'image/{format_type}'
                if format_type not in ['png', 'jpeg', 'webp']:
                    mime_type = 'image/png'  # Chrome probably converted it

                return Response(img_data, mimetype=mime_type)
            else:
                return jsonify(result), 500

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="screenshot",
            error=e,
            request_data={
                'format': request.args.get('format'),
                'quality': request.args.get('quality'),
                'full_page': request.args.get('full_page'),
                'width': request.args.get('width'),
                'height': request.args.get('height')
            }
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "parameters": dict(request.args),
            "crash_id": crash_data.get('timestamp')
        }), 500


@browser_routes.route('/cdp/drag', methods=['POST'])
def drag_element():
    """
    Drag and drop operation - RAW coordinates

    @route POST /cdp/drag
    @param {number} from_x - Start X coordinate
    @param {number} from_y - Start Y coordinate
    @param {number} to_x - End X coordinate
    @param {number} to_y - End Y coordinate
    @param {number} [duration] - Drag duration in ms
    @returns {object} Drag result or crash data

    @example
    // Normal drag
    {"from_x": 100, "from_y": 200, "to_x": 300, "to_y": 400}

    // Extreme coordinates
    {"from_x": -999999, "from_y": 999999, "to_x": 0, "to_y": 0}
    """
    try:
        data = request.get_json() or {}
        from_x = data.get('from_x', 0)
        from_y = data.get('from_y', 0)
        to_x = data.get('to_x', 100)
        to_y = data.get('to_y', 100)
        duration = data.get('duration', 500)  # Could be negative, huge

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Mouse down at start position
            cdp.send_command('Input.dispatchMouseEvent', {
                'type': 'mousePressed',
                'x': from_x,
                'y': from_y,
                'button': 'left'
            })

            # Move to end position
            cdp.send_command('Input.dispatchMouseEvent', {
                'type': 'mouseMoved',
                'x': to_x,
                'y': to_y
            })

            # Optional delay
            if duration > 0:
                import time
                time.sleep(duration / 1000.0)

            # Mouse up at end position
            result = cdp.send_command('Input.dispatchMouseEvent', {
                'type': 'mouseReleased',
                'x': to_x,
                'y': to_y,
                'button': 'left'
            })

            return jsonify({
                "success": True,
                "dragged": {
                    "from": [from_x, from_y],
                    "to": [to_x, to_y],
                    "duration": duration
                }
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="drag",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "drag_params": data,
            "crash_id": crash_data.get('timestamp')
        }), 500