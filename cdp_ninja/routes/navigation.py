"""
Navigation Routes - Page navigation and control with input validation
Navigate to URLs with proper validation and security checks
"""

import logging
from flask import Blueprint, jsonify, request
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter
from cdp_ninja.routes.input_validation import (
    validate_url, validate_integer_param, validate_boolean_param,
    validate_timeout, ValidationError
)

logger = logging.getLogger(__name__)
navigation_routes = Blueprint('navigation', __name__)


@navigation_routes.route('/cdp/page/navigate', methods=['POST'])
def navigate():
    """
    Navigate to a URL

    @route POST /cdp/page/navigate
    @param {string} url - URL to navigate to (http, https, or about:blank)
    @param {number} [timeout] - Navigation timeout in ms (default: 30000, max: 600000)
    @param {boolean} [wait_for_load] - Wait for page load complete (default: true)
    @returns {object} Navigation result

    @example
    // Normal navigation
    {"url": "https://example.com"}

    // About:blank
    {"url": "about:blank"}

    // With custom timeout
    {"url": "https://slow-site.example.com", "timeout": 60000}

    // No wait for load
    {"url": "https://example.com", "wait_for_load": false}
    """
    try:
        data = request.get_json() or {}
        url = validate_url(data.get('url', ''))
        timeout = validate_timeout(data.get('timeout', 30000))
        wait_for_load = validate_boolean_param(data.get('wait_for_load', True))

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Navigate to validated URL
            result = cdp.send_command('Page.navigate', {
                'url': url
            })

            navigation_result = {
                "navigation_id": result.get('result', {}).get('frameId'),
                "url": url,
                "cdp_result": result
            }

            # Optionally wait for load event
            if wait_for_load and 'error' not in result:
                import time
                start_time = time.time()
                timeout_secs = timeout / 1000.0

                # Wait for page load (or timeout)
                while time.time() - start_time < timeout_secs:
                    # Check if page finished loading
                    load_result = cdp.send_command('Runtime.evaluate', {
                        'expression': 'document.readyState',
                        'returnByValue': True
                    })

                    if (load_result.get('result', {}).get('result', {}).get('value') == 'complete'):
                        navigation_result['load_state'] = 'complete'
                        break

                    time.sleep(0.1)

                if 'load_state' not in navigation_result:
                    navigation_result['load_state'] = 'timeout'

            return jsonify(navigation_result)

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="navigate",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "error_type": type(e).__name__,
            "crash_id": crash_data.get('timestamp')
        }), 500


@navigation_routes.route('/cdp/page/reload', methods=['POST'])
def reload_page():
    """
    Reload current page

    @route POST /cdp/page/reload
    @param {boolean} [ignore_cache] - Bypass cache (default: false)
    @returns {object} Reload result

    @example
    // Simple reload
    {}

    // Hard reload (bypass cache)
    {"ignore_cache": true}

    // To run scripts after reload, use /cdp/execute separately
    """
    try:
        data = request.get_json() or {}
        ignore_cache = validate_boolean_param(data.get('ignore_cache', False))

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            params = {}
            if ignore_cache:
                params['ignoreCache'] = True

            result = cdp.send_command('Page.reload', params)

            return jsonify({
                "success": 'error' not in result,
                "ignore_cache": ignore_cache,
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="reload_page",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "error_type": type(e).__name__,
            "crash_id": crash_data.get('timestamp')
        }), 500


