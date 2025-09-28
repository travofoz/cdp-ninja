# Network Domain API

Network monitoring, request interception, and traffic analysis.

## Request Monitoring

### GET /cdp/network/requests
Get recent network requests and WebSocket frames.

**Response:**
```json
{
  "requests": [
    {
      "type": "http_request",
      "id": "request_123",
      "url": "https://api.example.com/data",
      "method": "GET",
      "timestamp": 1234567890,
      "response": {
        "status": 200,
        "headers": {"content-type": "application/json"}
      },
      "failed": false
    },
    {
      "type": "websocket_frame",
      "direction": "sent",
      "payload": "{\"action\": \"subscribe\"}"
    }
  ],
  "http_count": 15,
  "websocket_count": 3,
  "total": 18
}
```

## Request Blocking

### POST /cdp/network/block
Block URLs matching patterns.

**Request:**
```json
{
  "patterns": [
    "*://ads.example.com/*",
    "*://tracker.*/*",
    "*.jpg"
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8888/cdp/network/block \
  -H "Content-Type: application/json" \
  -d $'{"patterns": ["*://ads.*/*", "*://analytics.*/*"]}'
```

## Network Throttling

### POST /cdp/network/throttle
Simulate slow network conditions.

**Request:**
```json
{
  "offline": false,
  "download": 1000000,    // bytes/sec
  "upload": 500000,       // bytes/sec
  "latency": 100          // milliseconds
}
```

**Presets:**
```bash
# Slow 3G
curl -X POST http://localhost:8888/cdp/network/throttle \
  -d $'{"download": 400000, "upload": 400000, "latency": 400}'

# Fast 3G
curl -X POST http://localhost:8888/cdp/network/throttle \
  -d $'{"download": 1600000, "upload": 750000, "latency": 150}'

# Offline mode
curl -X POST http://localhost:8888/cdp/network/throttle \
  -d $'{"offline": true}'
```

## Cache Management

### GET /cdp/network/clear
Clear browser cache and cookies.

**Example:**
```bash
curl http://localhost:8888/cdp/network/clear
```

## Advanced Network Testing

### Request Interception
```bash
# Monitor all requests
curl http://localhost:8888/cdp/network/requests | jq '.requests[] | select(.failed == true)'

# Block social media
curl -X POST http://localhost:8888/cdp/network/block \
  -d $'{"patterns": ["*://facebook.com/*", "*://twitter.com/*", "*://instagram.com/*"]}"

# Simulate mobile network
curl -X POST http://localhost:8888/cdp/network/throttle \
  -d $'{"download": 1600000, "upload": 750000, "latency": 150}'
```

### Performance Analysis
```bash
# Capture network timeline
curl http://localhost:8888/cdp/network/requests > before.json
# ... perform actions ...
curl http://localhost:8888/cdp/network/requests > after.json

# Compare request counts
diff <(jq '.total' before.json) <(jq '.total' after.json)
```

## WebSocket Monitoring

CDP Ninja automatically captures WebSocket frames:
- **Direction**: `sent` or `received`
- **Payload**: Raw frame data
- **Timestamp**: When frame was captured

**Filter WebSocket frames:**
```bash
curl http://localhost:8888/cdp/network/requests | \
  jq '.requests[] | select(.type == "websocket_frame")'
```