"""
Stress Testing Routes - Aggressive boundary testing and performance limits
Breaking point discovery through controlled chaos and structural assault testing
"""

import logging
from flask import Blueprint, jsonify, request
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter

logger = logging.getLogger(__name__)
stress_testing_routes = Blueprint('stress_testing', __name__)


def _parse_request_params(request, param_names):
    """Utility: Parse request parameters from GET/POST"""
    if request.method == 'GET':
        return {name: request.args.get(name) for name in param_names}
    else:
        data = request.get_json() or {}
        return {name: data.get(name) for name in param_names}


@stress_testing_routes.route('/cdp/stress/memory_bomb', methods=['POST'])
def memory_stress_test():
    """
    Memory allocation stress testing and memory bomb simulation

    @route POST /cdp/stress/memory_bomb
    @param {number} [allocation_mb] - Memory to allocate in MB (default: 10)
    @param {number} [iterations] - Number of allocation iterations (default: 5)
    @param {boolean} [monitor_performance] - Monitor memory performance during test
    @param {boolean} [gradual_release] - Gradually release memory (safer)
    @param {number} [max_allocation] - Maximum total allocation limit in MB
    @returns {object} Memory stress test results

    @example
    // Basic memory stress test
    POST {"allocation_mb": 10, "iterations": 3}

    // Aggressive memory testing with monitoring
    POST {
      "allocation_mb": 50,
      "iterations": 10,
      "monitor_performance": true,
      "max_allocation": 500
    }

    // Safe gradual memory test
    POST {
      "allocation_mb": 20,
      "iterations": 5,
      "gradual_release": true,
      "monitor_performance": true
    }
    """
    try:
        data = request.get_json() or {}
        allocation_mb = min(int(data.get('allocation_mb', 10)), 1000)  # Safety limit
        iterations = min(int(data.get('iterations', 5)), 50)  # Safety limit
        monitor_performance = data.get('monitor_performance', True)
        gradual_release = data.get('gradual_release', True)
        max_allocation = min(int(data.get('max_allocation', 500)), 2000)  # Hard safety limit

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Memory stress testing code
            memory_stress_code = f"""
                (() => {{
                    const stressResults = {{
                        test_parameters: {{
                            allocation_mb: {allocation_mb},
                            iterations: {iterations},
                            monitor_performance: {str(monitor_performance).lower()},
                            gradual_release: {str(gradual_release).lower()},
                            max_allocation_mb: {max_allocation}
                        }},
                        memory_snapshots: [],
                        allocation_results: [],
                        performance_impact: {{}},
                        warnings: [],
                        success: true
                    }};

                    // Get initial memory state
                    if (performance.memory) {{
                        stressResults.initial_memory = {{
                            used_heap: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                            total_heap: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
                            heap_limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100
                        }};
                    }}

                    const allocatedArrays = [];
                    let totalAllocatedMB = 0;
                    const startTime = performance.now();

                    try {{
                        for (let i = 0; i < {iterations}; i++) {{
                            const iterationStart = performance.now();

                            // Check safety limits
                            if (totalAllocatedMB + {allocation_mb} > {max_allocation}) {{
                                stressResults.warnings.push(`Iteration ${{i}}: Would exceed max allocation limit`);
                                break;
                            }}

                            // Allocate memory (1MB = ~1 million characters)
                            const arraySize = {allocation_mb} * 1024 * 1024;
                            try {{
                                const memoryArray = new Array(arraySize).fill('x');
                                allocatedArrays.push(memoryArray);
                                totalAllocatedMB += {allocation_mb};

                                const iterationEnd = performance.now();
                                const allocationResult = {{
                                    iteration: i + 1,
                                    allocated_mb: {allocation_mb},
                                    total_allocated_mb: totalAllocatedMB,
                                    allocation_time_ms: Math.round((iterationEnd - iterationStart) * 100) / 100,
                                    success: true
                                }};

                                // Memory snapshot during iteration
                                if ({str(monitor_performance).lower()} && performance.memory) {{
                                    allocationResult.memory_state = {{
                                        used_heap: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                                        total_heap: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
                                        heap_usage_percent: Math.round((performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 10000) / 100
                                    }};
                                }}

                                stressResults.allocation_results.push(allocationResult);

                                // Gradual release if enabled
                                if ({str(gradual_release).lower()} && i > 0 && i % 2 === 0) {{
                                    const releasedArray = allocatedArrays.shift();
                                    if (releasedArray) {{
                                        totalAllocatedMB -= {allocation_mb};
                                        stressResults.warnings.push(`Iteration ${{i}}: Released memory block to prevent overflow`);
                                    }}
                                }}

                            }} catch (allocationError) {{
                                stressResults.allocation_results.push({{
                                    iteration: i + 1,
                                    allocated_mb: 0,
                                    error: allocationError.message,
                                    success: false
                                }});
                                stressResults.warnings.push(`Iteration ${{i}}: Memory allocation failed - ${{allocationError.message}}`);
                                break;
                            }}
                        }}

                        const endTime = performance.now();
                        stressResults.total_test_time_ms = Math.round((endTime - startTime) * 100) / 100;

                        // Final memory state
                        if (performance.memory) {{
                            stressResults.final_memory = {{
                                used_heap: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                                total_heap: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
                                heap_limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100
                            }};

                            stressResults.memory_delta = {{
                                heap_increase_mb: Math.round((stressResults.final_memory.used_heap - stressResults.initial_memory.used_heap) * 100) / 100,
                                heap_usage_change_percent: Math.round(((stressResults.final_memory.used_heap / stressResults.final_memory.heap_limit) -
                                                                      (stressResults.initial_memory.used_heap / stressResults.initial_memory.heap_limit)) * 10000) / 100
                            }};
                        }}

                        // Performance impact analysis
                        if ({str(monitor_performance).lower()}) {{
                            stressResults.performance_impact = {{
                                successful_allocations: stressResults.allocation_results.filter(r => r.success).length,
                                failed_allocations: stressResults.allocation_results.filter(r => !r.success).length,
                                avg_allocation_time: stressResults.allocation_results.length > 0 ?
                                    Math.round((stressResults.allocation_results.reduce((sum, r) => sum + (r.allocation_time_ms || 0), 0) /
                                               stressResults.allocation_results.length) * 100) / 100 : 0,
                                total_allocated_attempted_mb: {iterations} * {allocation_mb},
                                total_allocated_actual_mb: totalAllocatedMB
                            }};
                        }}

                        // Generate warnings and recommendations
                        if (stressResults.final_memory && stressResults.initial_memory) {{
                            const heapUsagePercent = (stressResults.final_memory.used_heap / stressResults.final_memory.heap_limit) * 100;
                            if (heapUsagePercent > 80) {{
                                stressResults.warnings.push(`High heap usage: ${{Math.round(heapUsagePercent)}}% of limit`);
                            }}
                            if (heapUsagePercent > 95) {{
                                stressResults.warnings.push(`CRITICAL: Heap usage approaching limit - potential out of memory`);
                            }}
                        }}

                        // Cleanup if gradual release not used
                        if (!{str(gradual_release).lower()}) {{
                            allocatedArrays.splice(0); // Clear references for garbage collection
                            stressResults.cleanup_performed = true;
                        }}

                    }} catch (testError) {{
                        stressResults.success = false;
                        stressResults.test_error = {{
                            name: testError.name,
                            message: testError.message
                        }};
                        stressResults.warnings.push(`Test failed: ${{testError.message}}`);
                    }}

                    return stressResults;
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': memory_stress_code,
                'returnByValue': True,
                'timeout': 30000  # 30 second timeout for stress test
            })

            stress_data = result.get('result', {}).get('result', {}).get('value')

            # Force garbage collection after stress test
            gc_result = cdp.send_command('Runtime.evaluate', {
                'expression': 'if (window.gc) { window.gc(); } else { "GC not available"; }',
                'returnByValue': True
            })

            return jsonify({
                "success": stress_data is not None and stress_data.get("success", False),
                "stress_test_results": stress_data,
                "garbage_collection": gc_result.get('result', {}).get('result', {}).get('value'),
                "test_parameters": {
                    "allocation_mb": allocation_mb,
                    "iterations": iterations,
                    "monitor_performance": monitor_performance,
                    "gradual_release": gradual_release,
                    "max_allocation": max_allocation
                },
                "safety_note": "Memory stress testing performed with safety limits"
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="memory_stress_test",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp'),
            "stress_parameters": data
        }), 500


@stress_testing_routes.route('/cdp/stress/cpu_burn', methods=['POST'])
def cpu_stress_test():
    """
    CPU intensive stress testing and performance boundary discovery

    @route POST /cdp/stress/cpu_burn
    @param {number} [duration_ms] - Test duration in milliseconds (default: 1000)
    @param {string} [test_type] - Type of CPU test (math, loop, recursion, mixed)
    @param {number} [intensity] - Test intensity level 1-10 (default: 5)
    @param {boolean} [monitor_performance] - Monitor CPU performance during test
    @param {boolean} [yield_control] - Yield control periodically (safer)
    @returns {object} CPU stress test results

    @example
    // Basic CPU stress test
    POST {"duration_ms": 2000, "test_type": "math"}

    // Intensive mixed CPU testing
    POST {
      "duration_ms": 5000,
      "test_type": "mixed",
      "intensity": 8,
      "monitor_performance": true
    }

    // Safe CPU test with yielding
    POST {
      "duration_ms": 3000,
      "test_type": "loop",
      "intensity": 6,
      "yield_control": true,
      "monitor_performance": true
    }
    """
    try:
        data = request.get_json() or {}
        duration_ms = min(int(data.get('duration_ms', 1000)), 30000)  # Safety limit: 30 seconds max
        test_type = data.get('test_type', 'math')
        intensity = min(max(int(data.get('intensity', 5)), 1), 10)  # 1-10 scale
        monitor_performance = data.get('monitor_performance', True)
        yield_control = data.get('yield_control', True)

        if test_type not in ['math', 'loop', 'recursion', 'mixed']:
            test_type = 'math'

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # CPU stress testing code
            cpu_stress_code = f"""
                (() => {{
                    const stressResults = {{
                        test_parameters: {{
                            duration_ms: {duration_ms},
                            test_type: '{test_type}',
                            intensity: {intensity},
                            monitor_performance: {str(monitor_performance).lower()},
                            yield_control: {str(yield_control).lower()}
                        }},
                        performance_snapshots: [],
                        operation_counts: {{}},
                        performance_impact: {{}},
                        warnings: [],
                        success: true
                    }};

                    const startTime = performance.now();
                    const endTime = startTime + {duration_ms};
                    let operationCount = 0;
                    let yieldCount = 0;

                    // Performance monitoring function
                    const capturePerformance = () => {{
                        if ({str(monitor_performance).lower()}) {{
                            const snapshot = {{
                                timestamp: performance.now() - startTime,
                                operations_completed: operationCount
                            }};

                            if (performance.memory) {{
                                snapshot.memory_used = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100;
                            }}

                            stressResults.performance_snapshots.push(snapshot);
                        }}
                    }};

                    // Initial performance snapshot
                    capturePerformance();

                    try {{
                        const runTest = () => {{
                            while (performance.now() < endTime) {{
                                // CPU intensive operations based on test type
                                if ('{test_type}' === 'math' || '{test_type}' === 'mixed') {{
                                    // Mathematical operations
                                    for (let i = 0; i < {intensity} * 100; i++) {{
                                        Math.sqrt(Math.pow(Math.random() * 1000, 2));
                                        Math.sin(Math.cos(Math.tan(Math.random() * Math.PI)));
                                        operationCount++;
                                    }}
                                }}

                                if ('{test_type}' === 'loop' || '{test_type}' === 'mixed') {{
                                    // Intensive looping
                                    let sum = 0;
                                    for (let i = 0; i < {intensity} * 1000; i++) {{
                                        sum += i * Math.random();
                                        if (i % 100 === 0) operationCount++;
                                    }}
                                }}

                                if ('{test_type}' === 'recursion' || '{test_type}' === 'mixed') {{
                                    // Controlled recursion
                                    const recursiveFunction = (n) => {{
                                        if (n <= 1) return 1;
                                        return n * recursiveFunction(n - 1);
                                    }};

                                    for (let i = 0; i < {intensity} * 2; i++) {{
                                        try {{
                                            recursiveFunction(Math.min(10 + {intensity}, 15)); // Safety limit
                                            operationCount++;
                                        }} catch (recursionError) {{
                                            stressResults.warnings.push(`Recursion limit hit: ${{recursionError.message}}`);
                                            break;
                                        }}
                                    }}
                                }}

                                // Yield control periodically if enabled
                                if ({str(yield_control).lower()} && operationCount % ({intensity} * 1000) === 0) {{
                                    // Small delay to prevent browser freeze
                                    const yieldTime = performance.now() + 1;
                                    while (performance.now() < yieldTime) {{
                                        // Tiny yield
                                    }}
                                    yieldCount++;
                                    capturePerformance();

                                    // Check if we should continue
                                    if (performance.now() >= endTime) break;
                                }}

                                // Safety check - prevent infinite loops
                                if (operationCount > {intensity} * 100000) {{
                                    stressResults.warnings.push(`Operation limit reached for safety`);
                                    break;
                                }}
                            }}
                        }};

                        // Run the stress test
                        runTest();

                        const actualDuration = performance.now() - startTime;

                        // Final performance snapshot
                        capturePerformance();

                        // Calculate results
                        stressResults.operation_counts = {{
                            total_operations: operationCount,
                            operations_per_second: Math.round((operationCount / (actualDuration / 1000)) * 100) / 100,
                            yield_count: yieldCount,
                            actual_duration_ms: Math.round(actualDuration * 100) / 100
                        }};

                        // Performance impact analysis
                        if ({str(monitor_performance).lower()} && stressResults.performance_snapshots.length > 1) {{
                            const first = stressResults.performance_snapshots[0];
                            const last = stressResults.performance_snapshots[stressResults.performance_snapshots.length - 1];

                            stressResults.performance_impact = {{
                                memory_increase_mb: last.memory_used ?
                                    Math.round((last.memory_used - first.memory_used) * 100) / 100 : 0,
                                operations_acceleration: stressResults.performance_snapshots.length > 2 ?
                                    Math.round(((last.operations_completed - first.operations_completed) /
                                               (last.timestamp - first.timestamp) * 1000) * 100) / 100 : 0,
                                performance_samples: stressResults.performance_snapshots.length
                            }};
                        }}

                        // Performance analysis and warnings
                        if (actualDuration > {duration_ms} * 1.5) {{
                            stressResults.warnings.push(`Test took longer than expected: ${{Math.round(actualDuration)}}ms vs ${{duration_ms}}ms`);
                        }}

                        if (stressResults.operation_counts.operations_per_second < 1000) {{
                            stressResults.warnings.push(`Low operation throughput detected: may indicate CPU bottleneck`);
                        }}

                        if (stressResults.operation_counts.operations_per_second > 100000) {{
                            stressResults.warnings.push(`Extremely high throughput: results may be cached or optimized`);
                        }}

                        // Test intensity recommendations
                        if ({intensity} > 7 && !{str(yield_control).lower()}) {{
                            stressResults.warnings.push(`High intensity without yielding may cause browser freezing`);
                        }}

                    }} catch (testError) {{
                        stressResults.success = false;
                        stressResults.test_error = {{
                            name: testError.name,
                            message: testError.message
                        }};
                        stressResults.warnings.push(`CPU stress test failed: ${{testError.message}}`);
                    }}

                    return stressResults;
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': cpu_stress_code,
                'returnByValue': True,
                'timeout': duration_ms + 10000  # Add buffer to CDP timeout
            })

            stress_data = result.get('result', {}).get('result', {}).get('value')

            return jsonify({
                "success": stress_data is not None and stress_data.get("success", False),
                "cpu_stress_results": stress_data,
                "test_parameters": {
                    "duration_ms": duration_ms,
                    "test_type": test_type,
                    "intensity": intensity,
                    "monitor_performance": monitor_performance,
                    "yield_control": yield_control
                },
                "safety_note": "CPU stress testing performed with safety limits and browser protection"
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="cpu_stress_test",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp'),
            "stress_parameters": data
        }), 500