@navigation_routes.route('/cdp/page/back', methods=['POST'])
def go_back():
    """
    Go back in browser history

    @route POST /cdp/page/back
    @returns {object} Back navigation result
    """
    try:
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Try CDP method first
            result = cdp.send_command('Page.goBackInNavigationHistory')

            # If that doesn't work, try JavaScript
            if 'error' in result:
                js_result = cdp.send_command('Runtime.evaluate', {
                    'expression': 'window.history.back(); "attempted"'
                })
                result = js_result

            return jsonify({
                "success": 'error' not in result,
                "method": "CDP" if 'Page.goBackInNavigationHistory' in str(result) else "JavaScript",
                "result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="go_back",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@navigation_routes.route('/cdp/page/forward', methods=['POST'])
def go_forward():
    """
    Go forward in browser history

    @route POST /cdp/page/forward
    @returns {object} Forward navigation result
    """
    try:
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Try CDP method first
            result = cdp.send_command('Page.goForwardInNavigationHistory')

            # If that doesn't work, try JavaScript
            if 'error' in result:
                js_result = cdp.send_command('Runtime.evaluate', {
                    'expression': 'window.history.forward(); "attempted"'
                })
                result = js_result

            return jsonify({
                "success": 'error' not in result,
                "method": "CDP" if 'Page.goForwardInNavigationHistory' in str(result) else "JavaScript",
                "result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="go_forward",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@navigation_routes.route('/cdp/page/stop', methods=['POST'])
def stop_loading():
    """
    Stop page loading

    @route POST /cdp/page/stop
    @returns {object} Stop result
    """
    try:
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            result = cdp.send_command('Page.stopLoading')

            return jsonify({
                "success": 'error' not in result,
                "stopped": True,
                "result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="stop_loading",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@navigation_routes.route('/cdp/page/info', methods=['GET'])
def get_page_info():
    """
    Get current page information

    @route GET /cdp/page/info
    @returns {object} Page information including URL, title, state
    """
    try:
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Get various page properties
            info_queries = {
                'url': 'window.location.href',
                'title': 'document.title',
                'ready_state': 'document.readyState',
                'referrer': 'document.referrer',
                'domain': 'document.domain',
                'protocol': 'window.location.protocol',
                'host': 'window.location.host',
                'pathname': 'window.location.pathname',
                'search': 'window.location.search',
                'hash': 'window.location.hash',
                'user_agent': 'navigator.userAgent',
                'cookie': 'document.cookie'
            }

            page_info = {}
            for key, query in info_queries.items():
                try:
                    result = cdp.send_command('Runtime.evaluate', {
                        'expression': query,
                        'returnByValue': True
                    })
                    page_info[key] = result.get('result', {}).get('result', {}).get('value')
                except Exception as e:
                    logger.debug(f"Failed to get page info for {key}: {e}")
                    page_info[key] = None

            return jsonify({
                "page_info": page_info,
                "timestamp": __import__('time').time()
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_page_info",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@navigation_routes.route('/cdp/page/viewport', methods=['POST'])
def set_viewport():
    """
    Set viewport/device metrics - ANY values allowed

    @route POST /cdp/page/viewport
    @param {number} [width] - Viewport width (can be 0, negative, huge)
    @param {number} [height] - Viewport height (can be 0, negative, huge)
    @param {number} [device_scale] - Device scale factor (can be 0, negative)
    @param {boolean} [mobile] - Mobile mode
    @returns {object} Viewport change result

    @example
    // Normal desktop
    {"width": 1920, "height": 1080, "device_scale": 1, "mobile": false}

    // Mobile device
    {"width": 375, "height": 667, "device_scale": 2, "mobile": true}

    // Extreme values - test limits
    {"width": 999999, "height": -100, "device_scale": 0}

    // Tiny viewport
    {"width": 1, "height": 1}
    """
    try:
        data = request.get_json() or {}
        width = data.get('width', 1024)
        height = data.get('height', 768)
        device_scale = data.get('device_scale', 1)
        mobile = data.get('mobile', False)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Send whatever values user provided - no validation
            result = cdp.send_command('Emulation.setDeviceMetricsOverride', {
                'width': width,          # Could be negative, zero, huge
                'height': height,        # Could be negative, zero, huge
                'deviceScaleFactor': device_scale,  # Could be zero, negative
                'mobile': mobile
            })

            return jsonify({
                "success": 'error' not in result,
                "applied_viewport": {
                    'width': width,
                    'height': height,
                    'device_scale': device_scale,
                    'mobile': mobile
                },
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="set_viewport",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "viewport_params": data,
            "crash_id": crash_data.get('timestamp')
        }), 500


@navigation_routes.route('/cdp/page/cookies', methods=['GET'])
def get_cookies():
    """
    Get all cookies for current page

    @route GET /cdp/page/cookies
    @returns {object} All cookies
    """
    try:
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            result = cdp.send_command('Network.getAllCookies')

            return jsonify({
                "success": 'error' not in result,
                "cookies": result.get('result', {}).get('cookies', []),
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_cookies",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@navigation_routes.route('/cdp/page/cookies', methods=['POST'])
def set_cookie():
    """
    Set a cookie - ANY values allowed

    @route POST /cdp/page/cookies
    @param {string} name - Cookie name (no validation)
    @param {string} value - Cookie value (no validation)
    @param {string} [domain] - Cookie domain
    @param {string} [path] - Cookie path
    @param {boolean} [secure] - Secure flag
    @param {boolean} [httpOnly] - HttpOnly flag
    @returns {object} Set cookie result

    @example
    // Normal cookie
    {"name": "test", "value": "hello"}

    // Malformed cookie - test parsing
    {"name": "bad=cookie", "value": "with\nnewlines\0null"}

    // Huge cookie - test limits
    {"name": "huge", "value": "x".repeat(100000)}
    """
    try:
        data = request.get_json() or {}
        name = data.get('name', '')     # Could be empty, malformed
        value = data.get('value', '')   # Could be huge, contain nulls
        domain = data.get('domain')
        path = data.get('path', '/')
        secure = data.get('secure', False)
        http_only = data.get('httpOnly', False)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            cookie_params = {
                'name': name,    # No validation
                'value': value,  # No validation
                'path': path,
                'secure': secure,
                'httpOnly': http_only
            }

            if domain:
                cookie_params['domain'] = domain

            result = cdp.send_command('Network.setCookie', cookie_params)

            return jsonify({
                "success": 'error' not in result,
                "cookie_set": cookie_params,
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="set_cookie",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "cookie_params": data,
            "crash_id": crash_data.get('timestamp')
        }), 500