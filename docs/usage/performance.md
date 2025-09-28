# Performance & Memory API

*Auto-generated from performance.py JSDoc comments*

## GET/POST /cdp/performance/metrics

**Function:** `collect_performance_metrics()`

Collect comprehensive performance metrics and Core Web Vitals

**Parameters:**
- `include_paint` *(boolean)* *(optional)*: Include paint timing metrics
- `include_navigation` *(boolean)* *(optional)*: Include navigation timing
- `include_resource` *(boolean)* *(optional)*: Include resource timing
- `duration` *(number)* *(optional)*: Collection duration in seconds

**Returns:** {object} Performance metrics data

**Examples:**
```javascript
// Basic performance metrics
GET /cdp/performance/metrics
// Comprehensive metrics with all timing data
POST {
"include_paint": true,
"include_navigation": true,
"include_resource": true,
"duration": 5
}
```

---

## GET/POST /cdp/performance/memory_monitor

**Function:** `monitor_memory_usage()`

Monitor memory usage patterns and detect potential leaks in background

**Parameters:**
- `monitoring_duration` *(number)* *(optional)*: Duration to monitor in seconds
- `sample_interval` *(number)* *(optional)*: Sample interval in milliseconds
- `track_allocations` *(boolean)* *(optional)*: Track allocation patterns
- `detect_leaks` *(boolean)* *(optional)*: Enable leak detection

**Returns:** {object} Memory monitoring data

**Examples:**
```javascript
// Basic memory monitoring
GET /cdp/performance/memory_monitor
// Detailed monitoring with leak detection
POST {
"monitoring_duration": 30,
"sample_interval": 1000,
"track_allocations": true,
"detect_leaks": true
}
```

---

## GET/POST /cdp/performance/rendering_metrics

**Function:** `analyze_rendering_performance()`

Analyze rendering performance including frame rates and paint events

**Parameters:**
- `monitoring_duration` *(number)* *(optional)*: Duration to monitor in seconds
- `track_frame_rate` *(boolean)* *(optional)*: Track frame rate metrics
- `analyze_paint_events` *(boolean)* *(optional)*: Analyze paint and layout events
- `detect_jank` *(boolean)* *(optional)*: Detect rendering jank

**Returns:** {object} Rendering performance analysis

**Examples:**
```javascript
// Basic rendering metrics
GET /cdp/performance/rendering_metrics
// Comprehensive rendering analysis
POST {
"monitoring_duration": 10,
"track_frame_rate": true,
"analyze_paint_events": true,
"detect_jank": true
}
```

---

## POST /cdp/performance/cpu_profiling

**Function:** `profile_cpu_usage()`

Profile CPU usage and identify performance bottlenecks

**Parameters:**
- `profiling_duration` *(number)* *(optional)*: Duration to profile in seconds
- `sample_stack_traces` *(boolean)* *(optional)*: Sample stack traces during profiling
- `analyze_hot_functions` *(boolean)* *(optional)*: Analyze hottest functions
- `profiling_mode` *(string)* *(optional)*: Profiling mode: 'sampling' or 'precision'

**Returns:** {object} CPU profiling results

**Examples:**
```javascript
// Basic CPU profiling
POST {"profiling_duration": 5}
// Comprehensive profiling with stack traces
POST {
"profiling_duration": 10,
"sample_stack_traces": true,
"analyze_hot_functions": true,
"profiling_mode": "precision"
}
```

---

## GET/POST /cdp/performance/resource_timing

**Function:** `analyze_resource_timing()`

Analyze resource loading performance and identify optimization opportunities

**Parameters:**
- `analysis_period` *(number)* *(optional)*: Period to analyze in seconds
- `include_third_party` *(boolean)* *(optional)*: Include third-party resources
- `detect_blocking` *(boolean)* *(optional)*: Detect render-blocking resources
- `resource_filter` *(string)* *(optional)*: Filter by resource type

**Returns:** {object} Resource timing analysis

