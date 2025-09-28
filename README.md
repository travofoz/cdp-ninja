# CDP Ninja 🥷

A lightweight Chrome DevTools Protocol bridge for browser debugging and automation without the bloat of Puppeteer or Playwright.

[![PyPI version](https://badge.fury.io/py/cdp-ninja.svg)](https://badge.fury.io/py/cdp-ninja)
[![Python Support](https://img.shields.io/pypi/pyversions/cdp-ninja.svg)](https://pypi.org/project/cdp-ninja/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ⚠️ SECURITY WARNING ⚠️

**CDP Ninja is intentionally dangerous for security testing and fuzzing:**

- 🚨 **No Input Validation**: Malformed selectors, XSS payloads, null bytes allowed
- 🚨 **No Rate Limiting**: Request flooding, memory bombs, infinite loops
- 🚨 **Shell Execution**: Remote code execution with `--shell` flag
- 🚨 **Raw DOM Access**: Direct HTML/script injection capabilities

**Philosophy**: If malformed data breaks it, it has bugs. This tool crashes things on purpose.

**Only use in secure, isolated environments for authorized testing.**

## Why CDP Ninja?

- **No Chromium Download**: Uses existing Chrome (saves 300MB)
- **Minimal Dependencies**: 16MB vs 350MB+ alternatives
- **Direct CDP Access**: Raw Chrome DevTools power, no abstractions
- **Remote Debugging**: SSH tunnel support for remote access
- **Nine Schools Architecture**: Specialized debugging agents for different domains

## Quick Start

### 1. Install
```bash
pip install cdp-ninja
# or
uv add cdp-ninja
```

### 2. Start Chrome with debugging
```bash
# Windows
chrome --remote-debugging-port=9222 --remote-allow-origins=*

# Linux/macOS
google-chrome --remote-debugging-port=9222 --remote-allow-origins=*
```

### 3. Run CDP Ninja
```bash
cdp-ninja
# With shell execution (dangerous)
cdp-ninja --shell
```

### 4. Test the connection
```bash
curl http://localhost:8888/cdp/status
curl http://localhost:8888/cdp/screenshot > test.png
```

## Nine Schools Architecture

CDP Ninja includes 9 specialized Claude Code debugging agents:

| School | Focus | Use Case |
|--------|-------|----------|
| 🥷 **Hidden Door** | Reconnaissance | Quick status checks, initial triage |
| ⚔️ **Nine Demons** | JavaScript | Error analysis, code debugging |
| 💎 **Jewel Tiger** | DOM Surgery | Element targeting, form handling |
| 🔷 **Jewel Heart** | Network Intel | Traffic analysis, API monitoring |
| 🛡️ **Divine Immovable** | Error Defense | Exception handling, recovery flows |
| ☁️ **Cloud Hiding** | Performance | Memory analysis, profiling |
| 🌳 **High Tree** | Accessibility | WCAG compliance, UX analysis |
| 🐅 **Tiger Knockdown** | Stress Testing | Breaking points, chaos engineering |
| 🔒 **Righteous** | Security | Vulnerability assessment, protection |

## Documentation

| Section | Description |
|---------|-------------|
| **[API Reference](docs/usage/readme.md)** | Complete API documentation by domain |
| **[System Commands](docs/usage/system.md)** | Shell execution, process info |
| **[Browser Interaction](docs/usage/browser.md)** | Click, type, scroll, screenshots |
| **[Network Monitoring](docs/usage/network.md)** | Request analysis, blocking, throttling |
| **[Security Testing](docs/usage/security.md)** | XSS, SQLi, fuzzing examples |

## CLI Commands

### Core Flags
```bash
# Server configuration
cdp-ninja --cdp-port 9222 --bridge-port 8888 --debug

# Enable dangerous shell execution
cdp-ninja --shell

# API documentation
cdp-ninja --usage
```

### Agent Management
```bash
# Install debugging agents locally
cdp-ninja --install-agents /path/to/claude/agents/

# Install debugging agents remotely
cdp-ninja --install-agents user@server:/remote/path/
```

### Remote Deployment (Multi-Step Process)
```bash
# 1. Install dependencies on remote server
cdp-ninja --install-deps user@server --web-backend=ttyd

# 2. Start CDP Ninja bridge locally FIRST
cdp-ninja --shell  # (in separate terminal)

# 3. Setup tunnel to expose local bridge on remote server
cdp-ninja --tunnel user@server

# 4. Start remote Claude interface with web access
cdp-ninja --invoke-claude user@server --web-backend=ttyd

# Kill all tunnels when done
cdp-ninja --kill-tunnels
```

### Single Machine Setup (Simpler)
```bash
# If running everything locally, just start the bridge:
cdp-ninja --shell
# No tunnels needed
```

### Deployment Options
```bash
# Show manual instructions instead of executing
cdp-ninja --install-deps user@server --instruct-only
cdp-ninja --tunnel user@server --instruct-only

# Choose web terminal backend
cdp-ninja --invoke-claude user@server --web-backend=gotty  # or ttyd

# Start browser with CDP debugging
cdp-ninja --start-browser
```

## Security Research

CDP Ninja has successfully bypassed BrowserScan.net bot detection, revealing gaps in current detection mechanisms. This tool is designed for:

- **Defensive Security Research**: Understanding automation detection limits
- **Responsible Disclosure**: Improving bot detection for the community
- **Educational Purposes**: Learning browser security boundaries

## Support

- **Issues**: [GitHub Issues](https://github.com/travofoz/cdp-ninja/issues)
- **Discussions**: [GitHub Discussions](https://github.com/travofoz/cdp-ninja/discussions)
- **Security**: Responsible disclosure for security findings

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*"Maximum insight with minimal presence"* - The Ninja Way 🥷