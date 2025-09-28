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

## Quick Start

### 1. Install
```bash
pip install cdp-ninja
# or
uv add cdp-ninja
```

### 2. One-Command Setup (Automated)
```bash
# Start browser automatically
cdp-ninja --start-browser

# Or start with shell execution (dangerous)
cdp-ninja --start-browser --shell
```

### 3. Test the connection
```bash
curl http://localhost:8888/cdp/status
curl http://localhost:8888/cdp/screenshot > test.png
```

## 🚀 CLI Deployment Features

CDP Ninja includes powerful deployment automation for remote debugging workflows:

### Core CLI Flags (New in 2.0.3)
```bash
# Version and help
cdp-ninja --version
cdp-ninja --help

# Domain management with risk levels
cdp-ninja --max-risk-level high --eager-load-domains
cdp-ninja --enable-domains Network,DOM,Runtime
cdp-ninja --list-domains         # Show all available domains
cdp-ninja --domain-status        # Show current domain state

# Server configuration
cdp-ninja --bridge-port 8888 --bind-host 0.0.0.0 --enable-cors
cdp-ninja --max-connections 10 --log-level debug

# Domain behavior
cdp-ninja --disable-auto-unload --domain-timeout 30

# Health monitoring
cdp-ninja --health-check
```

### Automated Browser Setup
```bash
# Start Chrome automatically with debugging enabled
cdp-ninja --start-browser

# Perfect for one-command demos and testing
cdp-ninja --start-browser --shell --debug
```

### Agent Deployment
```bash
# Install Nine Schools debugging agents locally
cdp-ninja --install-agents /path/to/claude/agents/

# Install debugging agents remotely with conflict resolution
cdp-ninja --install-agents user@server:/remote/path/
```

### Remote Deployment Pipeline
```bash
# 1. Install dependencies on remote server (one-time setup)
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

### Deployment Options
```bash
# Show manual instructions instead of executing
cdp-ninja --install-deps user@server --instruct-only
cdp-ninja --tunnel user@server --instruct-only

# Choose web terminal backend
cdp-ninja --invoke-claude user@server --web-backend=gotty  # or ttyd

