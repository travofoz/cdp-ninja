# CDP Ninja 🥷

A lightweight Chrome DevTools Protocol bridge that gives you powerful browser debugging capabilities without the bloat of Puppeteer or Playwright.

[![PyPI version](https://badge.fury.io/py/cdp-ninja.svg)](https://badge.fury.io/py/cdp-ninja)
[![Python Support](https://img.shields.io/pypi/pyversions/cdp-ninja.svg)](https://pypi.org/project/cdp-ninja/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ⚠️ SECURITY WARNING ⚠️

**CDP Ninja is intentionally dangerous for security testing and fuzzing. It allows:**

- 🚨 **No Input Validation**: Send malformed selectors, injection attempts, null bytes, XSS payloads
- 🚨 **No Rate Limiting**: Flood with requests, infinite loops, memory bombs
- 🚨 **PowerShell Execution**: Remote code execution when `ENABLE_POWERSHELL=true`
- 🚨 **Any URL Navigation**: javascript:, data:, file:// protocols allowed
- 🚨 **Raw DOM Manipulation**: HTML injection, script injection, attribute modification

**Philosophy**: If we can break it with malformed data, it has bugs. This tool crashes things on purpose.

**Only use CDP Ninja in secure, isolated environments for testing purposes.**

## Why CDP Ninja?

- **No Chromium Download**: Uses your existing Chrome installation (saves 300MB)
- **Minimal Dependencies**: Only 16MB of Python packages vs 350MB+ for alternatives
- **Direct CDP Access**: No abstraction layers, just raw Chrome DevTools power
- **Remote Debugging**: SSH tunnel support for debugging from anywhere
- **Claude Code Integration**: Works as a specialized debugging agent

## Architecture

```
Your Chrome → CDP WebSocket → Python Bridge → HTTP API → SSH Tunnel → Claude/Tools
     ↑             ↑              ↑             ↑           ↑
Already      Built-in        16MB deps    REST API    Remote access
installed    protocol
```

## Features

- 🖱️ **Full Browser Control**: Click, type, scroll, hover, drag
- 🌐 **Network Monitoring**: Capture all requests, responses, and timing
- 📊 **Performance Profiling**: Memory, CPU, rendering metrics
- 🐛 **Console Access**: Capture logs, errors, warnings
- 📸 **Screenshots**: Full page or viewport captures
- 🔍 **DOM Inspection**: Query, modify, and analyze page structure
- ⚡ **JavaScript Execution**: Run code in page context
- 🎯 **Bug Reproduction**: Automated workflows for reproducing issues

## Quick Start

### Prerequisites

1. **Chrome** installed
2. **Python 3.8+** installed

### Installation

```bash
# Install CDP Ninja
pip install git+https://github.com/travofoz/cdp-ninja.git

# Start Chrome with debugging enabled
# Windows PowerShell:
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="C:\temp\chrome-debug"

# Linux/macOS:
google-chrome --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=/tmp/chrome-debug

# Start CDP Ninja
cdp-ninja
```

**Test it works:**
```bash
curl http://localhost:8888/cdp/status
```

### Custom Settings

```bash
# Use different ports
cdp-ninja --bridge-port 9999 --cdp-port 9222

# Enable debug mode
cdp-ninja --debug
```

### SSH Tunnel Setup

To expose your local CDP Ninja to a remote server:

```bash
# From your local machine (where CDP Ninja runs)
ssh -R 8888:localhost:8888 user@your-server

# Now on the remote server:
curl http://localhost:8888/cdp/status
```

## Usage Examples

### Click a Button
```python
import requests

# Click by CSS selector
response = requests.post("http://localhost:8888/cdp/click",
                        json={"selector": "#submit-button"})

# Click by coordinates
response = requests.post("http://localhost:8888/cdp/click",
                        json={"x": 100, "y": 200})
```

### Capture Screenshot
```python
# Take screenshot
response = requests.get("http://localhost:8888/cdp/screenshot")
with open("screenshot.png", "wb") as f:
    f.write(response.content)

# Full page screenshot
response = requests.get("http://localhost:8888/cdp/screenshot?full_page=true")
```

### Execute JavaScript (⚠️ No Validation)
```python
# Normal JavaScript execution
response = requests.post("http://localhost:8888/cdp/execute",
                         json={"code": "document.querySelector('#result').innerText"})
result = response.json()

# ⚠️ Security Testing Examples (will attempt execution):
# Infinite loop test
requests.post("http://localhost:8888/cdp/execute",
              json={"code": "while(true) { console.log('crash test'); }"})

# Memory bomb test
requests.post("http://localhost:8888/cdp/execute",
              json={"code": "let a = []; while(true) a.push('x'.repeat(1000000));"})

# XSS injection test
requests.post("http://localhost:8888/cdp/execute",
              json={"code": "alert('XSS test: ' + document.cookie)"})
```

### Monitor Network Traffic
```python
# Get all recent network requests
response = requests.get("http://localhost:8888/cdp/network/requests")
for request in response.json():
    print(f"{request['method']} {request['url']} - Status: {request.get('response', {}).get('status')}")

# Block specific URLs
requests.post("http://localhost:8888/cdp/network/block",
              json={"patterns": ["*://*.doubleclick.net/*", "*://analytics.google.com/*"]})
```

### Fill Forms (⚠️ No Sanitization)
```python
# Normal form filling
requests.post("http://localhost:8888/cdp/form/fill", json={
    "fields": {
        "#email": "test@example.com",
        "#password": "secret123",
        "#username": "testuser"
    }
})

# ⚠️ Security Testing Examples:
# Malformed selectors and values with null bytes
requests.post("http://localhost:8888/cdp/form/fill", json={
    "fields": {
        ">>>invalid_selector<<<": "test\0null\nbytes",
        "#input": "x" * 1000000,  # Huge value test
        "#other": "'; DROP TABLE users; --"  # SQL injection attempt
    }
})

# Test malformed form submission
requests.post("http://localhost:8888/cdp/form/submit",
              json={"selector": ">>>invalid<<<"})
```

### Bug Reproduction Workflow
```python
# Automated bug reproduction with screenshots
response = requests.post("http://localhost:8888/debug/reproduce", json={
    "steps": [
        {"action": "navigate", "url": "http://localhost:3000"},
        {"action": "click", "selector": "#login-btn"},
        {"action": "type", "selector": "#email", "text": "test@example.com"},
        {"action": "click", "selector": "#submit"},
        {"action": "wait", "duration": 2},
        {"action": "click", "selector": "#submit"},  # Double-click bug
        {"action": "click", "selector": "#submit"}   # Triple-click bug
    ],
    "screenshots": True,
    "capture_console": True
})

print(f"Bug reproduced: {response.json()['completed']}")
```

## Claude Code Integration

Add to your Claude Code agent configuration:

```markdown
cdp-debugger: Browser debugging specialist using Chrome DevTools Protocol.
Captures network requests, console logs, executes JavaScript, takes screenshots,
clicks elements, fills forms. Use PROACTIVELY for debugging client-side issues,
reproducing bugs, and automated browser interaction. (Tools: WebFetch to CDP bridge)
```

Usage:
```python
from tools import Task

# Use the debugging agent
Task(
    subagent_type="cdp-debugger",
    description="Debug login form",
    prompt="Click login button 5 times rapidly and capture any console errors or network failures"
)
```

## API Reference

### Core Operations
- `GET /health` - Health check
- `GET /cdp/status` - CDP connection status
- `POST /cdp/command` - Execute raw CDP command

### Browser Interaction
- `POST /cdp/click` - Click element (selector or coordinates)
- `POST /cdp/type` - Type text into element
- `POST /cdp/scroll` - Scroll page
- `POST /cdp/hover` - Hover over element
- `GET /cdp/screenshot` - Capture screenshot

### Debugging Operations
- `GET /cdp/console/logs` - Get console output
- `GET /cdp/network/requests` - Get network activity
- `POST /cdp/execute` - Execute JavaScript
- `GET /cdp/dom/snapshot` - Get DOM tree

### Form Operations
- `POST /cdp/form/fill` - Fill form fields
- `POST /cdp/form/submit` - Submit form
- `GET /cdp/form/values` - Get form field values

### Page Navigation
- `POST /cdp/page/navigate` - Navigate to URL
- `GET /cdp/page/reload` - Reload page
- `GET /cdp/page/back` - Go back
- `GET /cdp/page/forward` - Go forward

### Network Control
- `POST /cdp/network/block` - Block URLs
- `POST /cdp/network/throttle` - Simulate slow network
- `GET /cdp/network/clear` - Clear network cache

### System Integration (⚠️ DANGEROUS)
- `POST /system/execute` - Execute RAW PowerShell/CMD/Bash commands (requires `ENABLE_POWERSHELL=true`)
- `GET /system/info` - System information and capabilities
- `GET /system/processes` - Browser process information
- `GET /system/chrome/info` - Chrome debugging information

**⚠️ PowerShell/Command Execution Setup:**
```bash
# Enable dangerous system commands (REQUIRED for /system/execute)
export ENABLE_POWERSHELL=true  # Linux/macOS
# OR
set ENABLE_POWERSHELL=true     # Windows CMD
# OR
$env:ENABLE_POWERSHELL="true"  # PowerShell
```

### Advanced Debugging
- `POST /debug/reproduce` - Automated bug reproduction
- `GET /debug/performance` - Performance metrics
- `GET /debug/memory` - Memory usage analysis

## Testing Philosophy

CDP Ninja is designed for **security testing and fuzzing**:

- **No Input Validation**: All endpoints accept ANY data to test application limits
- **Intentional Code Injection**: JavaScript string interpolation allows arbitrary code execution for testing
- **Crash Reporting**: When malformed data crashes Chrome, that's valuable debugging data
- **Raw Pass-Through**: Commands are sent exactly as provided to Chrome DevTools
- **Edge Case Testing**: Null bytes, huge values, malformed selectors are encouraged
- **Security Research**: XSS, injection attempts, protocol violations are allowed
- **Browser Vulnerability Discovery**: Test how browsers handle malformed CSS selectors and JavaScript

**The "vulnerabilities" in CDP Ninja are features, not bugs.**

**If CDP Ninja can break your application with malformed data, your application has bugs.**

This tool is intentionally permissive to help find vulnerabilities and edge cases through aggressive testing.

## Project Structure

```
cdp-ninja/
├── core/
│   ├── __init__.py
│   ├── cdp_client.py        # WebSocket CDP client with auto-reconnect
│   └── cdp_pool.py          # Connection pooling for performance
├── api/
│   ├── __init__.py
│   ├── server.py            # Main Flask application
│   ├── config.py            # Configuration with PowerShell toggle
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── browser.py       # RAW browser interaction (click, type, screenshot)
│   │   ├── debugging.py     # RAW JavaScript execution and console access
│   │   ├── navigation.py    # RAW navigation (any URL, any protocol)
│   │   ├── dom.py           # RAW DOM manipulation (no sanitization)
│   │   └── system.py        # RAW system commands (PowerShell/Bash)
│   └── utils/
│       └── error_reporter.py # Crash telemetry (not prevention)
├── setup/
│   ├── setup_windows.ps1   # Windows PowerShell installer
│   └── setup_unix.sh       # Linux/macOS bash installer
├── agent/
│   └── claude_agent.md     # Claude Code agent specification
├── examples/
│   ├── basic_usage.py      # Getting started examples
│   └── debug_nextjs.py     # Next.js debugging workflows
├── requirements.txt        # Python dependencies (16MB total)
├── README.md
├── LICENSE
└── setup.py
```

## Comparison with Alternatives

| Feature | CDP Ninja | Playwright | Puppeteer | Selenium |
|---------|----------------|------------|-----------|----------|
| Browser Download | 0 MB (uses your Chrome) | 300MB | 170MB | 0 MB |
| Python Package | 16MB | 50MB | N/A | 15MB |
| Memory Usage | ~50MB | ~500MB | ~400MB | ~200MB |
| Setup Time | <1 minute | 5+ minutes | 3+ minutes | 2+ minutes |
| Direct CDP Access | ✅ | ❌ (abstracted) | ❌ (abstracted) | ❌ (WebDriver) |
| Remote Debugging | ✅ SSH tunnel | ❌ Complex | ❌ Complex | ✅ Grid |
| Learning Curve | Low (REST API) | High | High | Medium |

## Common Issues & Solutions

### Installation Issues

**Problem: `ModuleNotFoundError` when running `cdp-ninja`**
```bash
# Solution: Force reinstall with no cache
pip install --force-reinstall --no-cache-dir git+https://github.com/travofoz/cdp-ninja.git
```

**Problem: `ImportError: cannot import name 'config'`**
```bash
# Solution: You have an old version, update to latest
pip uninstall cdp-ninja -y
pip install git+https://github.com/travofoz/cdp-ninja.git
```

### Connection Issues

**Problem: Chrome DevTools connection failed (403 Forbidden)**
```bash
# Solution: Chrome requires --remote-allow-origins flag
# Kill all Chrome processes first
Get-Process chrome | Stop-Process -Force  # Windows PowerShell
pkill chrome  # Linux/macOS

# Start Chrome with correct flags
chrome --remote-debugging-port=9222 --remote-allow-origins=*

# Windows PowerShell:
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="C:\temp\chrome-debug"
```

**Problem: Connection timeout on Windows**
```bash
# Chrome can be slow to respond on Windows
# This is fixed in v1.0.1+ (timeout increased to 30s)
pip install --upgrade git+https://github.com/travofoz/cdp-ninja.git
```

**Problem: Bridge server won't start on port 8888**
```bash
# Solution: Use a different port
cdp-ninja --bridge-port 9999
```

### Windows-Specific Issues

**Problem: PowerShell script execution disabled**
```powershell
# Solution: Enable script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Problem: Python not in PATH**
```powershell
# Solution: Use full path to Python
C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe -m pip install git+https://github.com/travofoz/cdp-ninja.git
```

### Verification Steps

```bash
# 1. Verify Chrome is accessible
curl http://localhost:9222/json
# Should return JSON with browser tabs

# 2. Verify CDP Ninja is running
curl http://localhost:8888/health
# Should return {"status": "ok"}

# 3. Test CDP connection
curl http://localhost:8888/cdp/status
# Should return connection details
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Built with ❤️ by developers who believe debugging should be simple, not bloated.

Special thanks to Claude (Anthropic) for architectural insights and implementation guidance.

## Support

- 📚 [API Documentation](USAGE.md) - Complete usage guide with examples
- 🐛 [Issues](https://github.com/travofoz/cdp-ninja/issues)
- 💬 [Discussions](https://github.com/travofoz/cdp-ninja/discussions)