#!/usr/bin/env python3
"""
CDP Ninja - Cross-Platform Installation Script
Automatically detects platform and runs appropriate installer
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def detect_platform():
    """Detect the current platform"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    elif system == 'linux':
        return 'linux'
    else:
        return 'unknown'


def get_script_dir():
    """Get the directory where this script is located"""
    return Path(__file__).parent.absolute()


def run_windows_installer(args):
    """Run the PowerShell installer on Windows"""
    script_path = get_script_dir() / "setup_windows.ps1"

    if not script_path.exists():
        print("❌ Windows installer not found:", script_path)
        return False

    print("🪟 Running Windows PowerShell installer...")

    # Convert Python args to PowerShell parameters
    ps_args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--'):
            # Convert --install-dir to -InstallDir
            param_name = arg[2:].replace('-', '').title()
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                ps_args.extend([f"-{param_name}", args[i + 1]])
                i += 2
            else:
                ps_args.append(f"-{param_name}")
                i += 1
        else:
            i += 1

    try:
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)] + ps_args
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ PowerShell installer failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ PowerShell not found. Please run setup_windows.ps1 manually.")
        return False


def run_unix_installer(args):
    """Run the bash installer on Linux/macOS"""
    script_path = get_script_dir() / "setup_unix.sh"

    if not script_path.exists():
        print("❌ Unix installer not found:", script_path)
        return False

    print("🐧 Running Unix bash installer...")

    try:
        cmd = [str(script_path)] + args
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Bash installer failed with exit code {e.returncode}")
        return False
    except PermissionError:
        print("❌ Permission denied. Make sure setup_unix.sh is executable:")
        print(f"  chmod +x {script_path}")
        return False


def show_help():
    """Show help message"""
    print("""
Debug Ninja - Cross-Platform Installer

USAGE:
    python install.py [OPTIONS]

This script automatically detects your platform and runs the appropriate installer:
  • Windows: setup_windows.ps1 (PowerShell)
  • Linux/macOS: setup_unix.sh (Bash)

COMMON OPTIONS:
    --install-dir DIR     Installation directory
    --cdp-port PORT       Chrome DevTools port (default: 9222)
    --bridge-port PORT    HTTP API bridge port (default: 8888)
    --skip-chrome         Skip Chrome setup and configuration
    --global-python       Use global Python instead of virtual environment
    --help               Show this help message

PLATFORM-SPECIFIC OPTIONS:
    Windows:
        --chrome-path PATH    Explicit path to Chrome executable
        --python-path PATH    Explicit path to Python executable
        --start-url URL       URL to open when Chrome starts

    Linux/macOS:
        --python-path PATH    Explicit path to Python executable
        --start-url URL       URL to open when Chrome starts

EXAMPLES:
    # Standard installation
    python install.py

    # Custom installation directory
    python install.py --install-dir ~/my-debug-ninja

    # Skip Chrome setup
    python install.py --skip-chrome

For platform-specific help, run the individual installers:
  • Windows: .\\setup\\setup_windows.ps1 --help
  • Linux/macOS: ./setup/setup_unix.sh --help
""")


def main():
    """Main installation function"""
    # Handle help first
    if '--help' in sys.argv or '-h' in sys.argv:
        show_help()
        return 0

    # Detect platform
    current_platform = detect_platform()

    print("🥷 Debug Ninja - Cross-Platform Installer")
    print("=" * 50)
    print(f"Detected platform: {current_platform.title()}")

    # Get command line arguments (excluding script name)
    args = sys.argv[1:]

    # Run appropriate installer
    success = False

    if current_platform == 'windows':
        success = run_windows_installer(args)
    elif current_platform in ['linux', 'macos']:
        success = run_unix_installer(args)
    else:
        print(f"❌ Unsupported platform: {current_platform}")
        print("Supported platforms: Windows, Linux, macOS")
        return 1

    if success:
        print("\n✅ Installation completed successfully!")
        print("\nNext steps:")
        print("1. Start Debug Ninja using the created shortcuts")
        print("2. Set up SSH tunnel if needed for remote access")
        print("3. Check the README.md for usage examples")
        return 0
    else:
        print("\n❌ Installation failed!")
        print("\nTroubleshooting:")
        print("1. Check that you have the required permissions")
        print("2. Ensure Python 3.8+ is installed")
        print("3. Try running the platform-specific installer directly")
        return 1


if __name__ == "__main__":
    sys.exit(main())