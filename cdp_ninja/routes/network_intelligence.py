"""
Network Intelligence Routes - Advanced network analysis and monitoring
Patient intelligence gathering via Network domain monitoring and analysis
"""

import logging
from flask import Blueprint, jsonify, request
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter

logger = logging.getLogger(__name__)
network_intelligence_routes = Blueprint('network_intelligence', __name__)


def _parse_request_params(request, param_names):
    """Utility: Parse request parameters from GET/POST"""
    if request.method == 'GET':
        return {name: request.args.get(name) for name in param_names}
    else:
        data = request.get_json() or {}
        return {name: data.get(name) for name in param_names}


@network_intelligence_routes.route('/cdp/network/timing', methods=['GET', 'POST'])
def analyze_network_timing():
    """
    Analyze network request timing and performance

    @route GET/POST /cdp/network/timing
    @param {string} [url_filter] - Filter by URL pattern
    @param {number} [limit] - Maximum requests to analyze
    @param {boolean} [detailed] - Include detailed timing breakdown
    @returns {object} Network timing analysis

    @example
    // Analyze all network timing
    GET /cdp/network/timing

    // Filter by URL pattern
    GET /cdp/network/timing?url_filter=api.example.com&limit=10

    // Detailed timing breakdown
    POST {"detailed": true, "limit": 5}
    """
    try:
        params = _parse_request_params(request, ['url_filter', 'limit', 'detailed'])
        url_filter = params['url_filter'] or ''
        limit = int(params['limit'] or 100)
        detailed = params['detailed'] in [True, 'true', '1']

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Get network events from the pool's event queue
            network_events = []

            # Use JavaScript to analyze network timing from browser perspective
            timing_code = f"""
                (() => {{
                    const performance = window.performance;
                    const entries = performance.getEntriesByType('navigation')
                        .concat(performance.getEntriesByType('resource'));

                    let filtered = entries;
                    if ('{url_filter}') {{
                        filtered = entries.filter(entry => entry.name.includes('{url_filter}'));
                    }}

                    const results = filtered.slice(0, {limit}).map(entry => {{
                        const basic = {{
                            name: entry.name,
                            type: entry.entryType,
                            duration: Math.round(entry.duration * 100) / 100,
                            size: entry.transferSize || 0,
                            start_time: Math.round(entry.startTime * 100) / 100
                        }};

                        if ({str(detailed).lower()}) {{
                            basic.timing_breakdown = {{
                                dns_lookup: Math.round((entry.domainLookupEnd - entry.domainLookupStart) * 100) / 100,
                                tcp_connect: Math.round((entry.connectEnd - entry.connectStart) * 100) / 100,
                                ssl_handshake: entry.secureConnectionStart > 0 ?
                                    Math.round((entry.connectEnd - entry.secureConnectionStart) * 100) / 100 : 0,
                                request_sent: Math.round((entry.responseStart - entry.requestStart) * 100) / 100,
                                response_download: Math.round((entry.responseEnd - entry.responseStart) * 100) / 100,
                                total_time: Math.round(entry.duration * 100) / 100
                            }};
                        }}

                        return basic;
                    }});

                    const stats = {{
                        total_requests: filtered.length,
                        avg_duration: filtered.length > 0 ?
                            Math.round((filtered.reduce((sum, e) => sum + e.duration, 0) / filtered.length) * 100) / 100 : 0,
                        total_transfer_size: filtered.reduce((sum, e) => sum + (e.transferSize || 0), 0),
                        slowest_request: filtered.length > 0 ?
                            Math.max(...filtered.map(e => e.duration)) : 0
                    }};

                    return {{
                        requests: results,
                        statistics: stats,
                        filter_applied: '{url_filter}',
                        detailed_timing: {str(detailed).lower()}
                    }};
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': timing_code,
                'returnByValue': True
            })

            timing_data = result.get('result', {}).get('result', {}).get('value')

            return jsonify({
                "success": timing_data is not None,
                "url_filter": url_filter,
                "limit": limit,
                "detailed": detailed,
                "timing_analysis": timing_data,
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="analyze_network_timing",
            error=e,
            request_data={'url_filter': url_filter, 'limit': limit, 'detailed': detailed}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@network_intelligence_routes.route('/cdp/network/websockets', methods=['GET', 'POST'])
def monitor_websockets():
    """
    Monitor WebSocket connections and messages

    @route GET/POST /cdp/network/websockets
    @param {boolean} [active_only] - Show only active connections
    @param {number} [message_limit] - Max messages per connection
    @param {string} [url_filter] - Filter by WebSocket URL pattern
    @returns {object} WebSocket monitoring data

    @example
    // Monitor all WebSocket connections
    GET /cdp/network/websockets

    // Only active connections with recent messages
    POST {"active_only": true, "message_limit": 50}

    // Filter by URL pattern
    GET /cdp/network/websockets?url_filter=wss://api.example.com
    """
    try:
        params = _parse_request_params(request, ['active_only', 'message_limit', 'url_filter'])
        active_only = params['active_only'] in [True, 'true', '1']
        message_limit = int(params['message_limit'] or 20)
        url_filter = params['url_filter'] or ''

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Use JavaScript to inspect WebSocket connections
            websocket_code = f"""
                (() => {{
                    const wsConnections = [];

                    // Check for existing WebSocket instances
                    if (window.WebSocket && window.WebSocket.prototype) {{
                        // Hook into WebSocket creation to track connections
                        const wsInfo = {{
                            total_connections: 0,
                            active_connections: 0,
                            connection_attempts: 0,
                            message: "WebSocket monitoring requires instrumentation. Use CDP Network events for full tracking."
                        }};

                        // Try to find WebSocket instances in global scope
                        for (let prop in window) {{
                            try {{
                                if (window[prop] instanceof WebSocket) {{
                                    const ws = window[prop];
                                    const connection = {{
                                        url: ws.url,
                                        ready_state: ws.readyState,
                                        ready_state_text: ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][ws.readyState],
                                        protocol: ws.protocol,
                                        extensions: ws.extensions,
                                        binary_type: ws.binaryType
                                    }};

                                    if (!'{url_filter}' || ws.url.includes('{url_filter}')) {{
                                        if (!{str(active_only).lower()} || ws.readyState === 1) {{
                                            wsConnections.push(connection);
                                        }}
                                    }}
                                }}
                            }} catch (e) {{
                                // Skip inaccessible properties
                            }}
                        }}

                        wsInfo.found_instances = wsConnections.length;
                        return {{
                            connections: wsConnections,
                            info: wsInfo,
                            filter_applied: '{url_filter}',
                            active_only: {str(active_only).lower()},
                            message_limit: {message_limit}
                        }};
                    }}

                    return {{
                        connections: [],
                        info: {{ message: "WebSocket not available or no connections found" }},
                        filter_applied: '{url_filter}',
                        active_only: {str(active_only).lower()}
                    }};
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': websocket_code,
                'returnByValue': True
            })

            websocket_data = result.get('result', {}).get('result', {}).get('value')

            return jsonify({
                "success": websocket_data is not None,
                "active_only": active_only,
                "message_limit": message_limit,
                "url_filter": url_filter,
                "websocket_monitoring": websocket_data,
                "cdp_result": result,
                "note": "For full WebSocket monitoring, enable Network.webSocketCreated events"
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="monitor_websockets",
            error=e,
            request_data={'active_only': active_only, 'message_limit': message_limit, 'url_filter': url_filter}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@network_intelligence_routes.route('/cdp/network/cache', methods=['GET', 'POST'])
def analyze_cache():
    """
    Analyze browser cache and caching behavior

    @route GET/POST /cdp/network/cache
    @param {string} [url_filter] - Filter by URL pattern
    @param {boolean} [detailed] - Include detailed cache analysis
    @param {boolean} [clear_first] - Clear cache before analysis
    @returns {object} Cache analysis data

    @example
    // Basic cache analysis
    GET /cdp/network/cache

    // Detailed cache analysis with filter
    POST {"url_filter": "api.example.com", "detailed": true}

    // Clear cache then analyze
    POST {"clear_first": true}
    """
    try:
        params = _parse_request_params(request, ['url_filter', 'detailed', 'clear_first'])
        url_filter = params['url_filter'] or ''
        detailed = params['detailed'] in [True, 'true', '1']
        clear_first = params['clear_first'] in [True, 'true', '1']

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            cache_analysis = {}

            # Clear cache if requested
            if clear_first:
                clear_result = cdp.send_command('Network.clearBrowserCache')
                cache_analysis['cache_cleared'] = 'error' not in clear_result

            # Analyze cache via Performance API and Network analysis
            cache_code = f"""
                (() => {{
                    const performance = window.performance;
                    const resources = performance.getEntriesByType('resource');

                    let filtered = resources;
                    if ('{url_filter}') {{
                        filtered = resources.filter(r => r.name.includes('{url_filter}'));
                    }}

                    const cache_analysis = {{
                        total_resources: filtered.length,
                        cached_resources: 0,
                        cache_hits: 0,
                        cache_misses: 0,
                        resources: []
                    }};

                    filtered.forEach(resource => {{
                        const cache_status = {{
                            url: resource.name,
                            transfer_size: resource.transferSize || 0,
                            encoded_size: resource.encodedBodySize || 0,
                            decoded_size: resource.decodedBodySize || 0,
                            from_cache: resource.transferSize === 0 && resource.decodedBodySize > 0,
                            cache_ratio: resource.encodedBodySize > 0 ?
                                Math.round((resource.decodedBodySize / resource.encodedBodySize) * 100) / 100 : 0
                        }};

                        if (cache_status.from_cache) {{
                            cache_analysis.cache_hits++;
                        }} else {{
                            cache_analysis.cache_misses++;
                        }}

                        if ({str(detailed).lower()}) {{
                            cache_status.timing = {{
                                duration: Math.round(resource.duration * 100) / 100,
                                response_start: Math.round(resource.responseStart * 100) / 100,
                                response_end: Math.round(resource.responseEnd * 100) / 100
                            }};
                        }}

                        cache_analysis.resources.push(cache_status);
                    }});

                    cache_analysis.cache_hit_ratio = cache_analysis.total_resources > 0 ?
                        Math.round((cache_analysis.cache_hits / cache_analysis.total_resources) * 10000) / 100 : 0;

                    cache_analysis.total_transfer_size = filtered.reduce((sum, r) => sum + (r.transferSize || 0), 0);
                    cache_analysis.total_decoded_size = filtered.reduce((sum, r) => sum + (r.decodedBodySize || 0), 0);

                    return cache_analysis;
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': cache_code,
                'returnByValue': True
            })

            cache_data = result.get('result', {}).get('result', {}).get('value')
            if cache_data:
                cache_analysis.update(cache_data)

            return jsonify({
                "success": cache_data is not None,
                "url_filter": url_filter,
                "detailed": detailed,
                "clear_first": clear_first,
                "cache_analysis": cache_analysis,
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="analyze_cache",
            error=e,
            request_data={'url_filter': url_filter, 'detailed': detailed, 'clear_first': clear_first}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@network_intelligence_routes.route('/cdp/network/cors', methods=['GET', 'POST'])
def detect_cors_violations():
    """
    Detect CORS violations and cross-origin issues

    @route GET/POST /cdp/network/cors
    @param {string} [origin_filter] - Filter by origin pattern
    @param {boolean} [violations_only] - Show only CORS violations
    @param {boolean} [include_preflight] - Include preflight requests
    @returns {object} CORS analysis and violations

    @example
    // Detect all CORS issues
    GET /cdp/network/cors

    // Only violations with preflight analysis
    POST {"violations_only": true, "include_preflight": true}

    // Filter by specific origin
    GET /cdp/network/cors?origin_filter=api.example.com
    """
    try:
        params = _parse_request_params(request, ['origin_filter', 'violations_only', 'include_preflight'])
        origin_filter = params['origin_filter'] or ''
        violations_only = params['violations_only'] in [True, 'true', '1']
        include_preflight = params['include_preflight'] in [True, 'true', '1']

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Analyze CORS via JavaScript and console monitoring
            cors_code = f"""
                (() => {{
                    const currentOrigin = window.location.origin;
                    const corsAnalysis = {{
                        current_origin: currentOrigin,
                        cross_origin_requests: [],
                        cors_violations: [],
                        preflight_requests: [],
                        summary: {{
                            total_cross_origin: 0,
                            cors_enabled: 0,
                            cors_violations: 0,
                            preflight_count: 0
                        }}
                    }};

                    // Analyze from Performance API
                    const resources = performance.getEntriesByType('resource');

                    resources.forEach(resource => {{
                        try {{
                            const resourceUrl = new URL(resource.name);
                            const resourceOrigin = resourceUrl.origin;

                            if (resourceOrigin !== currentOrigin) {{
                                const request_info = {{
                                    url: resource.name,
                                    origin: resourceOrigin,
                                    duration: Math.round(resource.duration * 100) / 100,
                                    size: resource.transferSize || 0,
                                    type: 'cross-origin'
                                }};

                                if (!'{origin_filter}' || resourceOrigin.includes('{origin_filter}')) {{
                                    corsAnalysis.cross_origin_requests.push(request_info);
                                    corsAnalysis.summary.total_cross_origin++;
                                }}
                            }}
                        }} catch (e) {{
                            // Skip invalid URLs
                        }}
                    }});

                    // Check console for CORS errors (basic detection)
                    corsAnalysis.note = "Full CORS violation detection requires Network domain event monitoring";
                    corsAnalysis.detection_method = "Performance API + URL origin analysis";

                    // Filter results if requested
                    if ({str(violations_only).lower()}) {{
                        // For now, we can't detect actual violations without Network events
                        corsAnalysis.limitation = "violations_only requires Network.loadingFailed events";
                    }}

                    if (!{str(include_preflight).lower()}) {{
                        corsAnalysis.preflight_requests = [];
                    }}

                    return corsAnalysis;
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': cors_code,
                'returnByValue': True
            })

            cors_data = result.get('result', {}).get('result', {}).get('value')

            return jsonify({
                "success": cors_data is not None,
                "origin_filter": origin_filter,
                "violations_only": violations_only,
                "include_preflight": include_preflight,
                "cors_analysis": cors_data,
                "cdp_result": result,
                "note": "For comprehensive CORS monitoring, enable Network domain events"
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="detect_cors_violations",
            error=e,
            request_data={'origin_filter': origin_filter, 'violations_only': violations_only, 'include_preflight': include_preflight}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500