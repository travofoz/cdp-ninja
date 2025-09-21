# Security Notice for CDP Ninja 🥷

## Intentional Design Philosophy

CDP Ninja is **intentionally insecure by design** for security testing and vulnerability research.

## "Vulnerabilities" That Are Actually Features

### 1. JavaScript Code Injection ✅ FEATURE
```python
# This allows arbitrary JavaScript execution - this is intentional
code = f"document.querySelector('{user_input}').click()"
```
**Purpose**: Test how browsers handle malformed selectors and JavaScript injection

### 2. No Input Sanitization ✅ FEATURE
- Raw selectors with special characters, null bytes, Unicode
- Huge payloads to test memory limits
- Malformed CSS selectors to crash browser engines
**Purpose**: Discover edge cases and browser vulnerabilities

### 3. PowerShell/Command Execution ✅ FEATURE
```python
# When ENABLE_POWERSHELL=true, this executes raw commands
subprocess.run(['powershell.exe', '-Command', user_command])
```
**Purpose**: Test system integration and command injection vulnerabilities

### 4. No Rate Limiting ✅ FEATURE
- Unlimited requests to test DoS conditions
- Infinite loops and memory bombs allowed
**Purpose**: Stress testing and resource exhaustion discovery

### 5. Any Protocol Navigation ✅ FEATURE
```python
# These are all allowed for testing
javascript:alert('test')
data:text/html,<script>alert('xss')</script>
file:///etc/passwd
```
**Purpose**: Test browser security boundaries and protocol handling

## Security Boundaries

### What CDP Ninja DOES protect:
- PowerShell execution behind `ENABLE_POWERSHELL` environment variable
- Clear documentation of dangerous capabilities
- Crash reporting to understand failure modes

### What CDP Ninja does NOT protect:
- Input validation (intentionally disabled)
- Rate limiting (intentionally disabled)
- JavaScript injection (intentionally enabled)
- Protocol restrictions (intentionally disabled)
- Memory/CPU limits (intentionally unlimited)

## Responsible Usage

### ✅ Appropriate Use Cases:
- Security research in isolated environments
- Browser vulnerability discovery
- Application security testing
- Edge case and fuzzing research
- Automated penetration testing

### ❌ Inappropriate Use Cases:
- Production environments
- Public-facing servers
- Untrusted networks
- Systems with sensitive data
- Shared development environments

## Disclosure Policy

If you discover that CDP Ninja can be used to exploit systems in ways beyond its intended scope, please:

1. **Do NOT** report "JavaScript injection" or "no input validation" - these are intentional features
2. **DO** report genuine security issues in the control mechanisms (e.g., PowerShell toggle bypass)
3. **DO** report issues with the SSH tunnel or connection security
4. **DO** report documentation improvements that could prevent misuse

## Legal Notice

CDP Ninja is provided for legitimate security testing purposes only. Users are responsible for:

- Obtaining proper authorization before testing
- Complying with all applicable laws and regulations
- Using the tool only in controlled, isolated environments
- Understanding the intentional security implications

**By using CDP Ninja, you acknowledge that it is designed to be dangerous and that you will use it responsibly.**