**Examples:**
```javascript
// Basic resource timing analysis
GET /cdp/performance/resource_timing
// Comprehensive resource analysis
POST {
"analysis_period": 10,
"include_third_party": true,
"detect_blocking": true,
"resource_filter": "all"
}
```

---

## GET/POST /cdp/performance/background_tasks

**Function:** `monitor_background_tasks()`

Monitor background tasks and service worker performance

**Parameters:**
- `monitoring_duration` *(number)* *(optional)*: Duration to monitor in seconds
- `track_service_workers` *(boolean)* *(optional)*: Track service worker activity
- `monitor_web_workers` *(boolean)* *(optional)*: Monitor web worker performance
- `detect_heavy_tasks` *(boolean)* *(optional)*: Detect CPU-heavy background tasks

**Returns:** {object} Background task monitoring data

**Examples:**
```javascript
// Basic background task monitoring
GET /cdp/performance/background_tasks
// Comprehensive background monitoring
POST {
"monitoring_duration": 15,
"track_service_workers": true,
"monitor_web_workers": true,
"detect_heavy_tasks": true
}
```

---

## GET/POST /cdp/performance/optimization_recommendations

**Function:** `generate_optimization_recommendations()`

Generate comprehensive performance optimization recommendations

**Parameters:**
- `analyze_resources` *(boolean)* *(optional)*: Analyze resource optimization opportunities
- `analyze_scripts` *(boolean)* *(optional)*: Analyze script performance issues
- `analyze_styles` *(boolean)* *(optional)*: Analyze CSS and style performance
- `priority_filter` *(string)* *(optional)*: Filter by priority: 'high', 'medium', 'low', 'all'

**Returns:** {object} Performance optimization recommendations

**Examples:**
```javascript
// Basic optimization recommendations
GET /cdp/performance/optimization_recommendations
// Comprehensive optimization analysis
POST {
"analyze_resources": true,
"analyze_scripts": true,
"analyze_styles": true,
"priority_filter": "all"
}
```

---

## GET/POST /cdp/performance/core_web_vitals

**Function:** `monitor_core_web_vitals()`

Monitor Core Web Vitals metrics in real-time

**Parameters:**
- `monitoring_duration` *(number)* *(optional)*: Duration to monitor in seconds
- `track_all_vitals` *(boolean)* *(optional)*: Track all vitals including experimental
- `provide_recommendations` *(boolean)* *(optional)*: Provide optimization recommendations
- `sample_rate` *(number)* *(optional)*: Sample rate for measurements (Hz)

**Returns:** {object} Core Web Vitals monitoring data

**Examples:**
```javascript
// Basic Core Web Vitals monitoring
GET /cdp/performance/core_web_vitals
// Comprehensive vitals monitoring
POST {
"monitoring_duration": 30,
"track_all_vitals": true,
"provide_recommendations": true,
"sample_rate": 2
}
```

---

## GET/POST /cdp/performance/budget_tracking

**Function:** `track_performance_budget()`

Track performance budget compliance and resource usage limits

**Parameters:**
- `budget_limits` *(object)* *(optional)*: Custom budget limits for resources
- `track_overtime` *(boolean)* *(optional)*: Track changes over time
- `alert_on_violation` *(boolean)* *(optional)*: Generate alerts for budget violations
- `budget_scope` *(string)* *(optional)*: Budget scope: 'page', 'critical_path', 'third_party'

**Returns:** {object} Performance budget tracking data

**Examples:**
```javascript
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
```

---

## POST /cdp/performance/optimization_impact

**Function:** `measure_optimization_impact()`

Measure the impact of performance optimizations through before/after analysis

**Parameters:**
- `baseline_metrics ` *(object)*: Baseline performance metrics for comparison
- `include_user_metrics` *(boolean)* *(optional)*: Include user-centric metrics (CWV)
- `analyze_resource_changes` *(boolean)* *(optional)*: Analyze resource loading changes
- `optimization_type` *(string)* *(optional)*: Type of optimization being measured

**Returns:** {object} Optimization impact analysis

**Examples:**
```javascript
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
```

---

