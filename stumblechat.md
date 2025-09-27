# StumbleChat Control via CDP-Ninja

## Working Method - Send Messages

Use the existing WebSocket connection through CDP execute endpoint:

```bash
curl -X POST "http://localhost:8888/cdp/execute" -H "Content-Type: application/json" -d '{
  "code": "if (window.wss && window.wss.readyState === 1) { const msg = JSON.stringify({\"stumble\":\"msg\",\"text\":\"test from original ws - can you see this?\"}); window.wss.send(msg); \"sent via original: \" + msg; } else \"original WebSocket not ready\""
}'
```

**Replace the message text with your own message:**
```bash
curl -X POST "http://localhost:8888/cdp/execute" -H "Content-Type: application/json" -d '{
  "code": "window.wss.send(JSON.stringify({\"stumble\":\"msg\",\"text\":\"YOUR MESSAGE HERE\"}))"
}'
```

## Monitor WebSocket Traffic

### Monitor All Chat Messages
```bash
curl -s "http://localhost:8888/cdp/network/requests" | jq -r '.requests[].events[] | select(.type == "webSocketFrameReceived") | .data.response.payloadData' | grep -E "msg" | tail -5
```

### Monitor Join Messages (Get Userlist)
```bash
curl -s "http://localhost:8888/cdp/network/requests" | jq -r '.requests[].events[] | select(.type == "webSocketFrameReceived") | .data.response.payloadData' | grep -E "joined|userlist" | tail -10
```

### Background Monitor for Userlist (Use this to capture joins)
```bash
while true; do curl -s "http://localhost:8888/cdp/network/requests" | jq -r '.requests[].events[] | select(.type == "webSocketFrameReceived") | .data.response.payloadData' | grep -E "joined|userlist" | head -1; sleep 1; done
```

### Monitor All WebSocket Traffic (Everything)
```bash
curl -s "http://localhost:8888/cdp/network/requests" | jq -r '.requests[].events[] | select(.type == "webSocketFrameReceived") | .data.response.payloadData' | grep -v "^0$" | tail -10
```

### Monitor Sent Messages
```bash
curl -s "http://localhost:8888/cdp/network/requests" | jq -r '.requests[].events[] | select(.type == "webSocketFrameSent") | .data.response.payloadData' | grep -v "^0$" | tail -5
```

## WebSocket Connection Details

- **Connection**: `window.wss` (existing StumbleChat WebSocket)
- **URL**: `wss://wss6.stumblechat.com/`
- **Status Check**: `window.wss.readyState === 1` (1 = OPEN)

## Message Formats

### Send Chat Message
```json
{"stumble":"msg","text":"your message here"}
```

### Received Chat Message
```json
{"stumble":"msg","handle":"697813","text":"user message"}
```

### Join Message (when user enters)
```json
{"stumble":"join","backgroundcolor":"#048007","namebackgroundcolor":"#60426D","messagetextcolor":"#FFFFFF","avatar":1,"handle":"697813","username":"DMX","nick":"DMX","mod":0,"guest":0}
```

## Key Discovery

- ✅ **Direct WebSocket works**: Using `window.wss.send()` with proper JSON successfully sends messages to chat
- ✅ **No authentication needed**: Existing page WebSocket is already authenticated
- ✅ **CDP Network monitoring**: Full WebSocket traffic visible via `/cdp/network/requests` endpoint
- ❌ **New WebSocket fails**: Creating fresh WebSocket connections don't work (need authentication/handshake)

## Network Endpoint Access

All WebSocket traffic (both sent and received) is accessible through:
```
GET http://localhost:8888/cdp/network/requests
```

This provides complete WebSocket frame data without needing console interceptors.

## Complete Workflow for Userlist Capture

1. **Start background monitoring for joins:**
```bash
while true; do curl -s "http://localhost:8888/cdp/network/requests" | jq -r '.requests[].events[] | select(.type == "webSocketFrameReceived") | .data.response.payloadData' | grep -E "joined|userlist" | head -1; sleep 1; done
```

2. **User refreshes the StumbleChat page**

3. **User hits "verify" or triggers join events**

4. **Check captured join messages to get handle-to-username mappings:**
```bash
curl -s "http://localhost:8888/cdp/network/requests" | jq -r '.requests[].events[] | select(.type == "webSocketFrameReceived") | .data.response.payloadData' | grep -E "join" | tail -10
```

5. **Join messages contain the mapping data you need**