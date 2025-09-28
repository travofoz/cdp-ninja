# Network Monitoring API

*Auto-generated from network_intelligence.py JSDoc comments*

## GET/POST /cdp/network/timing

**Function:** `analyze_network_timing()`

Analyze network request timing and performance

**Parameters:**
- `url_filter` *(string)* *(optional)*: Filter by URL pattern
- `limit` *(number)* *(optional)*: Maximum requests to analyze
- `detailed` *(boolean)* *(optional)*: Include detailed timing breakdown

**Returns:** {object} Network timing analysis

**Examples:**
```javascript
// Analyze all network timing
GET /cdp/network/timing
// Filter by URL pattern
GET /cdp/network/timing?url_filter=api.example.com&limit=10
// Detailed timing breakdown
POST {"detailed": true, "limit": 5}
```

---

## GET/POST /cdp/network/websockets

**Function:** `monitor_websockets()`

Monitor WebSocket connections and messages

**Parameters:**
- `active_only` *(boolean)* *(optional)*: Show only active connections
- `message_limit` *(number)* *(optional)*: Max messages per connection
- `url_filter` *(string)* *(optional)*: Filter by WebSocket URL pattern

**Returns:** {object} WebSocket monitoring data

**Examples:**
```javascript
// Monitor all WebSocket connections
GET /cdp/network/websockets
// Only active connections with recent messages
POST {"active_only": true, "message_limit": 50}
// Filter by URL pattern
GET /cdp/network/websockets?url_filter=wss://api.example.com
```

---

## GET/POST /cdp/network/cache

**Function:** `analyze_cache()`

Analyze browser cache and caching behavior

**Parameters:**
- `url_filter` *(string)* *(optional)*: Filter by URL pattern
- `detailed` *(boolean)* *(optional)*: Include detailed cache analysis
- `clear_first` *(boolean)* *(optional)*: Clear cache before analysis

**Returns:** {object} Cache analysis data

**Examples:**
```javascript
// Basic cache analysis
GET /cdp/network/cache
// Detailed cache analysis with filter
POST {"url_filter": "api.example.com", "detailed": true}
// Clear cache then analyze
POST {"clear_first": true}
```

---

## GET/POST /cdp/network/cors

**Function:** `detect_cors_violations()`

Detect CORS violations and cross-origin issues

**Parameters:**
- `origin_filter` *(string)* *(optional)*: Filter by origin pattern
- `violations_only` *(boolean)* *(optional)*: Show only CORS violations
- `include_preflight` *(boolean)* *(optional)*: Include preflight requests

**Returns:** {object} CORS analysis and violations

**Examples:**
```javascript
// Detect all CORS issues
GET /cdp/network/cors
// Only violations with preflight analysis
POST {"violations_only": true, "include_preflight": true}
// Filter by specific origin
GET /cdp/network/cors?origin_filter=api.example.com
```

---

