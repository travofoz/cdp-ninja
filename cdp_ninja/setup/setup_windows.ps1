<#
.SYNOPSIS
    CDP Ninja - Windows Installation Script

.DESCRIPTION
    Complete installation script for CDP Ninja on Windows.
    Sets up Python virtual environment, installs dependencies, configures Chrome,
    and creates shortcuts for easy startup.

.PARAMETER InstallDir
    Installation directory (default: $env:USERPROFILE\cdp-ninja)

.PARAMETER CDPPort
    Chrome DevTools Protocol port (default: 9222)

.PARAMETER BridgePort
    HTTP API bridge port (default: 8888)

.PARAMETER SkipChrome
    Skip Chrome setup and configuration

.PARAMETER GlobalPython
    Use global Python instead of virtual environment (not recommended)

.PARAMETER ChromePath
    Explicit path to Chrome executable

.PARAMETER PythonPath
    Explicit path to Python executable

.PARAMETER StartUrl
    URL to open when Chrome starts with debugging

.EXAMPLE
    .\setup_windows.ps1
    Standard installation with defaults

.EXAMPLE
    .\setup_windows.ps1 -InstallDir "C:\Tools\cdp-bridge" -StartUrl "http://localhost:3000"
    Custom installation directory and startup URL

.EXAMPLE
    .\setup_windows.ps1 -SkipChrome -GlobalPython
    Minimal installation without Chrome setup
#>

