"""
Debugging Routes - RAW debugging capabilities
Console, network, JavaScript execution, performance monitoring
No limits, no validation - everything goes through raw
"""

import logging
from flask import Blueprint, jsonify, request, current_app
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter

logger = logging.getLogger(__name__)
debugging_routes = Blueprint('debugging', __name__)


@debugging_routes.route('/cdp/execute', methods=['POST'])
def execute_javascript():
    """
    Execute ANY JavaScript in page context - COMPLETELY RAW

    @route POST /cdp/execute
    @param {string} code - ANY JavaScript, including injection attempts
    @param {boolean} [await] - Wait for promises to resolve
    @param {number} [timeout] - Execution timeout in ms (user controlled)
    @param {boolean} [return_by_value] - Return value instead of object reference
    @returns {object} Whatever Chrome returns (or crashes)

    @example
    // Normal JavaScript
    {"code": "document.title"}

    // XSS injection test
    {"code": "</script><script>alert('xss')</script>"}

    // Infinite loop test
    {"code": "while(true){}"}

    // Memory bomb test
    {"code": "let x = []; while(true) x.push(new Array(1000000))"}

    // Async operation
    {"code": "fetch('/api/data')", "await": true, "timeout": 5000}
    """
    try:
        data = request.get_json() or {}
        code = data.get('code', '')  # Could be empty, huge, malicious - we don't care
        await_promise = data.get('await', False)
        timeout = data.get('timeout', 30000)  # User-controlled timeout
        return_by_value = data.get('return_by_value', True)

        pool = get_global_pool()
        cdp = pool.acquire(timeout=timeout/1000)

        try:
            # Send EXACTLY what user provided - no sanitization
            result = cdp.send_command('Runtime.evaluate', {
                'expression': code,  # RAW, unescaped, unvalidated
                'returnByValue': return_by_value,
                'awaitPromise': await_promise,
                'timeout': timeout
            })

            # Add metadata about the execution
            if 'result' in result:
                result['debug_info'] = {
                    'code_length': len(code),
                    'code_preview': code[:200] if len(code) > 200 else code,
                    'execution_timeout': timeout,
                    'awaited_promise': await_promise
                }

            return jsonify(result)

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="execute_javascript",
            error=e,
            request_data={
                'code_length': len(data.get('code', '')),
                'code_preview': data.get('code', '')[:100],
                'timeout': data.get('timeout')
            }
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "error_type": type(e).__name__,
            "code_length": len(data.get('code', '')),
            "code_preview": data.get('code', '')[:100],
            "crash_id": crash_data.get('timestamp'),
            "possible_causes": [
                "Infinite loop",
                "Memory exhaustion",
                "Chrome security violation",
                "Syntax error",
                "Chrome process crashed"
            ]
        }), 500


