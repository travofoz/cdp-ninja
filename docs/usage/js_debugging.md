# JavaScript Debugging API

*Auto-generated from js_debugging.py JSDoc comments*

## POST /cdp/js/advanced_debugging

**Function:** `advanced_javascript_debugging()`

Advanced JavaScript debugging with stack trace analysis and error archaeology

**Parameters:**
- `expression ` *(string)*: JavaScript code to debug
- `stack_trace` *(boolean)* *(optional)*: Include stack trace analysis
- `scope_analysis` *(boolean)* *(optional)*: Analyze variable scopes
- `error_context` *(boolean)* *(optional)*: Include error context and suggestions
- `breakpoints` *(object)* *(optional)*: Conditional breakpoints to set

**Returns:** {object} Advanced debugging analysis

**Examples:**
```javascript
// Basic debugging analysis
POST {"expression": "console.log('debug test')"}
// Full debugging with error analysis
POST {
"expression": "throw new Error('test error')",
"stack_trace": true,
"scope_analysis": true,
"error_context": true
}
// Debug with breakpoint context
POST {
"expression": "function test() { var x = 1; return x + undefined; }; test();",
"stack_trace": true,
"scope_analysis": true
}
```

---

## POST /cdp/js/async_analysis

**Function:** `analyze_async_operations()`

Analyze asynchronous JavaScript operations and promise states

**Parameters:**
- `expression` *(string)* *(optional)*: Async expression to analyze
- `promise_tracking` *(boolean)* *(optional)*: Track promise states
- `callback_analysis` *(boolean)* *(optional)*: Analyze callback patterns
- `timeout` *(number)* *(optional)*: Analysis timeout in milliseconds
- `performance_timing` *(boolean)* *(optional)*: Include performance metrics

**Returns:** {object} Async operation analysis

**Examples:**
```javascript
// Analyze async expression
POST {
"expression": "fetch('/api/data').then(r => r.json())",
"promise_tracking": true,
"performance_timing": true
}
// Analyze overall async state
POST {
"promise_tracking": true,
"callback_analysis": true,
"timeout": 5000
}
// Performance-focused async analysis
POST {
"expression": "setTimeout(() => console.log('delayed'), 1000)",
"performance_timing": true
}
```

---

