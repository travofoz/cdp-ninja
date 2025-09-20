# Debug Ninja 🥷

A lightweight Chrome DevTools Protocol bridge that gives you powerful browser debugging capabilities without the bloat of Puppeteer or Playwright.

## Why Debug Ninja?

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

### Installation

#### Cross-Platform (Recommended)
```bash
# Clone repository
git clone https://github.com/yourusername/debug-ninja
cd debug-ninja

# Run cross-platform installer (auto-detects your OS)
python setup/install.py

# Start bridge
./start_bridge.sh          # Linux/macOS
# OR
.\start_bridge.bat         # Windows
```

#### Platform-Specific Installation

**Windows:**
```powershell
# Run PowerShell installer
.\setup\setup_windows.ps1

# Start bridge
.\start_bridge.bat
```

**Linux/macOS:**
```bash
# Run bash installer
./setup/setup_unix.sh

# Start bridge
./start_bridge.sh
```

### SSH Tunnel Setup

Debug Ninja supports both tunnel directions depending on your setup:

#### Option A: Access Remote Debug Ninja (Local Forward)
When Debug Ninja runs on a remote machine and you want to access it locally:
```bash
# From your local machine
ssh -L 8888:localhost:8888 user@remote-machine

# Now access bridge locally
curl http://localhost:8888/cdp/status
```

#### Option B: Expose Local Debug Ninja (Reverse Forward)
When Debug Ninja runs locally and Claude Code/remote tools need access:
```bash
# From your local machine (where Chrome/Debug Ninja runs)
ssh -R 8888:localhost:8888 user@claude-code-vps

# Remote system can now access your local bridge
curl http://localhost:8888/cdp/status
```

#### Test Connection
```bash
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

### Execute JavaScript
```python
# Run JavaScript in page context
response = requests.post("http://localhost:8888/cdp/execute",
                         json={"code": "document.querySelector('#result').innerText"})
result = response.json()
print(result.get('result', {}).get('value'))
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

### Fill Forms
```python
# Fill multiple form fields
requests.post("http://localhost:8888/cdp/form/fill", json={
    "fields": {
        "#email": "test@example.com",
        "#password": "secret123",
        "#username": "testuser"
    }
})

# Submit form
requests.post("http://localhost:8888/cdp/form/submit",
              json={"selector": "#login-form"})
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

### System Integration (Windows)
- `POST /system/powershell` - Execute PowerShell command
- `GET /system/processes` - List processes
- `GET /system/chrome/profiles` - List Chrome profiles

### Advanced Debugging
- `POST /debug/reproduce` - Automated bug reproduction
- `GET /debug/performance` - Performance metrics
- `GET /debug/memory` - Memory usage analysis

## Project Structure

```
debug-ninja/
├── core/
│   ├── __init__.py
│   └── cdp_client.py        # WebSocket CDP client with auto-reconnect
├── api/
│   ├── __init__.py
│   └── server.py            # Flask application with 40+ endpoints
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

| Feature | Debug Ninja | Playwright | Puppeteer | Selenium |
|---------|----------------|------------|-----------|----------|
| Browser Download | 0 MB (uses your Chrome) | 300MB | 170MB | 0 MB |
| Python Package | 16MB | 50MB | N/A | 15MB |
| Memory Usage | ~50MB | ~500MB | ~400MB | ~200MB |
| Setup Time | <1 minute | 5+ minutes | 3+ minutes | 2+ minutes |
| Direct CDP Access | ✅ | ❌ (abstracted) | ❌ (abstracted) | ❌ (WebDriver) |
| Remote Debugging | ✅ SSH tunnel | ❌ Complex | ❌ Complex | ✅ Grid |
| Learning Curve | Low (REST API) | High | High | Medium |

## Troubleshooting

### Chrome Not Found
```powershell
# Specify Chrome path manually
.\setup\setup_windows.ps1 -ChromePath "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

### Connection Failed
```bash
# Check if Chrome is running with debug port
curl http://localhost:9222/json

# Check if bridge is running
curl http://localhost:8888/health
```

### SSH Tunnel Issues
```bash
# Test local connection first
curl http://localhost:8888/cdp/status

# Use verbose SSH
ssh -v -L 8888:localhost:8888 user@windows-machine
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

- 📚 [Documentation](https://github.com/yourusername/cdp-thin-bridge/wiki)
- 🐛 [Issues](https://github.com/yourusername/cdp-thin-bridge/issues)
- 💬 [Discussions](https://github.com/yourusername/cdp-thin-bridge/discussions)