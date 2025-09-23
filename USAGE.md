# CDP Ninja API Usage Guide 🥷

Complete API documentation for CDP Ninja - Chrome DevTools Protocol Bridge

## Table of Contents
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [API Reference](#api-reference)
  - [System Endpoints](#system-endpoints)
  - [Browser Interaction](#browser-interaction)
  - [Page Navigation](#page-navigation)
  - [DOM Operations](#dom-operations)
  - [Form Automation](#form-automation)
  - [JavaScript Execution](#javascript-execution)
  - [Network Monitoring](#network-monitoring)
  - [Console Access](#console-access)
  - [Performance & Memory](#performance--memory)
  - [Advanced Debugging](#advanced-debugging)
- [Security Testing Examples](#security-testing-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Quick Start

### 1. Start Chrome with debugging
```bash
# Windows PowerShell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="C:\temp\chrome-debug"

# Linux/macOS
google-chrome --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=/tmp/chrome-debug
```

### 2. Start CDP Ninja
```bash
cdp-ninja
# or with custom ports
cdp-ninja --bridge-port 8888 --cdp-port 9222 --debug
```

### 3. Test the connection
```bash
curl http://localhost:8888/cdp/status
```

## Core Concepts

CDP Ninja acts as a transparent HTTP-to-WebSocket bridge:
- **No validation**: All inputs are passed directly to Chrome
- **No sanitization**: Malformed data is allowed for security testing
- **No rate limiting**: Test performance limits and DoS scenarios
- **Raw pass-through**: Direct access to Chrome DevTools Protocol

## API Reference

### System Endpoints

#### GET /health
Health check for the bridge server.

**Response:**
```json
{
  "status": "ok",
  "timestamp": 1702345678.123
}
```

#### GET /cdp/status
Check CDP connection status and active domains.

**Response:**
```json
{
  "connected": true,
  "host": "localhost",
  "port": 9222,
  "url": "ws://localhost:9222/devtools/page/ABC123",
  "events_queued": 42,
  "domains_active": ["Network", "Runtime", "Page", "DOM", "Console"]
}
```

#### GET /system/info
System information and capabilities.

**Response:**
```json
{
  "platform": "Windows",
  "chrome_debugger_port": 9222,
  "bridge_port": 8888,
  "powershell_enabled": false,
  "version": "1.0.1"
}
```

#### GET /system/chrome/info
Chrome browser and debugging information.

**Response:**
```json
{
  "browser": "Chrome/120.0.6099.109",
  "protocol_version": "1.3",
  "v8_version": "12.0.267.8",
  "webkit_version": "537.36",
  "tabs": [
    {
      "id": "ABC123",
      "type": "page",
      "title": "Example Domain",
      "url": "https://example.com"
    }
  ]
}
```

#### POST /system/execute
Execute system commands (requires ENABLE_POWERSHELL=true).

**Request:**
```json
{
  "command": "Get-Process chrome",
  "shell": "powershell"  // or "cmd" on Windows, "bash" on Unix
}
```

**Response:**
```json
{
  "output": "...",
  "exit_code": 0,
  "error": null
}
```

### Browser Interaction

#### POST /cdp/click
Click an element by selector or coordinates.

**By Selector:**
```json
{
  "selector": "#submit-button"
}
```

**By Coordinates:**
```json
{
  "x": 100,
  "y": 200,
  "button": "left",  // optional: "left", "right", "middle"
  "clickCount": 1     // optional: for double-click use 2
}
```

**Response:**
```json
{
  "success": true,
  "clicked": "#submit-button at (100, 200)"
}
```

#### POST /cdp/type
Type text into an element.

**Request:**
```json
{
  "selector": "#email-input",
  "text": "test@example.com",
  "delay": 50  // optional: ms between keystrokes
}
```

**Response:**
```json
{
  "success": true,
  "typed": "test@example.com into #email-input"
}
```

#### POST /cdp/scroll
Scroll the page or an element.

**Request:**
```json
{
  "x": 0,
  "y": 500,
  "selector": "#content",  // optional: scroll specific element
  "smooth": true           // optional: smooth scrolling
}
```

**Response:**
```json
{
  "success": true,
  "scrolled": "to (0, 500)"
}
```

#### POST /cdp/hover
Hover over an element.

**Request:**
```json
{
  "selector": "#menu-item"
}
```

**Response:**
```json
{
  "success": true,
  "hovering": "#menu-item"
}
```

#### POST /cdp/drag
Drag from one point to another.

**Request:**
```json
{
  "startX": 100,
  "startY": 100,
  "endX": 300,
  "endY": 400,
  "duration": 1000  // optional: animation duration in ms
}
```

**Response:**
```json
{
  "success": true,
  "dragged": "from (100,100) to (300,400)"
}
```

#### GET /cdp/screenshot
Capture a screenshot.

**Query Parameters:**
- `full_page` (boolean): Capture entire page vs viewport
- `format` (string): "png" or "jpeg" (default: "png")
- `quality` (integer): JPEG quality 0-100 (default: 80)

**Example:**
```bash
curl "http://localhost:8888/cdp/screenshot?full_page=true&format=jpeg&quality=90" -o screenshot.jpg
```

**Response:** Binary image data (Content-Type: image/png or image/jpeg)

### Page Navigation

#### POST /cdp/page/navigate
Navigate to a URL.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "success": true,
  "navigated": "https://example.com",
  "frameId": "ABC123"
}
```

#### GET /cdp/page/reload
Reload the current page.

**Query Parameters:**
- `hard` (boolean): Ignore cache (default: false)

**Response:**
```json
{
  "success": true,
  "reloaded": true
}
```

#### GET /cdp/page/back
Navigate back in history.

**Response:**
```json
{
  "success": true,
  "action": "back"
}
```

#### GET /cdp/page/forward
Navigate forward in history.

**Response:**
```json
{
  "success": true,
  "action": "forward"
}
```

#### GET /cdp/page/info
Get current page information.

**Response:**
```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "secure": true,
  "frameId": "ABC123",
  "loaderId": "DEF456"
}
```

### DOM Operations

#### GET /cdp/dom/snapshot
Get DOM tree snapshot.

**Query Parameters:**
- `depth` (integer): Tree depth (default: -1 for full tree)

**Response:**
```json
{
  "document": {
    "nodeId": 1,
    "nodeType": 9,
    "nodeName": "#document",
    "children": [...]
  }
}
```

#### POST /cdp/dom/query
Query DOM elements.

**Request:**
```json
{
  "selector": ".item",
  "all": true  // optional: querySelector vs querySelectorAll
}
```

**Response:**
```json
{
  "elements": [
    {
      "nodeId": 42,
      "nodeName": "DIV",
      "attributes": ["class", "item", "id", "item-1"],
      "textContent": "Item 1"
    }
  ],
  "count": 3
}
```

#### POST /cdp/dom/get_attributes
Get element attributes.

**Request:**
```json
{
  "selector": "#my-element"
}
```

**Response:**
```json
{
  "attributes": {
    "id": "my-element",
    "class": "container active",
    "data-value": "42"
  }
}
```

#### POST /cdp/dom/set_attribute
Set element attribute.

**Request:**
```json
{
  "selector": "#my-element",
  "name": "data-status",
  "value": "active"
}
```

**Response:**
```json
{
  "success": true,
  "modified": "#my-element"
}
```

#### POST /cdp/dom/remove_attribute
Remove element attribute.

**Request:**
```json
{
  "selector": "#my-element",
  "name": "disabled"
}
```

**Response:**
```json
{
  "success": true,
  "removed": "disabled from #my-element"
}
```

#### POST /cdp/dom/set_html
Set element's innerHTML.

**Request:**
```json
{
  "selector": "#content",
  "html": "<h1>New Content</h1><p>Description</p>"
}
```

**Response:**
```json
{
  "success": true,
  "updated": "#content"
}
```

### Form Automation

#### POST /cdp/form/fill
Fill multiple form fields at once.

**Request:**
```json
{
  "fields": {
    "#email": "test@example.com",
    "#password": "secret123",
    "[name='username']": "testuser",
    "#age": "25"
  },
  "delay": 50  // optional: ms between fields
}
```

**Response:**
```json
{
  "success": true,
  "filled": 4,
  "fields": ["#email", "#password", "[name='username']", "#age"]
}
```

#### POST /cdp/form/submit
Submit a form.

**Request:**
```json
{
  "selector": "#login-form"  // form selector or submit button selector
}
```

**Response:**
```json
{
  "success": true,
  "submitted": "#login-form"
}
```

#### GET /cdp/form/values
Get current form field values.

**Query Parameters:**
- `selector` (string): Form selector (optional, gets all inputs if not specified)

**Response:**
```json
{
  "values": {
    "#email": "test@example.com",
    "#password": "***",
    "#username": "testuser",
    "#remember": true
  }
}
```

#### POST /cdp/form/select
Select dropdown option.

**Request:**
```json
{
  "selector": "#country",
  "value": "US"  // or use "index": 2 or "text": "United States"
}
```

**Response:**
```json
{
  "success": true,
  "selected": "US in #country"
}
```

#### POST /cdp/form/checkbox
Toggle checkbox or radio button.

**Request:**
```json
{
  "selector": "#agree-terms",
  "checked": true  // or false to uncheck
}
```

**Response:**
```json
{
  "success": true,
  "checked": true
}
```

### JavaScript Execution

#### POST /cdp/execute
Execute JavaScript in page context.

**Request:**
```json
{
  "code": "document.title",
  "await": false  // optional: wait for promise resolution
}
```

**Response:**
```json
{
  "result": {
    "type": "string",
    "value": "Example Domain"
  },
  "success": true
}
```

**Async Example:**
```json
{
  "code": "fetch('/api/data').then(r => r.json())",
  "await": true
}
```

#### POST /cdp/evaluate
Evaluate expression and return result.

**Request:**
```json
{
  "expression": "window.location.href"
}
```

**Response:**
```json
{
  "result": "https://example.com",
  "type": "string"
}
```

### Network Monitoring

#### GET /cdp/network/requests
Get captured network requests.

**Query Parameters:**
- `limit` (integer): Maximum requests to return (default: 100)
- `filter` (string): URL pattern to filter

**Response:**
```json
{
  "requests": [
    {
      "requestId": "123.45",
      "url": "https://api.example.com/data",
      "method": "GET",
      "headers": {...},
      "timestamp": 1702345678.123,
      "response": {
        "status": 200,
        "statusText": "OK",
        "headers": {...},
        "mimeType": "application/json",
        "size": 1024
      }
    }
  ],
  "total": 42
}
```

#### POST /cdp/network/block
Block network requests by pattern.

**Request:**
```json
{
  "patterns": [
    "*://ads.*.com/*",
    "*.doubleclick.net/*",
    "*://*/analytics.js"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "blocking": 3
}
```

#### POST /cdp/network/throttle
Simulate network conditions.

**Request:**
```json
{
  "offline": false,
  "downloadThroughput": 1048576,  // bytes per second (1 Mbps)
  "uploadThroughput": 524288,      // bytes per second (0.5 Mbps)
  "latency": 100                   // milliseconds
}
```

**Response:**
```json
{
  "success": true,
  "conditions": "1Mbps down, 0.5Mbps up, 100ms latency"
}
```

#### GET /cdp/network/clear
Clear network cache and cookies.

**Response:**
```json
{
  "success": true,
  "cleared": ["cache", "cookies"]
}
```

#### POST /cdp/network/headers
Set custom headers for all requests.

**Request:**
```json
{
  "headers": {
    "X-Custom-Header": "value",
    "Authorization": "Bearer token123"
  }
}
```

**Response:**
```json
{
  "success": true,
  "headers_set": 2
}
```

### Console Access

#### GET /cdp/console/logs
Get captured console output.

**Query Parameters:**
- `level` (string): Filter by level (log, warn, error, info)
- `limit` (integer): Maximum entries (default: 100)

**Response:**
```json
{
  "logs": [
    {
      "level": "error",
      "text": "Uncaught TypeError: Cannot read property 'x' of undefined",
      "timestamp": 1702345678.123,
      "source": "javascript",
      "line": 42,
      "column": 15,
      "url": "https://example.com/app.js"
    }
  ],
  "total": 15
}
```

#### POST /cdp/console/clear
Clear console output.

**Response:**
```json
{
  "success": true,
  "cleared": true
}
```

### Performance & Memory

#### GET /cdp/performance/metrics
Get performance metrics.

**Response:**
```json
{
  "metrics": {
    "Timestamp": 1702345678.123,
    "Documents": 1,
    "Frames": 1,
    "JSEventListeners": 147,
    "Nodes": 1253,
    "LayoutCount": 12,
    "RecalcStyleCount": 15,
    "LayoutDuration": 0.045,
    "RecalcStyleDuration": 0.032,
    "ScriptDuration": 1.234,
    "TaskDuration": 2.456,
    "JSHeapUsedSize": 15234567,
    "JSHeapTotalSize": 20000000
  }
}
```

#### GET /cdp/memory/usage
Get memory usage details.

**Response:**
```json
{
  "usedJSHeapSize": 15234567,
  "totalJSHeapSize": 20000000,
  "jsHeapSizeLimit": 2147483648,
  "usage_percentage": 0.76
}
```

#### POST /cdp/memory/gc
Force garbage collection.

**Response:**
```json
{
  "success": true,
  "before": 15234567,
  "after": 10123456,
  "freed": 5111111
}
```

### Advanced Debugging

#### POST /debug/reproduce
Automated bug reproduction workflow.

**Request:**
```json
{
  "steps": [
    {"action": "navigate", "url": "https://example.com"},
    {"action": "wait", "duration": 2},
    {"action": "click", "selector": "#login"},
    {"action": "type", "selector": "#email", "text": "test@example.com"},
    {"action": "type", "selector": "#password", "text": "secret123"},
    {"action": "screenshot", "name": "before_submit"},
    {"action": "click", "selector": "#submit"},
    {"action": "wait_for", "selector": "#dashboard"},
    {"action": "screenshot", "name": "after_login"},
    {"action": "execute", "code": "console.log('Login successful')"}
  ],
  "screenshots": true,
  "capture_console": true,
  "capture_network": true
}
```

**Response:**
```json
{
  "completed": 8,
  "failed": 2,
  "errors": [
    {
      "step": 7,
      "action": "wait_for",
      "error": "Timeout waiting for #dashboard"
    }
  ],
  "screenshots": [
    "before_submit_1702345678.png",
    "after_login_1702345680.png"
  ],
  "console_logs": [...],
  "network_requests": [...]
}
```

#### POST /cdp/command
Execute raw CDP command.

**Request:**
```json
{
  "method": "Page.captureScreenshot",
  "params": {
    "format": "png",
    "quality": 100,
    "captureBeyondViewport": true
  }
}
```

**Response:**
```json
{
  "result": {
    "data": "base64_encoded_image_data..."
  }
}
```

## Security Testing Examples

CDP Ninja is designed for security testing. Here are examples of intentionally dangerous operations:

### XSS Testing
```python
# Test for XSS vulnerabilities
requests.post("http://localhost:8888/cdp/execute", json={
    "code": "alert('XSS'); document.cookie"
})

# Attempt script injection
requests.post("http://localhost:8888/cdp/dom/set_html", json={
    "selector": "#content",
    "html": "<script>alert('XSS')</script><img src=x onerror=alert('XSS')>"
})
```

### SQL Injection Testing
```python
# Test form fields with SQL injection attempts
requests.post("http://localhost:8888/cdp/form/fill", json={
    "fields": {
        "#username": "admin' OR '1'='1",
        "#password": "'; DROP TABLE users; --"
    }
})
```

### Memory Testing
```python
# Test browser memory limits
requests.post("http://localhost:8888/cdp/execute", json={
    "code": "let arr = []; while(true) arr.push('x'.repeat(1000000))"
})
```

### Malformed Data Testing
```python
# Send malformed selectors
requests.post("http://localhost:8888/cdp/click", json={
    "selector": ">>>invalid<<<selector//\\0"
})

# Send huge values
requests.post("http://localhost:8888/cdp/type", json={
    "selector": "#input",
    "text": "x" * 10000000
})

# Null byte injection
requests.post("http://localhost:8888/cdp/execute", json={
    "code": "document.title = 'test\\0null\\nbytes'"
})
```

### DOS Testing
```python
# Rapid-fire requests (no rate limiting)
import threading

def flood():
    for i in range(10000):
        requests.post("http://localhost:8888/cdp/click",
                     json={"x": i, "y": i})

threads = [threading.Thread(target=flood) for _ in range(100)]
for t in threads:
    t.start()
```

## Error Handling

CDP Ninja returns errors transparently from Chrome DevTools:

### Connection Errors
```json
{
  "error": "Not connected to Chrome DevTools",
  "suggestion": "Check Chrome is running with --remote-debugging-port=9222"
}
```

### CDP Errors
```json
{
  "error": {
    "code": -32000,
    "message": "Cannot find context with specified id"
  }
}
```

### Timeout Errors
```json
{
  "error": "Command timeout after 10s"
}
```

## Best Practices

### For Debugging
1. **Use screenshots liberally**: Capture state before and after actions
2. **Monitor console logs**: Catch JavaScript errors early
3. **Track network requests**: Identify failed API calls
4. **Chain actions**: Use `/debug/reproduce` for complex workflows

### For Security Testing
1. **Test in isolation**: Use dedicated test environments
2. **Monitor resources**: Watch memory and CPU during tests
3. **Log everything**: Capture all requests and responses
4. **Test edge cases**: Send malformed data, huge values, special characters

### For Performance Testing
1. **Disable throttling initially**: Get baseline performance
2. **Simulate real conditions**: Add network throttling gradually
3. **Monitor metrics**: Track layout counts, script duration
4. **Test resource limits**: Find breaking points

### SSH Tunnel Setup
```bash
# From Windows/local machine to remote server
ssh -R 8888:localhost:8888 user@your-server.com

# Now CDP Ninja is accessible on the remote server at localhost:8888
```

## Troubleshooting

### Chrome won't connect
- Ensure `--remote-allow-origins=*` flag is set
- Check no other Chrome instances are running
- Verify port 9222 is not in use

### Commands timeout
- Increase timeout in individual requests
- Check Chrome hasn't crashed
- Verify network connectivity

### Screenshots are blank
- Wait for page load: `{"action": "wait", "duration": 2}`
- Check if page requires authentication
- Verify viewport size is set correctly

## Python Client Example

```python
import requests
import json
import base64

class CDPNinja:
    def __init__(self, base_url="http://localhost:8888"):
        self.base_url = base_url

    def navigate(self, url):
        return requests.post(f"{self.base_url}/cdp/page/navigate",
                            json={"url": url}).json()

    def click(self, selector):
        return requests.post(f"{self.base_url}/cdp/click",
                            json={"selector": selector}).json()

    def type_text(self, selector, text):
        return requests.post(f"{self.base_url}/cdp/type",
                            json={"selector": selector, "text": text}).json()

    def screenshot(self, full_page=False):
        params = {"full_page": "true"} if full_page else {}
        response = requests.get(f"{self.base_url}/cdp/screenshot",
                               params=params)
        return response.content

    def execute_js(self, code):
        return requests.post(f"{self.base_url}/cdp/execute",
                            json={"code": code}).json()

    def get_console_logs(self, level=None):
        params = {"level": level} if level else {}
        return requests.get(f"{self.base_url}/cdp/console/logs",
                           params=params).json()

# Usage example
cdp = CDPNinja()
cdp.navigate("https://example.com")
cdp.click("#login-button")
cdp.type_text("#username", "testuser")
screenshot = cdp.screenshot(full_page=True)
with open("screenshot.png", "wb") as f:
    f.write(screenshot)
```

## Advanced CDP Commands

For direct Chrome DevTools Protocol access, use `/cdp/command`:

```python
# Enable animation domain
requests.post("http://localhost:8888/cdp/command", json={
    "method": "Animation.enable"
})

# Set device metrics override
requests.post("http://localhost:8888/cdp/command", json={
    "method": "Emulation.setDeviceMetricsOverride",
    "params": {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 3,
        "mobile": True
    }
})

# Emulate network conditions
requests.post("http://localhost:8888/cdp/command", json={
    "method": "Network.emulateNetworkConditions",
    "params": {
        "offline": False,
        "downloadThroughput": 1.5 * 1024 * 128,  # 1.5 Mbps
        "uploadThroughput": 750 * 128,           # 750 Kbps
        "latency": 40
    }
})
```

## Support

- 🐛 [Report Issues](https://github.com/travofoz/cdp-ninja/issues)
- 📚 [CDP Protocol Reference](https://chromedevtools.github.io/devtools-protocol/)
- 🥷 [CDP Ninja GitHub](https://github.com/travofoz/cdp-ninja)

Remember: CDP Ninja is intentionally dangerous for security testing. Never use it on production systems or without proper authorization.