param(
    [string]$InstallDir = "$env:USERPROFILE\cdp-ninja",
    [int]$CDPPort = 9222,
    [int]$BridgePort = 8888,
    [switch]$SkipChrome,
    [switch]$GlobalPython,
    [string]$ChromePath,
    [string]$PythonPath,
    [string]$StartUrl = "http://localhost:3690"
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Color output functions
function Write-Step {
    param(
        [string]$Message,
        [ValidateSet("INFO", "SUCCESS", "WARNING", "ERROR")]
        [string]$Status = "INFO"
    )

    $colors = @{
        "INFO"    = "Cyan"
        "SUCCESS" = "Green"
        "WARNING" = "Yellow"
        "ERROR"   = "Red"
    }

    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $colors[$Status]
}

function Test-AdminRights {
    """Check if running with administrator privileges"""
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-ChromeExecutable {
    """Locate Chrome executable in standard locations"""

    if ($ChromePath -and (Test-Path $ChromePath)) {
        Write-Step "Using specified Chrome path: $ChromePath" "SUCCESS"
        return $ChromePath
    }

    $searchPaths = @(
        "C:\Program Files\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
        "C:\Program Files\Chromium\Application\chrome.exe",
        "$env:LOCALAPPDATA\Chromium\Application\chrome.exe"
    )

    foreach ($path in $searchPaths) {
        if (Test-Path $path) {
            Write-Step "Found Chrome at: $path" "SUCCESS"
            return $path
        }
    }

    return $null
}

function Find-PythonExecutable {
    """Locate suitable Python executable"""

    if ($PythonPath -and (Test-Path $PythonPath)) {
        $version = & $PythonPath --version 2>&1
        if ($version -match "Python 3\.([89]|1[0-9])") {
            Write-Step "Using specified Python: $PythonPath ($version)" "SUCCESS"
            return $PythonPath
        }
    }

    $commands = @("python", "python3", "py")

    foreach ($cmd in $commands) {
        try {
            $version = & $cmd --version 2>&1
            if ($version -match "Python 3\.([89]|1[0-9])") {
                $pythonPath = (Get-Command $cmd).Source
                Write-Step "Found Python: $pythonPath ($version)" "SUCCESS"
                return $pythonPath
            }
        }
        catch {
            continue
        }
    }

    return $null
}

function Install-PythonPrompt {
    """Prompt user to install Python if not found"""

    Write-Step "Python 3.8+ is required but not found on this system" "WARNING"

    $choices = @(
        [System.Management.Automation.Host.ChoiceDescription]::new("&Download", "Open Python download page")
        [System.Management.Automation.Host.ChoiceDescription]::new("&Continue", "Continue without Python (will fail)")
        [System.Management.Automation.Host.ChoiceDescription]::new("&Exit", "Exit installation")
    )

    $result = $Host.UI.PromptForChoice(
        "Python Required",
        "Would you like to download Python from python.org?",
        $choices,
        0
    )

    switch ($result) {
        0 {
            Start-Process "https://www.python.org/downloads/"
            Write-Step "Please install Python 3.8+ and run this script again" "INFO"
            exit 0
        }
        1 {
            Write-Step "Continuing without Python - installation will fail" "WARNING"
            return $null
        }
        2 {
            Write-Step "Installation cancelled by user" "INFO"
            exit 0
        }
    }
}

function Setup-VirtualEnvironment {
    """Create and configure Python virtual environment"""
    param(
        [string]$Python,
        [string]$Dir
    )

    Write-Step "Setting up Python virtual environment..." "INFO"

    $venvPath = Join-Path $Dir "venv"

    if (-not (Test-Path $venvPath)) {
        Write-Step "Creating virtual environment..." "INFO"
        & $Python -m venv $venvPath

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment. Error code: $LASTEXITCODE"
        }

        Write-Step "Virtual environment created successfully" "SUCCESS"
    }
    else {
        Write-Step "Virtual environment already exists" "SUCCESS"
    }

    # Return virtual environment paths
    return @{
        Python    = Join-Path $venvPath "Scripts\python.exe"
        Pip       = Join-Path $venvPath "Scripts\pip.exe"
        Activate  = Join-Path $venvPath "Scripts\Activate.ps1"
        Directory = $venvPath
    }
}

function Install-PythonDependencies {
    """Install required Python packages"""
    param(
        [string]$Pip,
        [string]$Dir
    )

    Write-Step "Installing Python dependencies..." "INFO"

    # Create requirements.txt if it doesn't exist
    $requirementsFile = Join-Path $Dir "requirements.txt"
    if (-not (Test-Path $requirementsFile)) {
        $requirements = @"
flask==3.0.0
flask-cors==4.0.0
websocket-client==1.7.0
psutil==5.9.6
requests==2.31.0
python-dotenv==1.0.0
"@
        $requirements | Out-File -FilePath $requirementsFile -Encoding UTF8
        Write-Step "Created requirements.txt" "INFO"
    }

    # Upgrade pip first
    Write-Step "Upgrading pip..." "INFO"
    & $Pip install --upgrade pip --quiet

    if ($LASTEXITCODE -ne 0) {
        Write-Step "Failed to upgrade pip, continuing anyway..." "WARNING"
    }

    # Install dependencies
    Write-Step "Installing packages from requirements.txt..." "INFO"
    & $Pip install -r $requirementsFile --quiet

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install Python dependencies. Error code: $LASTEXITCODE"
    }

    Write-Step "Python dependencies installed successfully" "SUCCESS"
}

function Create-ProjectStructure {
    """Create the complete project directory structure"""
    param([string]$Dir)

    Write-Step "Creating project structure..." "INFO"

    $directories = @(
        "core",
        "api",
        "api\routes",
        "setup",
        "agent",
        "tests",
        "examples",
        "logs"
    )

    foreach ($directory in $directories) {
        $dirPath = Join-Path $Dir $directory
        if (-not (Test-Path $dirPath)) {
            New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        }
    }

    # Create __init__.py files for Python packages
    $initFiles = @("core\__init__.py", "api\__init__.py", "api\routes\__init__.py")
    foreach ($initFile in $initFiles) {
        $initPath = Join-Path $Dir $initFile
        if (-not (Test-Path $initPath)) {
            "" | Out-File -FilePath $initPath -Encoding UTF8
        }
    }

    Write-Step "Project structure created" "SUCCESS"
}

