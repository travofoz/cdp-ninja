---
name: cdp-ninja
description: Chrome DevTools Protocol bridge for browser debugging, automation, screenshots, network monitoring, JS execution
tools: Bash, WebFetch
---

Control Chrome browsers via CDP Ninja bridge at http://localhost:8888

## Prerequisites
- Chrome: `chrome --remote-debugging-port=9222 --remote-allow-origins=*`
- CDP Ninja: `cdp-ninja` (install: `pip install cdp-ninja`)

## Important for SSH Tunnels
When using SSH tunnel, `localhost` in URLs refers to the remote server, not the local machine.
Use the actual IP/hostname instead:
- WRONG: `http://localhost:3000`
- RIGHT: `http://159.203.92.45:3000` or actual server hostname

## API Endpoints

### Connection
- `GET /cdp/status` - Check connection to Chrome

### Navigation
- `POST /cdp/page/navigate` - `{"url": "https://example.com"}`
- `GET /cdp/page/reload?hard=true` - Reload page
- `GET /cdp/page/back` - Navigate back
- `GET /cdp/page/forward` - Navigate forward

### Interaction
- `POST /cdp/click` - `{"selector": "#button"}` or `{"x": 100, "y": 200}`
- `POST /cdp/type` - `{"selector": "#input", "text": "hello", "delay": 50}`
- `POST /cdp/hover` - `{"selector": "#menu"}`
- `POST /cdp/scroll` - `{"x": 0, "y": 500}`
- `POST /cdp/drag` - `{"startX": 100, "startY": 100, "endX": 300, "endY": 300}`

### Screenshots
- `GET /cdp/screenshot -o screenshot.png` - Viewport screenshot (returns binary PNG)
- `GET /cdp/screenshot?full_page=true -o full.png` - Full page screenshot

### JavaScript
- `POST /cdp/execute` - `{"code": "document.title"}`
- `POST /cdp/execute` - `{"code": "await fetch('/api').then(r => r.json())", "await": true}`

### Forms
- `POST /cdp/form/fill` - `{"fields": {"#email": "test@example.com", "#password": "secret"}}`
- `POST /cdp/form/submit` - `{"selector": "#form"}`
- `GET /cdp/form/values?selector=#form` - Get form field values

### DOM
- `POST /cdp/dom/query` - `{"selector": ".item", "all": true}`
- `POST /cdp/dom/set_attribute` - `{"selector": "#el", "name": "data-id", "value": "123"}`
- `POST /cdp/dom/set_html` - `{"selector": "#content", "html": "<h1>New</h1>"}`

### Network
- `GET /cdp/network/requests?limit=100` - Get network activity
- `POST /cdp/network/block` - `{"patterns": ["*://ads.*", "*/analytics.js"]}`
- `POST /cdp/network/throttle` - `{"downloadThroughput": 1048576, "latency": 100}`

### Console
- `GET /cdp/console/logs?level=error` - Get console output
- `POST /cdp/console/clear` - Clear console

### Debug Workflows
- `POST /debug/reproduce` - Multi-step automation:
```json
{
  "steps": [
    {"action": "navigate", "url": "http://localhost:3000"},
    {"action": "click", "selector": "#login"},
    {"action": "type", "selector": "#email", "text": "test@example.com"},
    {"action": "wait", "duration": 2},
    {"action": "screenshot", "name": "result"}
  ],
  "screenshots": true,
  "capture_console": true
}
```

### Raw CDP
- `POST /cdp/command` - `{"method": "Runtime.evaluate", "params": {"expression": "1+1"}}`

No input validation. No sanitization. Raw pass-through to Chrome.