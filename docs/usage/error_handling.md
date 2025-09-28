# Error Handling API

*Auto-generated from error_handling.py JSDoc comments*

## GET/POST /cdp/errors/exceptions

**Function:** `analyze_exceptions()`

Analyze JavaScript exceptions and runtime errors

**Parameters:**
- `filter` *(string)* *(optional)*: Filter exceptions by pattern
- `include_stack` *(boolean)* *(optional)*: Include stack traces
- `detailed_analysis` *(boolean)* *(optional)*: Perform detailed error analysis
- `time_window` *(number)* *(optional)*: Time window in minutes for error collection

**Returns:** {object} Exception analysis data

**Examples:**
```javascript
// Basic exception analysis
GET /cdp/errors/exceptions
// Detailed analysis with stack traces
POST {"include_stack": true, "detailed_analysis": true}
// Filter specific errors
GET /cdp/errors/exceptions?filter=TypeError&time_window=5
```

---

## GET/POST /cdp/errors/promises

**Function:** `track_promise_errors()`

Track unhandled promise rejections and async error patterns

**Parameters:**
- `monitoring_duration` *(number)* *(optional)*: How long to monitor in seconds
- `include_resolved` *(boolean)* *(optional)*: Include resolved promises
- `pattern_analysis` *(boolean)* *(optional)*: Analyze error patterns

**Returns:** {object} Promise error tracking data

**Examples:**
```javascript
// Monitor promises for 30 seconds
POST {"monitoring_duration": 30}
// Comprehensive promise analysis
POST {
"monitoring_duration": 60,
"include_resolved": true,
"pattern_analysis": true
}
```

---

## POST /cdp/errors/simulate

**Function:** `simulate_errors()`

Simulate various error conditions for testing error handling

**Parameters:**
- `error_type ` *(string)*: Type of error to simulate
- `custom_message` *(string)* *(optional)*: Custom error message
- `trigger_fallback` *(boolean)* *(optional)*: Test fallback mechanisms
- `error_params` *(object)* *(optional)*: Additional error parameters

**Returns:** {object} Error simulation results

**Examples:**
```javascript
// Simulate TypeError
POST {"error_type": "TypeError", "custom_message": "Test error"}
// Simulate network error with fallback testing
POST {
"error_type": "NetworkError",
"trigger_fallback": true,
"error_params": {"endpoint": "/api/test"}
}
```

---

## POST /cdp/state/corrupt

**Function:** `test_state_corruption()`

Test application state corruption and recovery mechanisms

**Parameters:**
- `corruption_type ` *(string)*: Type of state corruption to test
- `test_recovery` *(boolean)* *(optional)*: Test recovery mechanisms
- `corruption_params` *(object)* *(optional)*: Corruption parameters

**Returns:** {object} State corruption test results

**Examples:**
```javascript
// Test localStorage corruption
POST {"corruption_type": "localStorage", "test_recovery": true}
// Test DOM state corruption
POST {
"corruption_type": "DOM",
"corruption_params": {"target": "form", "corruption_level": "moderate"}
}
```

---

## POST /cdp/errors/boundary_test

**Function:** `test_error_boundaries()`

Test error boundary mechanisms and error propagation

**Parameters:**
- `boundary_type ` *(string)*: Type of error boundary to test
- `test_propagation` *(boolean)* *(optional)*: Test error propagation
- `error_depth` *(number)* *(optional)*: Depth of error propagation to test

**Returns:** {object} Error boundary test results

**Examples:**
```javascript
// Test basic error boundary
POST {"boundary_type": "try_catch", "test_propagation": true}
// Test deep error propagation
POST {
"boundary_type": "nested",
"test_propagation": true,
"error_depth": 5
}
```

---

## GET/POST /cdp/errors/memory_leak

**Function:** `detect_memory_leaks()`

Detect potential memory leaks and analyze memory usage patterns

**Parameters:**
- `monitoring_duration` *(number)* *(optional)*: Duration to monitor in seconds
- `force_gc` *(boolean)* *(optional)*: Force garbage collection before monitoring
- `detailed_analysis` *(boolean)* *(optional)*: Perform detailed heap analysis

**Returns:** {object} Memory leak detection results

**Examples:**
```javascript
// Basic memory leak detection
GET /cdp/errors/memory_leak
// Detailed analysis with garbage collection
POST {
"monitoring_duration": 30,
"force_gc": true,
"detailed_analysis": true
}
```

---

## GET/POST /cdp/errors/performance_impact

**Function:** `analyze_error_performance_impact()`

Analyze the performance impact of errors and exception handling

**Parameters:**
- `test_iterations` *(number)* *(optional)*: Number of test iterations
- `include_timing` *(boolean)* *(optional)*: Include detailed timing analysis
- `error_scenario` *(string)* *(optional)*: Specific error scenario to test

**Returns:** {object} Performance impact analysis

**Examples:**
```javascript
// Basic performance impact analysis
GET /cdp/errors/performance_impact
// Detailed timing with specific scenario
POST {
"test_iterations": 1000,
"include_timing": true,
"error_scenario": "try_catch_overhead"
}
```

---

## POST /cdp/errors/recovery_validation

**Function:** `validate_error_recovery()`

Validate error recovery mechanisms and resilience patterns

**Parameters:**
- `recovery_type ` *(string)*: Type of recovery mechanism to validate
- `recovery_config` *(object)* *(optional)*: Configuration for recovery testing
- `stress_test` *(boolean)* *(optional)*: Apply stress testing to recovery
- `failure_rate` *(number)* *(optional)*: Simulated failure rate (0-1)

**Returns:** {object} Recovery validation results

**Examples:**
```javascript
// Validate retry mechanism
POST {
"recovery_type": "retry_with_backoff",
"recovery_config": {"max_retries": 3, "base_delay": 100}
}
// Stress test circuit breaker
POST {
"recovery_type": "circuit_breaker",
"stress_test": true,
"failure_rate": 0.3
}
```

---

