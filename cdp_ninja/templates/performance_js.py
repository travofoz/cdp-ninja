"""
JavaScript Code Templates for Performance Monitoring
Extracted from performance.py to reduce code duplication and improve maintainability
Each endpoint has its JavaScript code externalized as a reusable template
"""

from typing import Optional


class PerformanceJSTemplates:
    """JavaScript templates for performance monitoring and Core Web Vitals analysis"""

    @staticmethod
    def collect_performance_metrics_template(
        duration: int,
        include_paint: bool,
        include_navigation: bool,
        include_resource: bool
    ) -> str:
        """Template for collecting performance metrics and Core Web Vitals"""
        return f"""
            (() => {{
                return new Promise((resolve) => {{
                    const performanceData = {{
                        collection_start: performance.now(),
                        duration_seconds: {duration},
                        include_paint: {str(include_paint).lower()},
                        include_navigation: {str(include_navigation).lower()},
                        include_resource: {str(include_resource).lower()},
                        core_web_vitals: {{}},
                        performance_observer_data: {{}},
                        resource_timing: [],
                        paint_timing: [],
                        navigation_timing: {{}},
                        memory_info: {{}}
                    }};

                    // Collect Core Web Vitals (LCP, FID, TTFB, CLS)
                    const vitalMetrics = [];

                    if ('PerformanceObserver' in window) {{
                        try {{
                            // LCP Observer
                            const lcpObserver = new PerformanceObserver((list) => {{
                                const entries = list.getEntries();
                                const lastEntry = entries[entries.length - 1];
                                vitalMetrics.push({{
                                    metric: 'LCP',
                                    value: lastEntry.startTime,
                                    timestamp: Date.now()
                                }});
                            }});
                            lcpObserver.observe({{entryTypes: ['largest-contentful-paint']}});

                            // FID Observer
                            const fidObserver = new PerformanceObserver((list) => {{
                                const entries = list.getEntries();
                                if (entries.length > 0) {{
                                    vitalMetrics.push({{
                                        metric: 'FID',
                                        value: entries[0].processingDuration,
                                        timestamp: Date.now()
                                    }});
                                }}
                            }});
                            fidObserver.observe({{entryTypes: ['first-input']}});
                        }} catch (e) {{
                            performanceData.observer_error = e.message;
                        }}
                    }}

                    // Paint timing
                    if ({str(include_paint).lower()} && performance.getEntriesByType) {{
                        const paintEntries = performance.getEntriesByType('paint');
                        paintEntries.forEach(entry => {{
                            performanceData.paint_timing.push({{
                                name: entry.name,
                                startTime: entry.startTime
                            }});
                        }});
                    }}

                    // Navigation timing
                    if ({str(include_navigation).lower()} && performance.timing) {{
                        const timing = performance.timing;
                        performanceData.navigation_timing = {{
                            dns: timing.domainLookupEnd - timing.domainLookupStart,
                            tcp: timing.connectEnd - timing.connectStart,
                            request: timing.responseStart - timing.requestStart,
                            response: timing.responseEnd - timing.responseStart,
                            dom: timing.domComplete - timing.domLoading,
                            load: timing.loadEventEnd - timing.loadEventStart,
                            total: timing.loadEventEnd - timing.fetchStart
                        }};
                    }}

                    // Resource timing
                    if ({str(include_resource).lower()} && performance.getEntriesByType) {{
                        const resourceEntries = performance.getEntriesByType('resource');
                        performanceData.resource_timing = resourceEntries.slice(0, 20).map(entry => ({{
                            name: entry.name,
                            duration: entry.duration,
                            size: entry.transferSize
                        }}));
                    }}

                    // Memory info
                    if (performance.memory) {{
                        performanceData.memory_info = {{
                            used_js_heap: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                            total_js_heap: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
                            heap_limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100
                        }};
                    }}

                    performanceData.core_web_vitals = vitalMetrics;
                    resolve(performanceData);
                }});
            }})()
        """

    @staticmethod
    def monitor_memory_usage_template(
        monitoring_duration: int,
        sample_interval: int,
        track_allocations: bool,
        detect_leaks: bool
    ) -> str:
        """Template for continuous memory usage monitoring"""
        return f"""
            (() => {{
                return new Promise((resolve) => {{
                    const memoryData = {{
                        monitoring_duration: {monitoring_duration},
                        sample_interval: {sample_interval},
                        track_allocations: {str(track_allocations).lower()},
                        detect_leaks: {str(detect_leaks).lower()},
                        samples: [],
                        initial_state: {{}},
                        final_state: {{}},
                        trends: {{}},
                        potential_leaks: []
                    }};

                    // Capture initial memory state
                    if (performance.memory) {{
                        memoryData.initial_state = {{
                            used_heap: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                            total_heap: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
                            heap_limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100,
                            timestamp: Date.now()
                        }};
                    }}

                    // Memory sampling loop
                    const sampleMemory = () => {{
                        if (performance.memory) {{
                            memoryData.samples.push({{
                                used_heap: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                                total_heap: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
                                timestamp: Date.now(),
                                heap_usage_percent: Math.round((performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 10000) / 100
                            }});
                        }}
                    }};

                    // Take samples at specified intervals
                    const startTime = Date.now();
                    const endTime = startTime + ({monitoring_duration} * 1000);
                    const interval = setInterval(() => {{
                        if (Date.now() >= endTime) {{
                            clearInterval(interval);
                        }} else {{
                            sampleMemory();
                        }}
                    }}, {sample_interval});

                    // Final sample and analysis
                    setTimeout(() => {{
                        sampleMemory();

                        if (performance.memory) {{
                            memoryData.final_state = {{
                                used_heap: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                                total_heap: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
                                heap_limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100,
                                timestamp: Date.now()
                            }};

                            // Leak detection
                            if ({str(detect_leaks).lower()}) {{
                                const heapGrowth = memoryData.final_state.used_heap - memoryData.initial_state.used_heap;
                                if (heapGrowth > 10) {{
                                    memoryData.potential_leaks.push({{
                                        type: 'continuous_growth',
                                        growth_mb: heapGrowth,
                                        severity: heapGrowth > 50 ? 'high' : 'medium'
                                    }});
                                }}
                            }}
                        }}

                        resolve(memoryData);
                    }}, {monitoring_duration} * 1000);
                }});
            }})()
        """

    @staticmethod
    def memory_analysis_template(threshold_mb: int = 50) -> str:
        """Quick memory analysis template"""
        return f"""
            (() => {{
                const analysis = {{
                    threshold_mb: {threshold_mb},
                    memory_state: {{}},
                    status: 'healthy',
                    recommendations: []
                }};

                if (performance.memory) {{
                    const usedMB = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100;
                    const limitMB = Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100;
                    const usagePercent = Math.round((usedMB / limitMB) * 10000) / 100;

                    analysis.memory_state = {{
                        used_heap_mb: usedMB,
                        heap_limit_mb: limitMB,
                        usage_percent: usagePercent
                    }};

                    if (usedMB > {threshold_mb}) {{
                        analysis.status = 'warning';
                        analysis.recommendations.push('Consider reviewing memory usage and potential leaks');
                    }}

                    if (usagePercent > 85) {{
                        analysis.status = 'critical';
                        analysis.recommendations.push('Heap usage critically high - immediate investigation needed');
                    }}
                }}

                return analysis;
            }})()
        """


# Template index for easy access
PERFORMANCE_TEMPLATES = {{
    'collect_metrics': PerformanceJSTemplates.collect_performance_metrics_template,
    'memory_monitor': PerformanceJSTemplates.monitor_memory_usage_template,
    'memory_analysis': PerformanceJSTemplates.memory_analysis_template
}}