@debugging_routes.route('/cdp/console/logs', methods=['GET'])
def get_console_logs():
    """
    Get console output from page - ALL messages, no filtering

    @route GET /cdp/console/logs
    @param {number} [limit] - Max entries to return (default: 100)
    @param {string} [level] - Filter by level (but we don't validate it)
    @returns {array} All console messages including errors, warnings, etc.

    @example
    // Get recent logs
    GET /cdp/console/logs

    // Get more logs
    GET /cdp/console/logs?limit=500

    // Try to filter (might not work if invalid level)
    GET /cdp/console/logs?level=invalid_level
    """
    try:
        limit = request.args.get('limit', 100)
        level_filter = request.args.get('level')  # No validation

        # Convert limit to int if possible
        try:
            limit = int(limit)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid limit parameter '{limit}': {e}")
            limit = 100  # Fallback

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Get console events from CDP client
            console_events = cdp.get_recent_events('Console', limit)
            runtime_events = cdp.get_recent_events('Runtime', limit)

            logs = []

            # Process console events
            for event in console_events:
                if event.method in ['Console.messageAdded']:
                    log_entry = event.params.copy()
                    log_entry['source'] = 'Console'
                    log_entry['timestamp'] = event.timestamp
                    logs.append(log_entry)

            # Process runtime console events
            for event in runtime_events:
                if event.method in ['Runtime.consoleAPICalled']:
                    log_entry = event.params.copy()
                    log_entry['source'] = 'Runtime'
                    log_entry['timestamp'] = event.timestamp
                    logs.append(log_entry)

            # Sort by timestamp
            logs.sort(key=lambda x: x.get('timestamp', 0))

            # Apply level filter if provided (no validation - just string match)
            if level_filter:
                logs = [log for log in logs if log.get('level') == level_filter]

            # Return raw log data
            return jsonify({
                "logs": logs[-limit:],  # Most recent entries
                "total_found": len(logs),
                "limit_applied": limit,
                "level_filter": level_filter
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_console_logs",
            error=e,
            request_data={'limit': request.args.get('limit'), 'level': request.args.get('level')}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@debugging_routes.route('/cdp/console/clear', methods=['POST'])
def clear_console():
    """
    Clear console output

    @route POST /cdp/console/clear
    @returns {object} Clear result
    """
    try:
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            result = cdp.send_command('Runtime.evaluate', {
                'expression': 'console.clear()'
            })

            return jsonify({
                "success": True,
                "cleared": True,
                "command_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="clear_console",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@debugging_routes.route('/cdp/network/requests', methods=['GET'])
def get_network_requests():
    """
    Get recent network requests with ALL details

    @route GET /cdp/network/requests
    @param {number} [limit] - Max requests to return
    @param {string} [url_filter] - Filter URLs (no validation)
    @returns {array} All network requests with full details

    @example
    // Get recent requests
    GET /cdp/network/requests

    // Get many requests
    GET /cdp/network/requests?limit=1000

    // Filter by URL pattern
    GET /cdp/network/requests?url_filter=api
    """
    try:
        limit = request.args.get('limit', 200)
        url_filter = request.args.get('url_filter')

        try:
            limit = int(limit)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid limit parameter '{limit}': {e}")
            limit = 200

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Get network events
            events = cdp.get_recent_events('Network', limit * 3)  # Get more events to group properly

            # Group by request ID
            requests = {}
            for event in events:
                if 'requestId' in event.params:
                    req_id = event.params['requestId']
                    if req_id not in requests:
                        requests[req_id] = {
                            'request_id': req_id,
                            'events': []
                        }

                    event_type = event.method.replace('Network.', '')
                    requests[req_id]['events'].append({
                        'type': event_type,
                        'timestamp': event.timestamp,
                        'data': event.params
                    })

                    # Extract key data for easier access
                    if event_type == 'requestWillBeSent':
                        req_data = event.params['request']
                        requests[req_id].update({
                            'url': req_data['url'],
                            'method': req_data['method'],
                            'headers': req_data.get('headers', {}),
                            'post_data': req_data.get('postData'),
                            'timestamp': event.params['timestamp']
                        })

                    elif event_type == 'responseReceived':
                        resp_data = event.params['response']
                        requests[req_id].update({
                            'status': resp_data.get('status'),
                            'status_text': resp_data.get('statusText'),
                            'response_headers': resp_data.get('headers', {}),
                            'mime_type': resp_data.get('mimeType')
                        })

                    elif event_type == 'loadingFailed':
                        requests[req_id]['failed'] = True
                        requests[req_id]['error'] = event.params.get('errorText')

            # Convert to list and sort by timestamp
            request_list = list(requests.values())
            request_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

            # Apply URL filter if provided (no validation)
            if url_filter:
                request_list = [req for req in request_list
                              if url_filter in req.get('url', '')]

            # Limit results
            request_list = request_list[:limit]

            return jsonify({
                "requests": request_list,
                "total_found": len(request_list),
                "limit_applied": limit,
                "url_filter": url_filter
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_network_requests",
            error=e,
            request_data={'limit': request.args.get('limit'), 'url_filter': request.args.get('url_filter')}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@debugging_routes.route('/cdp/network/block', methods=['POST'])
def block_urls():
    """
    Block URLs matching patterns - ANY patterns allowed

    @route POST /cdp/network/block
    @param {array} patterns - URL patterns to block (no validation)
    @returns {object} Block result

    @example
    // Block ads
    {"patterns": ["*://*.doubleclick.net/*", "*://analytics.google.com/*"]}

    // Block everything - see what breaks
    {"patterns": ["*"]}

    // Invalid patterns - test CDP behavior
    {"patterns": [">>>invalid<<<", "malformed[regex"]}
    """
    try:
        data = request.get_json() or {}
        patterns = data.get('patterns', [])  # No validation of patterns

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            result = cdp.send_command('Network.setBlockedURLs', {
                'urls': patterns  # Send exactly what user provided
            })

            return jsonify({
                "success": 'error' not in result,
                "blocked_patterns": patterns,
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="block_urls",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "patterns": data.get('patterns', []),
            "crash_id": crash_data.get('timestamp')
        }), 500


@debugging_routes.route('/cdp/network/throttle', methods=['POST'])
def throttle_network():
    """
    Simulate network conditions - ANY values allowed

    @route POST /cdp/network/throttle
    @param {boolean} [offline] - Completely offline
    @param {number} [download] - Download speed in bytes/sec (can be 0, negative)
    @param {number} [upload] - Upload speed in bytes/sec (can be huge)
    @param {number} [latency] - Network latency in ms (can be negative)
    @returns {object} Throttle result

    @example
    // Slow connection
    {"download": 1000, "upload": 500, "latency": 1000}

    // Impossible values - test limits
    {"download": -1, "upload": 999999999999, "latency": -5000}

    // Completely offline
    {"offline": true}

    // Zero bandwidth
    {"download": 0, "upload": 0}
    """
    try:
        data = request.get_json() or {}

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Send EXACTLY what user wants - no validation
            result = cdp.send_command('Network.emulateNetworkConditions', {
                'offline': data.get('offline', False),
                'downloadThroughput': data.get('download', -1),  # -1 means no throttle
                'uploadThroughput': data.get('upload', -1),
                'latency': data.get('latency', 0)
            })

            return jsonify({
                "success": 'error' not in result,
                "applied_conditions": {
                    'offline': data.get('offline', False),
                    'download': data.get('download', -1),
                    'upload': data.get('upload', -1),
                    'latency': data.get('latency', 0)
                },
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="throttle_network",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "throttle_params": data,
            "crash_id": crash_data.get('timestamp')
        }), 500


@debugging_routes.route('/cdp/network/clear', methods=['POST'])
def clear_network_cache():
    """
    Clear browser cache and cookies

    @route POST /cdp/network/clear
    @param {boolean} [cache] - Clear cache (default: true)
    @param {boolean} [cookies] - Clear cookies (default: false)
    @param {boolean} [storage] - Clear local storage (default: false)
    @returns {object} Clear result
    """
    try:
        data = request.get_json() or {}
        clear_cache = data.get('cache', True)
        clear_cookies = data.get('cookies', False)
        clear_storage = data.get('storage', False)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            results = {}

            if clear_cache:
                results['cache'] = cdp.send_command('Network.clearBrowserCache')

            if clear_cookies:
                results['cookies'] = cdp.send_command('Network.clearBrowserCookies')

            if clear_storage:
                results['storage'] = cdp.send_command('Runtime.evaluate', {
                    'expression': 'localStorage.clear(); sessionStorage.clear(); "cleared"'
                })

            return jsonify({
                "success": True,
                "cleared": {
                    'cache': clear_cache,
                    'cookies': clear_cookies,
                    'storage': clear_storage
                },
                "results": results
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="clear_network_cache",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@debugging_routes.route('/cdp/performance', methods=['GET'])
def get_performance_metrics():
    """
    Get performance metrics and timing data

    @route GET /cdp/performance
    @returns {object} Performance data from browser
    """
    try:
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Get performance timing
            timing_result = cdp.send_command('Runtime.evaluate', {
                'expression': 'window.performance.timing',
                'returnByValue': True
            })

            # Get memory info if available
            memory_result = cdp.send_command('Runtime.evaluate', {
                'expression': 'window.performance.memory || {}',
                'returnByValue': True
            })

            # Get navigation entries
            navigation_result = cdp.send_command('Runtime.evaluate', {
                'expression': 'window.performance.getEntriesByType("navigation")',
                'returnByValue': True
            })

            # Get resource entries
            resource_result = cdp.send_command('Runtime.evaluate', {
                'expression': 'window.performance.getEntriesByType("resource")',
                'returnByValue': True
            })

            return jsonify({
                "timing": timing_result.get('result', {}).get('value', {}),
                "memory": memory_result.get('result', {}).get('value', {}),
                "navigation": navigation_result.get('result', {}).get('value', []),
                "resources": resource_result.get('result', {}).get('value', [])
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_performance_metrics",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@debugging_routes.route('/debug/crash/stats', methods=['GET'])
def get_crash_stats():
    """
    Get debugging crash statistics - valuable telemetry data

    @route GET /debug/crash/stats
    @returns {object} Crash statistics and recent crashes
    """
    try:
        stats = crash_reporter.get_crash_summary()
        return jsonify(stats)

    except Exception as e:
        # Even the crash reporter can crash!
        return jsonify({
            "meta_crash": True,
            "error": "Crash reporter crashed",
            "details": str(e)
        }), 500