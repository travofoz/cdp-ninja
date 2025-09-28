# Performance Domain API

Performance monitoring, profiling, and optimization endpoints (10 endpoints).

## Core Performance Metrics

### GET /cdp/performance
Get comprehensive performance metrics and Core Web Vitals.

### GET /cdp/performance/metrics
Get detailed performance timing metrics.

### GET /cdp/performance/core_web_vitals
Get Core Web Vitals: LCP, FID, CLS scores.

### GET /cdp/performance/rendering_metrics
Get rendering performance metrics.

### GET /cdp/performance/resource_timing
Get resource loading timing information.

## Memory & CPU Analysis

### GET /cdp/performance/memory_monitor
Monitor JavaScript heap memory usage.

### POST /cdp/performance/cpu_profiling
Start/stop CPU profiling sessions.

## Background & Optimization

### GET /cdp/performance/background_tasks
Monitor background task performance.

### GET /cdp/performance/optimization_recommendations
Get automated performance optimization suggestions.

### GET /cdp/performance/optimization_impact
Measure impact of performance optimizations.

### GET /cdp/performance/budget_tracking
Track performance budget compliance.

## Example Usage

```bash
# Get Core Web Vitals
curl http://localhost:8888/cdp/performance/core_web_vitals

# Monitor memory usage
curl http://localhost:8888/cdp/performance/memory_monitor

# Start CPU profiling
curl -X POST http://localhost:8888/cdp/performance/cpu_profiling \
  -d '{"action": "start", "duration": 30}'
```

**Note**: Full endpoint documentation for all 10 performance endpoints pending comprehensive audit.