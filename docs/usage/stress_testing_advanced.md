# Advanced Stress Testing API

*Auto-generated from stress_testing_advanced.py JSDoc comments*

## POST /cdp/stress/click_storm

**Function:** `click_storm()`

Aggressive rapid clicking to test event handling limits

**Returns:** {object} Click storm results with performance impact and errors

---

## POST /cdp/stress/memory_bomb

**Function:** `memory_bomb()`

Aggressive memory allocation to test memory limits

**Returns:** {object} Memory stress test results with allocation patterns and system impact

---

## POST /cdp/stress/cpu_burn

**Function:** `cpu_burn()`

Intensive CPU computation to test performance limits

**Returns:** {object} CPU stress test results with performance metrics and system impact

---

## POST /cdp/stress/input_overflow

**Function:** `input_overflow()`

Test input field limits with oversized payloads

**Returns:** {object} Input overflow test results with field behavior and limitations

---

## POST /cdp/stress/storage_flood

**Function:** `storage_flood()`

Test browser storage limits with data flooding

**Returns:** {object} Storage flood results with capacity limits and performance impact

---

## POST /cdp/stress/chaos_monkey

**Function:** `chaos_monkey()`

Random unpredictable interactions to test system resilience

**Returns:** {object} Chaos monkey results with system stability analysis and discovered issues

---

## POST /cdp/stress/race_conditions

**Function:** `race_conditions()`

Trigger race conditions through concurrent operations

**Returns:** {object} Race condition test results with timing analysis and concurrency issues

---

## POST /cdp/stress/full_assault

**Function:** `full_assault()`

Comprehensive multi-vector stress test combining all attack patterns

**Returns:** {object} Full assault results with comprehensive system stress analysis

---

