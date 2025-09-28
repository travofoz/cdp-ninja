"""
Concurrency Testing JavaScript Templates
Race conditions, timing attacks, and concurrent operation testing
⚠️ NO INPUT VALIDATION - Raw string interpolation for timing attack research
"""

from typing import Optional


class ConcurrencyJS:
    """JavaScript templates for race condition testing and timing attack simulation

    ⚠️ WARNING: These templates are designed to discover race conditions and
    timing vulnerabilities through aggressive concurrent operations.
    """

    @staticmethod
    def race_conditions_test(async_operations: bool, timing_attacks: bool, concurrent_mutations: bool) -> str:
        """Generate race conditions testing JavaScript for concurrency vulnerabilities

        Args:
            async_operations: Enable asynchronous operation race testing
            timing_attacks: Enable timing-based attack simulation
            concurrent_mutations: Enable concurrent DOM mutation testing

        Returns:
            JavaScript code for comprehensive race condition testing
        """
        return f"""
        (() => {{
            const results = {{
                test_config: {{
                    async_operations: {str(async_operations).lower()},
                    timing_attacks: {str(timing_attacks).lower()},
                    concurrent_mutations: {str(concurrent_mutations).lower()}
                }},
                test_start: Date.now(),
                test_end: null,
                race_conditions_detected: [],
                timing_vulnerabilities: [],
                concurrency_issues: [],
                async_operation_results: [],
                mutation_conflicts: [],
                performance_anomalies: [],
                data_corruption_detected: false,
                inconsistent_states: [],
                thread_safety_violations: [],
                execution_timeline: []
            }};

            // Shared state for race condition testing
            const sharedState = {{
                counter: 0,
                data: {{}},
                operations: [],
                mutationCount: 0,
                accessAttempts: 0
            }};

            // Utility functions for race condition detection
            const raceUtils = {{
                createPromiseRace: (operations) => {{
                    return Promise.allSettled(operations.map((op, index) => {{
                        return new Promise((resolve, reject) => {{
                            const startTime = performance.now();

                            // Simulate varying execution times
                            const delay = Math.random() * 50;
                            setTimeout(() => {{
                                try {{
                                    const result = op();
                                    const endTime = performance.now();

                                    results.execution_timeline.push({{
                                        operation_index: index,
                                        start_time: startTime,
                                        end_time: endTime,
                                        duration: endTime - startTime,
                                        timestamp: Date.now()
                                    }});

                                    resolve({{ index, result, duration: endTime - startTime }});
                                }} catch (error) {{
                                    reject({{ index, error: error.message }});
                                }}
                            }}, delay);
                        }});
                    }}));
                }},

                detectInconsistentState: () => {{
                    const snapshot = JSON.stringify(sharedState);
                    setTimeout(() => {{
                        const laterSnapshot = JSON.stringify(sharedState);
                        if (snapshot !== laterSnapshot) {{
                            results.inconsistent_states.push({{
                                before: snapshot,
                                after: laterSnapshot,
                                timestamp: Date.now()
                            }});
                        }}
                    }}, 1);
                }},

                simulateTimingAttack: (operation, iterations = 100) => {{
                    const timings = [];
                    const promises = [];

                    for (let i = 0; i < iterations; i++) {{
                        promises.push(new Promise(resolve => {{
                            const start = performance.now();

                            operation().then(() => {{
                                const end = performance.now();
                                timings.push(end - start);
                                resolve();
                            }}).catch(() => {{
                                const end = performance.now();
                                timings.push(end - start);
                                resolve();
                            }});
                        }}));
                    }}

                    return Promise.all(promises).then(() => {{
                        const avgTiming = timings.reduce((a, b) => a + b, 0) / timings.length;
                        const variance = timings.reduce((acc, timing) => {{
                            return acc + Math.pow(timing - avgTiming, 2);
                        }}, 0) / timings.length;

                        // Look for suspicious timing patterns
                        if (variance > avgTiming * 0.5) {{
                            results.timing_vulnerabilities.push({{
                                operation: operation.name || 'anonymous',
                                average_timing: avgTiming,
                                variance: variance,
                                timing_samples: timings.slice(0, 10),
                                suspicious: true,
                                timestamp: Date.now()
                            }});
                        }}

                        return {{ avgTiming, variance, timings }};
                    }});
                }}
            }};

            // Async operations race testing
            if ({str(async_operations).lower()}) {{
                const asyncOperations = [
                    () => {{
                        sharedState.accessAttempts++;
                        return new Promise(resolve => {{
                            setTimeout(() => {{
                                const originalCounter = sharedState.counter;
                                sharedState.counter = originalCounter + 1;

                                // Simulate potential race condition
                                setTimeout(() => {{
                                    if (sharedState.counter !== originalCounter + 1) {{
                                        results.race_conditions_detected.push({{
                                            type: 'counter_race',
                                            expected: originalCounter + 1,
                                            actual: sharedState.counter,
                                            timestamp: Date.now()
                                        }});
                                    }}
                                    resolve(sharedState.counter);
                                }}, Math.random() * 10);
                            }}, Math.random() * 20);
                        }});
                    }},

                    () => {{
                        return new Promise(resolve => {{
                            const key = 'data_' + Date.now();
                            const value = Math.random();

                            sharedState.data[key] = value;

                            setTimeout(() => {{
                                if (sharedState.data[key] !== value) {{
                                    results.race_conditions_detected.push({{
                                        type: 'data_corruption',
                                        key: key,
                                        expected: value,
                                        actual: sharedState.data[key],
                                        timestamp: Date.now()
                                    }});
                                    results.data_corruption_detected = true;
                                }}
                                resolve({{ key, value }});
                            }}, Math.random() * 15);
                        }});
                    }},

                    () => {{
                        return new Promise(resolve => {{
                            const operationId = 'op_' + performance.now();
                            sharedState.operations.push(operationId);

                            setTimeout(() => {{
                                const index = sharedState.operations.indexOf(operationId);
                                if (index === -1) {{
                                    results.thread_safety_violations.push({{
                                        type: 'operation_lost',
                                        operation_id: operationId,
                                        timestamp: Date.now()
                                    }});
                                }}
                                resolve(operationId);
                            }}, Math.random() * 25);
                        }});
                    }}
                ];

                // Execute concurrent async operations
                raceUtils.createPromiseRace(asyncOperations).then(asyncResults => {{
                    results.async_operation_results = asyncResults;

                    // Analyze results for race conditions
                    const completionTimes = asyncResults.map(r => r.value?.duration || 0);
                    const timeVariance = Math.max(...completionTimes) - Math.min(...completionTimes);

                    if (timeVariance > 50) {{ // More than 50ms variance
                        results.race_conditions_detected.push({{
                            type: 'timing_variance',
                            variance_ms: timeVariance,
                            completion_times: completionTimes,
                            timestamp: Date.now()
                        }});
                    }}
                }});
            }}

            // Timing attack simulation
            if ({str(timing_attacks).lower()}) {{
                const timingOperations = [
                    () => {{
                        return new Promise(resolve => {{
                            // Simulate authentication timing
                            const validUser = 'admin';
                            const testUser = 'user' + Math.random().toString(36).substring(7);

                            const start = performance.now();

                            if (testUser === validUser) {{
                                // Simulate slow path for valid user
                                setTimeout(() => resolve(true), 50);
                            }} else {{
                                // Simulate fast path for invalid user
                                setTimeout(() => resolve(false), 10);
                            }}
                        }});
                    }},

                    () => {{
                        return new Promise(resolve => {{
                            // Simulate database query timing
                            const query = 'SELECT * FROM users WHERE id = ' + Math.floor(Math.random() * 1000);

                            const start = performance.now();

                            // Simulate query execution time based on data existence
                            const exists = Math.random() > 0.7;
                            const delay = exists ? 30 : 5; // Existing records take longer

                            setTimeout(() => resolve({{ exists, query }}), delay);
                        }});
                    }}
                ];

                timingOperations.forEach((operation, index) => {{
                    raceUtils.simulateTimingAttack(operation, 50).then(timingData => {{
                        results.performance_anomalies.push({{
                            operation_index: index,
                            timing_data: timingData,
                            timestamp: Date.now()
                        }});
                    }});
                }});
            }}

            // Concurrent DOM mutations
            if ({str(concurrent_mutations).lower()}) {{
                const mutationOperations = [
                    () => {{
                        const element = document.createElement('div');
                        element.id = 'race_test_' + performance.now();
                        element.textContent = 'Initial content';
                        document.body.appendChild(element);

                        return new Promise(resolve => {{
                            setTimeout(() => {{
                                if (document.getElementById(element.id)) {{
                                    element.textContent = 'Modified by operation 1';
                                    sharedState.mutationCount++;
                                }}
                                resolve(element.id);
                            }}, Math.random() * 20);
                        }});
                    }},

                    () => {{
                        return new Promise(resolve => {{
                            setTimeout(() => {{
                                const elements = document.querySelectorAll('[id^="race_test_"]');
                                elements.forEach(el => {{
                                    if (el.textContent !== 'Modified by operation 2') {{
                                        const original = el.textContent;
                                        el.textContent = 'Modified by operation 2';

                                        setTimeout(() => {{
                                            if (el.textContent !== 'Modified by operation 2') {{
                                                results.mutation_conflicts.push({{
                                                    element_id: el.id,
                                                    original_content: original,
                                                    expected_content: 'Modified by operation 2',
                                                    actual_content: el.textContent,
                                                    timestamp: Date.now()
                                                }});
                                            }}
                                        }}, 5);
                                    }}
                                }});
                                sharedState.mutationCount++;
                                resolve(elements.length);
                            }}, Math.random() * 15);
                        }});
                    }},

                    () => {{
                        return new Promise(resolve => {{
                            setTimeout(() => {{
                                const elements = document.querySelectorAll('[id^="race_test_"]');
                                const toRemove = Math.floor(elements.length / 2);

                                for (let i = 0; i < toRemove; i++) {{
                                    if (elements[i]) {{
                                        elements[i].remove();
                                    }}
                                }}

                                setTimeout(() => {{
                                    const remainingElements = document.querySelectorAll('[id^="race_test_"]');
                                    if (remainingElements.length !== elements.length - toRemove) {{
                                        results.mutation_conflicts.push({{
                                            type: 'removal_race',
                                            expected_remaining: elements.length - toRemove,
                                            actual_remaining: remainingElements.length,
                                            timestamp: Date.now()
                                        }});
                                    }}
                                }}, 10);

                                sharedState.mutationCount++;
                                resolve(toRemove);
                            }}, Math.random() * 10);
                        }});
                    }}
                ];

                // Execute concurrent mutations
                raceUtils.createPromiseRace(mutationOperations).then(mutationResults => {{
                    results.concurrency_issues = mutationResults.filter(r => r.status === 'rejected');

                    // Check for DOM consistency
                    setTimeout(() => {{
                        const finalElements = document.querySelectorAll('[id^="race_test_"]');
                        if (finalElements.length > 0) {{
                            const contentVariations = new Set();
                            finalElements.forEach(el => contentVariations.add(el.textContent));

                            if (contentVariations.size > 1) {{
                                results.race_conditions_detected.push({{
                                    type: 'dom_content_race',
                                    content_variations: Array.from(contentVariations),
                                    element_count: finalElements.length,
                                    timestamp: Date.now()
                                }});
                            }}
                        }}
                    }}, 100);
                }});
            }}

            // Memory barrier testing
            const memoryBarrierTest = () => {{
                const testData = {{
                    value1: 0,
                    value2: 0,
                    flag: false
                }};

                const writer = () => {{
                    testData.value1 = 42;
                    testData.value2 = 84;
                    testData.flag = true;
                }};

                const reader = () => {{
                    if (testData.flag) {{
                        if (testData.value1 !== 42 || testData.value2 !== 84) {{
                            results.race_conditions_detected.push({{
                                type: 'memory_reordering',
                                value1: testData.value1,
                                value2: testData.value2,
                                flag: testData.flag,
                                timestamp: Date.now()
                            }});
                        }}
                    }}
                }};

                // Execute writer and reader concurrently
                for (let i = 0; i < 1000; i++) {{
                    setTimeout(writer, Math.random() * 10);
                    setTimeout(reader, Math.random() * 10);
                }}
            }};

            memoryBarrierTest();

            // Return results after all tests complete
            setTimeout(() => {{
                results.test_end = Date.now();

                // Final state consistency check
                raceUtils.detectInconsistentState();

                // Summary analysis
                results.summary = {{
                    total_race_conditions: results.race_conditions_detected.length,
                    total_timing_vulnerabilities: results.timing_vulnerabilities.length,
                    total_mutation_conflicts: results.mutation_conflicts.length,
                    data_corruption_detected: results.data_corruption_detected,
                    thread_safety_violations: results.thread_safety_violations.length,
                    test_duration_ms: results.test_end - results.test_start
                }};

                return results;
            }}, 2000);

            return results;
        }})()
        """

    @staticmethod
    def deadlock_detection(resources: list, processes: int, timeout: int) -> str:
        """Generate deadlock detection JavaScript for resource contention testing

        Args:
            resources: List of resource identifiers
            processes: Number of concurrent processes to simulate
            timeout: Maximum wait time before deadlock detection

        Returns:
            JavaScript code for deadlock detection testing
        """
        resources_js = str(resources).replace("'", '"')

        return f"""
        (() => {{
            const results = {{
                resource_config: {resources_js},
                process_count: {processes},
                timeout_ms: {timeout},
                test_start: Date.now(),
                test_end: null,
                deadlocks_detected: [],
                resource_contention: [],
                process_states: [],
                lock_acquisitions: [],
                lock_releases: [],
                circular_waits: [],
                starvation_detected: false,
                livelock_detected: false
            }};

            // Resource management system
            const resourceManager = {{
                resources: {resources_js}.reduce((acc, resource) => {{
                    acc[resource] = {{
                        locked: false,
                        owner: null,
                        waitQueue: [],
                        accessCount: 0
                    }};
                    return acc;
                }}, {{}}),

                acquireLock: (resourceId, processId) => {{
                    return new Promise((resolve, reject) => {{
                        const resource = resourceManager.resources[resourceId];
                        const acquisition = {{
                            resource: resourceId,
                            process: processId,
                            timestamp: Date.now(),
                            status: 'pending'
                        }};

                        if (!resource.locked) {{
                            resource.locked = true;
                            resource.owner = processId;
                            resource.accessCount++;
                            acquisition.status = 'acquired';
                            results.lock_acquisitions.push(acquisition);
                            resolve(resourceId);
                        }} else {{
                            resource.waitQueue.push({{ processId, resolve, reject, timestamp: Date.now() }});
                            results.resource_contention.push({{
                                resource: resourceId,
                                requesting_process: processId,
                                blocking_process: resource.owner,
                                queue_length: resource.waitQueue.length,
                                timestamp: Date.now()
                            }});

                            // Timeout for deadlock detection
                            setTimeout(() => {{
                                const waitIndex = resource.waitQueue.findIndex(w => w.processId === processId);
                                if (waitIndex !== -1) {{
                                    resource.waitQueue.splice(waitIndex, 1);
                                    acquisition.status = 'timeout';
                                    results.lock_acquisitions.push(acquisition);

                                    results.deadlocks_detected.push({{
                                        type: 'timeout_deadlock',
                                        resource: resourceId,
                                        process: processId,
                                        timeout_ms: {timeout},
                                        timestamp: Date.now()
                                    }});

                                    reject(new Error('Lock acquisition timeout'));
                                }}
                            }}, {timeout});
                        }}
                    }});
                }},

                releaseLock: (resourceId, processId) => {{
                    const resource = resourceManager.resources[resourceId];
                    if (resource.owner === processId) {{
                        resource.locked = false;
                        resource.owner = null;

                        results.lock_releases.push({{
                            resource: resourceId,
                            process: processId,
                            timestamp: Date.now()
                        }});

                        // Wake up next waiting process
                        if (resource.waitQueue.length > 0) {{
                            const next = resource.waitQueue.shift();
                            resource.locked = true;
                            resource.owner = next.processId;
                            resource.accessCount++;
                            next.resolve(resourceId);
                        }}
                    }}
                }},

                detectCircularWait: () => {{
                    const waitGraph = {{}};

                    // Build wait-for graph
                    Object.keys(resourceManager.resources).forEach(resourceId => {{
                        const resource = resourceManager.resources[resourceId];
                        if (resource.locked && resource.waitQueue.length > 0) {{
                            resource.waitQueue.forEach(waiter => {{
                                if (!waitGraph[waiter.processId]) {{
                                    waitGraph[waiter.processId] = [];
                                }}
                                waitGraph[waiter.processId].push(resource.owner);
                            }});
                        }}
                    }});

                    // Detect cycles in wait-for graph
                    const visited = new Set();
                    const recursionStack = new Set();

                    const hasCycle = (node, path = []) => {{
                        if (recursionStack.has(node)) {{
                            const cycleStart = path.indexOf(node);
                            const cycle = path.slice(cycleStart);
                            cycle.push(node);

                            results.circular_waits.push({{
                                cycle: cycle,
                                detected_at: Date.now(),
                                type: 'circular_wait_deadlock'
                            }});

                            return true;
                        }}

                        if (visited.has(node)) {{
                            return false;
                        }}

                        visited.add(node);
                        recursionStack.add(node);
                        path.push(node);

                        const neighbors = waitGraph[node] || [];
                        for (let neighbor of neighbors) {{
                            if (hasCycle(neighbor, [...path])) {{
                                return true;
                            }}
                        }}

                        recursionStack.delete(node);
                        return false;
                    }};

                    Object.keys(waitGraph).forEach(processId => {{
                        if (!visited.has(processId)) {{
                            hasCycle(processId);
                        }}
                    }});
                }}
            }};

            // Simulate concurrent processes
            const processes = [];
            for (let i = 0; i < {processes}; i++) {{
                const processId = 'process_' + i;

                const processFunction = async () => {{
                    const state = {{
                        id: processId,
                        start_time: Date.now(),
                        end_time: null,
                        acquired_resources: [],
                        failed_acquisitions: [],
                        operations_completed: 0
                    }};

                    try {{
                        // Randomly select resources to acquire
                        const resourcesToAcquire = {resources_js}
                            .sort(() => Math.random() - 0.5)
                            .slice(0, Math.min(2, {resources_js}.length));

                        // Acquire resources in random order (potential for deadlock)
                        for (let resource of resourcesToAcquire) {{
                            try {{
                                await resourceManager.acquireLock(resource, processId);
                                state.acquired_resources.push(resource);

                                // Simulate work
                                await new Promise(resolve => setTimeout(resolve, Math.random() * 100));
                                state.operations_completed++;

                            }} catch (error) {{
                                state.failed_acquisitions.push({{
                                    resource: resource,
                                    error: error.message,
                                    timestamp: Date.now()
                                }});
                            }}
                        }}

                        // Release resources in reverse order
                        state.acquired_resources.reverse().forEach(resource => {{
                            resourceManager.releaseLock(resource, processId);
                        }});

                    }} catch (error) {{
                        state.error = error.message;
                    }} finally {{
                        state.end_time = Date.now();
                        results.process_states.push(state);
                    }}
                }};

                processes.push(processFunction());
            }}

            // Monitor for deadlocks
            const deadlockMonitor = setInterval(() => {{
                resourceManager.detectCircularWait();

                // Check for starvation
                Object.keys(resourceManager.resources).forEach(resourceId => {{
                    const resource = resourceManager.resources[resourceId];
                    if (resource.waitQueue.length > 0) {{
                        const oldestWait = Math.min(...resource.waitQueue.map(w => w.timestamp));
                        if (Date.now() - oldestWait > {timeout} * 2) {{
                            results.starvation_detected = true;
                            results.deadlocks_detected.push({{
                                type: 'starvation',
                                resource: resourceId,
                                waiting_time: Date.now() - oldestWait,
                                timestamp: Date.now()
                            }});
                        }}
                    }}
                }});

                // Check for livelock
                const recentAcquisitions = results.lock_acquisitions.filter(
                    acq => Date.now() - acq.timestamp < 1000
                );
                if (recentAcquisitions.length > {processes} * 5) {{
                    results.livelock_detected = true;
                }}

            }}, 100);

            // Wait for all processes to complete or timeout
            Promise.allSettled(processes).then(() => {{
                clearInterval(deadlockMonitor);
                results.test_end = Date.now();

                // Final analysis
                results.summary = {{
                    total_deadlocks: results.deadlocks_detected.length,
                    circular_waits: results.circular_waits.length,
                    resource_contentions: results.resource_contention.length,
                    processes_completed: results.process_states.filter(p => p.end_time).length,
                    starvation_detected: results.starvation_detected,
                    livelock_detected: results.livelock_detected,
                    test_duration_ms: results.test_end - results.test_start
                }};
            }});

            return new Promise(resolve => {{
                setTimeout(() => resolve(results), {timeout} + 1000);
            }});
        }})()
        """