# CDP Ninja API Usage Guide 🥷

Complete API documentation for CDP Ninja - Chrome DevTools Protocol Bridge

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

## ⚠️ Important: curl JSON Escaping

**curl is tricky with JSON escaping!** Most examples use `$'...'` bash syntax to handle quotes properly:

```bash
# ✅ CORRECT: Use $'...' for clean escaping
curl -X POST http://localhost:8888/cdp/execute -H "Content-Type: application/json" -d $'{"code": "alert(\\"Hello!\\")"}'

# ❌ WRONG: This becomes a mess with backslashes
curl -X POST http://localhost:8888/cdp/execute -H "Content-Type: application/json" -d "{\"code\": \"alert(\\\"Hello!\\\")\"}"
```

**How `$'...'` works:**
- `$'...'` enables ANSI-C quoting in bash
- `\\"` inside `$'...'` becomes literal `"` in the JSON
- Much cleaner than escaping every quote with backslashes

**If curl escaping confuses you:**
```python
# Use Python requests for clean JSON
import requests
requests.post("http://localhost:8888/cdp/execute", json={"code": 'alert("Hello!")'})
```

## Core Concepts

CDP Ninja acts as a transparent HTTP-to-WebSocket bridge:
- **No validation**: All inputs are passed directly to Chrome
- **No sanitization**: Malformed data is allowed for security testing
- **Raw pass-through**: Direct CDP command execution

## API Documentation by Domain

| Domain | File | Description |
|--------|------|-------------|
| **System** | [system.md](system.md) | System commands, shell execution, process info |
| **Browser** | [browser.md](browser.md) | Click, type, scroll, hover, drag interactions |
| **Page** | [page.md](page.md) | Navigation, reload, back/forward, screenshots |
| **DOM** | [dom.md](dom.md) | Element queries, attributes, HTML manipulation |
| **Forms** | [forms.md](forms.md) | Form filling, submission, field extraction |
| **JavaScript** | [javascript.md](javascript.md) | Code execution, evaluation, injection |
| **Network** | [network.md](network.md) | Request monitoring, blocking, throttling |
| **Console** | [console.md](console.md) | Log access, error collection |
| **Performance** | [performance.md](performance.md) | Memory analysis, profiling, metrics |
| **Debugging** | [debugging.md](debugging.md) | Advanced debugging, reproduction workflows |
| **Security** | [security.md](security.md) | Security testing examples and patterns |

## Error Handling

All endpoints return JSON responses with standard error patterns:
```json
{
  "error": "Description of what went wrong",
  "success": false,
  "crash": true,  // if internal error
  "timeout": true // if operation timed out
}
```

## Best Practices

- **Start simple**: Test basic endpoints before complex workflows
- **Check Chrome first**: Ensure Chrome DevTools is responding
- **Monitor console**: Watch for JavaScript errors during automation
- **Use timeouts**: Set appropriate timeouts for long operations
- **Security awareness**: This tool is intentionally dangerous for testing

## Support

- **Issues**: https://github.com/travofoz/cdp-ninja/issues
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Responsible disclosure for security findings