"""
JS Debugging Routes - Advanced JavaScript debugging and runtime analysis
JavaScript mastery through Runtime domain analysis and async operation monitoring
"""

import logging
from flask import Blueprint, jsonify, request
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter

logger = logging.getLogger(__name__)
js_debugging_routes = Blueprint('js_debugging', __name__)


def _parse_request_params(request, param_names):
    """Utility: Parse request parameters from GET/POST"""
    if request.method == 'GET':
        return {name: request.args.get(name) for name in param_names}
    else:
        data = request.get_json() or {}
        return {name: data.get(name) for name in param_names}


@js_debugging_routes.route('/cdp/js/advanced_debugging', methods=['POST'])
def advanced_javascript_debugging():
    """
    Advanced JavaScript debugging with stack trace analysis and error archaeology

    @route POST /cdp/js/advanced_debugging
    @param {string} expression - JavaScript code to debug
    @param {boolean} [stack_trace] - Include stack trace analysis
    @param {boolean} [scope_analysis] - Analyze variable scopes
    @param {boolean} [error_context] - Include error context and suggestions
    @param {object} [breakpoints] - Conditional breakpoints to set
    @returns {object} Advanced debugging analysis

    @example
    // Basic debugging analysis
    POST {"expression": "console.log('debug test')"}

    // Full debugging with error analysis
    POST {
      "expression": "throw new Error('test error')",
      "stack_trace": true,
      "scope_analysis": true,
      "error_context": true
    }

    // Debug with breakpoint context
    POST {
      "expression": "function test() { var x = 1; return x + undefined; }; test();",
      "stack_trace": true,
      "scope_analysis": true
    }
    """
    try:
        data = request.get_json() or {}
        expression = data.get('expression', '')
        stack_trace = data.get('stack_trace', False)
        scope_analysis = data.get('scope_analysis', False)
        error_context = data.get('error_context', False)
        breakpoints = data.get('breakpoints', {})

        if not expression:
            return jsonify({
                "success": False,
                "error": "No JavaScript expression provided"
            }), 400

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            debug_analysis = {
                "expression": expression,
                "execution_result": None,
                "error_analysis": None,
                "stack_trace_data": None,
                "scope_data": None,
                "debugging_suggestions": []
            }

            # Execute the expression with error capture
            execution_code = f"""
                (() => {{
                    const debugContext = {{
                        result: null,
                        error: null,
                        stack: null,
                        type: null,
                        execution_time: null
                    }};

                    const startTime = performance.now();

                    try {{
                        debugContext.result = eval(`{expression}`);
                        debugContext.type = typeof debugContext.result;
                        debugContext.execution_time = performance.now() - startTime;
                    }} catch (error) {{
                        debugContext.error = {{
                            name: error.name,
                            message: error.message,
                            stack: error.stack,
                            line_number: error.lineNumber || 'unknown',
                            column_number: error.columnNumber || 'unknown'
                        }};
                        debugContext.execution_time = performance.now() - startTime;
                    }}

                    return debugContext;
                }})()
            """

            execution_result = cdp.send_command('Runtime.evaluate', {
                'expression': execution_code,
                'returnByValue': True,
                'includeCommandLineAPI': True
            })

            if 'result' in execution_result:
                debug_analysis["execution_result"] = execution_result['result'].get('result', {}).get('value')

            # Advanced error analysis if requested
            if error_context and debug_analysis["execution_result"] and debug_analysis["execution_result"].get("error"):
                error_analysis_code = f"""
                    (() => {{
                        const error = {str(debug_analysis["execution_result"]["error"]).replace("'", '"')};
                        const analysis = {{
                            error_type: error.name,
                            error_category: "unknown",
                            suggestions: [],
                            common_causes: []
                        }};

                        // Categorize error types
                        switch (error.name) {{
                            case 'TypeError':
                                analysis.error_category = 'type_error';
                                analysis.suggestions.push('Check variable types and method availability');
                                analysis.common_causes.push('Undefined variables', 'Null reference', 'Wrong method call');
                                break;
                            case 'ReferenceError':
                                analysis.error_category = 'reference_error';
                                analysis.suggestions.push('Verify variable declarations and scope');
                                analysis.common_causes.push('Undeclared variables', 'Scope issues', 'Typos in variable names');
                                break;
                            case 'SyntaxError':
                                analysis.error_category = 'syntax_error';
                                analysis.suggestions.push('Check syntax and bracket matching');
                                analysis.common_causes.push('Missing brackets', 'Invalid operators', 'Malformed expressions');
                                break;
                            default:
                                analysis.error_category = 'runtime_error';
                                analysis.suggestions.push('Check runtime conditions and data flow');
                        }}

                        // Analyze error message for common patterns
                        if (error.message.includes('undefined')) {{
                            analysis.suggestions.push('Variable may be undefined - check initialization');
                        }}
                        if (error.message.includes('null')) {{
                            analysis.suggestions.push('Null reference detected - add null checks');
                        }}
                        if (error.message.includes('not a function')) {{
                            analysis.suggestions.push('Method does not exist - verify object structure');
                        }}

                        return analysis;
                    }})()
                """

                error_analysis_result = cdp.send_command('Runtime.evaluate', {
                    'expression': error_analysis_code,
                    'returnByValue': True
                })

                if 'result' in error_analysis_result:
                    debug_analysis["error_analysis"] = error_analysis_result['result'].get('result', {}).get('value')

            # Stack trace analysis if requested
            if stack_trace and debug_analysis["execution_result"] and debug_analysis["execution_result"].get("error"):
                stack_analysis_code = f"""
                    (() => {{
                        const stack = `{debug_analysis["execution_result"]["error"].get("stack", "")}`;
                        const lines = stack.split('\\n').filter(line => line.trim());

                        const stackAnalysis = {{
                            total_frames: lines.length,
                            frames: [],
                            call_chain: []
                        }};

                        lines.forEach((line, index) => {{
                            const frame = {{
                                frame_number: index,
                                raw_line: line.trim(),
                                function_name: 'unknown',
                                file_location: 'unknown',
                                is_user_code: false
                            }};

                            // Parse common stack trace formats
                            const atMatch = line.match(/at\\s+(.+?)\\s+\\((.+?)\\)/);
                            const simpleMatch = line.match(/at\\s+(.+)/);

                            if (atMatch) {{
                                frame.function_name = atMatch[1];
                                frame.file_location = atMatch[2];
                                frame.is_user_code = !atMatch[2].includes('chrome-extension://') &&
                                                   !atMatch[2].includes('native');
                            }} else if (simpleMatch) {{
                                frame.function_name = simpleMatch[1];
                                frame.is_user_code = !line.includes('chrome-extension://') &&
                                                   !line.includes('native');
                            }}

                            stackAnalysis.frames.push(frame);
                            if (frame.function_name !== 'unknown') {{
                                stackAnalysis.call_chain.push(frame.function_name);
                            }}
                        }});

                        return stackAnalysis;
                    }})()
                """

                stack_result = cdp.send_command('Runtime.evaluate', {
                    'expression': stack_analysis_code,
                    'returnByValue': True
                })

                if 'result' in stack_result:
                    debug_analysis["stack_trace_data"] = stack_result['result'].get('result', {}).get('value')

            # Scope analysis if requested
            if scope_analysis:
                scope_analysis_code = f"""
                    (() => {{
                        const scopeInfo = {{
                            global_variables: [],
                            local_context: {{}},
                            available_functions: [],
                            dom_references: {{}}
                        }};

                        // Analyze global scope
                        for (let prop in window) {{
                            if (window.hasOwnProperty(prop) && typeof window[prop] !== 'function') {{
                                scopeInfo.global_variables.push({{
                                    name: prop,
                                    type: typeof window[prop],
                                    value_preview: String(window[prop]).substring(0, 50)
                                }});
                            }}
                        }}

                        // Count available functions
                        for (let prop in window) {{
                            if (typeof window[prop] === 'function') {{
                                scopeInfo.available_functions.push(prop);
                            }}
                        }}

                        // DOM context
                        scopeInfo.dom_references.document_ready = document.readyState;
                        scopeInfo.dom_references.elements_count = document.querySelectorAll('*').length;
                        scopeInfo.dom_references.scripts_count = document.scripts.length;

                        scopeInfo.global_variables = scopeInfo.global_variables.slice(0, 20); // Limit for performance
                        scopeInfo.available_functions = scopeInfo.available_functions.slice(0, 30);

                        return scopeInfo;
                    }})()
                """

                scope_result = cdp.send_command('Runtime.evaluate', {
                    'expression': scope_analysis_code,
                    'returnByValue': True
                })

                if 'result' in scope_result:
                    debug_analysis["scope_data"] = scope_result['result'].get('result', {}).get('value')

            # Generate debugging suggestions
            suggestions = []
            if debug_analysis["execution_result"]:
                if debug_analysis["execution_result"].get("error"):
                    suggestions.append("Error detected - check error analysis for details")
                    suggestions.append("Use stack trace to identify exact failure point")
                else:
                    suggestions.append("Expression executed successfully")

                exec_time = debug_analysis["execution_result"].get("execution_time", 0)
                if exec_time > 100:
                    suggestions.append(f"Slow execution ({exec_time:.2f}ms) - consider optimization")

            if scope_analysis:
                suggestions.append("Use scope data to verify variable availability")

            debug_analysis["debugging_suggestions"] = suggestions

            return jsonify({
                "success": True,
                "debug_analysis": debug_analysis,
                "options": {
                    "stack_trace": stack_trace,
                    "scope_analysis": scope_analysis,
                    "error_context": error_context
                }
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="advanced_javascript_debugging",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "expression": expression,
            "crash_id": crash_data.get('timestamp')
        }), 500


