# CDP Ninja - Nine Schools Debugging Dojo

**Browser debugging transformed from tool-spamming chaos to ninja mastery**

## Project Overview

CDP Ninja is a Chrome DevTools Protocol bridge with 9 specialized Claude Code debugging agents inspired by traditional Bujinkan ninja martial arts schools. Each agent is a focused expert that routes complex issues to appropriate specialists.

## The Nine Schools Architecture

### Core Philosophy
- **Maximum insight with minimal tool usage** (20-40 focused tools vs 96 random)
- **Domain specialization over generalization**
- **Recommendation over recursion** - agents suggest specialists, never invoke
- **Self-sufficient operation** - complete CDP API knowledge embedded in each agent

### The Ninja Schools

1. **🥷 Hidden Door** (Togakure Ryū) - Reconnaissance specialist (20 tools)
   - Quick status checks, screenshot analysis, basic error detection
   - Entry point for 80% of debugging scenarios
   - Routes users to appropriate specialists

2. **⚔️ Nine Demons** (Kuki Shinden Ryū) - JavaScript master (30 tools)
   - Error archaeology, stack trace analysis, async debugging
   - Code execution, variable inspection, runtime evaluation
   - Most needed specialist for JavaScript errors

3. **💎 Jewel Tiger** (Gyokko Ryū) - DOM precision surgeon (40 tools)
   - Element targeting, form analysis, CSS selector mastery
   - Shadow DOM navigation, XPath expertise
   - Most complex domain requiring deep investigation

4. **🔷 Jewel Heart** (Gyokushin Ryū) - Network intelligence spy (30 tools)
   - Request/response analysis, authentication flows
   - Performance timing, WebSocket monitoring
   - Patient intelligence gathering approach

5. **🛡️ Divine Immovable** (Shinden Fudō Ryū) - Error defense shield (25 tools)
   - Error boundary analysis, exception handling review
   - Recovery flow validation, fallback testing
   - Defensive resilience focus

6. **☁️ Cloud Hiding** (Kumogakure Ryū) - Performance observer (30 tools)
   - Memory analysis, CPU profiling, rendering optimization
   - Background task monitoring, invisible surveillance
   - Core Web Vitals expertise

7. **🌳 High Tree** (Takagi Yōshin Ryū) - Accessibility advocate (25 tools)
   - WCAG compliance, screen reader compatibility
   - UX flow analysis, inclusive design validation
   - Compassionate elevated perspective

8. **🐅 Tiger Knockdown** (Kotō Ryū) - Aggressive stress tester (35 tools)
   - Breaking point discovery, chaos engineering
   - Structural assault, boundary testing
   - Fearless limit exploration

9. **🔒 Righteous** (Gikan Ryū) - Security guardian (30 tools)
   - Vulnerability assessment, authentication review
   - Data protection, ethical security testing
   - Protective moral conviction

## Usage Patterns

### Quick Debugging (Most Common)
```python
from tools import Task

# Start with Hidden Door for reconnaissance
Task(
    subagent_type="cdp-ninja-hidden-door",
    description="Quick debug check",
    prompt="Check if login form is working properly"
)
```

### Specific Issue Debugging
```python
# JavaScript errors
Task(subagent_type="cdp-ninja-nine-demons",
     prompt="Debug TypeError in user authentication")

# DOM/form issues
Task(subagent_type="cdp-ninja-jewel-tiger",
     prompt="Submit button appears but not clickable")

# Network problems
Task(subagent_type="cdp-ninja-jewel-heart",
     prompt="API calls failing with 500 errors")

# Performance issues
Task(subagent_type="cdp-ninja-cloud-hiding",
     prompt="Page load time over 5 seconds")
```

## Agent Routing Logic

Each agent automatically routes complex issues:

- **Hidden Door** → Routes to appropriate specialist based on findings
- **Nine Demons** → Routes DOM issues to Jewel Tiger, network to Jewel Heart
- **Jewel Tiger** → Routes JS errors to Nine Demons, accessibility to High Tree
- **All agents** → Route security concerns to Righteous, performance to Cloud Hiding

## CDP Bridge Requirements

### Prerequisites
1. Chrome running with `--remote-debugging-port=9222`
2. CDP Ninja bridge running on `localhost:8888`
3. SSH tunnel for remote access: `ssh -R 8888:localhost:8888 user@server`

### Common Setup
```bash
# Start Chrome with debugging
chrome --remote-debugging-port=9222 --remote-allow-origins=*

# Start CDP Ninja bridge
cdp-ninja --bridge-port 8888

# Test connection
curl http://localhost:8888/cdp/status
```

## Agent Architecture

### Tool Access (All Agents)
```yaml
tools: Bash, WebFetch, WebSearch, Read, Glob, Grep, TodoWrite
```
**Note**: No Task tool to prevent recursion - agents recommend, never invoke

### Self-Sufficiency Requirement
Each agent includes complete CDP API syntax with exact curl commands because agents are distributed separately and cannot access USAGE.md at runtime.

### Stopping Conditions
- Domain-specific tool limits (20-40 calls max)
- Confidence thresholds (80-90% issue identification)
- Domain boundaries (route outside expertise to specialists)
- User intent satisfaction (focused on actual request)

## Development Guidelines

### When to Use Which Agent
- **Unknown issue** → Hidden Door (reconnaissance first)
- **"Error in console"** → Nine Demons
- **"Button not working"** → Jewel Tiger
- **"Slow loading"** → Cloud Hiding or Jewel Heart
- **"Users can't access"** → High Tree or Righteous
- **"Testing limits"** → Tiger Knockdown

### Agent Testing
Each agent should be tested with:
1. **Specialization test** - handles their domain correctly
2. **Boundary test** - defers appropriately outside domain
3. **Recommendation test** - suggests correct specialists
4. **Tool limit test** - stays within efficiency bounds

## Project Structure
```
cdp-ninja/
├── agents/               # Nine Schools ninja agents
│   ├── cdp-ninja-hidden-door.md
│   ├── cdp-ninja-nine-demons.md
│   ├── cdp-ninja-jewel-tiger.md
│   ├── cdp-ninja-jewel-heart.md
│   ├── cdp-ninja-divine-immovable.md
│   ├── cdp-ninja-cloud-hiding.md
│   ├── cdp-ninja-high-tree.md
│   ├── cdp-ninja-tiger-knockdown.md
│   └── cdp-ninja-righteous.md
├── docs/                 # Project documentation
├── .claude/             # Development documentation
└── README.md            # Public project description
```

## Success Metrics

- **Tool efficiency**: 70%+ reduction from original 96-tool chaos
- **User satisfaction**: Clear path forward every debugging session
- **Domain coverage**: 95% of debugging scenarios handled by appropriate specialist
- **No recursion loops**: 0 incidents of agents calling other agents

## Philosophy

The Nine Schools represent the evolution from tool-spamming generalist to focused debugging masters. Each school embodies authentic ninja traditions while delivering modern debugging expertise:

*"From one thing, know ten thousand things"* - Miyamoto Musashi

Each debugging session teaches the path to the next. The Nine Schools provide the map, but the user walks the way.

---

**The ninja renaissance is complete.** 🥷⚔️💎🔷🛡️☁️🌳🐅🔒