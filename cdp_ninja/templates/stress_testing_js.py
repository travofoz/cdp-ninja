"""
Stress Testing JavaScript Templates
High-impact testing utilities for chaos engineering and breaking point discovery
⚠️ NO INPUT VALIDATION - Raw string interpolation for maximum chaos
"""

from typing import Optional


class StressTestingJS:
    """JavaScript templates for aggressive stress testing and chaos engineering

    ⚠️ WARNING: These templates are designed to break systems and discover
    vulnerabilities through aggressive testing. Use only in isolated environments.
    """

    @staticmethod
    def chaos_monkey(duration: int, random_clicks: bool, random_inputs: bool, unpredictable: bool) -> str:
        """Generate chaos monkey JavaScript for unpredictable system stress testing

        Args:
            duration: Test duration in milliseconds
            random_clicks: Enable random clicking on elements
            random_inputs: Enable random form input generation
            unpredictable: Enable truly unpredictable behavior patterns

        Returns:
            JavaScript code for chaos monkey execution
        """
        return f"""
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
                if (originalError) originalError(message, source, lineno, colno, error);
                return true;
            }};

            // Set up DOM mutation observer
            const observer = new MutationObserver((mutations) => {{
                results.system_stability.dom_mutations += mutations.length;
            }});
            observer.observe(document.body, {{ childList: true, subtree: true, attributes: true }});

            // Set up performance monitoring
            if (window.PerformanceObserver) {{
                const longTaskObserver = new PerformanceObserver((list) => {{
                    results.performance_monitoring.long_tasks += list.getEntries().length;
                }});
                try {{
                    longTaskObserver.observe({{ entryTypes: ['longtask'] }});
                }} catch (e) {{
                    // Long task API not supported
                }}
            }}

            // Chaos function library
            const chaosActions = {{
                randomClick: () => {{
                    const elements = Array.from(document.querySelectorAll('*')).filter(el => {{
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    }});
                    if (elements.length > 0) {{
                        const element = elements[Math.floor(Math.random() * elements.length)];
                        try {{
                            element.click();
                            results.interaction_stats.elements_interacted.add(element.tagName);
                            results.interaction_stats.successful_actions++;
                            results.chaos_activities.push({{
                                action: 'random_click',
                                target: element.tagName + (element.id ? '#' + element.id : ''),
                                timestamp: Date.now()
                            }});
                        }} catch (e) {{
                            results.interaction_stats.failed_actions++;
                            results.discovered_issues.push({{
                                type: 'click_error',
                                error: e.message,
                                element: element.tagName,
                                timestamp: Date.now()
                            }});
                        }}
                    }}
                }},

                randomInput: () => {{
                    const inputs = document.querySelectorAll('input, textarea, select');
                    if (inputs.length > 0) {{
                        const input = inputs[Math.floor(Math.random() * inputs.length)];
                        const chaosValues = [
                            'x'.repeat(Math.floor(Math.random() * 1000)),
                            '<script>alert("chaos")</script>',
                            '\\u0000\\u0001\\u0002',
                            'SELECT * FROM users; DROP TABLE users;--',
                            'javascript:alert("xss")',
                            '{{constructor: {{prototype: {{}}}}}',
                            String.fromCharCode(...Array.from({{length: 50}}, () => Math.floor(Math.random() * 65536)))
                        ];
                        try {{
                            const value = chaosValues[Math.floor(Math.random() * chaosValues.length)];
                            input.value = value;
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            results.interaction_stats.successful_actions++;
                            results.chaos_activities.push({{
                                action: 'random_input',
                                target: input.tagName + (input.name ? '[' + input.name + ']' : ''),
                                value_length: value.length,
                                timestamp: Date.now()
                            }});
                        }} catch (e) {{
                            results.interaction_stats.failed_actions++;
                            results.discovered_issues.push({{
                                type: 'input_error',
                                error: e.message,
                                element: input.tagName,
                                timestamp: Date.now()
                            }});
                        }}
                    }}
                }},

                randomScroll: () => {{
                    try {{
                        window.scrollTo(
                            Math.random() * document.body.scrollWidth,
                            Math.random() * document.body.scrollHeight
                        );
                        results.interaction_stats.successful_actions++;
                        results.chaos_activities.push({{
                            action: 'random_scroll',
                            timestamp: Date.now()
                        }});
                    }} catch (e) {{
                        results.interaction_stats.failed_actions++;
                    }}
                }},

                randomKeypress: () => {{
                    const keys = ['Enter', 'Escape', 'Tab', 'Space', 'F5', 'F12'];
                    const key = keys[Math.floor(Math.random() * keys.length)];
                    try {{
                        document.dispatchEvent(new KeyboardEvent('keydown', {{ key: key }}));
                        results.interaction_stats.successful_actions++;
                        results.chaos_activities.push({{
                            action: 'random_keypress',
                            key: key,
                            timestamp: Date.now()
                        }});
                    }} catch (e) {{
                        results.interaction_stats.failed_actions++;
                    }}
                }},

                memoryStress: () => {{
                    try {{
                        const arrays = [];
                        for (let i = 0; i < 100; i++) {{
                            arrays.push(new Array(1000).fill('stress'));
                        }}
                        // Let arrays be garbage collected
                        setTimeout(() => arrays.length = 0, 100);
                        results.chaos_activities.push({{
                            action: 'memory_stress',
                            timestamp: Date.now()
                        }});
                    }} catch (e) {{
                        results.discovered_issues.push({{
                            type: 'memory_error',
                            error: e.message,
                            timestamp: Date.now()
                        }});
                    }}
                }},

                domMutation: () => {{
                    try {{
                        const div = document.createElement('div');
                        div.innerHTML = '<span>Chaos ' + Math.random() + '</span>';
                        document.body.appendChild(div);
                        setTimeout(() => div.remove(), 1000);
                        results.interaction_stats.successful_actions++;
                        results.chaos_activities.push({{
                            action: 'dom_mutation',
                            timestamp: Date.now()
                        }});
                    }} catch (e) {{
                        results.interaction_stats.failed_actions++;
                    }}
                }}
            }};

            // Build action list based on configuration
            const actions = [];
            if ({str(random_clicks).lower()}) actions.push(chaosActions.randomClick);
            if ({str(random_inputs).lower()}) actions.push(chaosActions.randomInput);
            actions.push(chaosActions.randomScroll, chaosActions.randomKeypress, chaosActions.memoryStress, chaosActions.domMutation);

            // Chaos execution engine
            const startTime = Date.now();
            const chaosInterval = setInterval(() => {{
                if (Date.now() - startTime >= {duration}) {{
                    clearInterval(chaosInterval);

                    // Final memory check
                    if (performance.memory) {{
                        results.performance_monitoring.peak_memory = {{
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize
                        }};

                        const memoryGrowth = results.performance_monitoring.peak_memory.used -
                                           results.performance_monitoring.initial_memory.used;
                        if (memoryGrowth > 10 * 1024 * 1024) {{ // 10MB growth
                            results.system_stability.memory_leaks_detected = true;
                            results.discovered_issues.push({{
                                type: 'memory_leak',
                                growth_bytes: memoryGrowth,
                                timestamp: Date.now()
                            }});
                        }}
                    }}

                    // Performance degradation check
                    if (results.performance_monitoring.long_tasks > 5) {{
                        results.system_stability.performance_degradation = true;
                        results.discovered_issues.push({{
                            type: 'performance_degradation',
                            long_tasks: results.performance_monitoring.long_tasks,
                            timestamp: Date.now()
                        }});
                    }}

                    // Cleanup
                    observer.disconnect();
                    window.onerror = originalError;

                    // Convert Set to Array for JSON serialization
                    results.interaction_stats.elements_interacted = Array.from(results.interaction_stats.elements_interacted);

                    return results;
                }}

                // Execute random action
                if (actions.length > 0) {{
                    const action = {str(unpredictable).lower()} ?
                        actions[Math.floor(Math.random() * actions.length)] :
                        actions[results.interaction_stats.total_actions % actions.length];

                    action();
                    results.interaction_stats.total_actions++;
                }}
            }}, {str(unpredictable).lower()} ? Math.random() * 200 + 50 : 100);

            // Return results after duration (this is a hack for synchronous execution)
            return new Promise(resolve => {{
                setTimeout(() => {{
                    clearInterval(chaosInterval);
                    resolve(results);
                }}, {duration});
            }});
        }})()
        """

    @staticmethod
    def memory_bomb(size_mb: int, allocate_rate: int, monitor: bool) -> str:
        """Generate memory bomb JavaScript for memory stress testing

        Args:
            size_mb: Target memory allocation in megabytes
            allocate_rate: Allocation rate in MB per second
            monitor: Enable memory monitoring during allocation

        Returns:
            JavaScript code for memory bomb execution
        """
        return f"""
        (() => {{
            const results = {{
                target_size_mb: {size_mb},
                allocate_rate_mb_per_sec: {allocate_rate},
                monitoring_enabled: {str(monitor).lower()},
                allocation_start: Date.now(),
                allocation_end: null,
                memory_allocated_mb: 0,
                allocation_successful: false,
                memory_snapshots: [],
                browser_crashed: false,
                oom_detected: false,
                performance_impact: {{
                    initial_heap: null,
                    peak_heap: null,
                    allocation_time_ms: 0,
                    gc_pressure: false
                }},
                errors: []
            }};

            // Capture initial memory state
            if (performance.memory) {{
                results.performance_impact.initial_heap = {{
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit
                }};
            }}

            try {{
                const allocations = [];
                const bytesPerMB = 1024 * 1024;
                const targetBytes = {size_mb} * bytesPerMB;
                const allocationChunkSize = Math.max(1, {allocate_rate}) * bytesPerMB;
                const allocationInterval = 1000; // 1 second

                let totalAllocated = 0;

                const allocateMemory = () => {{
                    try {{
                        // Allocate chunk of memory
                        const chunk = new ArrayBuffer(allocationChunkSize);
                        const view = new Uint8Array(chunk);

                        // Fill with pseudo-random data to prevent optimization
                        for (let i = 0; i < view.length; i += 1024) {{
                            view[i] = Math.floor(Math.random() * 256);
                        }}

                        allocations.push({{ buffer: chunk, view: view, timestamp: Date.now() }});
                        totalAllocated += allocationChunkSize;
                        results.memory_allocated_mb = Math.round(totalAllocated / bytesPerMB);

                        // Memory monitoring snapshot
                        if ({str(monitor).lower()} && performance.memory) {{
                            results.memory_snapshots.push({{
                                timestamp: Date.now(),
                                used_mb: Math.round(performance.memory.usedJSHeapSize / bytesPerMB),
                                total_mb: Math.round(performance.memory.totalJSHeapSize / bytesPerMB),
                                allocated_mb: results.memory_allocated_mb
                            }});
                        }}

                        // Check if target reached
                        if (totalAllocated >= targetBytes) {{
                            results.allocation_successful = true;
                            results.allocation_end = Date.now();
                            results.performance_impact.allocation_time_ms = results.allocation_end - results.allocation_start;

                            // Capture peak memory
                            if (performance.memory) {{
                                results.performance_impact.peak_heap = {{
                                    used: performance.memory.usedJSHeapSize,
                                    total: performance.memory.totalJSHeapSize,
                                    limit: performance.memory.jsHeapSizeLimit
                                }};

                                // Check for GC pressure
                                const heapUtilization = performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit;
                                if (heapUtilization > 0.9) {{
                                    results.performance_impact.gc_pressure = true;
                                }}
                            }}

                            return results;
                        }}

                        // Continue allocation
                        setTimeout(allocateMemory, allocationInterval);

                    }} catch (error) {{
                        // Out of memory or allocation error
                        results.allocation_end = Date.now();
                        results.performance_impact.allocation_time_ms = results.allocation_end - results.allocation_start;

                        if (error.name === 'RangeError' || error.message.includes('memory')) {{
                            results.oom_detected = true;
                            results.errors.push({{
                                type: 'out_of_memory',
                                message: error.message,
                                allocated_mb: results.memory_allocated_mb,
                                timestamp: Date.now()
                            }});
                        }} else {{
                            results.errors.push({{
                                type: 'allocation_error',
                                message: error.message,
                                allocated_mb: results.memory_allocated_mb,
                                timestamp: Date.now()
                            }});
                        }}

                        return results;
                    }}
                }};

                // Start allocation process
                allocateMemory();

            }} catch (error) {{
                results.errors.push({{
                    type: 'initialization_error',
                    message: error.message,
                    timestamp: Date.now()
                }});
                return results;
            }}

            // Fallback timeout
            setTimeout(() => {{
                if (!results.allocation_end) {{
                    results.allocation_end = Date.now();
                    results.performance_impact.allocation_time_ms = results.allocation_end - results.allocation_start;
                    results.errors.push({{
                        type: 'timeout',
                        message: 'Allocation timed out',
                        timestamp: Date.now()
                    }});
                }}
            }}, 30000); // 30 second timeout

            return results;
        }})()
        """

    @staticmethod
    def click_storm(target: str, count: int, interval: int) -> str:
        """Generate click storm JavaScript for rapid clicking stress test

        Args:
            target: CSS selector for target element
            count: Number of clicks to perform
            interval: Interval between clicks in milliseconds

        Returns:
            JavaScript code for click storm execution
        """
        return f"""
        (() => {{
            const results = {{
                target_selector: '{target}',
                target_clicks: {count},
                click_interval_ms: {interval},
                storm_start: Date.now(),
                storm_end: null,
                clicks_performed: 0,
                clicks_successful: 0,
                clicks_failed: 0,
                target_found: false,
                target_responsive: true,
                performance_impact: {{
                    frame_drops: 0,
                    long_tasks: 0,
                    ui_frozen: false
                }},
                errors: [],
                click_timings: []
            }};

            try {{
                const targetElement = document.querySelector('{target}');
                if (!targetElement) {{
                    results.errors.push({{
                        type: 'target_not_found',
                        selector: '{target}',
                        timestamp: Date.now()
                    }});
                    return results;
                }}

                results.target_found = true;

                // Performance monitoring
                const frameDropDetector = () => {{
                    let lastFrame = performance.now();
                    const checkFrame = () => {{
                        const now = performance.now();
                        const frameDuration = now - lastFrame;
                        if (frameDuration > 32) {{ // More than 2 frames at 60fps
                            results.performance_impact.frame_drops++;
                        }}
                        lastFrame = now;
                        if (results.clicks_performed < {count}) {{
                            requestAnimationFrame(checkFrame);
                        }}
                    }};
                    requestAnimationFrame(checkFrame);
                }};
                frameDropDetector();

                let clickIndex = 0;
                const performClick = () => {{
                    const clickStart = performance.now();

                    try {{
                        targetElement.click();
                        results.clicks_successful++;

                        const clickEnd = performance.now();
                        results.click_timings.push({{
                            index: clickIndex,
                            duration_ms: clickEnd - clickStart,
                            timestamp: Date.now()
                        }});

                        // Check if UI is responsive
                        if (clickEnd - clickStart > 100) {{ // Click took more than 100ms
                            results.target_responsive = false;
                            if (clickEnd - clickStart > 1000) {{ // More than 1 second
                                results.performance_impact.ui_frozen = true;
                            }}
                        }}

                    }} catch (error) {{
                        results.clicks_failed++;
                        results.errors.push({{
                            type: 'click_error',
                            message: error.message,
                            click_index: clickIndex,
                            timestamp: Date.now()
                        }});
                    }}

                    results.clicks_performed++;
                    clickIndex++;

                    if (results.clicks_performed < {count}) {{
                        setTimeout(performClick, {interval});
                    }} else {{
                        results.storm_end = Date.now();
                    }}
                }};

                // Start click storm
                performClick();

            }} catch (error) {{
                results.errors.push({{
                    type: 'initialization_error',
                    message: error.message,
                    timestamp: Date.now()
                }});
            }}

            return results;
        }})()
        """