@js_debugging_routes.route('/cdp/js/async_analysis', methods=['POST'])
def analyze_async_operations():
    """
    Analyze asynchronous JavaScript operations and promise states

    @route POST /cdp/js/async_analysis
    @param {string} [expression] - Async expression to analyze
    @param {boolean} [promise_tracking] - Track promise states
    @param {boolean} [callback_analysis] - Analyze callback patterns
    @param {number} [timeout] - Analysis timeout in milliseconds
    @param {boolean} [performance_timing] - Include performance metrics
    @returns {object} Async operation analysis

    @example
    // Analyze async expression
    POST {
      "expression": "fetch('/api/data').then(r => r.json())",
      "promise_tracking": true,
      "performance_timing": true
    }

    // Analyze overall async state
    POST {
      "promise_tracking": true,
      "callback_analysis": true,
      "timeout": 5000
    }

    // Performance-focused async analysis
    POST {
      "expression": "setTimeout(() => console.log('delayed'), 1000)",
      "performance_timing": true
    }
    """
    try:
        data = request.get_json() or {}
        expression = data.get('expression', '')
        promise_tracking = data.get('promise_tracking', True)
        callback_analysis = data.get('callback_analysis', False)
        timeout = data.get('timeout', 3000)
        performance_timing = data.get('performance_timing', False)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            async_analysis = {
                "expression": expression,
                "promise_states": None,
                "callback_info": None,
                "performance_data": None,
                "async_suggestions": []
            }

            # Promise tracking analysis
            if promise_tracking:
                promise_code = f"""
                    (() => {{
                        const promiseAnalysis = {{
                            active_promises: 0,
                            resolved_promises: 0,
                            rejected_promises: 0,
                            pending_operations: [],
                            promise_chain_depth: 0
                        }};

                        // Hook into Promise constructor for tracking
                        const originalPromise = Promise;
                        let promiseCount = 0;
                        let resolvedCount = 0;
                        let rejectedCount = 0;

                        // Analyze existing promise state
                        const testPromise = new Promise((resolve) => {{
                            resolve('test');
                        }});

                        testPromise.then(() => {{
                            resolvedCount++;
                        }}).catch(() => {{
                            rejectedCount++;
                        }});

                        // Check for unhandled rejections
                        let unhandledRejections = 0;
                        window.addEventListener('unhandledrejection', (event) => {{
                            unhandledRejections++;
                        }});

                        // Performance API for async operations
                        const performanceEntries = performance.getEntriesByType('measure')
                            .concat(performance.getEntriesByType('mark'))
                            .filter(entry => entry.name.includes('async') || entry.name.includes('promise'));

                        promiseAnalysis.performance_entries = performanceEntries.length;
                        promiseAnalysis.unhandled_rejections = unhandledRejections;

                        // If expression provided, analyze it
                        if ('{expression}') {{
                            try {{
                                const result = eval(`{expression}`);
                                promiseAnalysis.expression_result = {{
                                    type: typeof result,
                                    is_promise: result instanceof Promise,
                                    is_thenable: result && typeof result.then === 'function'
                                }};

                                if (result instanceof Promise) {{
                                    promiseAnalysis.promise_created = true;
                                    // Note: Promise state inspection is limited in browser context
                                }}
                            }} catch (error) {{
                                promiseAnalysis.expression_error = {{
                                    name: error.name,
                                    message: error.message
                                }};
                            }}
                        }}

                        return promiseAnalysis;
                    }})()
                """

                promise_result = cdp.send_command('Runtime.evaluate', {
                    'expression': promise_code,
                    'returnByValue': True,
                    'awaitPromise': False
                })

                if 'result' in promise_result:
                    async_analysis["promise_states"] = promise_result['result'].get('result', {}).get('value')

            # Callback analysis
            if callback_analysis:
                callback_code = f"""
                    (() => {{
                        const callbackAnalysis = {{
                            setTimeout_calls: 0,
                            setInterval_calls: 0,
                            event_listeners: 0,
                            callback_patterns: []
                        }};

                        // Check for timer functions
                        const originalSetTimeout = window.setTimeout;
                        const originalSetInterval = window.setInterval;

                        // Count existing timers (limited visibility)
                        callbackAnalysis.note = "Timer counting requires instrumentation for full accuracy";

                        // Analyze event listeners on common elements
                        const elementsWithListeners = document.querySelectorAll('*');
                        let listenerCount = 0;

                        elementsWithListeners.forEach(element => {{
                            const events = ['click', 'load', 'change', 'submit', 'keydown', 'keyup'];
                            events.forEach(eventType => {{
                                // Note: getEventListeners is not available in standard context
                                if (element['on' + eventType]) {{
                                    listenerCount++;
                                }}
                            }});
                        }});

                        callbackAnalysis.estimated_event_listeners = listenerCount;

                        // Check for common async patterns
                        const scriptTags = document.querySelectorAll('script');
                        let callbackPatterns = [];

                        scriptTags.forEach(script => {{
                            if (script.textContent) {{
                                if (script.textContent.includes('setTimeout')) {{
                                    callbackPatterns.push('setTimeout_detected');
                                }}
                                if (script.textContent.includes('setInterval')) {{
                                    callbackPatterns.push('setInterval_detected');
                                }}
                                if (script.textContent.includes('.then(')) {{
                                    callbackPatterns.push('promise_chain_detected');
                                }}
                                if (script.textContent.includes('async ')) {{
                                    callbackPatterns.push('async_function_detected');
                                }}
                            }}
                        }});

                        callbackAnalysis.detected_patterns = [...new Set(callbackPatterns)];

                        return callbackAnalysis;
                    }})()
                """

                callback_result = cdp.send_command('Runtime.evaluate', {
                    'expression': callback_code,
                    'returnByValue': True
                })

                if 'result' in callback_result:
                    async_analysis["callback_info"] = callback_result['result'].get('result', {}).get('value')

            # Performance timing analysis
            if performance_timing:
                perf_code = f"""
                    (() => {{
                        const perfAnalysis = {{
                            navigation_timing: {{}},
                            resource_timing: [],
                            async_operations: [],
                            performance_marks: []
                        }};

                        // Navigation timing
                        if (performance.timing) {{
                            const timing = performance.timing;
                            perfAnalysis.navigation_timing = {{
                                page_load_time: timing.loadEventEnd - timing.navigationStart,
                                dom_ready_time: timing.domContentLoadedEventEnd - timing.navigationStart,
                                dns_time: timing.domainLookupEnd - timing.domainLookupStart,
                                tcp_time: timing.connectEnd - timing.connectStart,
                                response_time: timing.responseEnd - timing.responseStart
                            }};
                        }}

                        // Resource timing for async resources
                        const resources = performance.getEntriesByType('resource')
                            .filter(resource => resource.name.includes('api') ||
                                              resource.name.includes('ajax') ||
                                              resource.name.includes('fetch'))
                            .slice(0, 10); // Limit for performance

                        perfAnalysis.async_resources = resources.map(resource => ({{
                            name: resource.name,
                            duration: Math.round(resource.duration * 100) / 100,
                            transfer_size: resource.transferSize || 0,
                            response_time: Math.round((resource.responseEnd - resource.responseStart) * 100) / 100
                        }}));

                        // Performance marks
                        const marks = performance.getEntriesByType('mark').slice(0, 10);
                        perfAnalysis.performance_marks = marks.map(mark => ({{
                            name: mark.name,
                            start_time: Math.round(mark.startTime * 100) / 100
                        }}));

                        return perfAnalysis;
                    }})()
                """

                perf_result = cdp.send_command('Runtime.evaluate', {
                    'expression': perf_code,
                    'returnByValue': True
                })

                if 'result' in perf_result:
                    async_analysis["performance_data"] = perf_result['result'].get('result', {}).get('value')

            # Generate async suggestions
            suggestions = []

            if async_analysis["promise_states"]:
                if async_analysis["promise_states"].get("unhandled_rejections", 0) > 0:
                    suggestions.append("Unhandled promise rejections detected - add .catch() handlers")
                if async_analysis["promise_states"].get("expression_result", {}).get("is_promise"):
                    suggestions.append("Expression returns a promise - consider await or .then() handling")

            if async_analysis["callback_info"]:
                patterns = async_analysis["callback_info"].get("detected_patterns", [])
                if "setTimeout_detected" in patterns:
                    suggestions.append("setTimeout usage detected - ensure proper cleanup")
                if "setInterval_detected" in patterns:
                    suggestions.append("setInterval usage detected - verify clearInterval calls")

            if async_analysis["performance_data"]:
                resources = async_analysis["performance_data"].get("async_resources", [])
                slow_resources = [r for r in resources if r.get("duration", 0) > 1000]
                if slow_resources:
                    suggestions.append(f"Slow async resources detected: {len(slow_resources)} requests > 1s")

            if not suggestions:
                suggestions.append("Async analysis complete - no immediate issues detected")

            async_analysis["async_suggestions"] = suggestions

            return jsonify({
                "success": True,
                "async_analysis": async_analysis,
                "options": {
                    "promise_tracking": promise_tracking,
                    "callback_analysis": callback_analysis,
                    "performance_timing": performance_timing,
                    "timeout": timeout
                }
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="analyze_async_operations",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "expression": expression,
            "crash_id": crash_data.get('timestamp')
        }), 500