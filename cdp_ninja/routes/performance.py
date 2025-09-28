"""
Performance Monitoring Routes
Background performance analysis, memory monitoring, and rendering optimization
Using Performance domain for Core Web Vitals and profiling
"""

import logging
import json
from flask import Blueprint, jsonify, request
from cdp_ninja.core import get_global_pool
from cdp_ninja.core.domain_manager import CDPDomain
from cdp_ninja.routes.route_utils import (
    ensure_domain_available, create_domain_error_response, create_success_response,
    handle_cdp_error, parse_request_params, track_endpoint_usage, PERFORMANCE_DOMAINS
)

logger = logging.getLogger(__name__)
performance_routes = Blueprint('performance', __name__)


@performance_routes.route('/cdp/performance/metrics', methods=['GET', 'POST'])
def collect_performance_metrics():
    """
    Collect comprehensive performance metrics and Core Web Vitals

    @route GET/POST /cdp/performance/metrics
    @param {boolean} [include_paint] - Include paint timing metrics
    @param {boolean} [include_navigation] - Include navigation timing
    @param {boolean} [include_resource] - Include resource timing
    @param {number} [duration] - Collection duration in seconds
    @returns {object} Performance metrics data

    @example
    // Basic performance metrics
    GET /cdp/performance/metrics

    // Comprehensive metrics with all timing data
    POST {
      "include_paint": true,
      "include_navigation": true,
      "include_resource": true,
      "duration": 5
    }
    """
    try:
        params = parse_request_params(request, ['include_paint', 'include_navigation', 'include_resource', 'duration'])
        include_paint = params['include_paint'] in [True, 'true', '1']
        include_navigation = params['include_navigation'] in [True, 'true', '1']
        include_resource = params['include_resource'] in [True, 'true', '1']
        duration = int(params['duration'] or 3)

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.PERFORMANCE, "collect_performance_metrics"):
            return create_domain_error_response(CDPDomain.PERFORMANCE, "collect_performance_metrics")

        if not ensure_domain_available(CDPDomain.RUNTIME, "collect_performance_metrics"):
            return create_domain_error_response(CDPDomain.RUNTIME, "collect_performance_metrics")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Performance metrics collection code
            metrics_collection_code = f"""
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

                        // Collect Core Web Vitals
                        if (window.performance) {{
                            // Largest Contentful Paint (LCP)
                            if ('PerformanceObserver' in window) {{
                                try {{
                                    const lcpObserver = new PerformanceObserver((list) => {{
                                        const entries = list.getEntries();
                                        const lastEntry = entries[entries.length - 1];
                                        performanceData.core_web_vitals.lcp = {{
                                            value: lastEntry.startTime,
                                            element: lastEntry.element ? lastEntry.element.tagName : null,
                                            url: lastEntry.url || null,
                                            timestamp: Date.now()
                                        }};
                                    }});
                                    lcpObserver.observe({{entryTypes: ['largest-contentful-paint']}});

                                    // First Input Delay (FID) and Interaction to Next Paint (INP)
                                    const fidObserver = new PerformanceObserver((list) => {{
                                        const entries = list.getEntries();
                                        entries.forEach(entry => {{
                                            if (entry.entryType === 'first-input') {{
                                                performanceData.core_web_vitals.fid = {{
                                                    value: entry.processingStart - entry.startTime,
                                                    input_type: entry.name,
                                                    timestamp: Date.now()
                                                }};
                                            }}
                                        }});
                                    }});
                                    fidObserver.observe({{entryTypes: ['first-input']}});

                                    // Layout Shift (CLS)
                                    let clsValue = 0;
                                    const clsObserver = new PerformanceObserver((list) => {{
                                        const entries = list.getEntries();
                                        entries.forEach(entry => {{
                                            if (!entry.hadRecentInput) {{
                                                clsValue += entry.value;
                                            }}
                                        }});
                                        performanceData.core_web_vitals.cls = {{
                                            value: clsValue,
                                            timestamp: Date.now()
                                        }};
                                    }});
                                    clsObserver.observe({{entryTypes: ['layout-shift']}});

                                    // Store observers for cleanup
                                    performanceData.observers = [lcpObserver, fidObserver, clsObserver];
                                }} catch (observerError) {{
                                    performanceData.observer_error = observerError.message;
                                }}
                            }}

                            // Navigation Timing
                            if ({str(include_navigation).lower()}) {{
                                const navTiming = performance.getEntriesByType('navigation')[0];
                                if (navTiming) {{
                                    performanceData.navigation_timing = {{
                                        dns_lookup: navTiming.domainLookupEnd - navTiming.domainLookupStart,
                                        tcp_connect: navTiming.connectEnd - navTiming.connectStart,
                                        ssl_negotiate: navTiming.connectEnd - navTiming.secureConnectionStart,
                                        request_response: navTiming.responseEnd - navTiming.requestStart,
                                        dom_content_loaded: navTiming.domContentLoadedEventEnd - navTiming.domContentLoadedEventStart,
                                        load_complete: navTiming.loadEventEnd - navTiming.loadEventStart,
                                        total_time: navTiming.loadEventEnd - navTiming.navigationStart,
                                        redirect_time: navTiming.redirectEnd - navTiming.redirectStart,
                                        dom_interactive: navTiming.domInteractive - navTiming.navigationStart,
                                        first_byte: navTiming.responseStart - navTiming.navigationStart
                                    }};
                                }}
                            }}

                            // Paint Timing
                            if ({str(include_paint).lower()}) {{
                                const paintEntries = performance.getEntriesByType('paint');
                                performanceData.paint_timing = paintEntries.map(entry => ({{
                                    name: entry.name,
                                    start_time: entry.startTime,
                                    duration: entry.duration
                                }}));
                            }}

                            // Resource Timing
                            if ({str(include_resource).lower()}) {{
                                const resourceEntries = performance.getEntriesByType('resource');
                                performanceData.resource_timing = resourceEntries.slice(-20).map(entry => ({{
                                    name: entry.name,
                                    type: entry.initiatorType,
                                    start_time: entry.startTime,
                                    duration: entry.duration,
                                    transfer_size: entry.transferSize,
                                    encoded_size: entry.encodedBodySize,
                                    decoded_size: entry.decodedBodySize,
                                    cache_hit: entry.transferSize === 0 && entry.decodedBodySize > 0
                                }}));
                            }}

                            // Memory Information
                            if (performance.memory) {{
                                performanceData.memory_info = {{
                                    used_js_heap_size: performance.memory.usedJSHeapSize,
                                    total_js_heap_size: performance.memory.totalJSHeapSize,
                                    js_heap_size_limit: performance.memory.jsHeapSizeLimit,
                                    heap_usage_percent: (performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize) * 100
                                }};
                            }}
                        }}

                        // Collect data for specified duration
                        setTimeout(() => {{
                            // Clean up observers
                            if (performanceData.observers) {{
                                performanceData.observers.forEach(observer => {{
                                    try {{
                                        observer.disconnect();
                                    }} catch (e) {{
                                        // Observer already disconnected
                                    }}
                                }});
                            }}

                            performanceData.collection_end = performance.now();
                            performanceData.actual_duration_ms = performanceData.collection_end - performanceData.collection_start;

                            // Performance score calculation
                            let performanceScore = 100;

                            // Deduct points based on metrics
                            if (performanceData.core_web_vitals.lcp && performanceData.core_web_vitals.lcp.value > 2500) {{
                                performanceScore -= 30; // Poor LCP
                            }} else if (performanceData.core_web_vitals.lcp && performanceData.core_web_vitals.lcp.value > 1200) {{
                                performanceScore -= 15; // Needs improvement LCP
                            }}

                            if (performanceData.core_web_vitals.fid && performanceData.core_web_vitals.fid.value > 100) {{
                                performanceScore -= 25; // Poor FID
                            }}

                            if (performanceData.core_web_vitals.cls && performanceData.core_web_vitals.cls.value > 0.25) {{
                                performanceScore -= 20; // Poor CLS
                            }} else if (performanceData.core_web_vitals.cls && performanceData.core_web_vitals.cls.value > 0.1) {{
                                performanceScore -= 10; // Needs improvement CLS
                            }}

                            performanceData.performance_score = Math.max(0, performanceScore);
                            performanceData.performance_grade = performanceScore >= 90 ? 'A' :
                                                              performanceScore >= 75 ? 'B' :
                                                              performanceScore >= 60 ? 'C' :
                                                              performanceScore >= 40 ? 'D' : 'F';

                            resolve(performanceData);
                        }}, {duration * 1000});
                    }});
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': metrics_collection_code,
                'returnByValue': True,
                'awaitPromise': True,
                'timeout': (duration + 10) * 1000
            })

            metrics_data = result.get('result', {}).get('result', {}).get('value')

            # Track endpoint usage
            track_endpoint_usage("collect_performance_metrics", [CDPDomain.PERFORMANCE, CDPDomain.RUNTIME], params)

            return jsonify(create_success_response({
                "performance_metrics": metrics_data,
                "collection_parameters": {
                    "include_paint": include_paint,
                    "include_navigation": include_navigation,
                    "include_resource": include_resource,
                    "duration": duration
                }
            }, "collect_performance_metrics", [CDPDomain.PERFORMANCE, CDPDomain.RUNTIME]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("collect_performance_metrics", e, params, "collect_performance_metrics")


@performance_routes.route('/cdp/performance/memory_monitor', methods=['GET', 'POST'])
def monitor_memory_usage():
    """
    Monitor memory usage patterns and detect potential leaks in background

    @route GET/POST /cdp/performance/memory_monitor
    @param {number} [monitoring_duration] - Duration to monitor in seconds
    @param {number} [sample_interval] - Sample interval in milliseconds
    @param {boolean} [track_allocations] - Track allocation patterns
    @param {boolean} [detect_leaks] - Enable leak detection
    @returns {object} Memory monitoring data

    @example
    // Basic memory monitoring
    GET /cdp/performance/memory_monitor

    // Detailed monitoring with leak detection
    POST {
      "monitoring_duration": 30,
      "sample_interval": 1000,
      "track_allocations": true,
      "detect_leaks": true
    }
    """
    try:
        params = parse_request_params(request, ['monitoring_duration', 'sample_interval', 'track_allocations', 'detect_leaks'])
        monitoring_duration = int(params['monitoring_duration'] or 10)
        sample_interval = int(params['sample_interval'] or 500)
        track_allocations = params['track_allocations'] in [True, 'true', '1']
        detect_leaks = params['detect_leaks'] in [True, 'true', '1']

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.PERFORMANCE, "monitor_memory_usage"):
            return create_domain_error_response(CDPDomain.PERFORMANCE, "monitor_memory_usage")

        if not ensure_domain_available(CDPDomain.RUNTIME, "monitor_memory_usage"):
            return create_domain_error_response(CDPDomain.RUNTIME, "monitor_memory_usage")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Memory monitoring code
            memory_monitor_code = f"""
                (() => {{
                    return new Promise((resolve) => {{
                        const memoryMonitor = {{
                            monitoring_duration: {monitoring_duration},
                            sample_interval: {sample_interval},
                            track_allocations: {str(track_allocations).lower()},
                            detect_leaks: {str(detect_leaks).lower()},
                            start_time: performance.now(),
                            memory_samples: [],
                            allocation_timeline: [],
                            leak_suspects: [],
                            performance_impact: {{}}
                        }};

                        let sampleCount = 0;
                        const maxSamples = Math.floor(({monitoring_duration} * 1000) / {sample_interval});

                        // Baseline memory measurement
                        if (performance.memory) {{
                            memoryMonitor.baseline_memory = {{
                                used_js_heap_size: performance.memory.usedJSHeapSize,
                                total_js_heap_size: performance.memory.totalJSHeapSize,
                                js_heap_size_limit: performance.memory.jsHeapSizeLimit
                            }};
                        }}

                        // Allocation tracking setup
                        if ({str(track_allocations).lower()}) {{
                            // Monitor object creation patterns
                            const originalArrayFrom = Array.from;
                            const originalObjectCreate = Object.create;
                            let allocationCount = 0;

                            // Track large allocations
                            const trackAllocation = (type, size) => {{
                                allocationCount++;
                                if (allocationCount % 100 === 0) {{ // Sample every 100th allocation
                                    memoryMonitor.allocation_timeline.push({{
                                        timestamp: performance.now(),
                                        type: type,
                                        estimated_size: size,
                                        heap_used: performance.memory ? performance.memory.usedJSHeapSize : null
                                    }});
                                }}
                            }};

                            // Override allocation methods (simplified tracking)
                            Array.from = function(...args) {{
                                trackAllocation('Array', args[0] ? args[0].length : 0);
                                return originalArrayFrom.apply(this, args);
                            }};
                        }}

                        // Periodic memory sampling
                        const memoryInterval = setInterval(() => {{
                            if (performance.memory) {{
                                const sample = {{
                                    timestamp: performance.now(),
                                    used_js_heap_size: performance.memory.usedJSHeapSize,
                                    total_js_heap_size: performance.memory.totalJSHeapSize,
                                    js_heap_size_limit: performance.memory.jsHeapSizeLimit,
                                    sample_number: sampleCount + 1
                                }};

                                // Calculate growth rate
                                if (memoryMonitor.memory_samples.length > 0) {{
                                    const previous = memoryMonitor.memory_samples[memoryMonitor.memory_samples.length - 1];
                                    sample.growth_bytes = sample.used_js_heap_size - previous.used_js_heap_size;
                                    sample.growth_rate = sample.growth_bytes / ({sample_interval} / 1000); // bytes per second
                                }}

                                memoryMonitor.memory_samples.push(sample);
                            }}

                            sampleCount++;
                            if (sampleCount >= maxSamples) {{
                                clearInterval(memoryInterval);
                                finishMonitoring();
                            }}
                        }}, {sample_interval});

                        const finishMonitoring = () => {{
                            memoryMonitor.end_time = performance.now();
                            memoryMonitor.total_duration_ms = memoryMonitor.end_time - memoryMonitor.start_time;

                            // Analyze memory patterns
                            if (memoryMonitor.memory_samples.length > 2) {{
                                const samples = memoryMonitor.memory_samples;

                                // Calculate statistics
                                const growthRates = samples.filter(s => s.growth_rate !== undefined).map(s => s.growth_rate);
                                const totalGrowth = samples[samples.length - 1].used_js_heap_size - samples[0].used_js_heap_size;

                                memoryMonitor.analysis = {{
                                    total_growth_bytes: totalGrowth,
                                    avg_growth_rate: growthRates.reduce((a, b) => a + b, 0) / growthRates.length,
                                    max_growth_rate: Math.max(...growthRates),
                                    min_growth_rate: Math.min(...growthRates),
                                    growth_trend: totalGrowth > 0 ? 'increasing' : totalGrowth < 0 ? 'decreasing' : 'stable',
                                    samples_collected: samples.length
                                }};

                                // Leak detection
                                if ({str(detect_leaks).lower()}) {{
                                    // Detect continuous growth pattern
                                    let consecutiveGrowth = 0;
                                    let maxConsecutiveGrowth = 0;

                                    growthRates.forEach(rate => {{
                                        if (rate > 1000) {{ // Growing by more than 1KB/sec
                                            consecutiveGrowth++;
                                            maxConsecutiveGrowth = Math.max(maxConsecutiveGrowth, consecutiveGrowth);
                                        }} else {{
                                            consecutiveGrowth = 0;
                                        }}
                                    }});

                                    if (maxConsecutiveGrowth > 3) {{
                                        memoryMonitor.leak_suspects.push({{
                                            type: 'continuous_growth',
                                            severity: maxConsecutiveGrowth > 6 ? 'high' : 'medium',
                                            description: `Detected ${{maxConsecutiveGrowth}} consecutive periods of growth`,
                                            evidence: {{
                                                consecutive_growth_periods: maxConsecutiveGrowth,
                                                total_growth_kb: Math.round(totalGrowth / 1024)
                                            }}
                                        }});
                                    }}

                                    // Detect allocation vs memory growth mismatch
                                    if (memoryMonitor.allocation_timeline.length > 0) {{
                                        const allocationsInPeriod = memoryMonitor.allocation_timeline.length;
                                        const growthPerAllocation = totalGrowth / allocationsInPeriod;

                                        if (growthPerAllocation > 10000) {{ // More than 10KB per tracked allocation
                                            memoryMonitor.leak_suspects.push({{
                                                type: 'allocation_growth_mismatch',
                                                severity: 'medium',
                                                description: 'Memory growth exceeds expected allocation pattern',
                                                evidence: {{
                                                    growth_per_allocation_bytes: Math.round(growthPerAllocation),
                                                    tracked_allocations: allocationsInPeriod
                                                }}
                                            }});
                                        }}
                                    }}
                                }}

                                // Performance impact analysis
                                if (memoryMonitor.baseline_memory) {{
                                    const currentUsage = samples[samples.length - 1].used_js_heap_size;
                                    const usagePercent = (currentUsage / samples[samples.length - 1].js_heap_size_limit) * 100;

                                    memoryMonitor.performance_impact = {{
                                        memory_pressure: usagePercent > 80 ? 'high' : usagePercent > 60 ? 'medium' : 'low',
                                        heap_usage_percent: usagePercent,
                                        gc_pressure_risk: usagePercent > 70 ? 'elevated' : 'normal',
                                        recommendations: []
                                    }};

                                    if (usagePercent > 80) {{
                                        memoryMonitor.performance_impact.recommendations.push('High memory usage detected - investigate large objects');
                                    }}
                                    if (totalGrowth > 5000000) {{ // 5MB growth
                                        memoryMonitor.performance_impact.recommendations.push('Significant memory growth during monitoring - check for leaks');
                                    }}
                                    if (memoryMonitor.leak_suspects.length > 0) {{
                                        memoryMonitor.performance_impact.recommendations.push('Potential memory leaks detected - review allocation patterns');
                                    }}
                                }}
                            }}

                            resolve(memoryMonitor);
                        }};

                        // Start monitoring immediately if duration is 0
                        if ({monitoring_duration} === 0) {{
                            setTimeout(finishMonitoring, 100);
                        }}
                    }});
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': memory_monitor_code,
                'returnByValue': True,
                'awaitPromise': True,
                'timeout': (monitoring_duration + 10) * 1000
            })

            memory_data = result.get('result', {}).get('result', {}).get('value')

            # Track endpoint usage
            track_endpoint_usage("monitor_memory_usage", [CDPDomain.PERFORMANCE, CDPDomain.RUNTIME], params)

            return jsonify(create_success_response({
                "memory_monitoring": memory_data,
                "monitoring_parameters": {
                    "monitoring_duration": monitoring_duration,
                    "sample_interval": sample_interval,
                    "track_allocations": track_allocations,
                    "detect_leaks": detect_leaks
                }
            }, "monitor_memory_usage", [CDPDomain.PERFORMANCE, CDPDomain.RUNTIME]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("monitor_memory_usage", e, params, "monitor_memory_usage")


@performance_routes.route('/cdp/performance/rendering_metrics', methods=['GET', 'POST'])
def analyze_rendering_performance():
    """
    Analyze rendering performance including frame rates and paint events

    @route GET/POST /cdp/performance/rendering_metrics
    @param {number} [monitoring_duration] - Duration to monitor in seconds
    @param {boolean} [track_frame_rate] - Track frame rate metrics
    @param {boolean} [analyze_paint_events] - Analyze paint and layout events
    @param {boolean} [detect_jank] - Detect rendering jank
    @returns {object} Rendering performance analysis

    @example
    // Basic rendering metrics
    GET /cdp/performance/rendering_metrics

    // Comprehensive rendering analysis
    POST {
      "monitoring_duration": 10,
      "track_frame_rate": true,
      "analyze_paint_events": true,
      "detect_jank": true
    }
    """
    try:
        params = parse_request_params(request, ['monitoring_duration', 'track_frame_rate', 'analyze_paint_events', 'detect_jank'])
        monitoring_duration = int(params['monitoring_duration'] or 5)
        track_frame_rate = params['track_frame_rate'] in [True, 'true', '1']
        analyze_paint_events = params['analyze_paint_events'] in [True, 'true', '1']
        detect_jank = params['detect_jank'] in [True, 'true', '1']

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.PERFORMANCE, "analyze_rendering_performance"):
            return create_domain_error_response(CDPDomain.PERFORMANCE, "analyze_rendering_performance")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Rendering analysis code
            rendering_analysis_code = f"""
                (() => {{
                    return new Promise((resolve) => {{
                        const renderingAnalysis = {{
                            monitoring_duration: {monitoring_duration},
                            track_frame_rate: {str(track_frame_rate).lower()},
                            analyze_paint_events: {str(analyze_paint_events).lower()},
                            detect_jank: {str(detect_jank).lower()},
                            start_time: performance.now(),
                            frame_data: [],
                            paint_events: [],
                            jank_incidents: [],
                            performance_scores: {{}}
                        }};

                        let frameCount = 0;
                        let lastFrameTime = performance.now();
                        const frameTimes = [];

                        // Frame rate tracking
                        if ({str(track_frame_rate).lower()}) {{
                            const trackFrame = (timestamp) => {{
                                frameCount++;
                                const frameTime = timestamp - lastFrameTime;
                                frameTimes.push(frameTime);

                                renderingAnalysis.frame_data.push({{
                                    frame_number: frameCount,
                                    timestamp: timestamp,
                                    frame_time_ms: frameTime,
                                    fps: frameTime > 0 ? 1000 / frameTime : 0
                                }});

                                lastFrameTime = timestamp;

                                // Continue tracking if within duration
                                if (timestamp - renderingAnalysis.start_time < {monitoring_duration * 1000}) {{
                                    requestAnimationFrame(trackFrame);
                                }}
                            }};

                            requestAnimationFrame(trackFrame);
                        }}

                        // Paint event analysis using Performance Observer
                        if ({str(analyze_paint_events).lower()} && 'PerformanceObserver' in window) {{
                            try {{
                                const paintObserver = new PerformanceObserver((list) => {{
                                    const entries = list.getEntries();
                                    entries.forEach(entry => {{
                                        renderingAnalysis.paint_events.push({{
                                            name: entry.name,
                                            entry_type: entry.entryType,
                                            start_time: entry.startTime,
                                            duration: entry.duration,
                                            timestamp: performance.now()
                                        }});
                                    }});
                                }});

                                // Observe paint, layout, and measure events
                                paintObserver.observe({{entryTypes: ['paint', 'measure']}});

                                // Store observer for cleanup
                                renderingAnalysis.paint_observer = paintObserver;
                            }} catch (observerError) {{
                                renderingAnalysis.paint_observer_error = observerError.message;
                            }}
                        }}

                        // Jank detection
                        if ({str(detect_jank).lower()}) {{
                            const jankThreshold = 16.67; // 60fps threshold
                            let consecutiveSlowFrames = 0;

                            const detectJank = () => {{
                                if (frameTimes.length > 0) {{
                                    const recentFrames = frameTimes.slice(-10); // Last 10 frames
                                    const avgFrameTime = recentFrames.reduce((a, b) => a + b, 0) / recentFrames.length;

                                    if (avgFrameTime > jankThreshold) {{
                                        consecutiveSlowFrames++;

                                        if (consecutiveSlowFrames >= 3) {{ // 3 consecutive slow frames
                                            renderingAnalysis.jank_incidents.push({{
                                                timestamp: performance.now(),
                                                avg_frame_time: avgFrameTime,
                                                frames_affected: consecutiveSlowFrames,
                                                severity: avgFrameTime > 33 ? 'severe' : avgFrameTime > 25 ? 'moderate' : 'mild'
                                            }});
                                            consecutiveSlowFrames = 0; // Reset counter
                                        }}
                                    }} else {{
                                        consecutiveSlowFrames = 0;
                                    }}
                                }}

                                // Continue checking if within duration
                                if (performance.now() - renderingAnalysis.start_time < {monitoring_duration * 1000}) {{
                                    setTimeout(detectJank, 100); // Check every 100ms
                                }}
                            }};

                            setTimeout(detectJank, 100);
                        }}

                        // Finish analysis after duration
                        setTimeout(() => {{
                            // Clean up observers
                            if (renderingAnalysis.paint_observer) {{
                                try {{
                                    renderingAnalysis.paint_observer.disconnect();
                                }} catch (e) {{
                                    // Observer already disconnected
                                }}
                            }}

                            renderingAnalysis.end_time = performance.now();
                            renderingAnalysis.actual_duration_ms = renderingAnalysis.end_time - renderingAnalysis.start_time;

                            // Calculate performance metrics
                            if (frameTimes.length > 0) {{
                                const avgFrameTime = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
                                const minFrameTime = Math.min(...frameTimes);
                                const maxFrameTime = Math.max(...frameTimes);
                                const avgFPS = 1000 / avgFrameTime;

                                // Calculate frame time percentiles
                                const sortedFrameTimes = [...frameTimes].sort((a, b) => a - b);
                                const p50 = sortedFrameTimes[Math.floor(sortedFrameTimes.length * 0.5)];
                                const p95 = sortedFrameTimes[Math.floor(sortedFrameTimes.length * 0.95)];
                                const p99 = sortedFrameTimes[Math.floor(sortedFrameTimes.length * 0.99)];

                                renderingAnalysis.frame_statistics = {{
                                    total_frames: frameCount,
                                    avg_frame_time_ms: avgFrameTime,
                                    min_frame_time_ms: minFrameTime,
                                    max_frame_time_ms: maxFrameTime,
                                    avg_fps: avgFPS,
                                    frame_time_p50: p50,
                                    frame_time_p95: p95,
                                    frame_time_p99: p99,
                                    smooth_frames_percent: (frameTimes.filter(ft => ft <= 16.67).length / frameTimes.length) * 100
                                }};

                                // Performance scoring
                                let renderingScore = 100;

                                // Deduct points for poor frame rate
                                if (avgFPS < 30) {{
                                    renderingScore -= 40;
                                }} else if (avgFPS < 45) {{
                                    renderingScore -= 25;
                                }} else if (avgFPS < 55) {{
                                    renderingScore -= 10;
                                }}

                                // Deduct points for jank
                                if (renderingAnalysis.jank_incidents.length > 0) {{
                                    const severeJank = renderingAnalysis.jank_incidents.filter(j => j.severity === 'severe').length;
                                    const moderateJank = renderingAnalysis.jank_incidents.filter(j => j.severity === 'moderate').length;

                                    renderingScore -= (severeJank * 15) + (moderateJank * 8) + (renderingAnalysis.jank_incidents.length * 3);
                                }}

                                renderingAnalysis.performance_scores = {{
                                    rendering_score: Math.max(0, renderingScore),
                                    rendering_grade: renderingScore >= 90 ? 'A' :
                                                    renderingScore >= 75 ? 'B' :
                                                    renderingScore >= 60 ? 'C' :
                                                    renderingScore >= 40 ? 'D' : 'F',
                                    fps_category: avgFPS >= 55 ? 'excellent' :
                                                 avgFPS >= 45 ? 'good' :
                                                 avgFPS >= 30 ? 'fair' : 'poor',
                                    jank_level: renderingAnalysis.jank_incidents.length === 0 ? 'none' :
                                               renderingAnalysis.jank_incidents.length <= 2 ? 'low' :
                                               renderingAnalysis.jank_incidents.length <= 5 ? 'moderate' : 'high'
                                }};
                            }}

                            // Paint event analysis
                            if (renderingAnalysis.paint_events.length > 0) {{
                                const paintStats = {{
                                    total_paint_events: renderingAnalysis.paint_events.length,
                                    paint_types: {{}},
                                    avg_paint_duration: 0
                                }};

                                renderingAnalysis.paint_events.forEach(event => {{
                                    paintStats.paint_types[event.name] = (paintStats.paint_types[event.name] || 0) + 1;
                                }});

                                const durationsWithValues = renderingAnalysis.paint_events.filter(e => e.duration > 0);
                                if (durationsWithValues.length > 0) {{
                                    paintStats.avg_paint_duration = durationsWithValues.reduce((a, e) => a + e.duration, 0) / durationsWithValues.length;
                                }}

                                renderingAnalysis.paint_statistics = paintStats;
                            }}

                            // Generate recommendations
                            renderingAnalysis.recommendations = [];

                            if (renderingAnalysis.frame_statistics && renderingAnalysis.frame_statistics.avg_fps < 45) {{
                                renderingAnalysis.recommendations.push('Low frame rate detected - optimize animations and reduce DOM complexity');
                            }}

                            if (renderingAnalysis.jank_incidents.length > 0) {{
                                renderingAnalysis.recommendations.push('Rendering jank detected - review JavaScript execution and layout triggers');
                            }}

                            if (renderingAnalysis.frame_statistics && renderingAnalysis.frame_statistics.frame_time_p99 > 50) {{
                                renderingAnalysis.recommendations.push('High P99 frame time - investigate periodic performance issues');
                            }}

                            resolve(renderingAnalysis);
                        }}, {monitoring_duration * 1000});
                    }});
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': rendering_analysis_code,
                'returnByValue': True,
                'awaitPromise': True,
                'timeout': (monitoring_duration + 10) * 1000
            })

            rendering_data = result.get('result', {}).get('result', {}).get('value')

            # Track endpoint usage
            track_endpoint_usage("analyze_rendering_performance", [CDPDomain.PERFORMANCE], params)

            return jsonify(create_success_response({
                "rendering_analysis": rendering_data,
                "analysis_parameters": {
                    "monitoring_duration": monitoring_duration,
                    "track_frame_rate": track_frame_rate,
                    "analyze_paint_events": analyze_paint_events,
                    "detect_jank": detect_jank
                }
            }, "analyze_rendering_performance", [CDPDomain.PERFORMANCE]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("analyze_rendering_performance", e, params, "analyze_rendering_performance")


@performance_routes.route('/cdp/performance/cpu_profiling', methods=['POST'])
def profile_cpu_usage():
    """
    Profile CPU usage and identify performance bottlenecks

    @route POST /cdp/performance/cpu_profiling
    @param {number} [profiling_duration] - Duration to profile in seconds
    @param {boolean} [sample_stack_traces] - Sample stack traces during profiling
    @param {boolean} [analyze_hot_functions] - Analyze hottest functions
    @param {string} [profiling_mode] - Profiling mode: 'sampling' or 'precision'
    @returns {object} CPU profiling results

    @example
    // Basic CPU profiling
    POST {"profiling_duration": 5}

    // Comprehensive profiling with stack traces
    POST {
      "profiling_duration": 10,
      "sample_stack_traces": true,
      "analyze_hot_functions": true,
      "profiling_mode": "precision"
    }
    """
    try:
        data = request.get_json() or {}
        profiling_duration = int(data.get('profiling_duration', 5))
        sample_stack_traces = data.get('sample_stack_traces', False)
        analyze_hot_functions = data.get('analyze_hot_functions', False)
        profiling_mode = data.get('profiling_mode', 'sampling')

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.PERFORMANCE, "profile_cpu_usage"):
            return create_domain_error_response(CDPDomain.PERFORMANCE, "profile_cpu_usage")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Start CPU profiling
            start_result = cdp.send_command('Profiler.enable')
            if 'error' in start_result:
                return jsonify(start_result), 500

            # Set sampling interval based on mode
            sampling_interval = 100 if profiling_mode == 'precision' else 1000  # microseconds

            start_profiler = cdp.send_command('Profiler.start', {
                'callCount': True,
                'samplingInterval': sampling_interval
            })

            if 'error' in start_profiler:
                return jsonify(start_profiler), 500

            # CPU usage analysis code (runs during profiling)
            cpu_analysis_code = f"""
                (() => {{
                    return new Promise((resolve) => {{
                        const cpuAnalysis = {{
                            profiling_duration: {profiling_duration},
                            sample_stack_traces: {str(sample_stack_traces).lower()},
                            analyze_hot_functions: {str(analyze_hot_functions).lower()},
                            profiling_mode: '{profiling_mode}',
                            start_time: performance.now(),
                            cpu_measurements: [],
                            function_calls: {{}},
                            stack_samples: [],
                            performance_timeline: []
                        }};

                        // Simulate CPU-intensive work for measurement
                        const performCPUWork = () => {{
                            // Mathematical operations
                            let result = 0;
                            for (let i = 0; i < 10000; i++) {{
                                result += Math.sqrt(i) * Math.sin(i);
                            }}
                            return result;
                        }};

                        // Array operations
                        const performArrayWork = () => {{
                            const arr = Array.from({{length: 1000}}, (_, i) => i);
                            return arr.map(x => x * 2).filter(x => x % 3 === 0).reduce((a, b) => a + b, 0);
                        }};

                        // DOM operations
                        const performDOMWork = () => {{
                            const tempDiv = document.createElement('div');
                            for (let i = 0; i < 100; i++) {{
                                const span = document.createElement('span');
                                span.textContent = `Item ${{i}}`;
                                tempDiv.appendChild(span);
                            }}
                            return tempDiv.children.length;
                        }};

                        let workIteration = 0;
                        const workInterval = setInterval(() => {{
                            const workStart = performance.now();

                            // Rotate between different types of work
                            let workResult;
                            switch (workIteration % 3) {{
                                case 0:
                                    workResult = performCPUWork();
                                    break;
                                case 1:
                                    workResult = performArrayWork();
                                    break;
                                case 2:
                                    workResult = performDOMWork();
                                    break;
                            }}

                            const workDuration = performance.now() - workStart;

                            cpuAnalysis.performance_timeline.push({{
                                iteration: workIteration,
                                work_type: ['cpu_math', 'array_ops', 'dom_ops'][workIteration % 3],
                                duration_ms: workDuration,
                                timestamp: performance.now(),
                                result: typeof workResult === 'number' ? workResult : workResult.length || 0
                            }});

                            workIteration++;
                        }}, 200); // Every 200ms

                        // Stack trace sampling (if enabled)
                        if ({str(sample_stack_traces).lower()}) {{
                            const stackSamplingInterval = setInterval(() => {{
                                try {{
                                    const stack = new Error().stack;
                                    if (stack) {{
                                        cpuAnalysis.stack_samples.push({{
                                            timestamp: performance.now(),
                                            stack_trace: stack.split('\\n').slice(1, 6), // Top 5 stack frames
                                            sample_id: cpuAnalysis.stack_samples.length
                                        }});
                                    }}
                                }} catch (e) {{
                                    // Stack sampling failed
                                }}
                            }}, 50); // Sample every 50ms

                            cpuAnalysis.stack_sampling_interval = stackSamplingInterval;
                        }}

                        // Function call tracking (simplified)
                        if ({str(analyze_hot_functions).lower()}) {{
                            const originalConsoleLog = console.log;
                            let logCallCount = 0;

                            console.log = function(...args) {{
                                logCallCount++;
                                cpuAnalysis.function_calls.console_log = logCallCount;
                                return originalConsoleLog.apply(this, args);
                            }};

                            // Track setTimeout calls
                            const originalSetTimeout = window.setTimeout;
                            let timeoutCallCount = 0;

                            window.setTimeout = function(...args) {{
                                timeoutCallCount++;
                                cpuAnalysis.function_calls.setTimeout = timeoutCallCount;
                                return originalSetTimeout.apply(this, args);
                            }};
                        }}

                        // Finish profiling after duration
                        setTimeout(() => {{
                            clearInterval(workInterval);

                            if (cpuAnalysis.stack_sampling_interval) {{
                                clearInterval(cpuAnalysis.stack_sampling_interval);
                            }}

                            cpuAnalysis.end_time = performance.now();
                            cpuAnalysis.total_duration_ms = cpuAnalysis.end_time - cpuAnalysis.start_time;

                            // Analyze performance timeline
                            if (cpuAnalysis.performance_timeline.length > 0) {{
                                const timeline = cpuAnalysis.performance_timeline;
                                const workTypes = {{}};

                                timeline.forEach(entry => {{
                                    if (!workTypes[entry.work_type]) {{
                                        workTypes[entry.work_type] = {{
                                            count: 0,
                                            total_duration: 0,
                                            avg_duration: 0,
                                            max_duration: 0
                                        }};
                                    }}

                                    workTypes[entry.work_type].count++;
                                    workTypes[entry.work_type].total_duration += entry.duration_ms;
                                    workTypes[entry.work_type].max_duration = Math.max(
                                        workTypes[entry.work_type].max_duration,
                                        entry.duration_ms
                                    );
                                }});

                                // Calculate averages
                                Object.keys(workTypes).forEach(type => {{
                                    workTypes[type].avg_duration = workTypes[type].total_duration / workTypes[type].count;
                                }});

                                cpuAnalysis.work_type_analysis = workTypes;

                                // Overall performance metrics
                                const allDurations = timeline.map(t => t.duration_ms);
                                cpuAnalysis.performance_summary = {{
                                    total_work_iterations: timeline.length,
                                    avg_work_duration: allDurations.reduce((a, b) => a + b, 0) / allDurations.length,
                                    max_work_duration: Math.max(...allDurations),
                                    min_work_duration: Math.min(...allDurations),
                                    work_efficiency_score: Math.max(0, 100 - (Math.max(...allDurations) - Math.min(...allDurations)))
                                }};
                            }}

                            // Stack trace analysis
                            if (cpuAnalysis.stack_samples.length > 0) {{
                                const functionFrequency = {{}};
                                cpuAnalysis.stack_samples.forEach(sample => {{
                                    sample.stack_trace.forEach(frame => {{
                                        if (frame && frame.includes('at ')) {{
                                            const functionName = frame.split('at ')[1]?.split(' ')[0] || 'anonymous';
                                            functionFrequency[functionName] = (functionFrequency[functionName] || 0) + 1;
                                        }}
                                    }});
                                }});

                                cpuAnalysis.hot_functions = Object.entries(functionFrequency)
                                    .sort(([,a], [,b]) => b - a)
                                    .slice(0, 10)
                                    .map(([func, count]) => ({{
                                        function_name: func,
                                        sample_count: count,
                                        percentage: (count / cpuAnalysis.stack_samples.length) * 100
                                    }}));
                            }}

                            resolve(cpuAnalysis);
                        }}, {profiling_duration * 1000});
                    }});
                }})()
            """

            # Start the CPU analysis
            analysis_result = cdp.send_command('Runtime.evaluate', {
                'expression': cpu_analysis_code,
                'returnByValue': True,
                'awaitPromise': True,
                'timeout': (profiling_duration + 10) * 1000
            })

            # Stop profiling and get results
            stop_result = cdp.send_command('Profiler.stop')

            profiling_data = {
                "cpu_analysis": analysis_result.get('result', {}).get('result', {}).get('value'),
                "profiler_data": stop_result.get('result', {}).get('profile') if 'result' in stop_result else None
            }

            # Clean up
            cdp.send_command('Profiler.disable')

            # Track endpoint usage
            track_endpoint_usage("profile_cpu_usage", [CDPDomain.PERFORMANCE], data)

            return jsonify(create_success_response({
                "cpu_profiling": profiling_data,
                "profiling_parameters": {
                    "profiling_duration": profiling_duration,
                    "sample_stack_traces": sample_stack_traces,
                    "analyze_hot_functions": analyze_hot_functions,
                    "profiling_mode": profiling_mode
                }
            }, "profile_cpu_usage", [CDPDomain.PERFORMANCE]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("profile_cpu_usage", e, data, "profile_cpu_usage")


@performance_routes.route('/cdp/performance/resource_timing', methods=['GET', 'POST'])
def analyze_resource_timing():
    """
    Analyze resource loading performance and identify optimization opportunities

    @route GET/POST /cdp/performance/resource_timing
    @param {number} [analysis_period] - Period to analyze in seconds
    @param {boolean} [include_third_party] - Include third-party resources
    @param {boolean} [detect_blocking] - Detect render-blocking resources
    @param {string} [resource_filter] - Filter by resource type
    @returns {object} Resource timing analysis

    @example
    // Basic resource timing analysis
    GET /cdp/performance/resource_timing

    // Comprehensive resource analysis
    POST {
      "analysis_period": 10,
      "include_third_party": true,
      "detect_blocking": true,
      "resource_filter": "all"
    }
    """
    try:
        params = parse_request_params(request, ['analysis_period', 'include_third_party', 'detect_blocking', 'resource_filter'])
        analysis_period = int(params['analysis_period'] or 5)
        include_third_party = params['include_third_party'] in [True, 'true', '1']
        detect_blocking = params['detect_blocking'] in [True, 'true', '1']
        resource_filter = params['resource_filter'] or 'all'

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.PERFORMANCE, "analyze_resource_timing"):
            return create_domain_error_response(CDPDomain.PERFORMANCE, "analyze_resource_timing")

        if not ensure_domain_available(CDPDomain.RUNTIME, "analyze_resource_timing"):
            return create_domain_error_response(CDPDomain.RUNTIME, "analyze_resource_timing")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Resource timing analysis code
            resource_analysis_code = f"""
                (() => {{
                    const resourceAnalysis = {{
                        analysis_period: {analysis_period},
                        include_third_party: {str(include_third_party).lower()},
                        detect_blocking: {str(detect_blocking).lower()},
                        resource_filter: '{resource_filter}',
                        start_time: performance.now(),
                        resources: [],
                        timing_breakdown: {{}},
                        optimization_opportunities: [],
                        third_party_analysis: {{}},
                        blocking_resources: []
                    }};

                    // Get current resource timing entries
                    const currentResources = performance.getEntriesByType('resource');

                    currentResources.forEach(resource => {{
                        // Apply resource filter
                        if ('{resource_filter}' !== 'all') {{
                            if (resource.initiatorType !== '{resource_filter}') {{
                                return;
                            }}
                        }}

                        // Third-party detection
                        const isThirdParty = !resource.name.includes(window.location.hostname);
                        if (!{str(include_third_party).lower()} && isThirdParty) {{
                            return;
                        }}

                        const resourceData = {{
                            name: resource.name,
                            type: resource.initiatorType,
                            is_third_party: isThirdParty,
                            start_time: resource.startTime,
                            duration: resource.duration,
                            transfer_size: resource.transferSize,
                            encoded_size: resource.encodedBodySize,
                            decoded_size: resource.decodedBodySize,
                            cache_hit: resource.transferSize === 0 && resource.decodedBodySize > 0,
                            timing: {{
                                dns_lookup: resource.domainLookupEnd - resource.domainLookupStart,
                                tcp_connect: resource.connectEnd - resource.connectStart,
                                ssl_negotiate: resource.connectEnd - resource.secureConnectionStart,
                                request_sent: resource.requestStart - resource.connectEnd,
                                waiting: resource.responseStart - resource.requestStart,
                                content_download: resource.responseEnd - resource.responseStart
                            }}
                        }};

                        // Calculate efficiency metrics
                        resourceData.compression_ratio = resourceData.encoded_size > 0 ?
                            resourceData.decoded_size / resourceData.encoded_size : 1;

                        resourceData.speed_kbps = resourceData.transfer_size > 0 && resourceData.duration > 0 ?
                            (resourceData.transfer_size / 1024) / (resourceData.duration / 1000) : 0;

                        resourceAnalysis.resources.push(resourceData);
                    }});

                    // Analyze timing breakdown by resource type
                    const timingByType = {{}};
                    resourceAnalysis.resources.forEach(resource => {{
                        if (!timingByType[resource.type]) {{
                            timingByType[resource.type] = {{
                                count: 0,
                                total_duration: 0,
                                total_size: 0,
                                avg_duration: 0,
                                avg_size: 0,
                                cache_hit_rate: 0
                            }};
                        }}

                        const typeData = timingByType[resource.type];
                        typeData.count++;
                        typeData.total_duration += resource.duration;
                        typeData.total_size += resource.transfer_size;

                        if (resource.cache_hit) {{
                            typeData.cache_hits = (typeData.cache_hits || 0) + 1;
                        }}
                    }});

                    // Calculate averages
                    Object.keys(timingByType).forEach(type => {{
                        const data = timingByType[type];
                        data.avg_duration = data.total_duration / data.count;
                        data.avg_size = data.total_size / data.count;
                        data.cache_hit_rate = ((data.cache_hits || 0) / data.count) * 100;
                    }});

                    resourceAnalysis.timing_breakdown = timingByType;

                    // Detect render-blocking resources
                    if ({str(detect_blocking).lower()}) {{
                        resourceAnalysis.resources.forEach(resource => {{
                            let isBlocking = false;
                            let blockingReason = [];

                            // CSS files are typically render-blocking
                            if (resource.type === 'link' && resource.name.includes('.css')) {{
                                isBlocking = true;
                                blockingReason.push('CSS file blocks rendering');
                            }}

                            // Synchronous scripts in head are render-blocking
                            if (resource.type === 'script' && resource.start_time < 1000) {{ // Early loading
                                isBlocking = true;
                                blockingReason.push('Early script may block rendering');
                            }}

                            // Large resources that load early
                            if (resource.transfer_size > 100000 && resource.start_time < 2000) {{ // >100KB, early load
                                isBlocking = true;
                                blockingReason.push('Large resource loads early');
                            }}

                            if (isBlocking) {{
                                resourceAnalysis.blocking_resources.push({{
                                    name: resource.name,
                                    type: resource.type,
                                    size: resource.transfer_size,
                                    duration: resource.duration,
                                    reasons: blockingReason
                                }});
                            }}
                        }});
                    }}

                    // Third-party analysis
                    if ({str(include_third_party).lower()}) {{
                        const thirdPartyResources = resourceAnalysis.resources.filter(r => r.is_third_party);

                        if (thirdPartyResources.length > 0) {{
                            const thirdPartyDomains = {{}};
                            let totalThirdPartySize = 0;
                            let totalThirdPartyTime = 0;

                            thirdPartyResources.forEach(resource => {{
                                try {{
                                    const domain = new URL(resource.name).hostname;
                                    if (!thirdPartyDomains[domain]) {{
                                        thirdPartyDomains[domain] = {{
                                            count: 0,
                                            total_size: 0,
                                            total_time: 0
                                        }};
                                    }}

                                    thirdPartyDomains[domain].count++;
                                    thirdPartyDomains[domain].total_size += resource.transfer_size;
                                    thirdPartyDomains[domain].total_time += resource.duration;

                                    totalThirdPartySize += resource.transfer_size;
                                    totalThirdPartyTime += resource.duration;
                                }} catch (e) {{
                                    // Invalid URL
                                }}
                            }});

                            resourceAnalysis.third_party_analysis = {{
                                total_third_party_resources: thirdPartyResources.length,
                                total_third_party_size_kb: Math.round(totalThirdPartySize / 1024),
                                total_third_party_time_ms: totalThirdPartyTime,
                                third_party_domains: Object.entries(thirdPartyDomains)
                                    .sort(([,a], [,b]) => b.total_size - a.total_size)
                                    .slice(0, 10)
                                    .map(([domain, data]) => ({{
                                        domain,
                                        resource_count: data.count,
                                        total_size_kb: Math.round(data.total_size / 1024),
                                        total_time_ms: data.total_time
                                    }}))
                            }};
                        }}
                    }}

                    // Identify optimization opportunities
                    resourceAnalysis.resources.forEach(resource => {{
                        // Large uncompressed resources
                        if (resource.compression_ratio < 1.5 && resource.transfer_size > 50000) {{
                            resourceAnalysis.optimization_opportunities.push({{
                                type: 'compression',
                                resource: resource.name,
                                issue: 'Large resource with poor compression',
                                potential_savings_kb: Math.round((resource.transfer_size * 0.7) / 1024),
                                priority: 'high'
                            }});
                        }}

                        // Slow loading resources
                        if (resource.speed_kbps > 0 && resource.speed_kbps < 100) {{ // Less than 100 KB/s
                            resourceAnalysis.optimization_opportunities.push({{
                                type: 'slow_loading',
                                resource: resource.name,
                                issue: `Slow loading speed: ${{Math.round(resource.speed_kbps)}} KB/s`,
                                suggestion: 'Consider CDN or compression',
                                priority: 'medium'
                            }});
                        }}

                        // Resources with long DNS lookup
                        if (resource.timing.dns_lookup > 100) {{
                            resourceAnalysis.optimization_opportunities.push({{
                                type: 'dns_lookup',
                                resource: resource.name,
                                issue: `Long DNS lookup: ${{Math.round(resource.timing.dns_lookup)}}ms`,
                                suggestion: 'Consider DNS prefetch or connection preload',
                                priority: 'low'
                            }});
                        }}

                        // Resources with long SSL negotiation
                        if (resource.timing.ssl_negotiate > 200) {{
                            resourceAnalysis.optimization_opportunities.push({{
                                type: 'ssl_negotiate',
                                resource: resource.name,
                                issue: `Long SSL negotiation: ${{Math.round(resource.timing.ssl_negotiate)}}ms`,
                                suggestion: 'Consider connection keep-alive or HTTP/2',
                                priority: 'medium'
                            }});
                        }}
                    }});

                    // Overall performance metrics
                    const totalResources = resourceAnalysis.resources.length;
                    const totalSize = resourceAnalysis.resources.reduce((sum, r) => sum + r.transfer_size, 0);
                    const totalTime = resourceAnalysis.resources.reduce((sum, r) => sum + r.duration, 0);
                    const cacheHits = resourceAnalysis.resources.filter(r => r.cache_hit).length;

                    resourceAnalysis.performance_summary = {{
                        total_resources: totalResources,
                        total_size_kb: Math.round(totalSize / 1024),
                        total_loading_time_ms: totalTime,
                        cache_hit_rate: totalResources > 0 ? (cacheHits / totalResources) * 100 : 0,
                        avg_resource_size_kb: totalResources > 0 ? Math.round(totalSize / totalResources / 1024) : 0,
                        blocking_resources_count: resourceAnalysis.blocking_resources.length,
                        optimization_opportunities_count: resourceAnalysis.optimization_opportunities.length
                    }};

                    return resourceAnalysis;
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': resource_analysis_code,
                'returnByValue': True,
                'timeout': 15000
            })

            resource_data = result.get('result', {}).get('result', {}).get('value')

            # Track endpoint usage
            track_endpoint_usage("analyze_resource_timing", [CDPDomain.PERFORMANCE, CDPDomain.RUNTIME], params)

            return jsonify(create_success_response({
                "resource_timing_analysis": resource_data,
                "analysis_parameters": {
                    "analysis_period": analysis_period,
                    "include_third_party": include_third_party,
                    "detect_blocking": detect_blocking,
                    "resource_filter": resource_filter
                }
            }, "analyze_resource_timing", [CDPDomain.PERFORMANCE, CDPDomain.RUNTIME]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("analyze_resource_timing", e, params, "analyze_resource_timing")


@performance_routes.route('/cdp/performance/background_tasks', methods=['GET', 'POST'])
def monitor_background_tasks():
    """
    Monitor background tasks and service worker performance

    @route GET/POST /cdp/performance/background_tasks
    @param {number} [monitoring_duration] - Duration to monitor in seconds
    @param {boolean} [track_service_workers] - Track service worker activity
    @param {boolean} [monitor_web_workers] - Monitor web worker performance
    @param {boolean} [detect_heavy_tasks] - Detect CPU-heavy background tasks
    @returns {object} Background task monitoring data

    @example
    // Basic background task monitoring
    GET /cdp/performance/background_tasks

    // Comprehensive background monitoring
    POST {
      "monitoring_duration": 15,
      "track_service_workers": true,
      "monitor_web_workers": true,
      "detect_heavy_tasks": true
    }
    """
    try:
        params = parse_request_params(request, ['monitoring_duration', 'track_service_workers', 'monitor_web_workers', 'detect_heavy_tasks'])
        monitoring_duration = int(params['monitoring_duration'] or 8)
        track_service_workers = params['track_service_workers'] in [True, 'true', '1']
        monitor_web_workers = params['monitor_web_workers'] in [True, 'true', '1']
        detect_heavy_tasks = params['detect_heavy_tasks'] in [True, 'true', '1']

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.RUNTIME, "monitor_background_tasks"):
            return create_domain_error_response(CDPDomain.RUNTIME, "monitor_background_tasks")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Background task monitoring code
            background_monitor_code = f"""
                (() => {{
                    return new Promise((resolve) => {{
                        const backgroundMonitor = {{
                            monitoring_duration: {monitoring_duration},
                            track_service_workers: {str(track_service_workers).lower()},
                            monitor_web_workers: {str(monitor_web_workers).lower()},
                            detect_heavy_tasks: {str(detect_heavy_tasks).lower()},
                            start_time: performance.now(),
                            background_tasks: [],
                            service_worker_activity: [],
                            web_worker_activity: [],
                            heavy_tasks: [],
                            task_performance_metrics: {{}}
                        }};

                        // Monitor Service Worker activity
                        if ({str(track_service_workers).lower()} && 'serviceWorker' in navigator) {{
                            const serviceWorkerMonitor = () => {{
                                const registration = navigator.serviceWorker.controller;
                                if (registration) {{
                                    backgroundMonitor.service_worker_activity.push({{
                                        timestamp: performance.now(),
                                        state: registration.state,
                                        script_url: registration.scriptURL,
                                        scope: navigator.serviceWorker.scope || 'unknown'
                                    }});
                                }}

                                // Check for service worker messages
                                navigator.serviceWorker.addEventListener('message', (event) => {{
                                    backgroundMonitor.service_worker_activity.push({{
                                        timestamp: performance.now(),
                                        type: 'message',
                                        data: typeof event.data === 'string' ? event.data : JSON.stringify(event.data).substring(0, 100)
                                    }});
                                }});
                            }};

                            // Initial check and periodic monitoring
                            serviceWorkerMonitor();
                            const swInterval = setInterval(serviceWorkerMonitor, 1000);
                            backgroundMonitor.sw_interval = swInterval;
                        }}

                        // Monitor Web Workers
                        if ({str(monitor_web_workers).lower()}) {{
                            // Track existing workers (if any)
                            backgroundMonitor.initial_worker_count = 0; // Simplified tracking

                            // Create a test worker to monitor worker creation performance
                            try {{
                                const workerBlob = new Blob([`
                                    self.onmessage = function(e) {{
                                        const start = performance.now();
                                        // Simulate some work
                                        let result = 0;
                                        for (let i = 0; i < e.data.iterations; i++) {{
                                            result += Math.sqrt(i);
                                        }}
                                        const duration = performance.now() - start;
                                        self.postMessage({{result, duration, iterations: e.data.iterations}});
                                    }}
                                `], {{type: 'application/javascript'}});

                                const workerURL = URL.createObjectURL(workerBlob);
                                const testWorker = new Worker(workerURL);

                                let workerTaskCount = 0;
                                const sendWorkerTask = () => {{
                                    const iterations = 10000 + (workerTaskCount * 5000); // Increasing complexity
                                    const taskStart = performance.now();

                                    testWorker.postMessage({{iterations}});

                                    testWorker.onmessage = (e) => {{
                                        const taskEnd = performance.now();
                                        const totalDuration = taskEnd - taskStart;

                                        backgroundMonitor.web_worker_activity.push({{
                                            task_id: workerTaskCount,
                                            iterations: e.data.iterations,
                                            worker_duration_ms: e.data.duration,
                                            total_duration_ms: totalDuration,
                                            message_overhead_ms: totalDuration - e.data.duration,
                                            timestamp: taskEnd
                                        }});

                                        workerTaskCount++;
                                    }};
                                }};

                                // Send periodic tasks to worker
                                const workerInterval = setInterval(sendWorkerTask, 1500);
                                backgroundMonitor.worker_interval = workerInterval;
                                backgroundMonitor.test_worker = testWorker;

                            }} catch (workerError) {{
                                backgroundMonitor.worker_error = workerError.message;
                            }}
                        }}

                        // Monitor for heavy background tasks using Long Task Observer
                        if ({str(detect_heavy_tasks).lower()} && 'PerformanceObserver' in window) {{
                            try {{
                                const longTaskObserver = new PerformanceObserver((list) => {{
                                    const entries = list.getEntries();
                                    entries.forEach(entry => {{
                                        backgroundMonitor.heavy_tasks.push({{
                                            name: entry.name,
                                            entry_type: entry.entryType,
                                            start_time: entry.startTime,
                                            duration: entry.duration,
                                            attribution: entry.attribution ? entry.attribution.map(attr => ({{
                                                name: attr.name,
                                                container_type: attr.containerType,
                                                container_src: attr.containerSrc,
                                                container_id: attr.containerId,
                                                container_name: attr.containerName
                                            }})) : []
                                        }});
                                    }});
                                }});

                                longTaskObserver.observe({{entryTypes: ['longtask']}});
                                backgroundMonitor.long_task_observer = longTaskObserver;
                            }} catch (observerError) {{
                                backgroundMonitor.long_task_observer_error = observerError.message;
                            }}
                        }}

                        // Create some background tasks for monitoring
                        const createBackgroundTask = (taskType, intensity) => {{
                            const taskStart = performance.now();

                            return new Promise((taskResolve) => {{
                                const runTask = () => {{
                                    let result = 0;
                                    const iterations = intensity * 1000;

                                    switch (taskType) {{
                                        case 'computation':
                                            for (let i = 0; i < iterations; i++) {{
                                                result += Math.sqrt(i) * Math.sin(i / 100);
                                            }}
                                            break;
                                        case 'array_processing':
                                            const arr = Array.from({{length: iterations}}, (_, i) => i);
                                            result = arr.map(x => x * 2).filter(x => x % 3 === 0).length;
                                            break;
                                        case 'string_manipulation':
                                            let str = 'test';
                                            for (let i = 0; i < iterations / 100; i++) {{
                                                str += Math.random().toString(36).substring(7);
                                            }}
                                            result = str.length;
                                            break;
                                    }}

                                    const taskEnd = performance.now();

                                    backgroundMonitor.background_tasks.push({{
                                        task_type: taskType,
                                        intensity: intensity,
                                        duration_ms: taskEnd - taskStart,
                                        result: result,
                                        timestamp: taskEnd
                                    }});

                                    taskResolve(result);
                                }};

                                // Run task with a small delay to simulate background execution
                                setTimeout(runTask, 10);
                            }});
                        }};

                        // Execute background tasks periodically
                        let taskCounter = 0;
                        const taskTypes = ['computation', 'array_processing', 'string_manipulation'];

                        const taskInterval = setInterval(async () => {{
                            const taskType = taskTypes[taskCounter % taskTypes.length];
                            const intensity = 5 + (taskCounter % 3) * 5; // Varying intensity

                            await createBackgroundTask(taskType, intensity);
                            taskCounter++;
                        }}, 800);

                        backgroundMonitor.task_interval = taskInterval;

                        // Finish monitoring after duration
                        setTimeout(() => {{
                            // Clean up intervals and observers
                            if (backgroundMonitor.sw_interval) clearInterval(backgroundMonitor.sw_interval);
                            if (backgroundMonitor.worker_interval) clearInterval(backgroundMonitor.worker_interval);
                            if (backgroundMonitor.task_interval) clearInterval(backgroundMonitor.task_interval);
                            if (backgroundMonitor.long_task_observer) backgroundMonitor.long_task_observer.disconnect();
                            if (backgroundMonitor.test_worker) backgroundMonitor.test_worker.terminate();

                            backgroundMonitor.end_time = performance.now();
                            backgroundMonitor.total_duration_ms = backgroundMonitor.end_time - backgroundMonitor.start_time;

                            // Analyze background task performance
                            if (backgroundMonitor.background_tasks.length > 0) {{
                                const tasks = backgroundMonitor.background_tasks;
                                const tasksByType = {{}};

                                tasks.forEach(task => {{
                                    if (!tasksByType[task.task_type]) {{
                                        tasksByType[task.task_type] = {{
                                            count: 0,
                                            total_duration: 0,
                                            avg_duration: 0,
                                            max_duration: 0,
                                            min_duration: Infinity
                                        }};
                                    }}

                                    const typeData = tasksByType[task.task_type];
                                    typeData.count++;
                                    typeData.total_duration += task.duration_ms;
                                    typeData.max_duration = Math.max(typeData.max_duration, task.duration_ms);
                                    typeData.min_duration = Math.min(typeData.min_duration, task.duration_ms);
                                }});

                                // Calculate averages
                                Object.keys(tasksByType).forEach(type => {{
                                    tasksByType[type].avg_duration = tasksByType[type].total_duration / tasksByType[type].count;
                                }});

                                backgroundMonitor.task_performance_metrics = {{
                                    total_background_tasks: tasks.length,
                                    avg_task_duration: tasks.reduce((sum, t) => sum + t.duration_ms, 0) / tasks.length,
                                    task_breakdown: tasksByType,
                                    performance_overhead: (tasks.reduce((sum, t) => sum + t.duration_ms, 0) / backgroundMonitor.total_duration_ms) * 100
                                }};
                            }}

                            // Web Worker analysis
                            if (backgroundMonitor.web_worker_activity.length > 0) {{
                                const workerTasks = backgroundMonitor.web_worker_activity;
                                backgroundMonitor.worker_performance = {{
                                    total_worker_tasks: workerTasks.length,
                                    avg_worker_duration: workerTasks.reduce((sum, t) => sum + t.worker_duration_ms, 0) / workerTasks.length,
                                    avg_message_overhead: workerTasks.reduce((sum, t) => sum + t.message_overhead_ms, 0) / workerTasks.length,
                                    worker_efficiency: workerTasks.length > 0 ?
                                        (workerTasks.reduce((sum, t) => sum + t.worker_duration_ms, 0) /
                                         workerTasks.reduce((sum, t) => sum + t.total_duration_ms, 0)) * 100 : 0
                                }};
                            }}

                            // Heavy task analysis
                            if (backgroundMonitor.heavy_tasks.length > 0) {{
                                backgroundMonitor.heavy_task_analysis = {{
                                    total_heavy_tasks: backgroundMonitor.heavy_tasks.length,
                                    avg_heavy_task_duration: backgroundMonitor.heavy_tasks.reduce((sum, t) => sum + t.duration, 0) / backgroundMonitor.heavy_tasks.length,
                                    max_heavy_task_duration: Math.max(...backgroundMonitor.heavy_tasks.map(t => t.duration)),
                                    heavy_task_impact_percent: (backgroundMonitor.heavy_tasks.reduce((sum, t) => sum + t.duration, 0) / backgroundMonitor.total_duration_ms) * 100
                                }};
                            }}

                            resolve(backgroundMonitor);
                        }}, {monitoring_duration * 1000});
                    }});
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': background_monitor_code,
                'returnByValue': True,
                'awaitPromise': True,
                'timeout': (monitoring_duration + 15) * 1000
            })

            background_data = result.get('result', {}).get('result', {}).get('value')

            # Track endpoint usage
            track_endpoint_usage("monitor_background_tasks", [CDPDomain.RUNTIME], params)

            return jsonify(create_success_response({
                "background_task_monitoring": background_data,
                "monitoring_parameters": {
                    "monitoring_duration": monitoring_duration,
                    "track_service_workers": track_service_workers,
                    "monitor_web_workers": monitor_web_workers,
                    "detect_heavy_tasks": detect_heavy_tasks
                }
            }, "monitor_background_tasks", [CDPDomain.RUNTIME]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("monitor_background_tasks", e, params, "monitor_background_tasks")


@performance_routes.route('/cdp/performance/optimization_recommendations', methods=['GET', 'POST'])
def generate_optimization_recommendations():
    """
    Generate comprehensive performance optimization recommendations

    @route GET/POST /cdp/performance/optimization_recommendations
    @param {boolean} [analyze_resources] - Analyze resource optimization opportunities
    @param {boolean} [analyze_scripts] - Analyze script performance issues
    @param {boolean} [analyze_styles] - Analyze CSS and style performance
    @param {string} [priority_filter] - Filter by priority: 'high', 'medium', 'low', 'all'
    @returns {object} Performance optimization recommendations

    @example
    // Basic optimization recommendations
    GET /cdp/performance/optimization_recommendations

    // Comprehensive optimization analysis
    POST {
      "analyze_resources": true,
      "analyze_scripts": true,
      "analyze_styles": true,
      "priority_filter": "all"
    }
    """
    try:
        params = parse_request_params(request, ['analyze_resources', 'analyze_scripts', 'analyze_styles', 'priority_filter'])
        analyze_resources = params['analyze_resources'] in [True, 'true', '1']
        analyze_scripts = params['analyze_scripts'] in [True, 'true', '1']
        analyze_styles = params['analyze_styles'] in [True, 'true', '1']
        priority_filter = params['priority_filter'] or 'all'

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.RUNTIME, "generate_optimization_recommendations"):
            return create_domain_error_response(CDPDomain.RUNTIME, "generate_optimization_recommendations")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Optimization analysis code
            optimization_code = f"""
                (() => {{
                    const optimizationAnalysis = {{
                        analyze_resources: {str(analyze_resources).lower()},
                        analyze_scripts: {str(analyze_scripts).lower()},
                        analyze_styles: {str(analyze_styles).lower()},
                        priority_filter: '{priority_filter}',
                        analysis_start: performance.now(),
                        recommendations: [],
                        resource_analysis: {{}},
                        script_analysis: {{}},
                        style_analysis: {{}},
                        performance_budget: {{}}
                    }};

                    // Resource optimization analysis
                    if ({str(analyze_resources).lower()}) {{
                        const resources = performance.getEntriesByType('resource');
                        const resourceStats = {{
                            total_resources: resources.length,
                            total_size_bytes: 0,
                            large_resources: [],
                            slow_resources: [],
                            uncompressed_resources: []
                        }};

                        resources.forEach(resource => {{
                            resourceStats.total_size_bytes += resource.transferSize || 0;

                            // Identify large resources (>500KB)
                            if (resource.transferSize > 500000) {{
                                resourceStats.large_resources.push({{
                                    name: resource.name,
                                    size_kb: Math.round(resource.transferSize / 1024),
                                    type: resource.initiatorType
                                }});

                                optimizationAnalysis.recommendations.push({{
                                    category: 'resource_optimization',
                                    priority: 'high',
                                    title: 'Large Resource Detected',
                                    description: `Resource ${{resource.name.split('/').pop()}} is ${{Math.round(resource.transferSize / 1024)}}KB`,
                                    recommendation: 'Consider compression, code splitting, or lazy loading',
                                    potential_savings: `${{Math.round(resource.transferSize * 0.6 / 1024)}}KB with compression`,
                                    technical_details: {{
                                        resource_url: resource.name,
                                        current_size: resource.transferSize,
                                        resource_type: resource.initiatorType
                                    }}
                                }});
                            }}

                            // Identify slow loading resources (>3 seconds)
                            if (resource.duration > 3000) {{
                                resourceStats.slow_resources.push({{
                                    name: resource.name,
                                    duration_ms: resource.duration,
                                    type: resource.initiatorType
                                }});

                                optimizationAnalysis.recommendations.push({{
                                    category: 'resource_optimization',
                                    priority: 'medium',
                                    title: 'Slow Loading Resource',
                                    description: `Resource takes ${{Math.round(resource.duration / 1000)}}s to load`,
                                    recommendation: 'Optimize server response time, use CDN, or implement resource hints',
                                    potential_savings: `${{Math.round(resource.duration * 0.7)}}ms faster loading`,
                                    technical_details: {{
                                        resource_url: resource.name,
                                        current_duration: resource.duration,
                                        dns_time: resource.domainLookupEnd - resource.domainLookupStart,
                                        connect_time: resource.connectEnd - resource.connectStart
                                    }}
                                }});
                            }}

                            // Check for potential compression opportunities
                            const compressionRatio = resource.decodedBodySize > 0 ? resource.decodedBodySize / (resource.transferSize || 1) : 1;
                            if (compressionRatio < 2 && resource.transferSize > 10000) {{ // Less than 2:1 compression on files >10KB
                                resourceStats.uncompressed_resources.push({{
                                    name: resource.name,
                                    compression_ratio: compressionRatio,
                                    size_kb: Math.round(resource.transferSize / 1024)
                                }});

                                optimizationAnalysis.recommendations.push({{
                                    category: 'resource_optimization',
                                    priority: 'medium',
                                    title: 'Poor Compression Detected',
                                    description: `Resource has poor compression ratio (${{compressionRatio.toFixed(1)}}:1)`,
                                    recommendation: 'Enable gzip/brotli compression or optimize file format',
                                    potential_savings: `${{Math.round(resource.transferSize * 0.5 / 1024)}}KB with better compression`,
                                    technical_details: {{
                                        resource_url: resource.name,
                                        transfer_size: resource.transferSize,
                                        decoded_size: resource.decodedBodySize,
                                        compression_ratio: compressionRatio
                                    }}
                                }});
                            }}
                        }});

                        optimizationAnalysis.resource_analysis = resourceStats;
                    }}

                    // Script optimization analysis
                    if ({str(analyze_scripts).lower()}) {{
                        const scripts = Array.from(document.querySelectorAll('script'));
                        const scriptStats = {{
                            total_scripts: scripts.length,
                            external_scripts: 0,
                            blocking_scripts: 0,
                            large_inline_scripts: []
                        }};

                        scripts.forEach((script, index) => {{
                            if (script.src) {{
                                scriptStats.external_scripts++;

                                // Check if script lacks async/defer
                                if (!script.async && !script.defer) {{
                                    scriptStats.blocking_scripts++;

                                    optimizationAnalysis.recommendations.push({{
                                        category: 'script_optimization',
                                        priority: 'high',
                                        title: 'Render-Blocking Script',
                                        description: 'Script blocks HTML parsing and rendering',
                                        recommendation: 'Add async or defer attribute to non-critical scripts',
                                        potential_savings: 'Faster page load and improved FCP/LCP',
                                        technical_details: {{
                                            script_src: script.src,
                                            script_index: index,
                                            has_async: script.async,
                                            has_defer: script.defer
                                        }}
                                    }});
                                }}
                            }} else if (script.textContent && script.textContent.length > 1000) {{
                                // Large inline script
                                scriptStats.large_inline_scripts.push({{
                                    length: script.textContent.length,
                                    index: index
                                }});

                                optimizationAnalysis.recommendations.push({{
                                    category: 'script_optimization',
                                    priority: 'medium',
                                    title: 'Large Inline Script',
                                    description: `Inline script is ${{Math.round(script.textContent.length / 1024)}}KB`,
                                    recommendation: 'Move large inline scripts to external files for better caching',
                                    potential_savings: 'Better caching and reduced HTML size',
                                    technical_details: {{
                                        script_size: script.textContent.length,
                                        script_index: index,
                                        suggestion: 'externalize_script'
                                    }}
                                }});
                            }}
                        }});

                        // Check for duplicate script loading
                        const scriptSources = scripts.map(s => s.src).filter(src => src);
                        const duplicateSources = scriptSources.filter((src, index) => scriptSources.indexOf(src) !== index);
                        if (duplicateSources.length > 0) {{
                            optimizationAnalysis.recommendations.push({{
                                category: 'script_optimization',
                                priority: 'high',
                                title: 'Duplicate Script Loading',
                                description: `${{duplicateSources.length}} scripts are loaded multiple times`,
                                recommendation: 'Remove duplicate script tags and consolidate dependencies',
                                potential_savings: 'Reduced bandwidth and faster load times',
                                technical_details: {{
                                    duplicate_scripts: duplicateSources,
                                    duplicate_count: duplicateSources.length
                                }}
                            }});
                        }}

                        optimizationAnalysis.script_analysis = scriptStats;
                    }}

                    // Style optimization analysis
                    if ({str(analyze_styles).lower()}) {{
                        const stylesheets = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
                        const inlineStyles = Array.from(document.querySelectorAll('style'));
                        const styleStats = {{
                            external_stylesheets: stylesheets.length,
                            inline_styles: inlineStyles.length,
                            blocking_stylesheets: 0,
                            large_inline_styles: []
                        }};

                        // Analyze external stylesheets
                        stylesheets.forEach((link, index) => {{
                            // CSS files are render-blocking by default
                            if (!link.media || link.media === 'all' || link.media === 'screen') {{
                                styleStats.blocking_stylesheets++;

                                optimizationAnalysis.recommendations.push({{
                                    category: 'style_optimization',
                                    priority: 'medium',
                                    title: 'Render-Blocking CSS',
                                    description: 'CSS file blocks rendering until loaded',
                                    recommendation: 'Consider critical CSS inlining or media queries for non-critical styles',
                                    potential_savings: 'Faster First Contentful Paint (FCP)',
                                    technical_details: {{
                                        stylesheet_href: link.href,
                                        media_query: link.media || 'all',
                                        stylesheet_index: index
                                    }}
                                }});
                            }}
                        }});

                        // Analyze inline styles
                        inlineStyles.forEach((style, index) => {{
                            if (style.textContent && style.textContent.length > 2000) {{
                                styleStats.large_inline_styles.push({{
                                    length: style.textContent.length,
                                    index: index
                                }});

                                optimizationAnalysis.recommendations.push({{
                                    category: 'style_optimization',
                                    priority: 'low',
                                    title: 'Large Inline CSS',
                                    description: `Inline CSS is ${{Math.round(style.textContent.length / 1024)}}KB`,
                                    recommendation: 'Move large inline CSS to external files for better caching',
                                    potential_savings: 'Better caching and reduced HTML size',
                                    technical_details: {{
                                        style_size: style.textContent.length,
                                        style_index: index
                                    }}
                                }});
                            }}
                        }});

                        optimizationAnalysis.style_analysis = styleStats;
                    }}

                    // Performance budget analysis
                    if (performance.memory) {{
                        const memoryUsage = performance.memory.usedJSHeapSize / 1024 / 1024; // MB
                        const memoryLimit = performance.memory.jsHeapSizeLimit / 1024 / 1024; // MB

                        if (memoryUsage > 50) {{ // More than 50MB
                            optimizationAnalysis.recommendations.push({{
                                category: 'performance_budget',
                                priority: 'high',
                                title: 'High Memory Usage',
                                description: `JavaScript heap uses ${{Math.round(memoryUsage)}}MB`,
                                recommendation: 'Investigate memory leaks and optimize large object allocations',
                                potential_savings: 'Reduced memory pressure and better performance',
                                technical_details: {{
                                    memory_used_mb: memoryUsage,
                                    memory_limit_mb: memoryLimit,
                                    usage_percentage: (memoryUsage / memoryLimit) * 100
                                }}
                            }});
                        }}

                        optimizationAnalysis.performance_budget = {{
                            memory_used_mb: memoryUsage,
                            memory_limit_mb: memoryLimit,
                            memory_usage_percentage: (memoryUsage / memoryLimit) * 100
                        }};
                    }}

                    // General performance recommendations
                    const navTiming = performance.getEntriesByType('navigation')[0];
                    if (navTiming) {{
                        // Large DOM size check
                        const domElements = document.querySelectorAll('*').length;
                        if (domElements > 1500) {{
                            optimizationAnalysis.recommendations.push({{
                                category: 'performance_budget',
                                priority: 'medium',
                                title: 'Large DOM Size',
                                description: `Page has ${{domElements}} DOM elements`,
                                recommendation: 'Reduce DOM complexity, use virtualization for large lists',
                                potential_savings: 'Faster rendering and reduced memory usage',
                                technical_details: {{
                                    dom_element_count: domElements,
                                    recommended_max: 1500
                                }}
                            }});
                        }}

                        // DNS lookup time
                        const dnsTime = navTiming.domainLookupEnd - navTiming.domainLookupStart;
                        if (dnsTime > 200) {{
                            optimizationAnalysis.recommendations.push({{
                                category: 'network_optimization',
                                priority: 'low',
                                title: 'Slow DNS Lookup',
                                description: `DNS lookup takes ${{Math.round(dnsTime)}}ms`,
                                recommendation: 'Use DNS prefetch for external domains or consider faster DNS provider',
                                potential_savings: `${{Math.round(dnsTime * 0.7)}}ms faster page load`,
                                technical_details: {{
                                    dns_lookup_time: dnsTime,
                                    recommended_max: 200
                                }}
                            }});
                        }}
                    }}

                    // Filter recommendations by priority if specified
                    if ('{priority_filter}' !== 'all') {{
                        optimizationAnalysis.recommendations = optimizationAnalysis.recommendations.filter(
                            rec => rec.priority === '{priority_filter}'
                        );
                    }}

                    // Sort recommendations by priority
                    const priorityOrder = {{'high': 3, 'medium': 2, 'low': 1}};
                    optimizationAnalysis.recommendations.sort((a, b) =>
                        priorityOrder[b.priority] - priorityOrder[a.priority]
                    );

                    // Generate optimization summary
                    const summary = {{
                        total_recommendations: optimizationAnalysis.recommendations.length,
                        high_priority: optimizationAnalysis.recommendations.filter(r => r.priority === 'high').length,
                        medium_priority: optimizationAnalysis.recommendations.filter(r => r.priority === 'medium').length,
                        low_priority: optimizationAnalysis.recommendations.filter(r => r.priority === 'low').length,
                        categories: {{}}
                    }};

                    // Count by category
                    optimizationAnalysis.recommendations.forEach(rec => {{
                        summary.categories[rec.category] = (summary.categories[rec.category] || 0) + 1;
                    }});

                    optimizationAnalysis.optimization_summary = summary;
                    optimizationAnalysis.analysis_end = performance.now();
                    optimizationAnalysis.analysis_duration_ms = optimizationAnalysis.analysis_end - optimizationAnalysis.analysis_start;

                    return optimizationAnalysis;
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': optimization_code,
                'returnByValue': True,
                'timeout': 20000
            })

            optimization_data = result.get('result', {}).get('result', {}).get('value')

            # Track endpoint usage
            track_endpoint_usage("generate_optimization_recommendations", [CDPDomain.RUNTIME], params)

            return jsonify(create_success_response({
                "optimization_recommendations": optimization_data,
                "analysis_parameters": {
                    "analyze_resources": analyze_resources,
                    "analyze_scripts": analyze_scripts,
                    "analyze_styles": analyze_styles,
                    "priority_filter": priority_filter
                }
            }, "generate_optimization_recommendations", [CDPDomain.RUNTIME]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("generate_optimization_recommendations", e, params, "generate_optimization_recommendations")


@performance_routes.route('/cdp/performance/core_web_vitals', methods=['GET', 'POST'])
def monitor_core_web_vitals():
    """
    Monitor Core Web Vitals metrics in real-time

    @route GET/POST /cdp/performance/core_web_vitals
    @param {number} [monitoring_duration] - Duration to monitor in seconds
    @param {boolean} [track_all_vitals] - Track all vitals including experimental
    @param {boolean} [provide_recommendations] - Provide optimization recommendations
    @param {number} [sample_rate] - Sample rate for measurements (Hz)
    @returns {object} Core Web Vitals monitoring data

    @example
    // Basic Core Web Vitals monitoring
    GET /cdp/performance/core_web_vitals

    // Comprehensive vitals monitoring
    POST {
      "monitoring_duration": 30,
      "track_all_vitals": true,
      "provide_recommendations": true,
      "sample_rate": 2
    }
    """
    try:
        params = parse_request_params(request, ['monitoring_duration', 'track_all_vitals', 'provide_recommendations', 'sample_rate'])
        monitoring_duration = int(params['monitoring_duration'] or 10)
        track_all_vitals = params['track_all_vitals'] in [True, 'true', '1']
        provide_recommendations = params['provide_recommendations'] in [True, 'true', '1']
        sample_rate = float(params['sample_rate'] or 1)

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.RUNTIME, "monitor_core_web_vitals"):
            return create_domain_error_response(CDPDomain.RUNTIME, "monitor_core_web_vitals")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Core Web Vitals monitoring code
            vitals_monitoring_code = f"""
                (() => {{
                    return new Promise((resolve) => {{
                        const vitalsMonitor = {{
                            monitoring_duration: {monitoring_duration},
                            track_all_vitals: {str(track_all_vitals).lower()},
                            provide_recommendations: {str(provide_recommendations).lower()},
                            sample_rate: {sample_rate},
                            start_time: performance.now(),
                            vitals_data: {{}},
                            measurements: [],
                            thresholds: {{
                                lcp: {{ good: 2500, needs_improvement: 4000 }},
                                fid: {{ good: 100, needs_improvement: 300 }},
                                cls: {{ good: 0.1, needs_improvement: 0.25 }},
                                fcp: {{ good: 1800, needs_improvement: 3000 }},
                                ttfb: {{ good: 800, needs_improvement: 1800 }}
                            }},
                            recommendations: []
                        }};

                        // Initialize vitals tracking
                        vitalsMonitor.vitals_data = {{
                            lcp: null,
                            fid: null,
                            cls: {{ value: 0, entries: [] }},
                            fcp: null,
                            ttfb: null,
                            inp: null,
                            experimental_vitals: {{}}
                        }};

                        // Performance Observer for Core Web Vitals
                        if ('PerformanceObserver' in window) {{
                            try {{
                                // Largest Contentful Paint (LCP)
                                const lcpObserver = new PerformanceObserver((list) => {{
                                    const entries = list.getEntries();
                                    const lastEntry = entries[entries.length - 1];

                                    vitalsMonitor.vitals_data.lcp = {{
                                        value: lastEntry.startTime,
                                        element: lastEntry.element ? {{
                                            tag_name: lastEntry.element.tagName,
                                            id: lastEntry.element.id,
                                            class_name: lastEntry.element.className
                                        }} : null,
                                        url: lastEntry.url || null,
                                        timestamp: performance.now(),
                                        size: lastEntry.size || 0
                                    }};

                                    vitalsMonitor.measurements.push({{
                                        metric: 'LCP',
                                        value: lastEntry.startTime,
                                        timestamp: performance.now(),
                                        rating: lastEntry.startTime <= 2500 ? 'good' :
                                               lastEntry.startTime <= 4000 ? 'needs-improvement' : 'poor'
                                    }});
                                }});
                                lcpObserver.observe({{entryTypes: ['largest-contentful-paint']}});

                                // First Input Delay (FID)
                                const fidObserver = new PerformanceObserver((list) => {{
                                    const entries = list.getEntries();
                                    entries.forEach(entry => {{
                                        const fidValue = entry.processingStart - entry.startTime;

                                        vitalsMonitor.vitals_data.fid = {{
                                            value: fidValue,
                                            event_type: entry.name,
                                            timestamp: performance.now(),
                                            processing_start: entry.processingStart,
                                            start_time: entry.startTime
                                        }};

                                        vitalsMonitor.measurements.push({{
                                            metric: 'FID',
                                            value: fidValue,
                                            timestamp: performance.now(),
                                            rating: fidValue <= 100 ? 'good' :
                                                   fidValue <= 300 ? 'needs-improvement' : 'poor'
                                        }});
                                    }});
                                }});
                                fidObserver.observe({{entryTypes: ['first-input']}});

                                // Cumulative Layout Shift (CLS)
                                let clsValue = 0;
                                const clsObserver = new PerformanceObserver((list) => {{
                                    const entries = list.getEntries();
                                    entries.forEach(entry => {{
                                        if (!entry.hadRecentInput) {{
                                            clsValue += entry.value;
                                            vitalsMonitor.vitals_data.cls.entries.push({{
                                                value: entry.value,
                                                timestamp: performance.now(),
                                                had_recent_input: entry.hadRecentInput,
                                                sources: entry.sources ? entry.sources.map(source => ({{
                                                    node: source.node ? source.node.tagName : null
                                                }})) : []
                                            }});
                                        }}
                                    }});

                                    vitalsMonitor.vitals_data.cls.value = clsValue;

                                    vitalsMonitor.measurements.push({{
                                        metric: 'CLS',
                                        value: clsValue,
                                        timestamp: performance.now(),
                                        rating: clsValue <= 0.1 ? 'good' :
                                               clsValue <= 0.25 ? 'needs-improvement' : 'poor'
                                    }});
                                }});
                                clsObserver.observe({{entryTypes: ['layout-shift']}});

                                // First Contentful Paint (FCP)
                                const fcpObserver = new PerformanceObserver((list) => {{
                                    const entries = list.getEntries();
                                    entries.forEach(entry => {{
                                        if (entry.name === 'first-contentful-paint') {{
                                            vitalsMonitor.vitals_data.fcp = {{
                                                value: entry.startTime,
                                                timestamp: performance.now()
                                            }};

                                            vitalsMonitor.measurements.push({{
                                                metric: 'FCP',
                                                value: entry.startTime,
                                                timestamp: performance.now(),
                                                rating: entry.startTime <= 1800 ? 'good' :
                                                       entry.startTime <= 3000 ? 'needs-improvement' : 'poor'
                                            }});
                                        }}
                                    }});
                                }});
                                fcpObserver.observe({{entryTypes: ['paint']}});

                                // Time to First Byte (TTFB)
                                const navEntries = performance.getEntriesByType('navigation');
                                if (navEntries.length > 0) {{
                                    const ttfbValue = navEntries[0].responseStart - navEntries[0].requestStart;
                                    vitalsMonitor.vitals_data.ttfb = {{
                                        value: ttfbValue,
                                        timestamp: performance.now()
                                    }};

                                    vitalsMonitor.measurements.push({{
                                        metric: 'TTFB',
                                        value: ttfbValue,
                                        timestamp: performance.now(),
                                        rating: ttfbValue <= 800 ? 'good' :
                                               ttfbValue <= 1800 ? 'needs-improvement' : 'poor'
                                    }});
                                }}

                                // Track experimental vitals if requested
                                if ({str(track_all_vitals).lower()}) {{
                                    // Interaction to Next Paint (INP) - experimental
                                    try {{
                                        const inpObserver = new PerformanceObserver((list) => {{
                                            const entries = list.getEntries();
                                            entries.forEach(entry => {{
                                                vitalsMonitor.vitals_data.experimental_vitals.inp = {{
                                                    value: entry.duration,
                                                    timestamp: performance.now(),
                                                    event_type: entry.name
                                                }};
                                            }});
                                        }});
                                        inpObserver.observe({{entryTypes: ['event']}});
                                    }} catch (e) {{
                                        // INP not supported
                                    }}

                                    // Long Animation Frames (LoAF) - experimental
                                    try {{
                                        const loafObserver = new PerformanceObserver((list) => {{
                                            const entries = list.getEntries();
                                            vitalsMonitor.vitals_data.experimental_vitals.long_animation_frames =
                                                entries.map(entry => ({{
                                                    duration: entry.duration,
                                                    start_time: entry.startTime,
                                                    timestamp: performance.now()
                                                }}));
                                        }});
                                        loafObserver.observe({{entryTypes: ['long-animation-frame']}});
                                    }} catch (e) {{
                                        // LoAF not supported
                                    }}
                                }}

                                vitalsMonitor.observers = [lcpObserver, fidObserver, clsObserver, fcpObserver];

                            }} catch (observerError) {{
                                vitalsMonitor.observer_error = observerError.message;
                            }}
                        }}

                        // Periodic sampling for real-time monitoring
                        const sampleInterval = 1000 / {sample_rate}; // Convert Hz to ms
                        const samplingInterval = setInterval(() => {{
                            const currentTime = performance.now();

                            // Sample current state
                            const sample = {{
                                timestamp: currentTime,
                                lcp_current: vitalsMonitor.vitals_data.lcp ? vitalsMonitor.vitals_data.lcp.value : null,
                                fid_current: vitalsMonitor.vitals_data.fid ? vitalsMonitor.vitals_data.fid.value : null,
                                cls_current: vitalsMonitor.vitals_data.cls.value,
                                fcp_current: vitalsMonitor.vitals_data.fcp ? vitalsMonitor.vitals_data.fcp.value : null,
                                ttfb_current: vitalsMonitor.vitals_data.ttfb ? vitalsMonitor.vitals_data.ttfb.value : null
                            }};

                            vitalsMonitor.measurements.push(sample);
                        }}, sampleInterval);

                        // Finish monitoring after duration
                        setTimeout(() => {{
                            clearInterval(samplingInterval);

                            // Clean up observers
                            if (vitalsMonitor.observers) {{
                                vitalsMonitor.observers.forEach(observer => {{
                                    try {{
                                        observer.disconnect();
                                    }} catch (e) {{
                                        // Observer already disconnected
                                    }}
                                }});
                            }}

                            vitalsMonitor.end_time = performance.now();
                            vitalsMonitor.monitoring_duration_ms = vitalsMonitor.end_time - vitalsMonitor.start_time;

                            // Generate recommendations if requested
                            if ({str(provide_recommendations).lower()}) {{
                                const thresholds = vitalsMonitor.thresholds;

                                // LCP recommendations
                                if (vitalsMonitor.vitals_data.lcp && vitalsMonitor.vitals_data.lcp.value > thresholds.lcp.good) {{
                                    vitalsMonitor.recommendations.push({{
                                        metric: 'LCP',
                                        current_value: vitalsMonitor.vitals_data.lcp.value,
                                        target_value: thresholds.lcp.good,
                                        rating: vitalsMonitor.vitals_data.lcp.value > thresholds.lcp.needs_improvement ? 'poor' : 'needs-improvement',
                                        recommendations: [
                                            'Optimize largest contentful element loading',
                                            'Use resource hints (preload) for critical resources',
                                            'Optimize server response times',
                                            'Consider image optimization and WebP format'
                                        ]
                                    }});
                                }}

                                // FID recommendations
                                if (vitalsMonitor.vitals_data.fid && vitalsMonitor.vitals_data.fid.value > thresholds.fid.good) {{
                                    vitalsMonitor.recommendations.push({{
                                        metric: 'FID',
                                        current_value: vitalsMonitor.vitals_data.fid.value,
                                        target_value: thresholds.fid.good,
                                        rating: vitalsMonitor.vitals_data.fid.value > thresholds.fid.needs_improvement ? 'poor' : 'needs-improvement',
                                        recommendations: [
                                            'Reduce JavaScript execution time',
                                            'Split long tasks into smaller chunks',
                                            'Use web workers for heavy computations',
                                            'Implement code splitting and lazy loading'
                                        ]
                                    }});
                                }}

                                // CLS recommendations
                                if (vitalsMonitor.vitals_data.cls.value > thresholds.cls.good) {{
                                    vitalsMonitor.recommendations.push({{
                                        metric: 'CLS',
                                        current_value: vitalsMonitor.vitals_data.cls.value,
                                        target_value: thresholds.cls.good,
                                        rating: vitalsMonitor.vitals_data.cls.value > thresholds.cls.needs_improvement ? 'poor' : 'needs-improvement',
                                        recommendations: [
                                            'Set explicit dimensions for images and videos',
                                            'Avoid inserting content above existing content',
                                            'Use transform animations instead of layout changes',
                                            'Preload fonts to avoid font-display swaps'
                                        ]
                                    }});
                                }}

                                // FCP recommendations
                                if (vitalsMonitor.vitals_data.fcp && vitalsMonitor.vitals_data.fcp.value > thresholds.fcp.good) {{
                                    vitalsMonitor.recommendations.push({{
                                        metric: 'FCP',
                                        current_value: vitalsMonitor.vitals_data.fcp.value,
                                        target_value: thresholds.fcp.good,
                                        rating: vitalsMonitor.vitals_data.fcp.value > thresholds.fcp.needs_improvement ? 'poor' : 'needs-improvement',
                                        recommendations: [
                                            'Optimize critical rendering path',
                                            'Minimize render-blocking resources',
                                            'Inline critical CSS',
                                            'Optimize web fonts loading'
                                        ]
                                    }});
                                }}

                                // TTFB recommendations
                                if (vitalsMonitor.vitals_data.ttfb && vitalsMonitor.vitals_data.ttfb.value > thresholds.ttfb.good) {{
                                    vitalsMonitor.recommendations.push({{
                                        metric: 'TTFB',
                                        current_value: vitalsMonitor.vitals_data.ttfb.value,
                                        target_value: thresholds.ttfb.good,
                                        rating: vitalsMonitor.vitals_data.ttfb.value > thresholds.ttfb.needs_improvement ? 'poor' : 'needs-improvement',
                                        recommendations: [
                                            'Optimize server response time',
                                            'Use a Content Delivery Network (CDN)',
                                            'Optimize database queries',
                                            'Enable server-side caching'
                                        ]
                                    }});
                                }}
                            }}

                            // Calculate overall performance score
                            const scoreWeights = {{ lcp: 0.25, fid: 0.25, cls: 0.25, fcp: 0.15, ttfb: 0.1 }};
                            let weightedScore = 0;
                            let totalWeight = 0;

                            Object.keys(scoreWeights).forEach(metric => {{
                                const data = vitalsMonitor.vitals_data[metric];
                                if (data) {{
                                    const value = metric === 'cls' ? data.value : data.value;
                                    const threshold = vitalsMonitor.thresholds[metric];
                                    let score = 100;

                                    if (value > threshold.needs_improvement) {{
                                        score = 0;
                                    }} else if (value > threshold.good) {{
                                        score = 50;
                                    }}

                                    weightedScore += score * scoreWeights[metric];
                                    totalWeight += scoreWeights[metric];
                                }}
                            }});

                            vitalsMonitor.performance_score = totalWeight > 0 ? Math.round(weightedScore / totalWeight) : null;

                            resolve(vitalsMonitor);
                        }}, {monitoring_duration * 1000});
                    }});
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': vitals_monitoring_code,
                'returnByValue': True,
                'awaitPromise': True,
                'timeout': (monitoring_duration + 15) * 1000
            })

            vitals_data = result.get('result', {}).get('result', {}).get('value')

            # Track endpoint usage
            track_endpoint_usage("monitor_core_web_vitals", [CDPDomain.RUNTIME], params)

            return jsonify(create_success_response({
                "core_web_vitals_monitoring": vitals_data,
                "monitoring_parameters": {
                    "monitoring_duration": monitoring_duration,
                    "track_all_vitals": track_all_vitals,
                    "provide_recommendations": provide_recommendations,
                    "sample_rate": sample_rate
                }
            }, "monitor_core_web_vitals", [CDPDomain.RUNTIME]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("monitor_core_web_vitals", e, params, "monitor_core_web_vitals")


@performance_routes.route('/cdp/performance/budget_tracking', methods=['GET', 'POST'])
def track_performance_budget():
    """
    Track performance budget compliance and resource usage limits

    @route GET/POST /cdp/performance/budget_tracking
    @param {object} [budget_limits] - Custom budget limits for resources
    @param {boolean} [track_overtime] - Track changes over time
    @param {boolean} [alert_on_violation] - Generate alerts for budget violations
    @param {string} [budget_scope] - Budget scope: 'page', 'critical_path', 'third_party'
    @returns {object} Performance budget tracking data

    @example
    // Basic budget tracking
    GET /cdp/performance/budget_tracking

    // Custom budget tracking with alerts
    POST {
      "budget_limits": {
        "total_size_kb": 1500,
        "js_size_kb": 500,
        "css_size_kb": 100,
        "image_size_kb": 800,
        "font_size_kb": 100
      },
      "track_overtime": true,
      "alert_on_violation": true,
      "budget_scope": "page"
    }
    """
    try:
        params = parse_request_params(request, ['budget_limits', 'track_overtime', 'alert_on_violation', 'budget_scope'])
        budget_limits = params.get('budget_limits') or {}
        if isinstance(budget_limits, str):
            import json as json_module
            try:
                budget_limits = json_module.loads(budget_limits)
            except:
                budget_limits = {}

        track_overtime = params['track_overtime'] in [True, 'true', '1']
        alert_on_violation = params['alert_on_violation'] in [True, 'true', '1']
        budget_scope = params['budget_scope'] or 'page'

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.RUNTIME, "track_performance_budget"):
            return create_domain_error_response(CDPDomain.RUNTIME, "track_performance_budget")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Performance budget tracking code
            budget_tracking_code = f"""
                (() => {{
                    const budgetTracker = {{
                        budget_limits: {budget_limits},
                        track_overtime: {str(track_overtime).lower()},
                        alert_on_violation: {str(alert_on_violation).lower()},
                        budget_scope: '{budget_scope}',
                        tracking_start: performance.now(),
                        budget_status: {{}},
                        resource_breakdown: {{}},
                        violations: [],
                        compliance_score: 0,
                        recommendations: []
                    }};

                    // Default budget limits (industry best practices)
                    const defaultBudgets = {{
                        total_size_kb: 1600,        // Total page weight
                        js_size_kb: 600,            // JavaScript bundle size
                        css_size_kb: 150,           // CSS size
                        image_size_kb: 800,         // Images total
                        font_size_kb: 100,          // Web fonts
                        html_size_kb: 50,           // HTML document
                        third_party_size_kb: 400,   // Third-party resources
                        request_count: 50,          // Total HTTP requests
                        dom_elements: 1500,         // DOM node count
                        load_time_ms: 3000,         // Page load time
                        fcp_ms: 1800,              // First Contentful Paint
                        lcp_ms: 2500,              // Largest Contentful Paint
                        memory_mb: 50               // JavaScript heap usage
                    }};

                    // Merge custom limits with defaults
                    const activeBudgets = {{ ...defaultBudgets, ...budgetTracker.budget_limits }};
                    budgetTracker.active_budgets = activeBudgets;

                    // Analyze current resource usage
                    const resources = performance.getEntriesByType('resource');
                    const resourceStats = {{
                        total_size_kb: 0,
                        js_size_kb: 0,
                        css_size_kb: 0,
                        image_size_kb: 0,
                        font_size_kb: 0,
                        html_size_kb: 0,
                        third_party_size_kb: 0,
                        request_count: resources.length,
                        resources_by_type: {{}}
                    }};

                    // Calculate HTML size from navigation timing
                    const navEntries = performance.getEntriesByType('navigation');
                    if (navEntries.length > 0) {{
                        resourceStats.html_size_kb = Math.round((navEntries[0].transferSize || 0) / 1024);
                    }}

                    // Analyze resources by type
                    resources.forEach(resource => {{
                        const sizeKB = Math.round((resource.transferSize || 0) / 1024);
                        const isThirdParty = !resource.name.includes(window.location.hostname);

                        resourceStats.total_size_kb += sizeKB;

                        if (isThirdParty) {{
                            resourceStats.third_party_size_kb += sizeKB;
                        }}

                        // Categorize by type
                        const type = resource.initiatorType || 'other';
                        if (!resourceStats.resources_by_type[type]) {{
                            resourceStats.resources_by_type[type] = {{
                                count: 0,
                                size_kb: 0,
                                resources: []
                            }};
                        }}

                        resourceStats.resources_by_type[type].count++;
                        resourceStats.resources_by_type[type].size_kb += sizeKB;
                        resourceStats.resources_by_type[type].resources.push({{
                            name: resource.name,
                            size_kb: sizeKB,
                            duration: resource.duration,
                            is_third_party: isThirdParty
                        }});

                        // Resource type specific tracking
                        switch (type) {{
                            case 'script':
                                resourceStats.js_size_kb += sizeKB;
                                break;
                            case 'link':
                                if (resource.name.includes('.css')) {{
                                    resourceStats.css_size_kb += sizeKB;
                                }}
                                break;
                            case 'img':
                            case 'image':
                                resourceStats.image_size_kb += sizeKB;
                                break;
                            case 'font':
                                resourceStats.font_size_kb += sizeKB;
                                break;
                        }}
                    }});

                    // Check DOM element count
                    resourceStats.dom_elements = document.querySelectorAll('*').length;

                    // Check memory usage
                    if (performance.memory) {{
                        resourceStats.memory_mb = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
                    }}

                    // Check performance metrics
                    const navigationTiming = navEntries[0];
                    if (navigationTiming) {{
                        resourceStats.load_time_ms = navigationTiming.loadEventEnd - navigationTiming.navigationStart;
                    }}

                    // Get paint timing
                    const paintEntries = performance.getEntriesByType('paint');
                    paintEntries.forEach(entry => {{
                        if (entry.name === 'first-contentful-paint') {{
                            resourceStats.fcp_ms = entry.startTime;
                        }}
                    }});

                    // Get LCP if available
                    try {{
                        const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                        if (lcpEntries.length > 0) {{
                            resourceStats.lcp_ms = lcpEntries[lcpEntries.length - 1].startTime;
                        }}
                    }} catch (e) {{
                        // LCP not available
                    }}

                    budgetTracker.resource_breakdown = resourceStats;

                    // Check budget compliance
                    const budgetChecks = [
                        {{ metric: 'total_size_kb', current: resourceStats.total_size_kb, budget: activeBudgets.total_size_kb }},
                        {{ metric: 'js_size_kb', current: resourceStats.js_size_kb, budget: activeBudgets.js_size_kb }},
                        {{ metric: 'css_size_kb', current: resourceStats.css_size_kb, budget: activeBudgets.css_size_kb }},
                        {{ metric: 'image_size_kb', current: resourceStats.image_size_kb, budget: activeBudgets.image_size_kb }},
                        {{ metric: 'font_size_kb', current: resourceStats.font_size_kb, budget: activeBudgets.font_size_kb }},
                        {{ metric: 'html_size_kb', current: resourceStats.html_size_kb, budget: activeBudgets.html_size_kb }},
                        {{ metric: 'third_party_size_kb', current: resourceStats.third_party_size_kb, budget: activeBudgets.third_party_size_kb }},
                        {{ metric: 'request_count', current: resourceStats.request_count, budget: activeBudgets.request_count }},
                        {{ metric: 'dom_elements', current: resourceStats.dom_elements, budget: activeBudgets.dom_elements }},
                        {{ metric: 'load_time_ms', current: resourceStats.load_time_ms || 0, budget: activeBudgets.load_time_ms }},
                        {{ metric: 'fcp_ms', current: resourceStats.fcp_ms || 0, budget: activeBudgets.fcp_ms }},
                        {{ metric: 'lcp_ms', current: resourceStats.lcp_ms || 0, budget: activeBudgets.lcp_ms }},
                        {{ metric: 'memory_mb', current: resourceStats.memory_mb || 0, budget: activeBudgets.memory_mb }}
                    ];

                    let compliantMetrics = 0;
                    const totalMetrics = budgetChecks.length;

                    budgetChecks.forEach(check => {{
                        const usage_percentage = (check.current / check.budget) * 100;
                        const is_compliant = check.current <= check.budget;
                        const severity = usage_percentage > 120 ? 'critical' :
                                        usage_percentage > 100 ? 'high' :
                                        usage_percentage > 80 ? 'warning' : 'ok';

                        if (is_compliant) {{
                            compliantMetrics++;
                        }}

                        budgetTracker.budget_status[check.metric] = {{
                            current_value: check.current,
                            budget_limit: check.budget,
                            usage_percentage: Math.round(usage_percentage),
                            is_compliant: is_compliant,
                            severity: severity,
                            over_budget_amount: Math.max(0, check.current - check.budget)
                        }};

                        // Generate violations for over-budget items
                        if (!is_compliant && {str(alert_on_violation).lower()}) {{
                            budgetTracker.violations.push({{
                                metric: check.metric,
                                current_value: check.current,
                                budget_limit: check.budget,
                                over_budget_amount: check.current - check.budget,
                                usage_percentage: Math.round(usage_percentage),
                                severity: severity,
                                timestamp: performance.now()
                            }});
                        }}
                    }});

                    // Calculate compliance score
                    budgetTracker.compliance_score = Math.round((compliantMetrics / totalMetrics) * 100);

                    // Generate recommendations based on violations
                    if (budgetTracker.violations.length > 0) {{
                        const violationsByType = {{}};
                        budgetTracker.violations.forEach(violation => {{
                            violationsByType[violation.metric] = violation;
                        }});

                        // Resource size recommendations
                        if (violationsByType.total_size_kb) {{
                            budgetTracker.recommendations.push({{
                                category: 'resource_optimization',
                                priority: 'high',
                                title: 'Total Page Size Over Budget',
                                description: `Page size is ${{violationsByType.total_size_kb.over_budget_amount}}KB over budget`,
                                suggestions: [
                                    'Implement image compression and WebP format',
                                    'Enable gzip/brotli compression',
                                    'Minify CSS and JavaScript files',
                                    'Consider code splitting and lazy loading'
                                ]
                            }});
                        }}

                        if (violationsByType.js_size_kb) {{
                            budgetTracker.recommendations.push({{
                                category: 'javascript_optimization',
                                priority: 'high',
                                title: 'JavaScript Bundle Over Budget',
                                description: `JS size is ${{violationsByType.js_size_kb.over_budget_amount}}KB over budget`,
                                suggestions: [
                                    'Implement code splitting',
                                    'Remove unused JavaScript code',
                                    'Use dynamic imports for non-critical code',
                                    'Consider smaller alternative libraries'
                                ]
                            }});
                        }}

                        if (violationsByType.image_size_kb) {{
                            budgetTracker.recommendations.push({{
                                category: 'image_optimization',
                                priority: 'medium',
                                title: 'Image Size Over Budget',
                                description: `Image size is ${{violationsByType.image_size_kb.over_budget_amount}}KB over budget`,
                                suggestions: [
                                    'Compress images and use appropriate formats',
                                    'Implement responsive images with srcset',
                                    'Use lazy loading for below-the-fold images',
                                    'Consider WebP or AVIF formats'
                                ]
                            }});
                        }}

                        if (violationsByType.third_party_size_kb) {{
                            budgetTracker.recommendations.push({{
                                category: 'third_party_optimization',
                                priority: 'medium',
                                title: 'Third-Party Resources Over Budget',
                                description: `Third-party size is ${{violationsByType.third_party_size_kb.over_budget_amount}}KB over budget`,
                                suggestions: [
                                    'Audit and remove unnecessary third-party scripts',
                                    'Self-host critical third-party resources',
                                    'Use async loading for non-critical third-party scripts',
                                    'Implement resource hints for third-party domains'
                                ]
                            }});
                        }}

                        if (violationsByType.dom_elements) {{
                            budgetTracker.recommendations.push({{
                                category: 'dom_optimization',
                                priority: 'low',
                                title: 'DOM Size Over Budget',
                                description: `DOM has ${{violationsByType.dom_elements.over_budget_amount}} excess elements`,
                                suggestions: [
                                    'Simplify DOM structure',
                                    'Use CSS instead of nested divs where possible',
                                    'Implement virtual scrolling for large lists',
                                    'Remove unnecessary wrapper elements'
                                ]
                            }});
                        }}

                        if (violationsByType.load_time_ms) {{
                            budgetTracker.recommendations.push({{
                                category: 'performance_optimization',
                                priority: 'high',
                                title: 'Load Time Over Budget',
                                description: `Load time is ${{Math.round(violationsByType.load_time_ms.over_budget_amount)}}ms over budget`,
                                suggestions: [
                                    'Optimize critical rendering path',
                                    'Implement resource preloading',
                                    'Optimize server response times',
                                    'Use a Content Delivery Network (CDN)'
                                ]
                            }});
                        }}
                    }} else {{
                        budgetTracker.recommendations.push({{
                            category: 'compliance',
                            priority: 'info',
                            title: 'All Budgets Compliant',
                            description: 'All performance budgets are within limits',
                            suggestions: [
                                'Continue monitoring performance',
                                'Consider tightening budgets for better performance',
                                'Implement performance monitoring alerts',
                                'Document current performance baseline'
                            ]
                        }});
                    }}

                    // Budget utilization analysis
                    budgetTracker.budget_utilization = {{
                        highest_usage_metric: null,
                        lowest_usage_metric: null,
                        average_utilization: 0,
                        critical_violations: budgetTracker.violations.filter(v => v.severity === 'critical').length,
                        high_violations: budgetTracker.violations.filter(v => v.severity === 'high').length,
                        warning_violations: budgetTracker.violations.filter(v => v.severity === 'warning').length
                    }};

                    // Find highest and lowest usage
                    let highestUsage = 0;
                    let lowestUsage = 100;
                    let totalUsage = 0;

                    Object.entries(budgetTracker.budget_status).forEach(([metric, status]) => {{
                        if (status.usage_percentage > highestUsage) {{
                            highestUsage = status.usage_percentage;
                            budgetTracker.budget_utilization.highest_usage_metric = {{
                                metric: metric,
                                usage_percentage: status.usage_percentage
                            }};
                        }}

                        if (status.usage_percentage < lowestUsage) {{
                            lowestUsage = status.usage_percentage;
                            budgetTracker.budget_utilization.lowest_usage_metric = {{
                                metric: metric,
                                usage_percentage: status.usage_percentage
                            }};
                        }}

                        totalUsage += status.usage_percentage;
                    }});

                    budgetTracker.budget_utilization.average_utilization = Math.round(totalUsage / Object.keys(budgetTracker.budget_status).length);

                    budgetTracker.tracking_end = performance.now();
                    budgetTracker.analysis_duration_ms = budgetTracker.tracking_end - budgetTracker.tracking_start;

                    return budgetTracker;
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': budget_tracking_code,
                'returnByValue': True,
                'timeout': 15000
            })

            budget_data = result.get('result', {}).get('result', {}).get('value')

            # Track endpoint usage
            track_endpoint_usage("track_performance_budget", [CDPDomain.RUNTIME], params)

            return jsonify(create_success_response({
                "performance_budget_tracking": budget_data,
                "tracking_parameters": {
                    "budget_limits": budget_limits,
                    "track_overtime": track_overtime,
                    "alert_on_violation": alert_on_violation,
                    "budget_scope": budget_scope
                }
            }, "track_performance_budget", [CDPDomain.RUNTIME]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("track_performance_budget", e, params, "track_performance_budget")


@performance_routes.route('/cdp/performance/optimization_impact', methods=['POST'])
def measure_optimization_impact():
    """
    Measure the impact of performance optimizations through before/after analysis

    @route POST /cdp/performance/optimization_impact
    @param {object} baseline_metrics - Baseline performance metrics for comparison
    @param {boolean} [include_user_metrics] - Include user-centric metrics (CWV)
    @param {boolean} [analyze_resource_changes] - Analyze resource loading changes
    @param {string} [optimization_type] - Type of optimization being measured
    @returns {object} Optimization impact analysis

    @example
    // Measure optimization impact
    POST {
      "baseline_metrics": {
        "load_time": 3500,
        "fcp": 2100,
        "lcp": 3200,
        "cls": 0.15,
        "total_size_kb": 1800
      },
      "include_user_metrics": true,
      "analyze_resource_changes": true,
      "optimization_type": "image_compression"
    }
    """
    try:
        data = request.get_json() or {}
        baseline_metrics = data.get('baseline_metrics', {})
        include_user_metrics = data.get('include_user_metrics', True)
        analyze_resource_changes = data.get('analyze_resource_changes', True)
        optimization_type = data.get('optimization_type', 'general')

        # Ensure required domains
        if not ensure_domain_available(CDPDomain.RUNTIME, "measure_optimization_impact"):
            return create_domain_error_response(CDPDomain.RUNTIME, "measure_optimization_impact")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Optimization impact measurement code
            impact_measurement_code = f"""
                (() => {{
                    const impactAnalysis = {{
                        baseline_metrics: {baseline_metrics},
                        include_user_metrics: {str(include_user_metrics).lower()},
                        analyze_resource_changes: {str(analyze_resource_changes).lower()},
                        optimization_type: '{optimization_type}',
                        measurement_start: performance.now(),
                        current_metrics: {{}},
                        performance_deltas: {{}},
                        resource_analysis: {{}},
                        user_experience_impact: {{}},
                        optimization_effectiveness: {{}}
                    }};

                    // Collect current performance metrics
                    const navTiming = performance.getEntriesByType('navigation')[0];
                    if (navTiming) {{
                        impactAnalysis.current_metrics.load_time = navTiming.loadEventEnd - navTiming.navigationStart;
                        impactAnalysis.current_metrics.dns_time = navTiming.domainLookupEnd - navTiming.domainLookupStart;
                        impactAnalysis.current_metrics.connect_time = navTiming.connectEnd - navTiming.connectStart;
                        impactAnalysis.current_metrics.server_response_time = navTiming.responseStart - navTiming.requestStart;
                        impactAnalysis.current_metrics.dom_content_loaded = navTiming.domContentLoadedEventEnd - navTiming.navigationStart;
                    }}

                    // Paint timing
                    const paintEntries = performance.getEntriesByType('paint');
                    paintEntries.forEach(entry => {{
                        if (entry.name === 'first-contentful-paint') {{
                            impactAnalysis.current_metrics.fcp = entry.startTime;
                        }} else if (entry.name === 'first-paint') {{
                            impactAnalysis.current_metrics.fp = entry.startTime;
                        }}
                    }});

                    // Core Web Vitals (if available)
                    if ({str(include_user_metrics).lower()}) {{
                        try {{
                            const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                            if (lcpEntries.length > 0) {{
                                impactAnalysis.current_metrics.lcp = lcpEntries[lcpEntries.length - 1].startTime;
                            }}
                        }} catch (e) {{}}

                        try {{
                            const fidEntries = performance.getEntriesByType('first-input');
                            if (fidEntries.length > 0) {{
                                impactAnalysis.current_metrics.fid = fidEntries[0].processingStart - fidEntries[0].startTime;
                            }}
                        }} catch (e) {{}}

                        // CLS calculation (simplified)
                        let clsValue = 0;
                        try {{
                            const clsEntries = performance.getEntriesByType('layout-shift');
                            clsEntries.forEach(entry => {{
                                if (!entry.hadRecentInput) {{
                                    clsValue += entry.value;
                                }}
                            }});
                            impactAnalysis.current_metrics.cls = clsValue;
                        }} catch (e) {{}}
                    }}

                    // Resource analysis
                    if ({str(analyze_resource_changes).lower()}) {{
                        const resources = performance.getEntriesByType('resource');
                        const resourceStats = {{
                            total_resources: resources.length,
                            total_size_kb: 0,
                            by_type: {{}},
                            by_size: {{}},
                            by_domain: {{}}
                        }};

                        resources.forEach(resource => {{
                            const sizeKB = Math.round((resource.transferSize || 0) / 1024);
                            const type = resource.initiatorType || 'other';
                            const domain = new URL(resource.name).hostname;

                            resourceStats.total_size_kb += sizeKB;

                            // By type
                            if (!resourceStats.by_type[type]) {{
                                resourceStats.by_type[type] = {{ count: 0, size_kb: 0 }};
                            }}
                            resourceStats.by_type[type].count++;
                            resourceStats.by_type[type].size_kb += sizeKB;

                            // By size category
                            const sizeCategory = sizeKB < 10 ? 'small' :
                                               sizeKB < 100 ? 'medium' :
                                               sizeKB < 500 ? 'large' : 'very_large';
                            if (!resourceStats.by_size[sizeCategory]) {{
                                resourceStats.by_size[sizeCategory] = {{ count: 0, total_kb: 0 }};
                            }}
                            resourceStats.by_size[sizeCategory].count++;
                            resourceStats.by_size[sizeCategory].total_kb += sizeKB;

                            // By domain
                            if (!resourceStats.by_domain[domain]) {{
                                resourceStats.by_domain[domain] = {{ count: 0, size_kb: 0 }};
                            }}
                            resourceStats.by_domain[domain].count++;
                            resourceStats.by_domain[domain].size_kb += sizeKB;
                        }});

                        impactAnalysis.current_metrics.total_size_kb = resourceStats.total_size_kb;
                        impactAnalysis.current_metrics.resource_count = resourceStats.total_resources;
                        impactAnalysis.resource_analysis = resourceStats;
                    }}

                    // Memory usage
                    if (performance.memory) {{
                        impactAnalysis.current_metrics.memory_used_mb = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
                        impactAnalysis.current_metrics.memory_total_mb = Math.round(performance.memory.totalJSHeapSize / 1024 / 1024);
                        impactAnalysis.current_metrics.memory_limit_mb = Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024);
                    }}

                    // Calculate performance deltas
                    const baseline = impactAnalysis.baseline_metrics;
                    const current = impactAnalysis.current_metrics;

                    Object.keys(baseline).forEach(metric => {{
                        if (current[metric] !== undefined) {{
                            const baselineValue = baseline[metric];
                            const currentValue = current[metric];
                            const delta = currentValue - baselineValue;
                            const percentChange = baselineValue > 0 ? (delta / baselineValue) * 100 : 0;

                            impactAnalysis.performance_deltas[metric] = {{
                                baseline: baselineValue,
                                current: currentValue,
                                absolute_change: delta,
                                percent_change: Math.round(percentChange * 100) / 100,
                                improvement: delta < 0, // For most metrics, lower is better
                                impact_category: Math.abs(percentChange) < 5 ? 'minimal' :
                                               Math.abs(percentChange) < 15 ? 'moderate' :
                                               Math.abs(percentChange) < 30 ? 'significant' : 'major'
                            }};

                            // For CLS, higher values are worse
                            if (metric === 'cls') {{
                                impactAnalysis.performance_deltas[metric].improvement = delta < 0;
                            }}
                        }}
                    }});

                    // User experience impact analysis
                    if ({str(include_user_metrics).lower()}) {{
                        const uxMetrics = ['fcp', 'lcp', 'cls', 'fid', 'load_time'];
                        let improvedMetrics = 0;
                        let worsenedMetrics = 0;
                        let significantImprovements = 0;
                        let significantRegressions = 0;

                        uxMetrics.forEach(metric => {{
                            const delta = impactAnalysis.performance_deltas[metric];
                            if (delta) {{
                                if (delta.improvement) {{
                                    improvedMetrics++;
                                    if (delta.impact_category === 'significant' || delta.impact_category === 'major') {{
                                        significantImprovements++;
                                    }}
                                }} else if (delta.absolute_change > 0) {{
                                    worsenedMetrics++;
                                    if (delta.impact_category === 'significant' || delta.impact_category === 'major') {{
                                        significantRegressions++;
                                    }}
                                }}
                            }}
                        }});

                        // Calculate UX improvement score
                        const totalTrackedMetrics = uxMetrics.filter(m => impactAnalysis.performance_deltas[m]).length;
                        const uxScore = totalTrackedMetrics > 0 ?
                            Math.round(((improvedMetrics - worsenedMetrics) / totalTrackedMetrics) * 100) : 0;

                        impactAnalysis.user_experience_impact = {{
                            improved_metrics: improvedMetrics,
                            worsened_metrics: worsenedMetrics,
                            unchanged_metrics: totalTrackedMetrics - improvedMetrics - worsenedMetrics,
                            significant_improvements: significantImprovements,
                            significant_regressions: significantRegressions,
                            ux_improvement_score: uxScore,
                            overall_impact: uxScore > 50 ? 'positive' :
                                          uxScore < -50 ? 'negative' : 'neutral'
                        }};
                    }}

                    // Optimization effectiveness analysis
                    const effectiveness = {{
                        optimization_type: '{optimization_type}',
                        success_metrics: [],
                        regression_metrics: [],
                        effectiveness_score: 0,
                        recommendations: []
                    }};

                    // Analyze effectiveness based on optimization type
                    switch ('{optimization_type}') {{
                        case 'image_compression':
                            if (impactAnalysis.performance_deltas.total_size_kb && impactAnalysis.performance_deltas.total_size_kb.improvement) {{
                                effectiveness.success_metrics.push('Reduced total page size');
                            }}
                            if (impactAnalysis.performance_deltas.lcp && impactAnalysis.performance_deltas.lcp.improvement) {{
                                effectiveness.success_metrics.push('Improved Largest Contentful Paint');
                            }}
                            break;

                        case 'code_splitting':
                            if (impactAnalysis.performance_deltas.fcp && impactAnalysis.performance_deltas.fcp.improvement) {{
                                effectiveness.success_metrics.push('Improved First Contentful Paint');
                            }}
                            if (impactAnalysis.performance_deltas.load_time && impactAnalysis.performance_deltas.load_time.improvement) {{
                                effectiveness.success_metrics.push('Reduced load time');
                            }}
                            break;

                        case 'lazy_loading':
                            if (impactAnalysis.performance_deltas.fcp && impactAnalysis.performance_deltas.fcp.improvement) {{
                                effectiveness.success_metrics.push('Improved initial load performance');
                            }}
                            if (impactAnalysis.performance_deltas.resource_count && impactAnalysis.performance_deltas.resource_count.improvement) {{
                                effectiveness.success_metrics.push('Reduced initial resource count');
                            }}
                            break;

                        case 'cdn_implementation':
                            if (impactAnalysis.performance_deltas.server_response_time && impactAnalysis.performance_deltas.server_response_time.improvement) {{
                                effectiveness.success_metrics.push('Improved server response time');
                            }}
                            if (impactAnalysis.performance_deltas.load_time && impactAnalysis.performance_deltas.load_time.improvement) {{
                                effectiveness.success_metrics.push('Reduced overall load time');
                            }}
                            break;

                        default:
                            // General optimization analysis
                            Object.entries(impactAnalysis.performance_deltas).forEach(([metric, delta]) => {{
                                if (delta.improvement && (delta.impact_category === 'significant' || delta.impact_category === 'major')) {{
                                    effectiveness.success_metrics.push(`Improved ${{metric}}`);
                                }} else if (!delta.improvement && (delta.impact_category === 'significant' || delta.impact_category === 'major')) {{
                                    effectiveness.regression_metrics.push(`Regressed ${{metric}}`);
                                }}
                            }});
                    }}

                    // Calculate effectiveness score
                    const totalSignificantChanges = effectiveness.success_metrics.length + effectiveness.regression_metrics.length;
                    if (totalSignificantChanges > 0) {{
                        effectiveness.effectiveness_score = Math.round(
                            (effectiveness.success_metrics.length / totalSignificantChanges) * 100
                        );
                    }}

                    // Generate recommendations
                    if (effectiveness.effectiveness_score >= 80) {{
                        effectiveness.recommendations.push('Optimization was highly effective - consider applying similar optimizations to other areas');
                    }} else if (effectiveness.effectiveness_score >= 60) {{
                        effectiveness.recommendations.push('Optimization showed good results - monitor for sustained improvements');
                    }} else if (effectiveness.effectiveness_score >= 40) {{
                        effectiveness.recommendations.push('Optimization had mixed results - investigate potential side effects');
                    }} else {{
                        effectiveness.recommendations.push('Optimization was not effective - consider reverting or trying alternative approaches');
                    }}

                    if (effectiveness.regression_metrics.length > 0) {{
                        effectiveness.recommendations.push(`Address regressions in: ${{effectiveness.regression_metrics.join(', ')}}`);
                    }}

                    impactAnalysis.optimization_effectiveness = effectiveness;

                    impactAnalysis.measurement_end = performance.now();
                    impactAnalysis.analysis_duration_ms = impactAnalysis.measurement_end - impactAnalysis.measurement_start;

                    return impactAnalysis;
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': impact_measurement_code,
                'returnByValue': True,
                'timeout': 15000
            })

            impact_data = result.get('result', {}).get('result', {}).get('value')

            # Track endpoint usage
            track_endpoint_usage("measure_optimization_impact", [CDPDomain.RUNTIME], data)

            return jsonify(create_success_response({
                "optimization_impact_analysis": impact_data,
                "measurement_parameters": {
                    "baseline_metrics": baseline_metrics,
                    "include_user_metrics": include_user_metrics,
                    "analyze_resource_changes": analyze_resource_changes,
                    "optimization_type": optimization_type
                }
            }, "measure_optimization_impact", [CDPDomain.RUNTIME]))

        finally:
            pool.release(cdp)

    except Exception as e:
        return handle_cdp_error("measure_optimization_impact", e, data, "measure_optimization_impact")