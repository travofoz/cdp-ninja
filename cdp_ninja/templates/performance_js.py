"""
JavaScript Code Templates for Performance Monitoring
Extracted from performance.py to reduce code duplication and improve maintainability
Each endpoint has its JavaScript code externalized as a reusable template
"""

from typing import Optional


class PerformanceJSTemplates:
    """JavaScript templates for performance monitoring and Core Web Vitals analysis"""

    @staticmethod
    def collect_performance_metrics_template(duration: int, include_paint: bool, include_navigation: bool, include_resource: bool) -> str:
        """Template for collecting performance metrics and Core Web Vitals"""
        return f"""
            (() => {{
                return new Promise((resolve) => {{
                    const performanceData = {{
                        collection_start: performance.now(),
                        duration_seconds: {duration},
                        core_web_vitals: {{}},
                        resource_timing: [],
                        paint_timing: [],
                        navigation_timing: {{}},
                        memory_info: {{}}
                    }};

                    if ({str(include_paint).lower()} && performance.getEntriesByType) {{
                        const paintEntries = performance.getEntriesByType('paint');
                        performanceData.paint_timing = paintEntries.map(e => ({{name: e.name, time: e.startTime}}));
                    }}

                    if ({str(include_navigation).lower()} && performance.timing) {{
                        const t = performance.timing;
                        performanceData.navigation_timing = {{
                            dns: t.domainLookupEnd - t.domainLookupStart,
                            tcp: t.connectEnd - t.connectStart,
                            ttfb: t.responseStart - t.requestStart,
                            download: t.responseEnd - t.responseStart,
                            domload: t.domComplete - t.domLoading,
                            load: t.loadEventEnd - t.loadEventStart
                        }};
                    }}

                    if ({str(include_resource).lower()} && performance.getEntriesByType) {{
                        const resources = performance.getEntriesByType('resource');
                        performanceData.resource_timing = resources.slice(0, 20).map(r => ({{
                            name: r.name,
                            duration: Math.round(r.duration * 100) / 100,
                            size: r.transferSize || 0
                        }}));
                    }}

                    if (performance.memory) {{
                        performanceData.memory_info = {{
                            usedHeapSize: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                            jsHeapSizeLimit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100
                        }};
                    }}

                    resolve(performanceData);
                }});
            }})()
        """

    @staticmethod
    def monitor_memory_usage_template(monitoring_duration: int, sample_interval: int, track_allocations: bool, detect_leaks: bool) -> str:
        """Template for continuous memory monitoring"""
        return f"""
            (() => {{
                return new Promise((resolve) => {{
                    const memoryMonitor = {{
                        baseline_memory: {{}},
                        samples: [],
                        allocation_timeline: [],
                        leak_suspects: [],
                        performance_impact: {{}},
                        monitoring_parameters: {{
                            duration_seconds: {monitoring_duration},
                            sample_interval_ms: {sample_interval},
                            track_allocations: {str(track_allocations).lower()},
                            detect_leaks: {str(detect_leaks).lower()}
                        }}
                    }};

                    if (performance.memory) {{
                        memoryMonitor.baseline_memory = {{
                            usedJSHeapSize: performance.memory.usedJSHeapSize,
                            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                        }};
                    }}

                    const samples = [];
                    const startTime = Date.now();
                    const sampleMemory = () => {{
                        if (performance.memory) {{
                            samples.push({{
                                timestamp: Date.now() - startTime,
                                used_js_heap_size: performance.memory.usedJSHeapSize,
                                js_heap_size_limit: performance.memory.jsHeapSizeLimit,
                                total_js_heap_size: performance.memory.totalJSHeapSize
                            }});
                        }}
                    }};

                    const finishMonitoring = () => {{
                        sampleMemory();
                        memoryMonitor.samples = samples;

                        if ({str(detect_leaks).lower()} && samples.length > 1) {{
                            let totalGrowth = 0;
                            let maxConsecutiveGrowth = 0;
                            let currentConsecutive = 0;

                            for (let i = 1; i < samples.length; i++) {{
                                const growth = samples[i].used_js_heap_size - samples[i-1].used_js_heap_size;
                                if (growth > 0) {{
                                    totalGrowth += growth;
                                    currentConsecutive++;
                                    maxConsecutiveGrowth = Math.max(maxConsecutiveGrowth, currentConsecutive);
                                }} else {{
                                    currentConsecutive = 0;
                                }}
                            }}

                            if (maxConsecutiveGrowth > 3) {{
                                memoryMonitor.leak_suspects.push({{
                                    type: 'continuous_growth',
                                    severity: maxConsecutiveGrowth > 6 ? 'high' : 'medium'
                                }});
                            }}
                        }}

                        resolve(memoryMonitor);
                    }};

                    const interval = setInterval(sampleMemory, {sample_interval});
                    setTimeout(() => {{
                        clearInterval(interval);
                        finishMonitoring();
                    }}, {monitoring_duration} * 1000);
                }});
            }})()
        """

    @staticmethod
    def analyze_rendering_performance_template(monitoring_duration: int) -> str:
        """Template for rendering performance analysis"""
        return f"""
            (() => {{
                return new Promise((resolve) => {{
                    const rendering = {{
                        fps_samples: [],
                        paint_events: [],
                        reflow_warnings: [],
                        avg_fps: 0
                    }};

                    if ('PerformanceObserver' in window) {{
                        try {{
                            const paintObserver = new PerformanceObserver((list) => {{
                                list.getEntries().forEach(entry => {{
                                    rendering.paint_events.push({{
                                        name: entry.name,
                                        duration: entry.duration,
                                        startTime: entry.startTime
                                    }});
                                }});
                            }});
                            paintObserver.observe({{entryTypes: ['paint']}});
                        }} catch (e) {{}}
                    }}

                    setTimeout(() => resolve(rendering), {monitoring_duration} * 1000);
                }});
            }})()
        """

    @staticmethod
    def profile_cpu_usage_template(profiling_duration: int) -> str:
        """Template for CPU profiling"""
        return f"""
            (() => {{
                return new Promise((resolve) => {{
                    const cpuProfile = {{
                        duration_ms: {profiling_duration} * 1000,
                        start_time: performance.now(),
                        operation_count: 0,
                        estimated_cpu_usage: 0
                    }};

                    const startMemory = performance.memory?.usedJSHeapSize || 0;
                    const startTime = performance.now();
                    let opCount = 0;

                    const runOperations = () => {{
                        while (performance.now() - startTime < {profiling_duration} * 1000) {{
                            Math.sqrt(Math.random() * 1000000);
                            opCount++;
                            if (opCount % 10000 === 0) break;
                        }}
                    }};

                    runOperations();
                    cpuProfile.operation_count = opCount;

                    setTimeout(() => resolve(cpuProfile), 100);
                }});
            }})()
        """

    @staticmethod
    def analyze_resource_timing_template(analysis_period: int) -> str:
        """Template for resource timing analysis"""
        return f"""
            (() => {{
                const analysis = {{
                    resources: [],
                    summary: {{
                        total_resources: 0,
                        total_size_bytes: 0,
                        avg_duration_ms: 0
                    }}
                }};

                if (performance.getEntriesByType) {{
                    const resources = performance.getEntriesByType('resource');
                    analysis.resources = resources.slice(0, 50).map(r => ({{
                        name: r.name,
                        duration: Math.round(r.duration * 100) / 100,
                        transferSize: r.transferSize || 0,
                        type: r.initiatorType
                    }}));

                    analysis.summary.total_resources = resources.length;
                    analysis.summary.total_size_bytes = resources.reduce((sum, r) => sum + (r.transferSize || 0), 0);
                    analysis.summary.avg_duration_ms = Math.round(
                        resources.reduce((sum, r) => sum + r.duration, 0) / resources.length * 100
                    ) / 100;
                }}

                return analysis;
            }})()
        """

    @staticmethod
    def monitor_background_tasks_template(monitoring_duration: int) -> str:
        """Template for background task monitoring"""
        return f"""
            (() => {{
                return new Promise((resolve) => {{
                    const tasks = {{
                        background_tasks: [],
                        task_count: 0,
                        monitoring_duration: {monitoring_duration}
                    }};

                    if ('PerformanceObserver' in window) {{
                        try {{
                            const taskObserver = new PerformanceObserver((list) => {{
                                list.getEntries().forEach(entry => {{
                                    tasks.background_tasks.push({{
                                        duration: entry.duration,
                                        name: entry.name
                                    }});
                                    tasks.task_count++;
                                }});
                            }});
                            taskObserver.observe({{entryTypes: ['longtask']}});
                        }} catch (e) {{}}
                    }}

                    setTimeout(() => resolve(tasks), {monitoring_duration} * 1000);
                }});
            }})()
        """

    @staticmethod
    def generate_optimization_recommendations_template() -> str:
        """Template for optimization recommendations"""
        return """
            (() => {
                const recommendations = {
                    performance_issues: [],
                    optimization_opportunities: [],
                    priority: []
                };

                if (performance.timing) {
                    const t = performance.timing;
                    const loadTime = t.loadEventEnd - t.fetchStart;

                    if (loadTime > 3000) {
                        recommendations.performance_issues.push({
                            issue: 'Slow page load',
                            duration_ms: loadTime,
                            severity: 'high'
                        });
                    }
                }

                if (performance.memory) {
                    const usagePercent = (performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 100;
                    if (usagePercent > 80) {
                        recommendations.performance_issues.push({
                            issue: 'High memory usage',
                            usage_percent: Math.round(usagePercent),
                            severity: 'medium'
                        });
                    }
                }

                return recommendations;
            })()
        """

    @staticmethod
    def monitor_core_web_vitals_template(monitoring_duration: int) -> str:
        """Template for Core Web Vitals monitoring"""
        return f"""
            (() => {{
                return new Promise((resolve) => {{
                    const vitals = {{
                        lcp: null,
                        fid: null,
                        cls: 0,
                        ttfb: 0,
                        samples: []
                    }};

                    if ('PerformanceObserver' in window) {{
                        try {{
                            const lcpObserver = new PerformanceObserver((list) => {{
                                const entries = list.getEntries();
                                if (entries.length > 0) {{
                                    vitals.lcp = entries[entries.length - 1].startTime;
                                }}
                            }});
                            lcpObserver.observe({{entryTypes: ['largest-contentful-paint']}});

                            const fidObserver = new PerformanceObserver((list) => {{
                                if (list.getEntries().length > 0) {{
                                    vitals.fid = list.getEntries()[0].processingDuration;
                                }}
                            }});
                            fidObserver.observe({{entryTypes: ['first-input']}});
                        }} catch (e) {{}}
                    }}

                    if (performance.timing) {{
                        vitals.ttfb = performance.timing.responseStart - performance.timing.navigationStart;
                    }}

                    setTimeout(() => resolve(vitals), {monitoring_duration} * 1000);
                }});
            }})()
        """

    @staticmethod
    def track_performance_budget_template(budget_type: str) -> str:
        """Template for performance budget tracking"""
        return f"""
            (() => {{
                const budget = {{
                    budget_type: {repr(budget_type)},
                    current_metrics: {{}},
                    budget_limits: {{}},
                    status: 'unknown'
                }};

                if (performance.timing) {{
                    const t = performance.timing;
                    budget.current_metrics = {{
                        page_load_ms: t.loadEventEnd - t.fetchStart,
                        dom_interactive_ms: t.domInteractive - t.navigationStart,
                        first_paint_ms: (performance.getEntriesByType('paint')[0]?.startTime || 0)
                    }};
                }}

                if (performance.memory) {{
                    budget.current_metrics.heap_size_mb = Math.round(
                        performance.memory.usedJSHeapSize / 1024 / 1024 * 100
                    ) / 100;
                }}

                return budget;
            }})()
        """

    @staticmethod
    def measure_optimization_impact_template(before_snapshot: dict, after_snapshot: dict) -> str:
        """Template for measuring optimization impact"""
        return """
            (() => {
                const impact = {
                    before: {},
                    after: {},
                    improvement_metrics: {},
                    performance_delta: {}
                };

                if (performance.timing) {
                    const t = performance.timing;
                    const loadTime = t.loadEventEnd - t.fetchStart;
                    impact.after.load_time_ms = loadTime;
                }

                if (performance.memory) {
                    impact.after.memory_usage_mb = Math.round(
                        performance.memory.usedJSHeapSize / 1024 / 1024 * 100
                    ) / 100;
                }

                return impact;
            })()
        """


# Template index for easy access
PERFORMANCE_TEMPLATES = {
    'collect_metrics': PerformanceJSTemplates.collect_performance_metrics_template,
    'memory_monitor': PerformanceJSTemplates.monitor_memory_usage_template,
    'rendering': PerformanceJSTemplates.analyze_rendering_performance_template,
    'cpu_profile': PerformanceJSTemplates.profile_cpu_usage_template,
    'resource_timing': PerformanceJSTemplates.analyze_resource_timing_template,
    'background_tasks': PerformanceJSTemplates.monitor_background_tasks_template,
    'recommendations': PerformanceJSTemplates.generate_optimization_recommendations_template,
    'core_vitals': PerformanceJSTemplates.monitor_core_web_vitals_template,
    'budget': PerformanceJSTemplates.track_performance_budget_template,
    'impact': PerformanceJSTemplates.measure_optimization_impact_template
}
