"""
CDP Ninja Configuration
NO validation, NO sanitization, just raw configuration options
User controls their own destiny
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class CDPNinjaConfig:
    """
    Configuration for CDP Ninja - Raw debugging power

    @class DebugNinjaConfig
    @property {int} cdp_port - Chrome DevTools Protocol port
    @property {int} bridge_port - HTTP API bridge port
    @property {bool} enable_powershell - Allow PowerShell execution (DANGEROUS!)
    @property {int} max_events - Maximum events to queue (big buffer for fuzzing)
    @property {str} bind_host - Host to bind to (127.0.0.1 for local, 0.0.0.0 for network)
    @property {int} chrome_timeout - Timeout for Chrome commands (generous for debugging)
    @property {bool} enable_cors - Enable CORS for remote access
    @property {bool} debug_mode - Enable Flask debug mode
    """

    # Core settings
    cdp_port: int = int(os.getenv('CDP_PORT', 9222))
    bridge_port: int = int(os.getenv('BRIDGE_PORT', 8888))

    # Security toggles (user choice)
    enable_powershell: bool = os.getenv('ENABLE_POWERSHELL', 'false').lower() == 'true'

    # Performance settings
    max_events: int = int(os.getenv('MAX_EVENTS', 10000))  # Big buffer for stress testing
    chrome_timeout: int = int(os.getenv('CHROME_TIMEOUT', 30))  # Generous timeout

    # Network settings
    bind_host: str = os.getenv('BIND_HOST', '127.0.0.1')  # localhost by default
    enable_cors: bool = os.getenv('ENABLE_CORS', 'true').lower() == 'true'

    # Debug settings
    debug_mode: bool = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

    def __post_init__(self):
        """
        Print warnings for dangerous settings
        But don't prevent anything - user chose this
        """
        if self.enable_powershell:
            print("🚨 WARNING: PowerShell execution ENABLED")
            print("   This allows ARBITRARY COMMAND EXECUTION on your system!")
            print("   Set ENABLE_POWERSHELL=false to disable")
            print()

        if self.bind_host != '127.0.0.1':
            print("🌐 WARNING: Binding to non-localhost interface")
            print(f"   CDP Ninja accessible from network on {self.bind_host}:{self.bridge_port}")
            print("   Anyone on your network can control your browser!")
            print()

        print(f"🥷 CDP Ninja Config:")
        print(f"   CDP Port: {self.cdp_port}")
        print(f"   Bridge Port: {self.bridge_port}")
        print(f"   Bind Host: {self.bind_host}")
        print(f"   PowerShell: {'ENABLED' if self.enable_powershell else 'DISABLED'}")
        print(f"   Max Events: {self.max_events}")
        print()


def get_config() -> CDPNinjaConfig:
    """
    Get the current configuration

    @returns {CDPNinjaConfig} Current configuration instance
    """
    return CDPNinjaConfig()


# Global config instance
config = CDPNinjaConfig()


def print_environment_help():
    """
    Print help for environment variables
    """
    print("""
🥷 CDP Ninja Environment Variables:

Core Settings:
  CDP_PORT=9222              Chrome DevTools Protocol port
  BRIDGE_PORT=8888           HTTP API bridge port

Security Toggles:
  ENABLE_POWERSHELL=false    Allow PowerShell execution (DANGEROUS!)

Performance:
  MAX_EVENTS=10000          Event buffer size (big for stress testing)
  CHROME_TIMEOUT=30         Chrome command timeout in seconds

Network:
  BIND_HOST=127.0.0.1       Interface to bind to (0.0.0.0 for network)
  ENABLE_CORS=true          Enable CORS headers

Debug:
  DEBUG_MODE=false          Enable Flask debug mode

Examples:
  # Enable PowerShell (if you're brave)
  export ENABLE_POWERSHELL=true

  # Allow network access (if you're really brave)
  export BIND_HOST=0.0.0.0

  # Stress testing with huge buffer
  export MAX_EVENTS=50000

  # Debug mode for development
  export DEBUG_MODE=true
""")


if __name__ == "__main__":
    # Show environment help when run directly
    print_environment_help()

    # Show current config
    config = get_config()
    print("Current configuration loaded successfully!")