"""
Debugging Routes - RAW debugging capabilities with input validation
Console, network, JavaScript execution, performance monitoring
Validates bounds and types while allowing raw JavaScript execution
"""

import logging
from flask import Blueprint, jsonify, request, current_app
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter
from cdp_ninja.routes.input_validation import (
    validate_timeout, validate_integer_param, validate_boolean_param,
    validate_array_param, ValidationError
)

logger = logging.getLogger(__name__)
debugging_routes = Blueprint('debugging', __name__)


@debugging_routes.route('/cdp/execute', methods=['POST'])
def execute_javascript():
    """
    Execute ANY JavaScript in page context with timeout validation

    @route POST /cdp/execute
    @param {string} code - ANY JavaScript, including injection attempts
    @param {boolean} [await] - Wait for promises to resolve
    @param {number} [timeout] - Execution timeout in ms (0-600000, default: 30000)
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
        # Try JSON first, fallback to raw text for easier usage
        data = None
        try:
            data = request.get_json()
            if data:
                code = data.get('code', '') or data.get('expression', '')
                await_promise = validate_boolean_param(data.get('await', False))
                timeout = validate_timeout(data.get('timeout', 30000))
                return_by_value = validate_boolean_param(data.get('return_by_value', False))
            else:
                raise ValueError("No JSON data")
        except (ValueError, TypeError):
            # Fallback: treat entire request body as raw JavaScript code
            code = request.get_data(as_text=True)
            await_promise = False
            timeout = 30000
            return_by_value = False
            logger.debug("Using raw text fallback for JavaScript code")

        # Debug: log what we actually received
        logger.debug(f"Received code: {repr(code)}")

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

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        # Handle case where data wasn't set due to JSON parsing failure
        safe_data = data if data else {}
        crash_data = crash_reporter.report_crash(
            operation="execute_javascript",
            error=e,
            request_data={
                'code_length': len(safe_data.get('code', '')),
                'code_preview': safe_data.get('code', '')[:100],
                'timeout': safe_data.get('timeout')
            }
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "error_type": type(e).__name__,
            "code_length": len(safe_data.get('code', '')),
            "code_preview": safe_data.get('code', '')[:100],
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
    Get console output from page with validated parameters

    @route GET /cdp/console/logs
    @param {number} [limit] - Max entries to return (1-10000, default: 100)
    @param {string} [level] - Filter by level (log, info, warning, error)
    @returns {array} All console messages including errors, warnings, etc.

    @example
    // Get recent logs
    GET /cdp/console/logs

    // Get more logs
    GET /cdp/console/logs?limit=500

    // Try to filter by level
    GET /cdp/console/logs?level=error
    """
    try:
        limit = validate_integer_param(request.args.get('limit', 100), "limit", default=100, min_val=1, max_val=10000)

        # Validate level filter - whitelist valid log levels
        level_filter = request.args.get('level', '').lower()
        valid_levels = {'log', 'debug', 'info', 'warning', 'error', 'all', ''}
        if level_filter and level_filter not in valid_levels:
            # If invalid level provided, return error instead of silently returning empty
            return jsonify({
                "error": f"Invalid log level: {level_filter}",
                "valid_levels": list(valid_levels - {''})
            }), 400

        # Convert 'all' to '' (empty string means no filter)
        if level_filter == 'all':
            level_filter = ''

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

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

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
            # Clear browser console display
            result = cdp.send_command('Runtime.evaluate', {
                'expression': 'console.clear()'
            })

            # Stop any running intervals/timers that might continue generating logs
            cdp.send_command('Runtime.evaluate', {
                'expression': '''
                // Clear all intervals and timeouts to stop log generation
                for (let i = 1; i < 99999; i++) {
                    window.clearInterval(i);
                    window.clearTimeout(i);
                }
                '''
            })

            # Clear CDP Ninja's internal event storage (all domains) - after stopping timers
            cdp.clear_events(None)

            # Wait briefly for any final events to settle, then clear again
            import time
            time.sleep(0.1)
            cdp.clear_events(None)

            return jsonify({
                "success": True,
                "cleared": True,
                "browser_cleared": True,
                "storage_cleared": True,
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


@debugging_routes.route('/cdp/debug/events', methods=['GET'])
def debug_events():
    """DEBUG: Show all recent events to debug console log issue"""
    try:
        domain_filter = request.args.get('domain')

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # If domain filter specified, return actual events
            if domain_filter:
                events = cdp.get_recent_events(domain_filter, 100)
                event_data = []
                for event in events:
                    event_data.append({
                        "method": event.method,
                        "domain": event.domain,
                        "timestamp": event.timestamp,
                        "params": event.params
                    })
                return jsonify({"events": event_data})

            # Otherwise return debug analysis
            all_events = cdp.get_recent_events(None, 200)  # Get from general queue
            console_events = cdp.get_recent_events('Console', 50)
            runtime_events = cdp.get_recent_events('Runtime', 50)

            debug_info = {
                "total_events": len(all_events),
                "console_events_count": len(console_events),
                "runtime_events_count": len(runtime_events),
                "domains_with_events": {},
                "recent_methods": [],
                "sample_events": []
            }

            # Analyze all events
            domain_counts = {}
            for event in all_events[-50:]:  # Last 50 events
                domain = event.domain
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
                debug_info["recent_methods"].append(event.method)

                # Add sample events
                if len(debug_info["sample_events"]) < 10:
                    debug_info["sample_events"].append({
                        "method": event.method,
                        "domain": event.domain,
                        "timestamp": event.timestamp,
                        "params_keys": list(event.params.keys()) if event.params else []
                    })

            debug_info["domains_with_events"] = domain_counts

            return jsonify(debug_info)

        finally:
            pool.release(cdp)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@debugging_routes.route('/cdp/network/requests', methods=['GET'])
def get_network_requests():
    """
    Get recent network requests with validated parameters

    @route GET /cdp/network/requests
    @param {number} [limit] - Max requests to return (1-10000, default: 200)
    @param {string} [url_filter] - Filter URLs
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
        limit = validate_integer_param(request.args.get('limit', 200), "limit", default=200, min_val=1, max_val=10000)
        url_filter = request.args.get('url_filter')  # String filter, no injection risk

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

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

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
    Simulate network conditions with validated parameters

    @route POST /cdp/network/throttle
    @param {boolean} [offline] - Completely offline
    @param {number} [download] - Download speed in bytes/sec (-1 to 1000000000, -1 = no limit)
    @param {number} [upload] - Upload speed in bytes/sec (-1 to 1000000000, -1 = no limit)
    @param {number} [latency] - Network latency in ms (0 to 600000)
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
        offline = validate_boolean_param(data.get('offline', False))

        # Download/upload throughput: -1 (no limit) or 0+ (bytes/sec)
        download = data.get('download', -1)
        upload = data.get('upload', -1)
        latency = data.get('latency', 0)

        # Validate throughput values
        try:
            download = int(download)
            if download < -1:
                raise ValidationError("download must be -1 (no limit) or >= 0")
            if download > 1000000000:
                raise ValidationError("download too large (max 1000000000 bytes/sec)")
        except (ValueError, TypeError):
            raise ValidationError(f"download must be an integer, got {download}")

        try:
            upload = int(upload)
            if upload < -1:
                raise ValidationError("upload must be -1 (no limit) or >= 0")
            if upload > 1000000000:
                raise ValidationError("upload too large (max 1000000000 bytes/sec)")
        except (ValueError, TypeError):
            raise ValidationError(f"upload must be an integer, got {upload}")

        # Validate latency (0-600000ms = 0-10 minutes max)
        try:
            latency = int(latency)
            if latency < 0:
                raise ValidationError("latency cannot be negative")
            if latency > 600000:
                raise ValidationError("latency too large (max 600000ms)")
        except (ValueError, TypeError):
            raise ValidationError(f"latency must be an integer, got {latency}")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Send validated network conditions
            result = cdp.send_command('Network.emulateNetworkConditions', {
                'offline': offline,
                'downloadThroughput': download,  # -1 means no throttle
                'uploadThroughput': upload,
                'latency': latency
            })

            return jsonify({
                "success": 'error' not in result,
                "applied_conditions": {
                    'offline': offline,
                    'download': download,
                    'upload': upload,
                    'latency': latency
                },
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

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
            # Get performance timing (using modern Navigation Timing Level 2 API)
            timing_result = cdp.send_command('Runtime.evaluate', {
                'expression': 'window.performance.timing || performance.getEntriesByType("navigation")[0]',
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
                "timing": timing_result.get('result', {}).get('result', {}).get('value', {}),
                "memory": memory_result.get('result', {}).get('result', {}).get('value', {}),
                "navigation": navigation_result.get('result', {}).get('result', {}).get('value', []),
                "resources": resource_result.get('result', {}).get('result', {}).get('value', [])
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


@debugging_routes.route('/cdp/domains/status', methods=['GET'])
def get_domain_status():
    """
    Get CDP domain status

    @route GET /cdp/domains/status
    @returns {object} Domain status and configuration
    """
    try:
        from cdp_ninja.core.domain_manager import get_domain_manager

        domain_manager = get_domain_manager()
        status = domain_manager.get_domain_status()

        return jsonify(status)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "domains_available": False
        }), 500


@debugging_routes.route('/cdp/domains/<domain>/enable', methods=['POST'])
def enable_domain(domain):
    """
    Enable specific CDP domain

    @route POST /cdp/domains/<domain>/enable
    @returns {object} Enable result
    """
    try:
        from cdp_ninja.core.domain_manager import get_domain_manager, CDPDomain

        # Convert string to CDPDomain enum
        try:
            domain_enum = CDPDomain(domain)
        except ValueError:
            return jsonify({
                "error": f"Unknown domain: {domain}",
                "available_domains": [d.value for d in CDPDomain]
            }), 400

        domain_manager = get_domain_manager()
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Set CDP client for domain operations
            domain_manager.set_cdp_client(cdp)

            # Enable domain
            success = domain_manager.ensure_domain(domain_enum, "api_enable")

            return jsonify({
                "success": success,
                "domain": domain,
                "enabled": success,
                "status": domain_manager.get_domain_status()["domain_details"].get(domain, {})
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "domain": domain,
            "enabled": False
        }), 500


@debugging_routes.route('/cdp/domains/<domain>/disable', methods=['POST'])
def disable_domain_endpoint(domain):
    """
    Disable specific CDP domain

    @route POST /cdp/domains/<domain>/disable
    @returns {object} Disable result
    """
    try:
        from cdp_ninja.core.domain_manager import get_domain_manager, CDPDomain

        # Convert string to CDPDomain enum
        try:
            domain_enum = CDPDomain(domain)
        except ValueError:
            return jsonify({
                "error": f"Unknown domain: {domain}",
                "available_domains": [d.value for d in CDPDomain]
            }), 400

        data = request.get_json() or {}
        force = data.get('force', False)

        domain_manager = get_domain_manager()
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Set CDP client for domain operations
            domain_manager.set_cdp_client(cdp)

            # Disable domain
            success = domain_manager.disable_domain(domain_enum, force=force)

            return jsonify({
                "success": success,
                "domain": domain,
                "disabled": success,
                "status": domain_manager.get_domain_status()["domain_details"].get(domain, {})
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "domain": domain,
            "disabled": False
        }), 500