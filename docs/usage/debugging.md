# Debugging API

*Auto-generated from debugging.py JSDoc comments*

## POST /cdp/execute

**Function:** `execute_javascript()`

Execute ANY JavaScript in page context - COMPLETELY RAW

**Parameters:**
- `code ` *(string)*: ANY JavaScript, including injection attempts
- `await` *(boolean)* *(optional)*: Wait for promises to resolve
- `timeout` *(number)* *(optional)*: Execution timeout in ms (user controlled)
- `return_by_value` *(boolean)* *(optional)*: Return value instead of object reference

**Returns:** {object} Whatever Chrome returns (or crashes)

**Examples:**
```javascript
// Normal JavaScript
{"code": "document.title"}
// XSS injection test
{"code": "</script><script>alert('xss')</script>"}
// Infinite loop test
{"code": "while(true){}"}
// Memory bomb test
{"code": "let x = []; while(true) x.push(new Array(1000000))"}
// Async operation
{"code": "fetch('/api/data')", "await": true, "timeout": 5000}
```

---

## GET /cdp/console/logs

**Function:** `get_console_logs()`

Get console output from page - ALL messages, no filtering

**Parameters:**
- `limit` *(number)* *(optional)*: Max entries to return (default: 100)
- `level` *(string)* *(optional)*: Filter by level (but we don't validate it)

**Returns:** {array} All console messages including errors, warnings, etc.

**Examples:**
```javascript
// Get recent logs
GET /cdp/console/logs
// Get more logs
GET /cdp/console/logs?limit=500
// Try to filter (might not work if invalid level)
GET /cdp/console/logs?level=invalid_level
```

---

## POST /cdp/console/clear

**Function:** `clear_console()`

Clear console output

**Returns:** {object} Clear result

---

## GET /cdp/network/requests

**Function:** `get_network_requests()`

Get recent network requests with ALL details

**Parameters:**
- `limit` *(number)* *(optional)*: Max requests to return
- `url_filter` *(string)* *(optional)*: Filter URLs (no validation)

**Returns:** {array} All network requests with full details

**Examples:**
```javascript
// Get recent requests
GET /cdp/network/requests
// Get many requests
GET /cdp/network/requests?limit=1000
// Filter by URL pattern
GET /cdp/network/requests?url_filter=api
```

---

## POST /cdp/network/block

**Function:** `block_urls()`

Block URLs matching patterns - ANY patterns allowed

**Parameters:**
- `patterns ` *(array)*: URL patterns to block (no validation)

**Returns:** {object} Block result

**Examples:**
```javascript
// Block ads
{"patterns": ["*://*.doubleclick.net/*", "*://analytics.google.com/*"]}
// Block everything - see what breaks
{"patterns": ["*"]}
// Invalid patterns - test CDP behavior
{"patterns": [">>>invalid<<<", "malformed[regex"]}
```

---

## POST /cdp/network/throttle

**Function:** `throttle_network()`

Simulate network conditions - ANY values allowed

**Parameters:**
- `offline` *(boolean)* *(optional)*: Completely offline
- `download` *(number)* *(optional)*: Download speed in bytes/sec (can be 0, negative)
- `upload` *(number)* *(optional)*: Upload speed in bytes/sec (can be huge)
- `latency` *(number)* *(optional)*: Network latency in ms (can be negative)

**Returns:** {object} Throttle result

**Examples:**
```javascript
// Slow connection
{"download": 1000, "upload": 500, "latency": 1000}
// Impossible values - test limits
{"download": -1, "upload": 999999999999, "latency": -5000}
// Completely offline
{"offline": true}
// Zero bandwidth
{"download": 0, "upload": 0}
```

---

## POST /cdp/network/clear

**Function:** `clear_network_cache()`

Clear browser cache and cookies

**Parameters:**
- `cache` *(boolean)* *(optional)*: Clear cache (default: true)
- `cookies` *(boolean)* *(optional)*: Clear cookies (default: false)
- `storage` *(boolean)* *(optional)*: Clear local storage (default: false)

**Returns:** {object} Clear result

---

## GET /cdp/performance

**Function:** `get_performance_metrics()`

Get performance metrics and timing data

**Returns:** {object} Performance data from browser

---

## GET /debug/crash/stats

**Function:** `get_crash_stats()`

Get debugging crash statistics - valuable telemetry data

**Returns:** {object} Crash statistics and recent crashes

---