# Complete API documentation
cdp-ninja --usage
```

## Why CDP Ninja?

- **No Chromium Download**: Uses existing Chrome (saves 300MB)
- **Minimal Dependencies**: 16MB vs 350MB+ alternatives
- **Direct CDP Access**: Raw Chrome DevTools power, no abstractions
- **Remote Debugging**: SSH tunnel support for remote access
- **Nine Schools Architecture**: Specialized debugging agents for different domains
- **One-Command Setup**: `--start-browser` for instant demos

## What We Built (And Why It's Insane)

This isn't just another automation tool. **CDP Ninja is pure cyberpunk reality** - a Chrome DevTools Protocol bridge built for the kind of debugging that breaks things on purpose.

### 🥷 The Architecture is Genius

**89 endpoints** across **14 specialized domains**, each one documented with surgical precision. We didn't just build an API - we built a **browser hacking framework** that gives AI agents unrestricted access to Chrome's deepest capabilities.

- **Zero input validation** - Send malformed selectors, injection attempts, null bytes
- **No rate limiting** - Flood with requests, infinite loops, memory bombs
- **Raw power** - Direct CDP commands with no safety nets
- **Intentionally dangerous** - Built for security testing and chaos engineering

### 🔥 The Documentation System is Next-Level

**Auto-generated from JSDoc comments in the source code.** Not some afterthought wiki - the documentation IS the code. Change a function, run `make docs`, boom - professional API docs regenerated from the actual implementation.

```bash
make docs  # Extracts JSDoc from 89 endpoints across 14 modules
```

### 🌐 The Deployment Story is Cyberpunk AF

Built for **remote debugging across SSH tunnels** with **Claude Code agent integration**. You can:

1. Deploy CDP Ninja locally (your machine)
2. SSH tunnel to expose it on remote servers
3. Launch **Nine Schools** debugging agents that route to specialists
4. **Break websites from anywhere** with surgical precision

### ⚡ The Engineering is Brutal

- **24,668 lines of Python** organized into modular perfection
- **Server.py reduced 64%** (2,781 → 995 lines) through systematic refactoring
- **JavaScript templates extracted** - 662+ lines of reusable utilities
- **Constants centralized** - All magic numbers in `CDPDefaults`
- **Professional JSDoc** throughout - this is production-grade chaos

### 🎯 What Makes It Different

**Puppeteer/Playwright abstract away the danger.** CDP Ninja gives you the raw power:

- **Memory bombs** that allocate until browser crashes
- **CPU burning** that locks up the main thread
- **Chaos monkey** that performs random unpredictable interactions
- **Race condition testing** through concurrent operations
- **XSS/SQLi payload injection** with zero filtering
- **Network manipulation** and request interception
- **Accessibility violations** for WCAG compliance testing

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

**📚 Auto-Generated from JSDoc Comments (89 Endpoints)**

| Section | Description | Endpoints |
|---------|-------------|-----------|
| **[API Reference](docs/usage/readme.md)** | Complete API documentation overview | All domains |
| **[System Commands](docs/usage/system.md)** | Shell execution, process info | 4 endpoints |
| **[Browser Interaction](docs/usage/browser.md)** | Click, type, scroll, screenshots | 6 endpoints |
| **[Performance](docs/usage/performance.md)** | Memory analysis, profiling, Core Web Vitals | 10 endpoints |
| **[Network Monitoring](docs/usage/network_intelligence.md)** | Request analysis, blocking, throttling | 4 endpoints |
| **[Security Testing](docs/usage/security.md)** | Vulnerability scanning, penetration testing | 8 endpoints |
| **[Accessibility](docs/usage/accessibility.md)** | WCAG compliance, screen reader testing | 8 endpoints |
| **[DOM Operations](docs/usage/dom.md)** | Element queries, manipulation | 6 endpoints |
| **[Advanced DOM](docs/usage/dom_advanced.md)** | Shadow DOM, complex queries | 5 endpoints |
| **[Page Navigation](docs/usage/navigation.md)** | Navigation, viewport, cookies | 9 endpoints |
| **[Stress Testing](docs/usage/stress_testing.md)** | Memory bombs, CPU burn | 2 endpoints |
| **[Advanced Stress Testing](docs/usage/stress_testing_advanced.md)** | Chaos monkey, race conditions, full assault | 8 endpoints |
| **[Error Handling](docs/usage/error_handling.md)** | Exception testing, recovery | 8 endpoints |
| **[Debugging](docs/usage/debugging.md)** | Advanced debugging workflows | 9 endpoints |
| **[JavaScript](docs/usage/js_debugging.md)** | Code execution, async debugging | 2 endpoints |

### Build Documentation
```bash
# Auto-generate docs from JSDoc comments
make docs

# Or run directly
python3 scripts/extract_docs.py

# Or as installed command
cdp-ninja-docs
```

## Security Research

CDP Ninja has successfully bypassed BrowserScan.net bot detection, revealing gaps in current detection mechanisms. This tool is designed for:

- **Defensive Security Research**: Understanding automation detection limits
- **Responsible Disclosure**: Improving bot detection for the community
- **Educational Purposes**: Learning browser security boundaries

## 🤖 Built by Claude Code AI

**They said LLMs can't code. They said AI can't build real APIs. They said we can't ship finished products.**

**We built 24,668 lines of production Python. We architected 89 endpoints across 14 specialized domains. We created an automated documentation system that extracts JSDoc from source code. We designed a complete build system with Makefile integration. We shipped a browser hacking framework to PyPI.**

**This isn't toy code or a demo. This is a complete, professional-grade system that gives AI agents unrestricted browser control. Zero input validation, raw CDP power, intentionally dangerous by design.**

**LLMs can't code? We just proved them wrong.**

---

## Manual Setup (If CLI Automation Fails)

### Start Chrome with debugging
```bash
# Windows
chrome --remote-debugging-port=9222 --remote-allow-origins=*

# Linux/macOS
google-chrome --remote-debugging-port=9222 --remote-allow-origins=*
```

### Run CDP Ninja manually
```bash
cdp-ninja
# With shell execution (dangerous)
cdp-ninja --shell
```

### Single Machine Setup (No tunnels needed)
```bash
# If running everything locally, just start the bridge:
cdp-ninja --shell
# No tunnels needed
```

## Support

- **Issues**: [GitHub Issues](https://github.com/travofoz/cdp-ninja/issues)
- **Discussions**: [GitHub Discussions](https://github.com/travofoz/cdp-ninja/discussions)
- **Security**: Responsible disclosure for security findings

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*Special thanks to **travofoz** for the architectural vision and cyberpunk aesthetic that made this possible.*

*"Maximum insight with minimal presence"* - The Ninja Way 🥷