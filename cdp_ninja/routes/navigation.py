"""
Navigation Routes - RAW page control
Navigate anywhere, any URL scheme, any protocol
Test edge cases and invalid URLs
"""

import logging
from flask import Blueprint, jsonify, request
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter

logger = logging.getLogger(__name__)
navigation_routes = Blueprint('navigation', __name__)


@navigation_routes.route('/cdp/page/navigate', methods=['POST'])
def navigate():
    """
    Navigate to ANY URL - no restrictions

    @route POST /cdp/page/navigate
    @param {string} url - ANY URL, valid or invalid
    @param {number} [timeout] - Navigation timeout in ms
    @param {boolean} [wait_for_load] - Wait for page load complete
    @returns {object} Navigation result

    @example
    // Normal navigation
    {"url": "https://example.com"}

    // Test edge cases
    {"url": "ftp://invalid.protocol"}
    {"url": "javascript:alert('xss')"}
    {"url": "data:text/html,<script>alert('data')</script>"}

    // Local files
    {"url": "file:///etc/passwd"}

    // Malformed URLs
    {"url": "not-a-url-at-all"}
    {"url": "http://[invalid-ipv6]/test"}
    """
    try:
        data = request.get_json() or {}
        url = data.get('url', '')  # Empty URLs are valid tests too
        timeout = data.get('timeout', 30000)  # User-controlled timeout
        wait_for_load = data.get('wait_for_load', True)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Send EXACTLY what user provided - no URL validation
            result = cdp.send_command('Page.navigate', {
                'url': url  # Could be anything!
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

                # Wait for page load (or timeout)
                while time.time() - start_time < (timeout / 1000):
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

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="navigate",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "url": data.get('url', ''),
            "crash_id": crash_data.get('timestamp'),
            "possible_causes": [
                "Invalid URL format",
                "Blocked protocol",
                "Network error",
                "Chrome security restriction",
                "Navigation timeout"
            ]
        }), 500


@navigation_routes.route('/cdp/page/reload', methods=['POST'])
def reload_page():
    """
    Reload current page with optional parameters

    @route POST /cdp/page/reload
    @param {boolean} [ignore_cache] - Bypass cache
    @param {string} [script_to_evaluate] - Script to run after reload
    @returns {object} Reload result

    @example
    // Simple reload
    {}

    // Hard reload
    {"ignore_cache": true}

    // Reload with script injection
    {"script_to_evaluate": "alert('reloaded')"}
    """
    try:
        data = request.get_json() or {}
        ignore_cache = data.get('ignore_cache', False)
        script_to_evaluate = data.get('script_to_evaluate')  # Could be malicious

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            params = {}
            if ignore_cache:
                params['ignoreCache'] = True
            if script_to_evaluate:
                params['scriptToEvaluateOnLoad'] = script_to_evaluate  # RAW script

            result = cdp.send_command('Page.reload', params)

            return jsonify({
                "success": 'error' not in result,
                "ignore_cache": ignore_cache,
                "script_injected": bool(script_to_evaluate),
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="reload_page",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
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