function Setup-ChromeDebug {
    """Configure Chrome for debugging"""
    param(
        [string]$ChromeExe,
        [int]$Port,
        [string]$Url
    )

    if ($SkipChrome) {
        Write-Step "Skipping Chrome setup (--SkipChrome specified)" "WARNING"
        return
    }

    Write-Step "Configuring Chrome for debugging..." "INFO"

    # Kill existing Chrome debug instances
    Write-Step "Stopping existing Chrome debug instances..." "INFO"
    Get-Process chrome -ErrorAction SilentlyContinue |
        Where-Object {
            try {
                $_.CommandLine -like "*remote-debugging*"
            }
            catch {
                $false
            }
        } |
        Stop-Process -Force -ErrorAction SilentlyContinue

    Start-Sleep -Seconds 2

    # Create clean debug profile
    $debugProfile = Join-Path $env:TEMP "cdp-debug-profile"
    if (Test-Path $debugProfile) {
        try {
            Remove-Item -Path $debugProfile -Recurse -Force -ErrorAction SilentlyContinue
        }
        catch {
            Write-Step "Could not remove old debug profile, continuing..." "WARNING"
        }
    }

    New-Item -ItemType Directory -Path $debugProfile -Force | Out-Null

    # Chrome startup arguments
    $chromeArgs = @(
        "--remote-debugging-port=$Port",
        "--user-data-dir=`"$debugProfile`"",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        $Url
    )

    # Start Chrome with debugging
    Write-Step "Starting Chrome with debugging on port $Port..." "INFO"
    Start-Process $ChromeExe -ArgumentList $chromeArgs

    # Wait for Chrome to start
    Start-Sleep -Seconds 4

    # Verify Chrome DevTools is accessible
    $maxAttempts = 10
    $connected = $false

    for ($i = 1; $i -le $maxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Port/json" -UseBasicParsing -TimeoutSec 2
            $tabs = $response.Content | ConvertFrom-Json

            if ($tabs.Count -gt 0) {
                $connected = $true
                Write-Step "Chrome DevTools verified - $($tabs.Count) tab(s) available" "SUCCESS"
                Write-Step "WebSocket URL: $($tabs[0].webSocketDebuggerUrl)" "INFO"
                break
            }
        }
        catch {
            if ($i -eq $maxAttempts) {
                Write-Step "Chrome DevTools verification failed after $maxAttempts attempts" "WARNING"
            }
            else {
                Write-Step "Attempt $i/$maxAttempts - waiting for Chrome..." "INFO"
                Start-Sleep -Seconds 2
            }
        }
    }

    if (-not $connected) {
        Write-Step "Chrome DevTools may not be accessible on port $Port" "WARNING"
        Write-Step "You may need to manually start Chrome with: $ChromeExe $($chromeArgs -join ' ')" "INFO"
    }
}

function Create-StartupScripts {
    """Create convenient startup scripts and shortcuts"""
    param(
        [string]$Dir,
        [hashtable]$Venv,
        [int]$BridgePort
    )

    Write-Step "Creating startup scripts..." "INFO"

    # Batch file for easy startup
    $batchScript = @"
@echo off
title CDP Ninja
cd /d "$Dir"
echo Starting CDP Ninja...
echo.
call venv\Scripts\activate.bat
echo Virtual environment activated
echo Starting server on http://localhost:$BridgePort
echo Press Ctrl+C to stop
echo.
python -m api.server
pause
"@

    $batchFile = Join-Path $Dir "start_bridge.bat"
    $batchScript | Out-File -FilePath $batchFile -Encoding ASCII

    # PowerShell script for advanced users
    $psScript = @"
# CDP Ninja Startup Script
Set-Location "$Dir"
& .\venv\Scripts\Activate.ps1
python -m api.server
"@

    $psFile = Join-Path $Dir "start_bridge.ps1"
    $psScript | Out-File -FilePath $psFile -Encoding UTF8

    # Create desktop shortcut
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $shortcut = `$WshShell.CreateShortcut("$env:USERPROFILE\Desktop\CDP Ninja.lnk")
        $shortcut.TargetPath = $batchFile
        $shortcut.WorkingDirectory = $Dir
        $shortcut.Description = "CDP Ninja - Browser Debugging Tool"
        $shortcut.IconLocation = "chrome.exe,0"
        $shortcut.Save()

        Write-Step "Desktop shortcut created" "SUCCESS"
    }
    catch {
        Write-Step "Could not create desktop shortcut: $_" "WARNING"
    }

    Write-Step "Startup scripts created" "SUCCESS"
}

