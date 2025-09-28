"""
Advanced Stress Testing Routes
Breaking point discovery and chaos engineering
10 endpoints for boundary testing and structural assault
"""

import logging
from flask import Blueprint, request, jsonify
from cdp_ninja.core.cdp_pool import get_global_pool
from cdp_ninja.core.domain_manager import CDPDomain
from .route_utils import (
    require_domains, create_success_response, handle_cdp_error,
    parse_request_params, track_endpoint_usage
)

logger = logging.getLogger(__name__)

stress_testing_advanced_routes = Blueprint('stress_testing_advanced', __name__)


@stress_testing_advanced_routes.route('/cdp/stress/click_storm', methods=['POST'])
@require_domains([CDPDomain.DOM, CDPDomain.INPUT])
def click_storm():
    """
    Aggressive rapid clicking to test event handling limits

    @route POST /cdp/stress/click_storm
    @body {string} target - CSS selector for click target
    @body {number} [count=100] - Number of clicks to perform
    @body {number} [interval=10] - Milliseconds between clicks
    @returns {object} Click storm results with performance impact and errors
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            target = data.get('target')
            count = data.get('count', 100)
            interval = data.get('interval', 10)

            if not target:
                return jsonify({"error": "target selector required"}), 400

            client.send_command('DOM.enable')
            client.send_command('Input.enable') if hasattr(client, 'send_command') else None

            click_storm_js = f"""
            (() => {{
                const results = {{
                    target_selector: '{target}',
                    clicks_requested: {count},
                    clicks_executed: 0,
                    interval_ms: {interval},
                    errors: [],
                    performance_impact: {{
                        start_time: performance.now(),
                        end_time: null,
                        total_duration: 0,
                        memory_before: null,
                        memory_after: null
                    }},
                    target_analysis: {{
                        elements_found: 0,
                        elements_clickable: 0,
                        event_listeners: 0
                    }}
                }};

                // Capture initial memory if available
                if (performance.memory) {{
                    results.performance_impact.memory_before = {{
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    }};
                }}

                // Find target elements
                const targets = document.querySelectorAll('{target}');
                results.target_analysis.elements_found = targets.length;

                if (targets.length === 0) {{
                    results.errors.push({{
                        type: 'no_targets',
                        message: 'No elements found matching selector'
                    }});
                    return results;
                }}

                // Check if elements are clickable
                targets.forEach(element => {{
                    const rect = element.getBoundingClientRect();
                    const isVisible = rect.width > 0 && rect.height > 0;
                    const styles = window.getComputedStyle(element);
                    const isInteractive = element.tagName === 'BUTTON' ||
                                         element.tagName === 'A' ||
                                         element.onclick ||
                                         element.getAttribute('role') === 'button' ||
                                         styles.cursor === 'pointer';

                    if (isVisible && (isInteractive || element.click)) {{
                        results.target_analysis.elements_clickable++;
                    }}
                }});

                // Aggressive clicking loop
                let clickCount = 0;
                const clickInterval = setInterval(() => {{
                    if (clickCount >= {count}) {{
                        clearInterval(clickInterval);

                        // Capture final metrics
                        results.performance_impact.end_time = performance.now();
                        results.performance_impact.total_duration =
                            results.performance_impact.end_time - results.performance_impact.start_time;

                        if (performance.memory) {{
                            results.performance_impact.memory_after = {{
                                used: performance.memory.usedJSHeapSize,
                                total: performance.memory.totalJSHeapSize,
                                limit: performance.memory.jsHeapSizeLimit
                            }};

                            results.performance_impact.memory_delta = {{
                                used: results.performance_impact.memory_after.used -
                                      results.performance_impact.memory_before.used,
                                total: results.performance_impact.memory_after.total -
                                       results.performance_impact.memory_before.total
                            }};
                        }}

                        return;
                    }}

                    // Click all matching elements
                    targets.forEach((element, index) => {{
                        try {{
                            element.click();
                            clickCount++;
                            results.clicks_executed++;
                        }} catch (error) {{
                            results.errors.push({{
                                type: 'click_error',
                                element_index: index,
                                message: error.message,
                                click_number: clickCount
                            }});
                        }}
                    }});
                }}, {interval});

                // Return initial state, final results will be captured by interval
                return new Promise(resolve => {{
                    setTimeout(() => {{
                        resolve(results);
                    }}, ({count} * {interval}) + 500);
                }});
            }})()
            """

            click_result = client.send_command('Runtime.evaluate', {
                'expression': click_storm_js,
                'returnByValue': True,
                'awaitPromise': True
            })

            storm_data = {
                "click_storm_results": click_result.get('result', {}).get('value', {}),
                "test_parameters": {
                    "target": target,
                    "count": count,
                    "interval": interval
                }
            }

            track_endpoint_usage('click_storm', [CDPDomain.DOM, CDPDomain.INPUT], {
                'target': target,
                'count': count,
                'clicks_executed': storm_data.get('click_storm_results', {}).get('clicks_executed', 0)
            })

            return jsonify(create_success_response(storm_data, 'click_storm', [CDPDomain.DOM, CDPDomain.INPUT]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('click_storm', e, {'target': target}, 'click_storm')


@stress_testing_advanced_routes.route('/cdp/stress/memory_bomb', methods=['POST'])
@require_domains([CDPDomain.RUNTIME, CDPDomain.MEMORY])
def memory_bomb():
    """
    Aggressive memory allocation to test memory limits

    @route POST /cdp/stress/memory_bomb
    @body {number} [size_mb=100] - Memory to allocate in MB
    @body {string} [allocate_rate=fast] - Allocation speed (slow, medium, fast)
    @body {boolean} [monitor=true] - Monitor memory usage during test
    @returns {object} Memory stress test results with allocation patterns and system impact
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            size_mb = data.get('size_mb', 100)
            allocate_rate = data.get('allocate_rate', 'fast')
            monitor = data.get('monitor', True)

            client.send_command('Runtime.enable')
            client.send_command('HeapProfiler.enable') if monitor else None

            # Get initial heap snapshot if monitoring
            initial_snapshot = None
            if monitor:
                initial_snapshot = client.send_command('HeapProfiler.takeHeapSnapshot')

            memory_bomb_js = f"""
            (() => {{
                const results = {{
                    target_size_mb: {size_mb},
                    allocation_rate: '{allocate_rate}',
                    monitoring_enabled: {str(monitor).lower()},
                    memory_allocations: [],
                    system_impact: {{
                        initial_memory: null,
                        peak_memory: null,
                        final_memory: null,
                        gc_triggered: false
                    }},
                    performance_degradation: {{
                        initial_fps: null,
                        degraded_fps: null,
                        responsiveness_loss: 0
                    }},
                    allocation_errors: []
                }};

                // Capture initial memory state
                if (performance.memory) {{
                    results.system_impact.initial_memory = {{
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    }};
                }}

                // Determine allocation parameters
                const bytesToAllocate = {size_mb} * 1024 * 1024;
                const chunkSize = {{
                    'slow': 1024 * 100,    // 100KB chunks
                    'medium': 1024 * 500,  // 500KB chunks
                    'fast': 1024 * 1024    // 1MB chunks
                }}['{allocate_rate}'] || 1024 * 1024;

                const delay = {{
                    'slow': 100,
                    'medium': 50,
                    'fast': 10
                }}['{allocate_rate}'] || 10;

                let allocatedBytes = 0;
                let allocationIndex = 0;
                const memoryHogs = [];

                // Start allocation process
                const allocateChunk = () => {{
                    try {{
                        // Create large array to consume memory
                        const chunk = new ArrayBuffer(chunkSize);
                        const view = new Uint8Array(chunk);

                        // Fill with data to ensure allocation
                        for (let i = 0; i < Math.min(view.length, 1000); i++) {{
                            view[i] = Math.floor(Math.random() * 256);
                        }}

                        memoryHogs.push({{ buffer: chunk, view: view }});
                        allocatedBytes += chunkSize;
                        allocationIndex++;

                        // Track allocation
                        const currentMemory = performance.memory ? {{
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize
                        }} : null;

                        results.memory_allocations.push({{
                            allocation_index: allocationIndex,
                            chunk_size_bytes: chunkSize,
                            total_allocated_bytes: allocatedBytes,
                            memory_after_allocation: currentMemory,
                            timestamp: Date.now()
                        }});

                        // Update peak memory
                        if (currentMemory && (!results.system_impact.peak_memory ||
                            currentMemory.used > results.system_impact.peak_memory.used)) {{
                            results.system_impact.peak_memory = currentMemory;
                        }}

                        // Check if we've hit the target or limits
                        if (allocatedBytes >= bytesToAllocate) {{
                            finalizeTest();
                            return;
                        }}

                        // Check for memory pressure
                        if (currentMemory && currentMemory.used > currentMemory.total * 0.9) {{
                            results.system_impact.gc_triggered = true;
                            // Force garbage collection attempt
                            if (window.gc) {{
                                window.gc();
                            }}
                        }}

                        // Continue allocation
                        setTimeout(allocateChunk, delay);

                    }} catch (error) {{
                        results.allocation_errors.push({{
                            allocation_index: allocationIndex,
                            error_type: error.name,
                            error_message: error.message,
                            allocated_before_error: allocatedBytes
                        }});

                        // Try to continue with smaller chunks
                        if (chunkSize > 1024) {{
                            chunkSize = Math.floor(chunkSize / 2);
                            setTimeout(allocateChunk, delay);
                        }} else {{
                            finalizeTest();
                        }}
                    }}
                }};

                const finalizeTest = () => {{
                    // Capture final memory state
                    if (performance.memory) {{
                        results.system_impact.final_memory = {{
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize,
                            limit: performance.memory.jsHeapSizeLimit
                        }};
                    }}

                    // Calculate memory efficiency
                    if (results.system_impact.initial_memory && results.system_impact.final_memory) {{
                        results.system_impact.actual_increase =
                            results.system_impact.final_memory.used - results.system_impact.initial_memory.used;
                        results.system_impact.allocation_efficiency =
                            results.system_impact.actual_increase / allocatedBytes;
                    }}

                    // Test responsiveness after allocation
                    const responsiveStart = performance.now();
                    setTimeout(() => {{
                        const responsiveEnd = performance.now();
                        const expectedDelay = 10;
                        const actualDelay = responsiveEnd - responsiveStart;
                        results.performance_degradation.responsiveness_loss = actualDelay - expectedDelay;
                    }}, 10);
                }};

                // Start the memory bomb
                allocateChunk();

                // Return results after allocation completes
                return new Promise(resolve => {{
                    const checkCompletion = () => {{
                        if (allocatedBytes >= bytesToAllocate || results.allocation_errors.length > 5) {{
                            setTimeout(() => resolve(results), 100);
                        }} else {{
                            setTimeout(checkCompletion, 200);
                        }}
                    }};
                    checkCompletion();
                }});
            }})()
            """

            memory_result = client.send_command('Runtime.evaluate', {
                'expression': memory_bomb_js,
                'returnByValue': True,
                'awaitPromise': True
            })

            # Get final heap snapshot if monitoring
            final_snapshot = None
            if monitor:
                final_snapshot = client.send_command('HeapProfiler.takeHeapSnapshot')

            memory_data = {
                "memory_bomb_results": memory_result.get('result', {}).get('value', {}),
                "heap_snapshots": {
                    "initial": initial_snapshot.get('success', False) if initial_snapshot else None,
                    "final": final_snapshot.get('success', False) if final_snapshot else None
                },
                "test_parameters": {
                    "size_mb": size_mb,
                    "allocate_rate": allocate_rate,
                    "monitor": monitor
                }
            }

            track_endpoint_usage('memory_bomb', [CDPDomain.RUNTIME, CDPDomain.MEMORY], {
                'size_mb': size_mb,
                'allocate_rate': allocate_rate,
                'bytes_allocated': memory_data.get('memory_bomb_results', {}).get('allocatedBytes', 0)
            })

            return jsonify(create_success_response(memory_data, 'memory_bomb', [CDPDomain.RUNTIME, CDPDomain.MEMORY]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('memory_bomb', e, {'size_mb': size_mb}, 'memory_bomb')


@stress_testing_advanced_routes.route('/cdp/stress/cpu_burn', methods=['POST'])
@require_domains([CDPDomain.RUNTIME])
def cpu_burn():
    """
    Intensive CPU computation to test performance limits

    @route POST /cdp/stress/cpu_burn
    @body {number} [duration=5000] - Test duration in milliseconds
    @body {string} [intensity=high] - CPU intensity (low, medium, high)
    @body {boolean} [block_main_thread=true] - Whether to block main thread
    @returns {object} CPU stress test results with performance metrics and system impact
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            duration = data.get('duration', 5000)
            intensity = data.get('intensity', 'high')
            block_main_thread = data.get('block_main_thread', True)

            client.send_command('Runtime.enable')

            cpu_burn_js = f"""
            (() => {{
                const results = {{
                    duration_ms: {duration},
                    intensity_level: '{intensity}',
                    blocks_main_thread: {str(block_main_thread).lower()},
                    performance_metrics: {{
                        start_time: performance.now(),
                        end_time: null,
                        total_duration: 0,
                        operations_completed: 0,
                        operations_per_second: 0
                    }},
                    system_impact: {{
                        initial_memory: null,
                        peak_memory: null,
                        memory_growth: 0,
                        frame_drops: 0,
                        main_thread_blocked_ms: 0
                    }},
                    computation_results: {{
                        calculations_performed: 0,
                        hash_operations: 0,
                        prime_numbers_found: 0,
                        fibonacci_computed: 0
                    }}
                }};

                // Capture initial state
                if (performance.memory) {{
                    results.system_impact.initial_memory = {{
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize
                    }};
                }}

                // Define intensity parameters
                const intensityParams = {{
                    'low': {{ iterations: 1000, complexity: 1, chunk_size: 100 }},
                    'medium': {{ iterations: 10000, complexity: 5, chunk_size: 500 }},
                    'high': {{ iterations: 100000, complexity: 10, chunk_size: 1000 }}
                }}['{intensity}'] || {{ iterations: 100000, complexity: 10, chunk_size: 1000 }};

                let operationsCompleted = 0;
                let startTime = performance.now();
                let endTime = startTime + {duration};

                // CPU-intensive computation functions
                const computeHash = (input) => {{
                    let hash = 0;
                    for (let i = 0; i < input.length; i++) {{
                        const char = input.charCodeAt(i);
                        hash = ((hash << 5) - hash) + char;
                        hash = hash & hash; // Convert to 32-bit integer
                    }}
                    return hash;
                }};

                const isPrime = (n) => {{
                    if (n <= 1) return false;
                    if (n <= 3) return true;
                    if (n % 2 === 0 || n % 3 === 0) return false;

                    for (let i = 5; i * i <= n; i += 6) {{
                        if (n % i === 0 || n % (i + 2) === 0) return false;
                    }}
                    return true;
                }};

                const fibonacci = (n) => {{
                    if (n <= 1) return n;
                    let a = 0, b = 1, temp;
                    for (let i = 2; i <= n; i++) {{
                        temp = a + b;
                        a = b;
                        b = temp;
                    }}
                    return b;
                }};

                const performIntensiveCalculations = () => {{
                    const batchStart = performance.now();

                    for (let i = 0; i < intensityParams.chunk_size && performance.now() < endTime; i++) {{
                        // Hash computation
                        const hashInput = 'stress_test_' + operationsCompleted + '_' + Math.random();
                        computeHash(hashInput);
                        results.computation_results.hash_operations++;

                        // Prime number testing
                        const testNumber = Math.floor(Math.random() * 10000) + 1000;
                        if (isPrime(testNumber)) {{
                            results.computation_results.prime_numbers_found++;
                        }}

                        // Fibonacci computation
                        const fibN = Math.floor(Math.random() * 30) + 10;
                        fibonacci(fibN);
                        results.computation_results.fibonacci_computed++;

                        // Complex mathematical operations
                        for (let j = 0; j < intensityParams.complexity; j++) {{
                            Math.sin(Math.random() * 1000) * Math.cos(Math.random() * 1000);
                            Math.sqrt(Math.random() * 1000000);
                            Math.pow(Math.random() * 100, 3);
                        }}

                        operationsCompleted++;
                        results.computation_results.calculations_performed++;
                    }}

                    const batchEnd = performance.now();
                    const batchDuration = batchEnd - batchStart;

                    // Track main thread blocking
                    if ({str(block_main_thread).lower()} && batchDuration > 16.67) {{ // More than one frame at 60fps
                        results.system_impact.main_thread_blocked_ms += batchDuration;
                        results.system_impact.frame_drops += Math.floor(batchDuration / 16.67);
                    }}

                    // Update memory tracking
                    if (performance.memory) {{
                        const currentMemory = {{
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize
                        }};

                        if (!results.system_impact.peak_memory ||
                            currentMemory.used > results.system_impact.peak_memory.used) {{
                            results.system_impact.peak_memory = currentMemory;
                        }}
                    }}

                    // Continue or finish
                    if (performance.now() < endTime) {{
                        if ({str(block_main_thread).lower()}) {{
                            // Immediately continue (blocking)
                            performIntensiveCalculations();
                        }} else {{
                            // Use setTimeout to yield to main thread
                            setTimeout(performIntensiveCalculations, 0);
                        }}
                    }} else {{
                        finalizeBurnTest();
                    }}
                }};

                const finalizeBurnTest = () => {{
                    results.performance_metrics.end_time = performance.now();
                    results.performance_metrics.total_duration =
                        results.performance_metrics.end_time - results.performance_metrics.start_time;
                    results.performance_metrics.operations_completed = operationsCompleted;
                    results.performance_metrics.operations_per_second =
                        operationsCompleted / (results.performance_metrics.total_duration / 1000);

                    // Calculate memory growth
                    if (results.system_impact.initial_memory && results.system_impact.peak_memory) {{
                        results.system_impact.memory_growth =
                            results.system_impact.peak_memory.used - results.system_impact.initial_memory.used;
                    }}
                }};

                // Start CPU burn test
                performIntensiveCalculations();

                // Return results after completion
                return new Promise(resolve => {{
                    const checkCompletion = () => {{
                        if (performance.now() >= endTime || results.performance_metrics.end_time) {{
                            setTimeout(() => resolve(results), 50);
                        }} else {{
                            setTimeout(checkCompletion, 100);
                        }}
                    }};
                    checkCompletion();
                }});
            }})()
            """

            cpu_result = client.send_command('Runtime.evaluate', {
                'expression': cpu_burn_js,
                'returnByValue': True,
                'awaitPromise': True
            })

            cpu_data = {
                "cpu_burn_results": cpu_result.get('result', {}).get('value', {}),
                "test_parameters": {
                    "duration": duration,
                    "intensity": intensity,
                    "block_main_thread": block_main_thread
                }
            }

            track_endpoint_usage('cpu_burn', [CDPDomain.RUNTIME], {
                'duration': duration,
                'intensity': intensity,
                'operations_completed': cpu_data.get('cpu_burn_results', {}).get('performance_metrics', {}).get('operations_completed', 0)
            })

            return jsonify(create_success_response(cpu_data, 'cpu_burn', [CDPDomain.RUNTIME]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('cpu_burn', e, {'duration': duration}, 'cpu_burn')


@stress_testing_advanced_routes.route('/cdp/stress/input_overflow', methods=['POST'])
@require_domains([CDPDomain.DOM, CDPDomain.INPUT])
def input_overflow():
    """
    Test input field limits with oversized payloads

    @route POST /cdp/stress/input_overflow
    @body {string} selector - CSS selector for input fields
    @body {number} [payload_size=10000] - Size of input payload in characters
    @body {boolean} [special_chars=true] - Include special characters
    @returns {object} Input overflow test results with field behavior and limitations
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            selector = data.get('selector')
            payload_size = data.get('payload_size', 10000)
            special_chars = data.get('special_chars', True)

            if not selector:
                return jsonify({"error": "selector required"}), 400

            client.send_command('DOM.enable')

            input_overflow_js = f"""
            (() => {{
                const results = {{
                    selector: '{selector}',
                    payload_size_requested: {payload_size},
                    include_special_chars: {str(special_chars).lower()},
                    input_tests: [],
                    overflow_patterns: [],
                    security_implications: [],
                    performance_impact: {{
                        start_time: performance.now(),
                        input_time_per_field: [],
                        total_time: 0
                    }}
                }};

                // Generate test payload
                let basePayload = 'A'.repeat(Math.floor({payload_size} * 0.7));

                if ({str(special_chars).lower()}) {{
                    const specialChars = '!@#$%^&*()_+-=[]{{}}|;:,.<>?`~\\"\\'\\\\/\\n\\r\\t';
                    const sqlChars = "'; DROP TABLE users; --";
                    const xssChars = '<script>alert("XSS")</script>';
                    const unicodeChars = '\\u0000\\u0001\\u0002\\uFEFF\\u200B\\u200C\\u200D';

                    basePayload += specialChars.repeat(10) + sqlChars + xssChars + unicodeChars;
                }}

                // Ensure exact payload size
                const payload = basePayload.substring(0, {payload_size});

                // Find target input fields
                const inputs = document.querySelectorAll('{selector}');
                results.input_tests = [];

                if (inputs.length === 0) {{
                    results.error = 'No input fields found matching selector';
                    return results;
                }}

                inputs.forEach((input, index) => {{
                    const fieldStart = performance.now();

                    const inputTest = {{
                        input_index: index,
                        input_type: input.type || input.tagName.toLowerCase(),
                        input_id: input.id || '',
                        input_name: input.name || '',
                        original_value: input.value || '',
                        maxlength_attribute: input.getAttribute('maxlength'),
                        test_results: {{
                            payload_accepted: false,
                            actual_length: 0,
                            truncated: false,
                            validation_triggered: false,
                            error_messages: [],
                            performance_degradation: false
                        }},
                        security_findings: []
                    }};

                    try {{
                        // Store original event listeners to detect changes
                        const originalOninput = input.oninput;
                        const originalOnchange = input.onchange;

                        // Attempt to set the large payload
                        input.focus();
                        input.value = payload;

                        // Trigger input events
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));

                        // Check actual accepted value
                        inputTest.test_results.payload_accepted = input.value.length > 0;
                        inputTest.test_results.actual_length = input.value.length;
                        inputTest.test_results.truncated = input.value.length < payload.length;

                        // Check for validation responses
                        const validationMessage = input.validationMessage;
                        if (validationMessage) {{
                            inputTest.test_results.validation_triggered = true;
                            inputTest.test_results.error_messages.push(validationMessage);
                        }}

                        // Check for form validation
                        const form = input.closest('form');
                        if (form) {{
                            const formValid = form.checkValidity();
                            if (!formValid) {{
                                inputTest.test_results.validation_triggered = true;
                            }}
                        }}

                        // Security analysis
                        if (input.value.includes('<script>')) {{
                            inputTest.security_findings.push({{
                                type: 'xss_payload_accepted',
                                severity: 'critical',
                                description: 'Input accepts script tags without sanitization'
                            }});
                        }}

                        if (input.value.includes('DROP TABLE')) {{
                            inputTest.security_findings.push({{
                                type: 'sql_injection_payload',
                                severity: 'critical',
                                description: 'Input accepts SQL injection patterns'
                            }});
                        }}

                        if (input.value.includes('\\u0000')) {{
                            inputTest.security_findings.push({{
                                type: 'null_byte_injection',
                                severity: 'high',
                                description: 'Input accepts null bytes and control characters'
                            }});
                        }}

                        // Check for buffer overflow patterns
                        if (inputTest.test_results.actual_length > 100000) {{
                            results.overflow_patterns.push({{
                                input_index: index,
                                type: 'potential_buffer_overflow',
                                accepted_length: inputTest.test_results.actual_length,
                                description: 'Input accepts extremely large payloads'
                            }});
                        }}

                        // Performance impact check
                        const fieldEnd = performance.now();
                        const fieldDuration = fieldEnd - fieldStart;
                        results.performance_impact.input_time_per_field.push(fieldDuration);

                        if (fieldDuration > 100) {{ // More than 100ms is significant
                            inputTest.test_results.performance_degradation = true;
                        }}

                    }} catch (error) {{
                        inputTest.test_results.error_messages.push({{
                            type: 'exception',
                            message: error.message
                        }});
                    }}

                    results.input_tests.push(inputTest);
                }});

                // Aggregate security implications
                const allSecurityFindings = results.input_tests.flatMap(test => test.security_findings);
                const criticalFindings = allSecurityFindings.filter(f => f.severity === 'critical');
                const highFindings = allSecurityFindings.filter(f => f.severity === 'high');

                if (criticalFindings.length > 0) {{
                    results.security_implications.push({{
                        risk_level: 'critical',
                        count: criticalFindings.length,
                        description: 'Critical security vulnerabilities detected',
                        recommendation: 'Implement immediate input sanitization and validation'
                    }});
                }}

                if (highFindings.length > 0) {{
                    results.security_implications.push({{
                        risk_level: 'high',
                        count: highFindings.length,
                        description: 'High-risk input handling detected',
                        recommendation: 'Review and strengthen input validation'
                    }});
                }}

                // Calculate total performance impact
                results.performance_impact.total_time = performance.now() - results.performance_impact.start_time;

                return results;
            }})()
            """

            overflow_result = client.send_command('Runtime.evaluate', {
                'expression': input_overflow_js,
                'returnByValue': True
            })

            overflow_data = {
                "input_overflow_results": overflow_result.get('result', {}).get('value', {}),
                "test_parameters": {
                    "selector": selector,
                    "payload_size": payload_size,
                    "special_chars": special_chars
                }
            }

            track_endpoint_usage('input_overflow', [CDPDomain.DOM, CDPDomain.INPUT], {
                'selector': selector,
                'payload_size': payload_size,
                'inputs_tested': len(overflow_data.get('input_overflow_results', {}).get('input_tests', []))
            })

            return jsonify(create_success_response(overflow_data, 'input_overflow', [CDPDomain.DOM, CDPDomain.INPUT]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('input_overflow', e, {'selector': selector}, 'input_overflow')


@stress_testing_advanced_routes.route('/cdp/stress/storage_flood', methods=['POST'])
@require_domains([CDPDomain.RUNTIME])
def storage_flood():
    """
    Test browser storage limits with data flooding

    @route POST /cdp/stress/storage_flood
    @body {string} [type=localStorage] - Storage type (localStorage, sessionStorage, indexedDB)
    @body {boolean} [fill_to_limit=true] - Fill until storage limit reached
    @body {boolean} [oversized_values=true] - Use oversized values to test limits
    @returns {object} Storage flood results with capacity limits and performance impact
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            storage_type = data.get('type', 'localStorage')
            fill_to_limit = data.get('fill_to_limit', True)
            oversized_values = data.get('oversized_values', True)

            client.send_command('Runtime.enable')

            storage_flood_js = f"""
            (() => {{
                const results = {{
                    storage_type: '{storage_type}',
                    fill_to_limit: {str(fill_to_limit).lower()},
                    oversized_values: {str(oversized_values).lower()},
                    storage_analysis: {{
                        initial_items: 0,
                        items_added: 0,
                        bytes_stored: 0,
                        storage_limit_reached: false,
                        quota_exceeded_errors: 0
                    }},
                    performance_metrics: {{
                        start_time: performance.now(),
                        operation_times: [],
                        total_time: 0,
                        operations_per_second: 0
                    }},
                    limit_discovery: {{
                        max_key_length: 0,
                        max_value_length: 0,
                        estimated_total_capacity: 0,
                        actual_capacity_used: 0
                    }},
                    errors: []
                }};

                let storage;

                // Select storage mechanism
                try {{
                    if ('{storage_type}' === 'localStorage') {{
                        storage = localStorage;
                        results.storage_analysis.initial_items = localStorage.length;
                    }} else if ('{storage_type}' === 'sessionStorage') {{
                        storage = sessionStorage;
                        results.storage_analysis.initial_items = sessionStorage.length;
                    }} else {{
                        results.errors.push({{
                            type: 'unsupported_storage',
                            message: 'Storage type not supported in this test'
                        }});
                        return results;
                    }}
                }} catch (error) {{
                    results.errors.push({{
                        type: 'storage_access_error',
                        message: error.message
                    }});
                    return results;
                }}

                // Generate test data
                const generateValue = (size) => {{
                    if ({str(oversized_values).lower()}) {{
                        // Include various data types to test serialization
                        const baseData = 'X'.repeat(Math.floor(size * 0.8));
                        const jsonData = JSON.stringify({{
                            text: baseData,
                            number: Math.random() * 1000000,
                            array: new Array(100).fill(Math.random()),
                            object: {{ nested: {{ deep: {{ value: 'test' }} }} }},
                            special: '\\u0000\\uFEFF\\u200B"\\'\\\\'
                        }});
                        return jsonData.substring(0, size);
                    }} else {{
                        return 'test_data_' + 'A'.repeat(size - 10);
                    }}
                }};

                let itemIndex = 0;
                let totalBytes = 0;

                // Storage flooding loop
                const floodStorage = () => {{
                    const operationStart = performance.now();

                    try {{
                        // Progressive size testing
                        let valueSize = 1024; // Start with 1KB

                        if ({str(oversized_values).lower()}) {{
                            // Exponentially increase size to find limits
                            valueSize = Math.min(1024 * Math.pow(2, Math.floor(itemIndex / 10)), 1024 * 1024); // Up to 1MB
                        }}

                        const key = `stress_test_key_${{itemIndex}}_${{Date.now()}}`;
                        const value = generateValue(valueSize);

                        // Test key length limits
                        if (key.length > results.limit_discovery.max_key_length) {{
                            results.limit_discovery.max_key_length = key.length;
                        }}

                        if (value.length > results.limit_discovery.max_value_length) {{
                            results.limit_discovery.max_value_length = value.length;
                        }}

                        // Attempt storage
                        storage.setItem(key, value);

                        // Verify storage
                        const retrieved = storage.getItem(key);
                        if (retrieved !== value) {{
                            results.errors.push({{
                                type: 'data_corruption',
                                item_index: itemIndex,
                                message: 'Stored value differs from retrieved value'
                            }});
                        }}

                        itemIndex++;
                        totalBytes += key.length + value.length;
                        results.storage_analysis.items_added++;
                        results.storage_analysis.bytes_stored = totalBytes;

                        const operationEnd = performance.now();
                        results.performance_metrics.operation_times.push(operationEnd - operationStart);

                        // Check if we should continue
                        if ({str(fill_to_limit).lower()} &&
                            (itemIndex < 10000) && // Safety limit
                            !results.storage_analysis.storage_limit_reached) {{

                            // Use setTimeout to prevent blocking
                            setTimeout(floodStorage, 1);
                        }} else {{
                            finalizeTest();
                        }}

                    }} catch (error) {{
                        const operationEnd = performance.now();
                        results.performance_metrics.operation_times.push(operationEnd - operationStart);

                        if (error.name === 'QuotaExceededError' ||
                            error.message.includes('quota') ||
                            error.message.includes('storage')) {{

                            results.storage_analysis.quota_exceeded_errors++;
                            results.storage_analysis.storage_limit_reached = true;

                            results.errors.push({{
                                type: 'quota_exceeded',
                                item_index: itemIndex,
                                bytes_when_failed: totalBytes,
                                message: error.message
                            }});

                            finalizeTest();
                        }} else {{
                            results.errors.push({{
                                type: 'storage_error',
                                item_index: itemIndex,
                                message: error.message
                            }});

                            // Try to continue with smaller data
                            if (itemIndex < 100) {{
                                setTimeout(floodStorage, 10);
                            }} else {{
                                finalizeTest();
                            }}
                        }}
                    }}
                }};

                const finalizeTest = () => {{
                    results.performance_metrics.total_time = performance.now() - results.performance_metrics.start_time;

                    if (results.performance_metrics.operation_times.length > 0) {{
                        results.performance_metrics.operations_per_second =
                            results.performance_metrics.operation_times.length / (results.performance_metrics.total_time / 1000);
                    }}

                    // Estimate storage characteristics
                    if (results.storage_analysis.storage_limit_reached) {{
                        results.limit_discovery.estimated_total_capacity = totalBytes;
                    }}

                    results.limit_discovery.actual_capacity_used = totalBytes;

                    // Calculate storage efficiency
                    const avgOperationTime = results.performance_metrics.operation_times.length > 0
                        ? results.performance_metrics.operation_times.reduce((a, b) => a + b, 0) / results.performance_metrics.operation_times.length
                        : 0;

                    results.performance_metrics.average_operation_time_ms = avgOperationTime;

                    // Test cleanup capability
                    try {{
                        // Remove test items
                        for (let i = 0; i < Math.min(itemIndex, 10); i++) {{
                            const testKey = Object.keys(storage).find(key => key.startsWith('stress_test_key_'));
                            if (testKey) {{
                                storage.removeItem(testKey);
                            }}
                        }}
                    }} catch (cleanupError) {{
                        results.errors.push({{
                            type: 'cleanup_error',
                            message: cleanupError.message
                        }});
                    }}
                }};

                // Start the storage flood
                floodStorage();

                // Return results after completion
                return new Promise(resolve => {{
                    const checkCompletion = () => {{
                        if (results.storage_analysis.storage_limit_reached ||
                            results.performance_metrics.total_time > 0 ||
                            results.errors.length > 10) {{
                            setTimeout(() => resolve(results), 100);
                        }} else {{
                            setTimeout(checkCompletion, 200);
                        }}
                    }};
                    setTimeout(checkCompletion, 500);
                }});
            }})()
            """

            storage_result = client.send_command('Runtime.evaluate', {
                'expression': storage_flood_js,
                'returnByValue': True,
                'awaitPromise': True
            })

            storage_data = {
                "storage_flood_results": storage_result.get('result', {}).get('value', {}),
                "test_parameters": {
                    "storage_type": storage_type,
                    "fill_to_limit": fill_to_limit,
                    "oversized_values": oversized_values
                }
            }

            track_endpoint_usage('storage_flood', [CDPDomain.RUNTIME], {
                'storage_type': storage_type,
                'fill_to_limit': fill_to_limit,
                'bytes_stored': storage_data.get('storage_flood_results', {}).get('storage_analysis', {}).get('bytes_stored', 0)
            })

            return jsonify(create_success_response(storage_data, 'storage_flood', [CDPDomain.RUNTIME]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('storage_flood', e, {'storage_type': storage_type}, 'storage_flood')


@stress_testing_advanced_routes.route('/cdp/stress/chaos_monkey', methods=['POST'])
@require_domains([CDPDomain.DOM, CDPDomain.INPUT, CDPDomain.RUNTIME])
def chaos_monkey():
    """
    Random unpredictable interactions to test system resilience

    @route POST /cdp/stress/chaos_monkey
    @body {number} [duration=30000] - Chaos duration in milliseconds
    @body {boolean} [random_clicks=true] - Perform random clicking
    @body {boolean} [random_inputs=true] - Fill inputs with random data
    @body {boolean} [unpredictable=true] - Enable truly chaotic behavior
    @returns {object} Chaos monkey results with system stability analysis and discovered issues
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            duration = data.get('duration', 30000)
            random_clicks = data.get('random_clicks', True)
            random_inputs = data.get('random_inputs', True)
            unpredictable = data.get('unpredictable', True)

            client.send_command('DOM.enable')
            client.send_command('Runtime.enable')

            chaos_js = f"""
            (() => {{
                const results = {{
                    duration_ms: {duration},
                    random_clicks_enabled: {str(random_clicks).lower()},
                    random_inputs_enabled: {str(random_inputs).lower()},
                    unpredictable_mode: {str(unpredictable).lower()},
                    chaos_activities: [],
                    system_stability: {{
                        errors_triggered: 0,
                        console_errors: [],
                        dom_mutations: 0,
                        performance_degradation: false,
                        memory_leaks_detected: false
                    }},
                    discovered_issues: [],
                    interaction_stats: {{
                        total_actions: 0,
                        successful_actions: 0,
                        failed_actions: 0,
                        elements_interacted: new Set()
                    }},
                    performance_monitoring: {{
                        initial_memory: null,
                        peak_memory: null,
                        frame_drops: 0,
                        long_tasks: 0
                    }}
                }};

                // Capture initial state
                if (performance.memory) {{
                    results.performance_monitoring.initial_memory = {{
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize
                    }};
                }}

                // Set up error monitoring
                const originalError = window.onerror;
                window.onerror = (message, source, lineno, colno, error) => {{
                    results.system_stability.errors_triggered++;
                    results.system_stability.console_errors.push({{
                        message: message,
                        source: source,
                        line: lineno,
                        column: colno,
                        timestamp: Date.now()
                    }});

                    if (originalError) {{
                        return originalError(message, source, lineno, colno, error);
                    }}
                }};

                // Set up DOM mutation monitoring
                let mutationCount = 0;
                const observer = new MutationObserver((mutations) => {{
                    mutationCount += mutations.length;
                    results.system_stability.dom_mutations = mutationCount;
                }});

                observer.observe(document.body, {{
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeOldValue: true
                }});

                // Chaos utility functions
                const getRandomElement = (selector) => {{
                    const elements = document.querySelectorAll(selector);
                    return elements[Math.floor(Math.random() * elements.length)];
                }};

                const generateRandomText = (length = 50) => {{
                    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{{}}|;:,.<>?';
                    if ({str(unpredictable).lower()}) {{
                        // Add more chaotic characters
                        chars += '\\n\\r\\t\\u0000\\u0001\\u0002\\uFEFF\\u200B<script>alert("chaos")</script>';
                    }}

                    let result = '';
                    for (let i = 0; i < length; i++) {{
                        result += chars.charAt(Math.floor(Math.random() * chars.length));
                    }}
                    return result;
                }};

                const performChaosAction = () => {{
                    const actionStart = performance.now();
                    let actionType = '';
                    let success = false;
                    let error = null;

                    try {{
                        const actions = [];

                        if ({str(random_clicks).lower()}) {{
                            actions.push('click', 'doubleclick', 'rightclick');
                        }}

                        if ({str(random_inputs).lower()}) {{
                            actions.push('input', 'select', 'focus');
                        }}

                        if ({str(unpredictable).lower()}) {{
                            actions.push('scroll', 'resize', 'navigate', 'dommanipulation');
                        }}

                        actionType = actions[Math.floor(Math.random() * actions.length)];
                        const actionId = `chaos_${{Date.now()}}_${{Math.random()}}`;

                        switch (actionType) {{
                            case 'click':
                            case 'doubleclick':
                            case 'rightclick':
                                const clickableElements = 'button, a, input, select, [onclick], [role="button"], div, span';
                                const clickTarget = getRandomElement(clickableElements);
                                if (clickTarget) {{
                                    if (actionType === 'doubleclick') {{
                                        clickTarget.dispatchEvent(new MouseEvent('dblclick', {{ bubbles: true }}));
                                    }} else if (actionType === 'rightclick') {{
                                        clickTarget.dispatchEvent(new MouseEvent('contextmenu', {{ bubbles: true }}));
                                    }} else {{
                                        clickTarget.click();
                                    }}
                                    results.interaction_stats.elements_interacted.add(clickTarget.tagName);
                                    success = true;
                                }}
                                break;

                            case 'input':
                                const inputTarget = getRandomElement('input, textarea, select, [contenteditable]');
                                if (inputTarget) {{
                                    if (inputTarget.tagName === 'SELECT') {{
                                        const options = inputTarget.querySelectorAll('option');
                                        if (options.length > 0) {{
                                            inputTarget.selectedIndex = Math.floor(Math.random() * options.length);
                                        }}
                                    }} else {{
                                        const randomLength = Math.floor(Math.random() * 500) + 10;
                                        inputTarget.value = generateRandomText(randomLength);
                                        inputTarget.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    }}
                                    results.interaction_stats.elements_interacted.add(inputTarget.tagName);
                                    success = true;
                                }}
                                break;

                            case 'focus':
                                const focusTarget = getRandomElement('input, button, select, textarea, a');
                                if (focusTarget) {{
                                    focusTarget.focus();
                                    success = true;
                                }}
                                break;

                            case 'scroll':
                                const scrollAmount = Math.floor(Math.random() * 1000) - 500;
                                window.scrollBy(0, scrollAmount);
                                success = true;
                                break;

                            case 'resize':
                                // Simulate window events
                                window.dispatchEvent(new Event('resize'));
                                success = true;
                                break;

                            case 'navigate':
                                // Simulate navigation without actually navigating
                                window.history.pushState({{ chaos: true }}, '', '#chaos_' + Math.random());
                                success = true;
                                break;

                            case 'dommanipulation':
                                if ({str(unpredictable).lower()}) {{
                                    const manipulationTarget = getRandomElement('div, span, p');
                                    if (manipulationTarget) {{
                                        const actions = ['addClass', 'removeClass', 'changeText', 'changeStyle'];
                                        const domAction = actions[Math.floor(Math.random() * actions.length)];

                                        switch (domAction) {{
                                            case 'addClass':
                                                manipulationTarget.classList.add('chaos-test-class');
                                                break;
                                            case 'removeClass':
                                                if (manipulationTarget.classList.length > 0) {{
                                                    manipulationTarget.classList.remove(manipulationTarget.classList[0]);
                                                }}
                                                break;
                                            case 'changeText':
                                                if (manipulationTarget.childNodes.length === 1 && manipulationTarget.childNodes[0].nodeType === 3) {{
                                                    manipulationTarget.textContent = 'CHAOS: ' + generateRandomText(20);
                                                }}
                                                break;
                                            case 'changeStyle':
                                                manipulationTarget.style.backgroundColor = `hsl(${{Math.floor(Math.random() * 360)}}, 50%, 50%)`;
                                                break;
                                        }}
                                        success = true;
                                    }}
                                }}
                                break;
                        }}

                        results.interaction_stats.total_actions++;
                        if (success) {{
                            results.interaction_stats.successful_actions++;
                        }} else {{
                            results.interaction_stats.failed_actions++;
                        }}

                    }} catch (e) {{
                        error = e.message;
                        results.interaction_stats.failed_actions++;
                        results.system_stability.errors_triggered++;
                    }}

                    const actionEnd = performance.now();
                    const actionDuration = actionEnd - actionStart;

                    results.chaos_activities.push({{
                        action_id: `chaos_${{Date.now()}}_${{Math.random()}}`,
                        action_type: actionType,
                        success: success,
                        duration_ms: actionDuration,
                        error: error,
                        timestamp: Date.now()
                    }});

                    // Monitor for performance issues
                    if (actionDuration > 50) {{ // Slow action
                        results.performance_monitoring.long_tasks++;
                    }}

                    // Check memory usage
                    if (performance.memory) {{
                        const currentMemory = {{
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize
                        }};

                        if (!results.performance_monitoring.peak_memory ||
                            currentMemory.used > results.performance_monitoring.peak_memory.used) {{
                            results.performance_monitoring.peak_memory = currentMemory;
                        }}

                        // Detect potential memory leaks
                        if (results.performance_monitoring.initial_memory &&
                            currentMemory.used > results.performance_monitoring.initial_memory.used * 2) {{
                            results.system_stability.memory_leaks_detected = true;
                        }}
                    }}
                }};

                // Start chaos monkey
                const chaosInterval = setInterval(() => {{
                    performChaosAction();

                    // Random delay between actions
                    const nextDelay = Math.floor(Math.random() * 200) + 50;
                    setTimeout(() => {{}}, nextDelay);
                }}, 100);

                // Stop chaos after duration
                setTimeout(() => {{
                    clearInterval(chaosInterval);
                    observer.disconnect();

                    // Restore original error handler
                    window.onerror = originalError;

                    // Final analysis
                    results.interaction_stats.elements_interacted = Array.from(results.interaction_stats.elements_interacted);

                    // Check for performance degradation
                    if (results.performance_monitoring.long_tasks > results.interaction_stats.total_actions * 0.1) {{
                        results.system_stability.performance_degradation = true;
                        results.discovered_issues.push({{
                            type: 'performance_degradation',
                            severity: 'medium',
                            description: 'Significant number of slow operations detected',
                            metric: `${{results.performance_monitoring.long_tasks}} slow tasks out of ${{results.interaction_stats.total_actions}} total`
                        }});
                    }}

                    // Check error rate
                    const errorRate = results.system_stability.errors_triggered / results.interaction_stats.total_actions;
                    if (errorRate > 0.1) {{
                        results.discovered_issues.push({{
                            type: 'high_error_rate',
                            severity: 'high',
                            description: 'High error rate during chaos testing',
                            metric: `${{Math.round(errorRate * 100)}}% error rate`
                        }});
                    }}

                    // Check DOM stability
                    if (results.system_stability.dom_mutations > results.interaction_stats.total_actions * 5) {{
                        results.discovered_issues.push({{
                            type: 'excessive_dom_mutations',
                            severity: 'medium',
                            description: 'Excessive DOM mutations detected',
                            metric: `${{results.system_stability.dom_mutations}} mutations for ${{results.interaction_stats.total_actions}} actions`
                        }});
                    }}

                }}, {duration});

                // Return results after chaos completes
                return new Promise(resolve => {{
                    setTimeout(() => {{
                        resolve(results);
                    }}, {duration} + 1000);
                }});
            }})()
            """

            chaos_result = client.send_command('Runtime.evaluate', {
                'expression': chaos_js,
                'returnByValue': True,
                'awaitPromise': True
            })

            chaos_data = {
                "chaos_monkey_results": chaos_result.get('result', {}).get('value', {}),
                "test_parameters": {
                    "duration": duration,
                    "random_clicks": random_clicks,
                    "random_inputs": random_inputs,
                    "unpredictable": unpredictable
                }
            }

            track_endpoint_usage('chaos_monkey', [CDPDomain.DOM, CDPDomain.INPUT, CDPDomain.RUNTIME], {
                'duration': duration,
                'random_clicks': random_clicks,
                'total_actions': chaos_data.get('chaos_monkey_results', {}).get('interaction_stats', {}).get('total_actions', 0)
            })

            return jsonify(create_success_response(chaos_data, 'chaos_monkey', [CDPDomain.DOM, CDPDomain.INPUT, CDPDomain.RUNTIME]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('chaos_monkey', e, {'duration': duration}, 'chaos_monkey')


@stress_testing_advanced_routes.route('/cdp/stress/race_conditions', methods=['POST'])
@require_domains([CDPDomain.RUNTIME])
def race_conditions():
    """
    Trigger race conditions through concurrent operations

    @route POST /cdp/stress/race_conditions
    @body {boolean} [async_operations=true] - Test async operation races
    @body {boolean} [timing_attacks=true] - Perform timing-based attacks
    @body {boolean} [concurrent_mutations=true] - Test concurrent DOM mutations
    @returns {object} Race condition test results with timing analysis and concurrency issues
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            async_operations = data.get('async_operations', True)
            timing_attacks = data.get('timing_attacks', True)
            concurrent_mutations = data.get('concurrent_mutations', True)

            client.send_command('Runtime.enable')

            race_conditions_js = f"""
            (() => {{
                const results = {{
                    async_operations_test: {str(async_operations).lower()},
                    timing_attacks_test: {str(timing_attacks).lower()},
                    concurrent_mutations_test: {str(concurrent_mutations).lower()},
                    race_scenarios: [],
                    timing_analysis: {{
                        operation_timings: [],
                        timing_inconsistencies: [],
                        race_conditions_detected: 0
                    }},
                    concurrency_issues: [],
                    async_operation_results: [],
                    performance_impact: {{
                        start_time: performance.now(),
                        end_time: null,
                        total_duration: 0
                    }}
                }};

                let scenarioIndex = 0;

                // Async operations race testing
                if ({str(async_operations).lower()}) {{
                    const asyncTests = [];

                    // Test 1: Promise race conditions
                    const promiseRaceTest = new Promise((resolve) => {{
                        let sharedState = {{ value: 0, updates: [] }};
                        const promises = [];

                        for (let i = 0; i < 10; i++) {{
                            promises.push(new Promise((resolveInner) => {{
                                setTimeout(() => {{
                                    const oldValue = sharedState.value;
                                    // Simulate async work
                                    setTimeout(() => {{
                                        sharedState.value = oldValue + 1;
                                        sharedState.updates.push({{
                                            thread: i,
                                            oldValue: oldValue,
                                            newValue: sharedState.value,
                                            timestamp: performance.now()
                                        }});
                                        resolveInner(sharedState.value);
                                    }}, Math.random() * 50);
                                }}, Math.random() * 100);
                            }}));
                        }}

                        Promise.all(promises).then((values) => {{
                            const expectedValue = 10;
                            const actualValue = sharedState.value;

                            results.race_scenarios.push({{
                                scenario_index: scenarioIndex++,
                                test_type: 'promise_race_condition',
                                expected_value: expectedValue,
                                actual_value: actualValue,
                                race_detected: actualValue !== expectedValue,
                                individual_results: values,
                                update_sequence: sharedState.updates,
                                description: 'Multiple promises updating shared state concurrently'
                            }});

                            if (actualValue !== expectedValue) {{
                                results.timing_analysis.race_conditions_detected++;
                                results.concurrency_issues.push({{
                                    type: 'promise_race_condition',
                                    severity: 'medium',
                                    description: `Expected ${{expectedValue}}, got ${{actualValue}} due to race condition`
                                }});
                            }}

                            resolve();
                        }});
                    }});

                    asyncTests.push(promiseRaceTest);

                    // Test 2: setTimeout race conditions
                    const timeoutRaceTest = new Promise((resolve) => {{
                        let counter = 0;
                        let results_array = [];
                        let completedOperations = 0;

                        for (let i = 0; i < 5; i++) {{
                            setTimeout(() => {{
                                const operationStart = performance.now();

                                // Read-modify-write operation with intentional delay
                                const currentValue = counter;
                                setTimeout(() => {{
                                    counter = currentValue + 1;
                                    const operationEnd = performance.now();

                                    results_array.push({{
                                        operation_id: i,
                                        read_value: currentValue,
                                        written_value: counter,
                                        duration: operationEnd - operationStart,
                                        timestamp: operationEnd
                                    }});

                                    completedOperations++;
                                    if (completedOperations === 5) {{
                                        results.race_scenarios.push({{
                                            scenario_index: scenarioIndex++,
                                            test_type: 'timeout_race_condition',
                                            expected_final_counter: 5,
                                            actual_final_counter: counter,
                                            race_detected: counter !== 5,
                                            operation_details: results_array,
                                            description: 'setTimeout operations racing to update counter'
                                        }});

                                        if (counter !== 5) {{
                                            results.timing_analysis.race_conditions_detected++;
                                        }}

                                        resolve();
                                    }}
                                }}, Math.random() * 30);
                            }}, i * 10);
                        }}
                    }});

                    asyncTests.push(timeoutRaceTest);

                    // Wait for all async tests
                    Promise.all(asyncTests).then(() => {{
                        // Continue with other tests
                    }});
                }}

                // Timing attack simulation
                if ({str(timing_attacks).lower()}) {{
                    const timingTests = [];

                    // Test timing-based information disclosure
                    const timingAttackTest = () => {{
                        const timingResults = [];

                        for (let i = 0; i < 100; i++) {{
                            const start = performance.now();

                            // Simulate operation that might leak timing information
                            const testValue = Math.random() > 0.5 ? 'correct' : 'incorrect';

                            if (testValue === 'correct') {{
                                // Simulate slightly longer processing for "correct" values
                                for (let j = 0; j < 1000; j++) {{
                                    Math.sqrt(j);
                                }}
                            }} else {{
                                // Simulate shorter processing for "incorrect" values
                                for (let j = 0; j < 800; j++) {{
                                    Math.sqrt(j);
                                }}
                            }}

                            const end = performance.now();
                            const duration = end - start;

                            timingResults.push({{
                                test_iteration: i,
                                test_value: testValue,
                                operation_duration: duration,
                                timestamp: end
                            }});

                            results.timing_analysis.operation_timings.push({{
                                operation_type: 'timing_attack_simulation',
                                duration: duration,
                                value_type: testValue
                            }});
                        }}

                        // Analyze timing patterns
                        const correctTimings = timingResults.filter(r => r.test_value === 'correct').map(r => r.operation_duration);
                        const incorrectTimings = timingResults.filter(r => r.test_value === 'incorrect').map(r => r.operation_duration);

                        if (correctTimings.length > 0 && incorrectTimings.length > 0) {{
                            const correctAvg = correctTimings.reduce((a, b) => a + b, 0) / correctTimings.length;
                            const incorrectAvg = incorrectTimings.reduce((a, b) => a + b, 0) / incorrectTimings.length;
                            const timingDifference = Math.abs(correctAvg - incorrectAvg);

                            if (timingDifference > 0.1) {{ // 0.1ms difference threshold
                                results.timing_analysis.timing_inconsistencies.push({{
                                    type: 'timing_information_leak',
                                    correct_avg_timing: correctAvg,
                                    incorrect_avg_timing: incorrectAvg,
                                    timing_difference_ms: timingDifference,
                                    severity: timingDifference > 1 ? 'high' : 'medium',
                                    description: 'Timing difference detected between correct and incorrect operations'
                                }});
                            }}
                        }}

                        results.race_scenarios.push({{
                            scenario_index: scenarioIndex++,
                            test_type: 'timing_attack_simulation',
                            iterations: 100,
                            timing_difference_detected: results.timing_analysis.timing_inconsistencies.length > 0,
                            average_timings: {{
                                correct: correctTimings.length > 0 ? correctTimings.reduce((a, b) => a + b, 0) / correctTimings.length : 0,
                                incorrect: incorrectTimings.length > 0 ? incorrectTimings.reduce((a, b) => a + b, 0) / incorrectTimings.length : 0
                            }},
                            description: 'Timing-based information disclosure test'
                        }});
                    }};

                    timingAttackTest();
                }}

                // Concurrent DOM mutations
                if ({str(concurrent_mutations).lower()}) {{
                    const mutationTests = [];

                    const domMutationRaceTest = new Promise((resolve) => {{
                        // Create test container
                        const testContainer = document.createElement('div');
                        testContainer.id = 'race-condition-test-container';
                        document.body.appendChild(testContainer);

                        let mutationCounter = 0;
                        let completedMutations = 0;
                        const totalMutations = 10;
                        const mutationResults = [];

                        // Set up mutation observer
                        const observer = new MutationObserver((mutations) => {{
                            mutations.forEach((mutation) => {{
                                mutationResults.push({{
                                    type: mutation.type,
                                    target: mutation.target.tagName,
                                    timestamp: performance.now(),
                                    added_nodes: mutation.addedNodes.length,
                                    removed_nodes: mutation.removedNodes.length
                                }});
                            }});
                        }});

                        observer.observe(testContainer, {{
                            childList: true,
                            subtree: true,
                            attributes: true
                        }});

                        // Concurrent DOM mutations
                        for (let i = 0; i < totalMutations; i++) {{
                            setTimeout(() => {{
                                const mutationStart = performance.now();

                                try {{
                                    // Race condition: multiple operations on same element
                                    const element = document.createElement('div');
                                    element.textContent = `Mutation ${{i}}`;
                                    element.id = `race-element-${{mutationCounter++}}`;

                                    testContainer.appendChild(element);

                                    // Immediate modification
                                    setTimeout(() => {{
                                        if (element.parentNode) {{
                                            element.style.backgroundColor = 'red';
                                            element.textContent += ' - Modified';
                                        }}
                                    }}, 1);

                                    // Conflicting operation
                                    setTimeout(() => {{
                                        if (element.parentNode) {{
                                            element.remove();
                                        }}
                                    }}, 5);

                                }} catch (error) {{
                                    results.concurrency_issues.push({{
                                        type: 'dom_mutation_error',
                                        severity: 'medium',
                                        description: error.message,
                                        mutation_index: i
                                    }});
                                }}

                                completedMutations++;
                                if (completedMutations === totalMutations) {{
                                    setTimeout(() => {{
                                        observer.disconnect();

                                        results.race_scenarios.push({{
                                            scenario_index: scenarioIndex++,
                                            test_type: 'concurrent_dom_mutations',
                                            mutations_attempted: totalMutations,
                                            mutations_observed: mutationResults.length,
                                            final_child_count: testContainer.children.length,
                                            race_detected: mutationResults.length !== totalMutations * 3, // Each operation should cause ~3 mutations
                                            mutation_details: mutationResults,
                                            description: 'Concurrent DOM mutations on shared container'
                                        }});

                                        // Cleanup
                                        if (testContainer.parentNode) {{
                                            testContainer.remove();
                                        }}

                                        resolve();
                                    }}, 100);
                                }}
                            }}, i * 10);
                        }}
                    }});

                    mutationTests.push(domMutationRaceTest);
                }}

                // Finalize results
                const finalizeResults = () => {{
                    results.performance_impact.end_time = performance.now();
                    results.performance_impact.total_duration =
                        results.performance_impact.end_time - results.performance_impact.start_time;

                    // Summary analysis
                    const totalRaceConditions = results.race_scenarios.filter(s => s.race_detected).length;
                    if (totalRaceConditions > 0) {{
                        results.concurrency_issues.push({{
                            type: 'race_conditions_summary',
                            severity: 'high',
                            description: `${{totalRaceConditions}} race conditions detected out of ${{results.race_scenarios.length}} scenarios`,
                            recommendation: 'Review concurrent operations and implement proper synchronization'
                        }});
                    }}
                }};

                // Return results after all tests complete
                return new Promise(resolve => {{
                    setTimeout(() => {{
                        finalizeResults();
                        resolve(results);
                    }}, 2000); // Allow time for all async operations
                }});
            }})()
            """

            race_result = client.send_command('Runtime.evaluate', {
                'expression': race_conditions_js,
                'returnByValue': True,
                'awaitPromise': True
            })

            race_data = {
                "race_conditions_results": race_result.get('result', {}).get('value', {}),
                "test_parameters": {
                    "async_operations": async_operations,
                    "timing_attacks": timing_attacks,
                    "concurrent_mutations": concurrent_mutations
                }
            }

            track_endpoint_usage('race_conditions', [CDPDomain.RUNTIME], {
                'async_operations': async_operations,
                'timing_attacks': timing_attacks,
                'race_scenarios': len(race_data.get('race_conditions_results', {}).get('race_scenarios', []))
            })

            return jsonify(create_success_response(race_data, 'race_conditions', [CDPDomain.RUNTIME]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('race_conditions', e,
                              {'async_operations': async_operations}, 'race_conditions')


@stress_testing_advanced_routes.route('/cdp/stress/full_assault', methods=['POST'])
@require_domains([CDPDomain.DOM, CDPDomain.INPUT, CDPDomain.RUNTIME, CDPDomain.MEMORY])
def full_assault():
    """
    Comprehensive multi-vector stress test combining all attack patterns

    @route POST /cdp/stress/full_assault
    @body {boolean} [memory=true] - Include memory stress testing
    @body {boolean} [cpu=true] - Include CPU intensive operations
    @body {boolean} [network=true] - Include network stress testing
    @body {boolean} [interactions=true] - Include UI interaction stress
    @body {number} [duration=15000] - Total assault duration in milliseconds
    @returns {object} Full assault results with comprehensive system stress analysis
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            memory = data.get('memory', True)
            cpu = data.get('cpu', True)
            network = data.get('network', True)
            interactions = data.get('interactions', True)
            duration = data.get('duration', 15000)

            client.send_command('DOM.enable')
            client.send_command('Runtime.enable')
            client.send_command('Memory.enable') if memory else None

            full_assault_js = f"""
            (() => {{
                const results = {{
                    assault_duration_ms: {duration},
                    attack_vectors: {{
                        memory_stress: {str(memory).lower()},
                        cpu_stress: {str(cpu).lower()},
                        network_stress: {str(network).lower()},
                        interaction_stress: {str(interactions).lower()}
                    }},
                    system_state: {{
                        initial: null,
                        during_assault: [],
                        final: null,
                        system_survived: true
                    }},
                    assault_phases: [],
                    critical_failures: [],
                    performance_degradation: {{
                        memory_growth: 0,
                        cpu_saturation: false,
                        ui_responsiveness_loss: 0,
                        frame_rate_impact: 0
                    }},
                    resilience_metrics: {{
                        error_recovery_rate: 0,
                        graceful_degradation: false,
                        stability_score: 0
                    }}
                }};

                // Capture initial system state
                const captureSystemState = (phase) => {{
                    const state = {{
                        timestamp: performance.now(),
                        phase: phase,
                        memory: performance.memory ? {{
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize,
                            limit: performance.memory.jsHeapSizeLimit
                        }} : null,
                        dom_nodes: document.querySelectorAll('*').length,
                        active_timers: 0, // Approximation
                        console_errors: 0
                    }};

                    if (phase === 'initial') {{
                        results.system_state.initial = state;
                    }} else if (phase === 'final') {{
                        results.system_state.final = state;
                    }} else {{
                        results.system_state.during_assault.push(state);
                    }}

                    return state;
                }};

                captureSystemState('initial');

                // Error tracking
                let errorCount = 0;
                const originalError = window.onerror;
                window.onerror = (message, source, lineno, colno, error) => {{
                    errorCount++;
                    if (errorCount > 10) {{ // Too many errors indicates system failure
                        results.system_state.system_survived = false;
                        results.critical_failures.push({{
                            type: 'error_cascade',
                            error_count: errorCount,
                            description: 'System overwhelmed by errors'
                        }});
                    }}
                    return originalError ? originalError(message, source, lineno, colno, error) : false;
                }};

                // Track assault progress
                let currentPhase = 0;
                const totalPhases = Object.values(results.attack_vectors).filter(v => v).length;

                // Memory assault phase
                if ({str(memory).lower()}) {{
                    const memoryAssault = () => {{
                        const phaseStart = performance.now();
                        currentPhase++;

                        const memoryHogs = [];
                        let allocatedBytes = 0;
                        const targetMB = 50; // Aggressive but not system-killing

                        try {{
                            for (let i = 0; i < 20; i++) {{
                                const chunk = new ArrayBuffer(targetMB * 1024 * 1024 / 20);
                                const view = new Uint8Array(chunk);
                                // Fill with data to ensure allocation
                                for (let j = 0; j < Math.min(view.length, 1000); j++) {{
                                    view[j] = Math.floor(Math.random() * 256);
                                }}
                                memoryHogs.push({{ chunk, view }});
                                allocatedBytes += chunk.byteLength;

                                // Yield periodically
                                if (i % 5 === 0) {{
                                    setTimeout(() => {{}}, 0);
                                }}
                            }}

                            const phaseEnd = performance.now();
                            results.assault_phases.push({{
                                phase: 'memory_assault',
                                duration: phaseEnd - phaseStart,
                                success: true,
                                allocated_bytes: allocatedBytes,
                                chunks_created: memoryHogs.length
                            }});

                            captureSystemState('memory_phase');

                        }} catch (error) {{
                            results.critical_failures.push({{
                                type: 'memory_allocation_failure',
                                phase: 'memory_assault',
                                error: error.message
                            }});
                        }}
                    }};

                    memoryAssault();
                }}

                // CPU assault phase
                if ({str(cpu).lower()}) {{
                    const cpuAssault = () => {{
                        const phaseStart = performance.now();
                        currentPhase++;

                        let operationsCompleted = 0;
                        const cpuBurnDuration = Math.min({duration} * 0.3, 5000); // Max 5 seconds of CPU burn

                        const intensiveComputation = () => {{
                            const start = performance.now();

                            while (performance.now() - start < 50 && performance.now() - phaseStart < cpuBurnDuration) {{
                                // CPU-intensive operations
                                for (let i = 0; i < 10000; i++) {{
                                    Math.sin(Math.random() * 1000) * Math.cos(Math.random() * 1000);
                                    Math.sqrt(Math.random() * 1000000);
                                }}

                                // Hash computation
                                let hash = 0;
                                const str = 'stress_test_' + operationsCompleted;
                                for (let i = 0; i < str.length; i++) {{
                                    const char = str.charCodeAt(i);
                                    hash = ((hash << 5) - hash) + char;
                                    hash = hash & hash;
                                }}

                                operationsCompleted++;
                            }}

                            if (performance.now() - phaseStart < cpuBurnDuration) {{
                                setTimeout(intensiveComputation, 10); // Brief yield
                            }} else {{
                                const phaseEnd = performance.now();
                                results.assault_phases.push({{
                                    phase: 'cpu_assault',
                                    duration: phaseEnd - phaseStart,
                                    success: true,
                                    operations_completed: operationsCompleted,
                                    cpu_saturation_detected: phaseEnd - phaseStart > cpuBurnDuration * 1.5
                                }});

                                if (phaseEnd - phaseStart > cpuBurnDuration * 1.5) {{
                                    results.performance_degradation.cpu_saturation = true;
                                }}

                                captureSystemState('cpu_phase');
                            }}
                        }};

                        intensiveComputation();
                    }};

                    setTimeout(cpuAssault, 1000);
                }}

                // Network assault phase (simulated)
                if ({str(network).lower()}) {{
                    const networkAssault = () => {{
                        const phaseStart = performance.now();
                        currentPhase++;

                        let requestsCompleted = 0;
                        let networkErrors = 0;
                        const maxRequests = 20;

                        // Simulate network stress with rapid requests
                        for (let i = 0; i < maxRequests; i++) {{
                            setTimeout(() => {{
                                try {{
                                    // Create fake network requests
                                    const xhr = new XMLHttpRequest();
                                    xhr.timeout = 100; // Short timeout to fail fast

                                    xhr.onload = () => requestsCompleted++;
                                    xhr.onerror = () => networkErrors++;
                                    xhr.ontimeout = () => networkErrors++;

                                    // Request to non-existent endpoint to simulate load
                                    xhr.open('GET', '/non-existent-stress-test-endpoint?id=' + i, true);
                                    xhr.send();

                                }} catch (error) {{
                                    networkErrors++;
                                }}

                                if (i === maxRequests - 1) {{
                                    setTimeout(() => {{
                                        const phaseEnd = performance.now();
                                        results.assault_phases.push({{
                                            phase: 'network_assault',
                                            duration: phaseEnd - phaseStart,
                                            success: true,
                                            requests_attempted: maxRequests,
                                            requests_completed: requestsCompleted,
                                            network_errors: networkErrors
                                        }});

                                        captureSystemState('network_phase');
                                    }}, 500);
                                }}
                            }}, i * 50);
                        }}
                    }};

                    setTimeout(networkAssault, 2000);
                }}

                // Interaction assault phase
                if ({str(interactions).lower()}) {{
                    const interactionAssault = () => {{
                        const phaseStart = performance.now();
                        currentPhase++;

                        let interactionCount = 0;
                        let interactionErrors = 0;
                        const maxInteractions = 100;

                        const performChaosInteraction = () => {{
                            try {{
                                const elements = document.querySelectorAll('button, a, input, div, span');
                                if (elements.length > 0) {{
                                    const randomElement = elements[Math.floor(Math.random() * elements.length)];

                                    // Random interaction
                                    const interactions = ['click', 'focus', 'mouseover', 'mouseout'];
                                    const randomInteraction = interactions[Math.floor(Math.random() * interactions.length)];

                                    switch (randomInteraction) {{
                                        case 'click':
                                            randomElement.click();
                                            break;
                                        case 'focus':
                                            if (randomElement.focus) randomElement.focus();
                                            break;
                                        case 'mouseover':
                                            randomElement.dispatchEvent(new MouseEvent('mouseover', {{ bubbles: true }}));
                                            break;
                                        case 'mouseout':
                                            randomElement.dispatchEvent(new MouseEvent('mouseout', {{ bubbles: true }}));
                                            break;
                                    }}
                                }}

                                interactionCount++;

                                if (interactionCount < maxInteractions && performance.now() - phaseStart < 3000) {{
                                    setTimeout(performChaosInteraction, Math.random() * 20 + 5);
                                }} else {{
                                    const phaseEnd = performance.now();
                                    results.assault_phases.push({{
                                        phase: 'interaction_assault',
                                        duration: phaseEnd - phaseStart,
                                        success: true,
                                        interactions_performed: interactionCount,
                                        interaction_errors: interactionErrors
                                    }});

                                    captureSystemState('interaction_phase');
                                }}

                            }} catch (error) {{
                                interactionErrors++;
                                if (interactionErrors > 5) {{
                                    results.critical_failures.push({{
                                        type: 'interaction_cascade_failure',
                                        phase: 'interaction_assault',
                                        error_count: interactionErrors
                                    }});
                                    return;
                                }}

                                // Continue despite errors
                                setTimeout(performChaosInteraction, 50);
                            }}
                        }};

                        performChaosInteraction();
                    }};

                    setTimeout(interactionAssault, 3000);
                }}

                // Finalize assault after duration
                setTimeout(() => {{
                    window.onerror = originalError;
                    captureSystemState('final');

                    // Calculate performance degradation
                    if (results.system_state.initial && results.system_state.final) {{
                        if (results.system_state.initial.memory && results.system_state.final.memory) {{
                            results.performance_degradation.memory_growth =
                                results.system_state.final.memory.used - results.system_state.initial.memory.used;
                        }}

                        // Check for UI responsiveness
                        const responsiveStart = performance.now();
                        setTimeout(() => {{
                            const responsiveEnd = performance.now();
                            const expectedDelay = 10;
                            const actualDelay = responsiveEnd - responsiveStart;
                            results.performance_degradation.ui_responsiveness_loss = actualDelay - expectedDelay;
                        }}, 10);
                    }}

                    // Calculate resilience metrics
                    const successfulPhases = results.assault_phases.filter(p => p.success).length;
                    const totalPhases = results.assault_phases.length;

                    results.resilience_metrics.error_recovery_rate =
                        totalPhases > 0 ? successfulPhases / totalPhases : 0;

                    results.resilience_metrics.graceful_degradation =
                        results.critical_failures.length === 0 && results.system_state.system_survived;

                    results.resilience_metrics.stability_score =
                        Math.round((results.resilience_metrics.error_recovery_rate * 0.6 +
                                   (results.resilience_metrics.graceful_degradation ? 0.4 : 0)) * 100);

                    // Final system health check
                    if (results.critical_failures.length > 3) {{
                        results.system_state.system_survived = false;
                    }}

                }}, {duration});

                // Return results after assault completes
                return new Promise(resolve => {{
                    setTimeout(() => {{
                        resolve(results);
                    }}, {duration} + 2000);
                }});
            }})()
            """

            assault_result = client.send_command('Runtime.evaluate', {
                'expression': full_assault_js,
                'returnByValue': True,
                'awaitPromise': True
            })

            assault_data = {
                "full_assault_results": assault_result.get('result', {}).get('value', {}),
                "test_parameters": {
                    "memory": memory,
                    "cpu": cpu,
                    "network": network,
                    "interactions": interactions,
                    "duration": duration
                }
            }

            track_endpoint_usage('full_assault', [CDPDomain.DOM, CDPDomain.INPUT, CDPDomain.RUNTIME, CDPDomain.MEMORY], {
                'memory': memory,
                'cpu': cpu,
                'duration': duration,
                'system_survived': assault_data.get('full_assault_results', {}).get('system_state', {}).get('system_survived', False)
            })

            return jsonify(create_success_response(assault_data, 'full_assault', [CDPDomain.DOM, CDPDomain.INPUT, CDPDomain.RUNTIME, CDPDomain.MEMORY]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('full_assault', e, {'duration': duration}, 'full_assault')