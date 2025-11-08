"""
Browser Interaction Routes - Browser control with input validation
Provides click, type, scroll, hover, drag, and screenshot functionality
"""

import base64
import json
import logging
from flask import Blueprint, jsonify, request, Response, current_app
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter
from cdp_ninja.routes.input_validation import (
    validate_selector, validate_coordinate, validate_coordinates,
    validate_text_input, validate_integer_param, validate_boolean_param,
    validate_timeout, javascript_safe_value, ValidationError
)

logger = logging.getLogger(__name__)
browser_routes = Blueprint('browser', __name__)


@browser_routes.route('/cdp/click', methods=['POST'])
def click_element():
    """
    Click on element by selector or coordinates

    @route POST /cdp/click
    @param {string} [selector] - CSS selector for element to click
    @param {number} [x] - X coordinate for click
    @param {number} [y] - Y coordinate for click
    @param {string} [button] - Mouse button: left, right, middle (default: left)
    @param {number} [clickCount] - Number of clicks (default: 1)
    @returns {object} Click result

    @example
    // Click by selector
    {"selector": "#submit-button"}

    // Click by coordinates
    {"x": 100, "y": 200}

    // Right-click
    {"selector": "#menu", "button": "right"}

    // Double-click
    {"selector": "#button", "clickCount": 2}
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
                # Validate selector
                selector = validate_selector(data['selector'])
                button = data.get('button', 'left')
                click_count = validate_integer_param(data.get('clickCount', 1), 'clickCount', min_val=1, max_val=100)

                # Use JSON encoding for safe string interpolation
                code = f"""
                    (() => {{
                        const el = document.querySelector({javascript_safe_value(selector)});
                        if (el) {{
                            el.click();
                            return {{success: true, selector: {javascript_safe_value(selector)}}};
                        }}
                        return {{success: false, error: 'Element not found', selector: {javascript_safe_value(selector)}}};
                    }})()
                """

                result = cdp.send_command('Runtime.evaluate', {
                    'expression': code,
                    'returnByValue': True
                })

            elif 'x' in data and 'y' in data:
                # Validate coordinates
                x, y = validate_coordinates(data['x'], data['y'])
                button = data.get('button', 'left')
                click_count = validate_integer_param(data.get('clickCount', 1), 'clickCount', min_val=1, max_val=100)

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
                return jsonify({"error": "Must provide either selector or x,y coordinates"}), 400

            return jsonify(result)

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
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
    Type text into element or focused input

    @route POST /cdp/type
    @param {string} text - Text to type (max 100,000 characters)
    @param {string} [selector] - Element to focus first (optional)
    @param {number} [delay] - Delay between characters in ms (0-1000)
    @returns {object} Success status

    @example
    // Type into field
    {"text": "hello world", "selector": "#input"}

    // Type with delay for slow text entry
    {"text": "password123", "delay": 50}
    """
    try:
        data = request.get_json() or {}
        text = validate_text_input(data.get('text', ''), 'text')
        selector = data.get('selector')
        delay = validate_integer_param(data.get('delay', 0), 'delay', min_val=0, max_val=1000)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Focus element if selector provided
            if selector:
                validate_selector(selector)
                focus_code = f"document.querySelector({javascript_safe_value(selector)}).focus()"
                cdp.send_command('Runtime.evaluate', {'expression': focus_code})

            # Type each character with optional delay
            typed_count = 0
            for char in text:
                result = cdp.send_command('Input.dispatchKeyEvent', {
                    'type': 'char',
                    'text': char
                })

                if 'error' in result:
                    break

                typed_count += 1

                if delay > 0:
                    import time
                    time.sleep(delay / 1000.0)

            return jsonify({
                "success": True,
                "typed_length": typed_count,
                "total_length": len(text),
                "selector": selector
            })

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="type",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "error_type": type(e).__name__,
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
                        if (!el) return {{error: "element_not_found"}};

                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 && rect.height === 0) {{
                            return {{error: "element_has_no_dimensions"}};
                        }}

                        const x = rect.left + rect.width / 2;
                        const y = rect.top + rect.height / 2;

                        return {{
                            x: x,
                            y: y,
                            rect: {{
                                left: rect.left,
                                top: rect.top,
                                width: rect.width,
                                height: rect.height
                            }}
                        }};
                    }})()
                """

                coord_result = cdp.send_command('Runtime.evaluate', {
                    'expression': code,
                    'returnByValue': True
                })

                if 'result' in coord_result and 'result' in coord_result['result']:
                    coords = coord_result['result']['result']['value']
                    if coords and not coords.get('error') and 'x' in coords and 'y' in coords:
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
                            "rect": coords.get('rect', {}),
                            "method": "selector"
                        })
                    elif coords and coords.get('error'):
                        return jsonify({
                            "success": False,
                            "error": coords['error'],
                            "selector": selector
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