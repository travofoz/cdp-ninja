# System Domain API

System commands, shell execution, and process information endpoints.

## Shell Execution

### POST /system/execute
Execute raw system commands (requires `--shell` flag).

**Request:**
```json
{
  "command": "calc.exe",
  "shell": "cmd",
  "timeout": 30,
  "capture_output": true
}
```

**Response:**
```json
{
  "success": true,
  "command": "calc.exe",
  "shell": "cmd",
  "return_code": 0,
  "stdout": "",
  "stderr": "",
  "platform": "Windows",
  "timeout": 30
}
```

**Shells:**
- Windows: `powershell`, `cmd`
- Linux/macOS: `bash`, `sh`

**Examples:**
```bash
# Windows PowerShell
curl -X POST http://localhost:8888/system/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "Get-Process", "shell": "powershell"}'

# Linux/macOS bash
curl -X POST http://localhost:8888/system/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "ps aux", "shell": "bash"}'
```

## System Information

### GET /system/info
Get system platform and capabilities.

**Response:**
```json
{
  "system_info": {
    "platform": "Windows",
    "platform_release": "10",
    "machine": "AMD64",
    "shell_execution_enabled": true,
    "available_shells": ["powershell", "cmd"],
    "powershell_available": true
  }
}
```

### GET /system/processes
Get browser process information via JavaScript.

### GET /system/chrome/info
Get Chrome version and debugging information.

## Security Notes

⚠️ **WARNING**: Shell execution allows arbitrary command execution on your system. Only enable with `--shell` flag when needed for testing.