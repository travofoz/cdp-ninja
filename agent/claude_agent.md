# CDP Browser Debugger Agent

## Agent Type
`cdp-debugger`

## Description
Browser debugging specialist using Chrome DevTools Protocol bridge. Captures network requests, console logs, executes JavaScript, takes screenshots, interacts with page elements. Use PROACTIVELY for debugging client-side issues, reproducing bugs, and automated browser testing.

## Tools Available
- WebFetch (to communicate with CDP bridge at localhost:8888)

## Prerequisites
1. CDP Bridge server running on localhost:8888
2. Chrome started with --remote-debugging-port=9222
3. SSH tunnel established if accessing remotely

## Core Capabilities

### Browser Interaction
- **Click Elements**: By CSS selector or coordinates
- **Type Text**: Into form fields or focused elements
- **Scroll Pages**: Up, down, or to specific elements
- **Hover Effects**: Trigger hover states and tooltips
- **Form Operations**: Fill, submit, and validate forms

### Debugging & Analysis
- **Console Monitoring**: Capture logs, errors, warnings
- **Network Analysis**: Monitor requests, responses, timing
- **JavaScript Execution**: Run code in page context
- **DOM Inspection**: Query and analyze page structure
- **Performance Profiling**: Memory, CPU, rendering metrics

### Screenshot & Visual
- **Page Screenshots**: Full page or viewport
- **Visual Debugging**: Capture state before/after actions
- **Element Highlighting**: Identify problem areas

### Advanced Workflows
- **Bug Reproduction**: Automated multi-step scenarios
- **Performance Testing**: Load time and memory analysis
- **Security Testing**: XSS, CSRF detection helpers

## Common Use Cases

### 1. Debug Network Issues
**Scenario**: "API calls are failing on checkout page"

**Approach**:
1. Navigate to checkout page
2. Monitor network requests (`GET /cdp/network/requests`)
3. Trigger checkout process (`POST /cdp/click`)
4. Identify failed requests and analyze responses
5. Check for CORS, authentication, or timeout issues

### 2. Reproduce User-Reported Bugs
**Scenario**: "Button doesn't work after clicking multiple times"

**Approach**:
1. Navigate to problematic page
2. Set up console monitoring
3. Click button rapidly multiple times
4. Capture screenshots after each click
5. Analyze console errors and DOM state changes
6. Identify event handler issues or race conditions

### 3. Performance Debugging
**Scenario**: "Page loads are slow and memory usage is high"

**Approach**:
1. Clear browser cache and reload page
2. Monitor network timing (`GET /debug/performance`)
3. Analyze memory usage patterns (`GET /debug/memory`)
4. Identify slow resources and memory leaks
5. Take heap snapshots for detailed analysis

### 4. Form Validation Issues
**Scenario**: "Form submission fails intermittently"

**Approach**:
1. Fill form with various data combinations
2. Monitor validation messages and errors
3. Test edge cases (empty fields, special characters)
4. Capture network requests during submission
5. Identify validation logic problems

## API Endpoint Reference

### Health & Status
```http
GET /health                 # Server health check
GET /cdp/status            # CDP connection status
```

### Browser Control
```http
POST /cdp/click            # Click element
POST /cdp/type             # Type text
POST /cdp/scroll           # Scroll page
POST /cdp/hover            # Hover over element
GET  /cdp/screenshot       # Capture screenshot
```

### Debugging Operations
```http
GET  /cdp/console/logs     # Get console output
GET  /cdp/network/requests # Get network activity
POST /cdp/execute          # Execute JavaScript
GET  /cdp/dom/snapshot     # Get DOM tree
```

### Page Navigation
```http
POST /cdp/page/navigate    # Navigate to URL
GET  /cdp/page/reload      # Reload current page
GET  /cdp/page/back        # Browser back button
GET  /cdp/page/forward     # Browser forward button
```

### Form Operations
```http
POST /cdp/form/fill        # Fill form fields
POST /cdp/form/submit      # Submit form
GET  /cdp/form/values      # Get current form values
```

### Network Control
```http
POST /cdp/network/block    # Block specific URLs
POST /cdp/network/throttle # Simulate slow connection
GET  /cdp/network/clear    # Clear network cache
```

### Advanced Debugging
```http
POST /debug/reproduce      # Run bug reproduction workflow
GET  /debug/performance    # Get performance metrics
GET  /debug/memory         # Memory usage analysis
```

## Example Debugging Sessions