function Create-ConfigurationFile {
    """Create default configuration file"""
    param([string]$Dir, [int]$CDPPort, [int]$BridgePort)

    $config = @{
        "cdp" = @{
            "port" = $CDPPort
            "host" = "localhost"
            "auto_reconnect" = $true
            "max_events" = 1000
        }
        "bridge" = @{
            "port" = $BridgePort
            "host" = "0.0.0.0"
            "debug" = $false
        }
        "chrome" = @{
            "profile_dir" = "$env:TEMP\cdp-debug-profile"
            "additional_args" = @()
        }
        "logging" = @{
            "level" = "INFO"
            "file" = "logs\cdp-bridge.log"
        }
    }

    $configFile = Join-Path $Dir "config.json"
    $config | ConvertTo-Json -Depth 3 | Out-File -FilePath $configFile -Encoding UTF8

    Write-Step "Configuration file created: config.json" "SUCCESS"
}

function Show-InstallationSummary {
    """Display installation completion summary"""
    param(
        [string]$Dir,
        [int]$BridgePort,
        [int]$CDPPort,
        [bool]$ChromeConfigured
    )

    # Get local IP for SSH instructions
    $localIP = try {
        (Get-NetIPAddress -AddressFamily IPv4 |
         Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } |
         Select-Object -First 1).IPAddress
    }
    catch {
        "YOUR_WINDOWS_IP"
    }

    $summary = @"

========================================
🎉 CDP Ninja Installation Complete!
========================================

Installation Directory: $Dir
Bridge URL: http://localhost:$BridgePort
Chrome DevTools: http://localhost:$CDPPort

🚀 Quick Start:
1. Double-click 'CDP Ninja' on your desktop
2. Or run: $Dir\start_bridge.bat

🔗 For Remote Access (SSH Tunnel):
ssh -L ${BridgePort}:localhost:$BridgePort username@$localIP

📚 Usage Examples:
• Health Check: curl http://localhost:$BridgePort/health
• Take Screenshot: curl http://localhost:$BridgePort/cdp/screenshot > screenshot.png
• Execute JavaScript: curl -X POST http://localhost:$BridgePort/cdp/execute -H "Content-Type: application/json" -d '{"code":"document.title"}'

🔧 Configuration:
Edit config.json to customize settings

📖 Documentation:
See README.md for complete API reference and examples

"@

    if (-not $ChromeConfigured) {
        $summary += @"
⚠️  Chrome Setup Skipped:
To enable Chrome debugging manually:
chrome.exe --remote-debugging-port=$CDPPort --user-data-dir="$env:TEMP\cdp-debug-profile" $StartUrl

"@
    }

    Write-Host $summary -ForegroundColor Green

    # Save summary to file
    $summary | Out-File -FilePath (Join-Path $Dir "INSTALLATION_COMPLETE.txt") -Encoding UTF8

    # Open installation directory
    try {
        Start-Process explorer.exe $Dir
    }
    catch {
        Write-Step "Could not open installation directory automatically" "WARNING"
    }
}

function Test-Installation {
    """Basic installation verification"""
    param(
        [hashtable]$Venv,
        [string]$Dir
    )

    Write-Step "Testing installation..." "INFO"

    # Test Python imports
    $testScript = @"
try:
    import flask
    import websocket
    import psutil
    import requests
    print("SUCCESS: All required packages available")
except ImportError as e:
    print(f"ERROR: Missing package - {e}")
    exit(1)
"@

    $testFile = Join-Path $Dir "test_install.py"
    $testScript | Out-File -FilePath $testFile -Encoding UTF8

    try {
        $output = & $Venv.Python $testFile 2>&1
        if ($output -like "*SUCCESS*") {
            Write-Step "Package imports verified" "SUCCESS"
        }
        else {
            Write-Step "Package import test failed: $output" "WARNING"
        }

        Remove-Item $testFile -ErrorAction SilentlyContinue
    }
    catch {
        Write-Step "Could not verify package imports" "WARNING"
    }
}

