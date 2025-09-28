# Stress Testing API

*Auto-generated from stress_testing.py JSDoc comments*

## POST /cdp/stress/memory_bomb

**Function:** `memory_stress_test()`

Memory allocation stress testing and memory bomb simulation

**Parameters:**
- `allocation_mb` *(number)* *(optional)*: Memory to allocate in MB (default: 10)
- `iterations` *(number)* *(optional)*: Number of allocation iterations (default: 5)
- `monitor_performance` *(boolean)* *(optional)*: Monitor memory performance during test
- `gradual_release` *(boolean)* *(optional)*: Gradually release memory (safer)
- `max_allocation` *(number)* *(optional)*: Maximum total allocation limit in MB

**Returns:** {object} Memory stress test results

**Examples:**
```javascript
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
```

---

## POST /cdp/stress/cpu_burn

**Function:** `cpu_stress_test()`

CPU intensive stress testing and performance boundary discovery

**Parameters:**
- `duration_ms` *(number)* *(optional)*: Test duration in milliseconds (default: 1000)
- `test_type` *(string)* *(optional)*: Type of CPU test (math, loop, recursion, mixed)
- `intensity` *(number)* *(optional)*: Test intensity level 1-10 (default: 5)
- `monitor_performance` *(boolean)* *(optional)*: Monitor CPU performance during test
- `yield_control` *(boolean)* *(optional)*: Yield control periodically (safer)

**Returns:** {object} CPU stress test results

**Examples:**
```javascript
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
```

---

