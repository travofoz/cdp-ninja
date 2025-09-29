# CDP Ninja E2E Test Suite

Comprehensive domain-based testing to prevent architectural regressions like the console logging issue fixed in v2.0.8.

## Overview

**Complete coverage of all 90 endpoints across 10 domains:**

1. **Console Domain** (3 endpoints) - Console logging and clearing
2. **Network Domain** (14 endpoints) - Network requests, timing, WebSockets
3. **Performance Domain** (10 endpoints) - Metrics, memory monitoring, profiling
4. **DOM Domain** (11 endpoints) - Element querying, form handling, manipulation
5. **Security Domain** (8 endpoints) - Vulnerability scanning, authentication
6. **Accessibility Domain** (8 endpoints) - WCAG compliance, screen reader testing
7. **Error Handling Domain** (8 endpoints) - Exception analysis, recovery testing
8. **Stress Testing Domain** (10 endpoints) - Memory bombs, CPU burns, chaos testing
9. **Browser Interaction Domain** (6 endpoints) - Click, type, scroll, screenshot
10. **Navigation Domain** (9 endpoints) - Page navigation, history, viewport
11. **JavaScript Debugging Domain** (2 endpoints) - Advanced debugging, async analysis
12. **System Domain** (4 endpoints) - Command execution, system monitoring

## Key Features

### Cross-Instance Consistency Testing
Every domain test includes **cross-instance consistency validation** to prevent the exact regression we fixed:
- Server CDPClient vs Pool CDPClient event consistency
- Prevents fragmented event storage issues
- Validates centralized EventManager architecture

### Predictable Error Scenarios
Tests require controlled demo site with known error patterns:
- `TypeError: Cannot read property 'x' of undefined` for console testing
- Network 404/500 errors for network testing
- Memory leaks and CPU spikes for performance testing
- Form validation errors for DOM testing

### Domain-Specific Event Validation
Each test validates that CDP events are properly captured:
- Console: `Console.messageAdded`, `Runtime.consoleAPICalled`
- Network: `Network.requestWillBeSent`, `Network.responseReceived`
- Performance: `Performance.metrics`
- DOM: `DOM.documentUpdated`, `DOM.childNodeInserted`

## Prerequisites

1. **Chrome with debugging:** `chrome --remote-debugging-port=9222`
2. **CDP Ninja bridge:** Running on `localhost:8888` (via tunnel)
3. **Demo site:** Available at `cdp-ninja-test.meatspace.lol`
4. **SSH tunnel:** `ssh -R 8888:localhost:8888 user@server`

## Usage

### Run All Tests
```bash
python tests/run_e2e_tests.py
```

### Run Specific Domain
```bash
# Test console logging regression specifically
python tests/run_e2e_tests.py --domain console

# Test network request capture
python tests/run_e2e_tests.py --domain network

# Test performance monitoring
python tests/run_e2e_tests.py --domain performance

# Test DOM interactions
python tests/run_e2e_tests.py --domain dom

# Test security scanning
python tests/run_e2e_tests.py --domain security

# Test accessibility compliance
python tests/run_e2e_tests.py --domain accessibility

# Test error handling resilience
python tests/run_e2e_tests.py --domain error_handling

# Test stress testing capabilities
python tests/run_e2e_tests.py --domain stress_testing

# Test browser automation
python tests/run_e2e_tests.py --domain browser_interaction

# Test page navigation
python tests/run_e2e_tests.py --domain navigation

# Test JavaScript debugging
python tests/run_e2e_tests.py --domain js_debugging

# Test system management
python tests/run_e2e_tests.py --domain system
```

### Verbose Output
```bash
python tests/run_e2e_tests.py --verbose
```

### Skip Prerequisites Check
```bash
python tests/run_e2e_tests.py --skip-prereq-check
```

## Test Architecture

### Base Test Class (`CDPNinjaE2ETest`)
- Common setup/teardown for all domain tests
- CDP Ninja connection verification
- Cross-instance consistency validation utilities
- Event waiting and cleanup helpers

### Domain Test Classes
Each domain has dedicated test class with:
- Domain-specific endpoint testing
- Event flow validation
- Error scenario testing
- Cross-instance consistency checks

### Demo Site Requirements
Tests define exactly what controlled scenarios the demo site needs:

**Console Domain Pages:**
- `/console-error-standard` → TypeError with undefined property
- `/console-warn-standard` → Warning message
- `/console-log-standard` → Log message
- `/console-multiple-logs` → Multiple console events

**Network Domain Pages:**
- `/network-requests-standard` → Makes `/api/test-endpoint`
- `/network-404-error` → Triggers 404 request
- `/network-slow-request` → Large/slow resource
- `/network-cors-error` → CORS violation

**And so on for all domains...**

## Regression Prevention

This test suite specifically prevents:

1. **Console Logging Regression** (v2.0.8 fix)
   - Server CDPClient has events, Pool CDPClient returns empty
   - Cross-instance consistency validation catches this

2. **Event Storage Fragmentation**
   - Events stored per-instance instead of centralized
   - Domain tests validate EventManager consistency

3. **Domain Filtering Issues**
   - Events not filtered by enabled domains
   - Each test validates proper domain isolation

4. **Endpoint Response Inconsistencies**
   - Different endpoints returning different data for same events
   - Comprehensive endpoint coverage catches mismatches

## Success Metrics

- **100% endpoint coverage** - All 90 endpoints tested
- **Zero regression tolerance** - Any architectural change breaking event flow fails tests
- **Fast feedback** - Individual domain tests complete in seconds
- **Clear diagnostics** - Failed tests point to exact endpoint/scenario

The console logging regression would have been caught immediately by `TestConsoleDomain.test_console_logs_endpoint_regression()`.

## Next Steps

1. **Implement demo site** with all required test scenarios
2. **Set up CI/CD** to run tests on every deployment
3. **Add performance benchmarks** for regression detection
4. **Extend stress testing** for production load simulation