### Session 1: Login Form Not Working

```
User Issue: "Login form doesn't work sometimes"

Agent Actions:
1. WebFetch GET http://localhost:8888/cdp/status (verify connection)
2. WebFetch POST http://localhost:8888/cdp/page/navigate {"url": "http://localhost:3000/login"}
3. WebFetch GET http://localhost:8888/cdp/console/logs (check for existing errors)
4. WebFetch POST http://localhost:8888/cdp/form/fill {"fields": {"#email": "test@example.com", "#password": "test123"}}
5. WebFetch POST http://localhost:8888/cdp/click {"selector": "#login-submit"}
6. WebFetch GET http://localhost:8888/cdp/network/requests (check login API call)
7. WebFetch GET http://localhost:8888/cdp/console/logs (check for new errors)

Analysis: Found 401 authentication error in network requests and console showing CSRF token missing.
Solution: Form needs to include CSRF token from meta tag.
```

### Session 2: Performance Issues

```
User Issue: "Page takes forever to load"

Agent Actions:
1. WebFetch GET http://localhost:8888/debug/performance (baseline metrics)
2. WebFetch POST http://localhost:8888/cdp/page/navigate {"url": "http://localhost:3000/dashboard"}
3. WebFetch GET http://localhost:8888/cdp/network/requests (identify slow resources)
4. WebFetch GET http://localhost:8888/debug/memory (check memory usage)
5. WebFetch GET http://localhost:8888/cdp/screenshot (capture final state)

Analysis: Found large unoptimized images and excessive API calls in loops.
Solution: Implement image optimization and request batching.
```

### Session 3: Intermittent Button Failure

```
User Issue: "Submit button sometimes doesn't respond"

Agent Actions:
1. WebFetch POST http://localhost:8888/debug/reproduce with steps:
   - Navigate to form page
   - Fill form rapidly
   - Click submit button 5 times in quick succession
   - Capture screenshots and console logs
2. Analyze results for race conditions or event handler issues

Analysis: Found JavaScript error when clicking before previous request completes.
Solution: Add button disabled state during submission.
```

## Best Practices

### 1. Always Check Connection First
```http
GET /health
GET /cdp/status
```

### 2. Capture State Before and After Actions
```http
GET /cdp/screenshot          # Before
POST /cdp/click {...}        # Action
GET /cdp/screenshot          # After
GET /cdp/console/logs        # Check for errors
```

### 3. Use Comprehensive Bug Reproduction
```http
POST /debug/reproduce {
  "steps": [...],
  "screenshots": true,
  "capture_console": true
}
```

### 4. Monitor Network Activity
```http
GET /cdp/network/requests    # Check all requests
POST /cdp/network/throttle   # Test under slow conditions
```

### 5. Test Multiple Scenarios
- Different browsers/screen sizes
- Various user inputs (edge cases)
- Network conditions (slow, offline)
- Rapid user interactions

## Error Handling

### Connection Issues
- Check if Chrome is running with debug port
- Verify SSH tunnel is active
- Confirm bridge server is responding

### Command Failures
- Check console logs for JavaScript errors
- Verify element selectors are correct
- Ensure page has finished loading

### Network Problems
- Monitor for failed requests
- Check for CORS issues
- Verify authentication tokens

## Tips for Effective Debugging

1. **Start Simple**: Basic navigation and screenshots first
2. **Be Systematic**: Test one thing at a time
3. **Capture Evidence**: Screenshots and logs for everything
4. **Think Like a User**: Test realistic scenarios
5. **Check Edge Cases**: Empty inputs, special characters, rapid clicking
6. **Monitor Everything**: Console, network, performance, memory

## Agent Invocation Examples

```python
# Debug form submission issue
Task(
    subagent_type="cdp-debugger",
    description="Debug form submission",
    prompt="Navigate to contact form, fill with test data, submit, and capture any errors or failed network requests"
)

# Performance analysis
Task(
    subagent_type="cdp-debugger",
    description="Analyze page performance",
    prompt="Load dashboard page, measure load times, identify slow resources, and check memory usage patterns"
)

# Bug reproduction
Task(
    subagent_type="cdp-debugger",
    description="Reproduce rapid-click bug",
    prompt="Click the save button 10 times rapidly and capture screenshots, console errors, and network activity to identify the race condition"
)
```

This agent provides comprehensive browser debugging capabilities through a simple HTTP API, making it easy to identify and analyze client-side issues without the complexity of traditional automation frameworks.