# ============================================================================
# MAIN INSTALLATION FLOW
# ============================================================================

try {
    Write-Host "`n" + "="*60 -ForegroundColor Cyan
    Write-Host "  CDP THIN BRIDGE - WINDOWS INSTALLATION" -ForegroundColor Cyan
    Write-Host "="*60 -ForegroundColor Cyan
    Write-Host ""

    # Check if running as administrator
    if (Test-AdminRights) {
        Write-Step "Running with administrator privileges" "WARNING"
        Write-Step "Consider running as regular user for security" "INFO"
    }

    # Step 1: Find Chrome
    Write-Step "Checking Chrome installation..." "INFO"
    $chrome = Find-ChromeExecutable
    if (-not $chrome -and -not $SkipChrome) {
        Write-Step "Chrome not found. Install Chrome first or use -SkipChrome parameter" "ERROR"
        Write-Step "Download from: https://www.google.com/chrome/" "INFO"
        exit 1
    }
    elseif ($chrome) {
        Write-Step "Chrome executable verified" "SUCCESS"
    }

    # Step 2: Find Python
    Write-Step "Checking Python installation..." "INFO"
    $python = Find-PythonExecutable
    if (-not $python) {
        $python = Install-PythonPrompt
        if (-not $python) {
            Write-Step "Cannot proceed without Python 3.8+" "ERROR"
            exit 1
        }
    }

    # Step 3: Create installation directory
    Write-Step "Creating installation directory..." "INFO"
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    Set-Location $InstallDir
    Write-Step "Installation directory: $InstallDir" "SUCCESS"

    # Step 4: Create project structure
    Create-ProjectStructure -Dir $InstallDir

    # Step 5: Setup Python environment
    if ($GlobalPython) {
        Write-Step "Using global Python installation (not recommended)" "WARNING"
        $venv = @{
            Python = $python
            Pip = "pip"
        }
    }
    else {
        $venv = Setup-VirtualEnvironment -Python $python -Dir $InstallDir
    }

    # Step 6: Install dependencies
    Install-PythonDependencies -Pip $venv.Pip -Dir $InstallDir

    # Step 7: Create configuration
    Create-ConfigurationFile -Dir $InstallDir -CDPPort $CDPPort -BridgePort $BridgePort

    # Step 8: Create startup scripts
    Create-StartupScripts -Dir $InstallDir -Venv $venv -BridgePort $BridgePort

    # Step 9: Setup Chrome debugging
    $chromeConfigured = $false
    if ($chrome) {
        Setup-ChromeDebug -ChromeExe $chrome -Port $CDPPort -Url $StartUrl
        $chromeConfigured = $true
    }

    # Step 10: Test installation
    if (-not $GlobalPython) {
        Test-Installation -Venv $venv -Dir $InstallDir
    }

    # Step 11: Show completion summary
    Show-InstallationSummary -Dir $InstallDir -BridgePort $BridgePort -CDPPort $CDPPort -ChromeConfigured $chromeConfigured

    Write-Step "Installation completed successfully! 🎉" "SUCCESS"
}
catch {
    Write-Step "Installation failed: $_" "ERROR"
    Write-Step "Error details: $($_.Exception.Message)" "ERROR"

    if ($_.Exception.InnerException) {
        Write-Step "Inner exception: $($_.Exception.InnerException.Message)" "ERROR"
    }

    Write-Step "For support, please check the documentation or file an issue" "INFO"
    exit 1
}
finally {
    # Restore original location
    if ($pwd.Path -ne $InstallDir) {
        Set-Location $pwd.Path
    }
}