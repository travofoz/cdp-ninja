"""
CDP Ninja Installers
Handles installation of dependencies locally and remotely
"""

import subprocess
import platform as plt
from .platforms import detect_local_platform, detect_remote_platform, check_existing_dependencies
from .ssh_utils import verify_ssh_access_remote, check_remote_dependencies
from .verification import verify_remote_installations, verify_local_installations


def install_deps_local(web_backend):
    """Install dependencies locally"""
    print("🔍 Detecting local platform...")
    platform_info = detect_local_platform()
    if not platform_info:
        return False

    print(f"🖥️  Platform: {platform_info['os']} ({platform_info['package_manager']})")

    # Check existing dependencies
    existing_deps = check_existing_dependencies()
    print(f"📊 Found {len(existing_deps)} existing dependencies")

    success = True

    # Install Claude CLI
    if 'claude' not in existing_deps:
        success &= install_claude_cli_local(platform_info)
    else:
        print("✅ Claude CLI already installed")

    # Install tmux
    if 'tmux' not in existing_deps:
        success &= install_tmux_local(platform_info)
    else:
        print("✅ tmux already installed")

    # Install uv
    if 'uv' not in existing_deps:
        success &= install_uv_local(platform_info)
    else:
        print("✅ uv already installed")

    # Install web backend
    if web_backend not in existing_deps:
        success &= install_web_backend_local(web_backend, platform_info)
    else:
        print(f"✅ {web_backend} already installed")

    if success:
        success &= verify_local_installations(web_backend)

    return success


def install_deps_remote(target_host, web_backend):
    """Install dependencies on remote host (SSH key authentication required)"""
    print(f"🔑 Using SSH key authentication (passwords not supported)")
    print(f"🖥️  Target host: {target_host}")

    # Test SSH connection first
    if not verify_ssh_access_remote(target_host):
        return False

    # Detect remote platform
    platform_info = detect_remote_platform(target_host)
    if not platform_info:
        return False

    print(f"🖥️  Remote platform: {platform_info['os']} ({platform_info['package_manager']})")

    # Check existing dependencies on remote
    existing_deps = check_remote_dependencies(target_host)
    print(f"📊 Found {len(existing_deps)} existing dependencies on remote")

    success = True

    # Install Claude CLI
    if 'claude' not in existing_deps:
        success &= install_claude_cli_remote(target_host, platform_info)
    else:
        print("✅ Claude CLI already installed on remote")

    # Install tmux
    if 'tmux' not in existing_deps:
        success &= install_tmux_remote(target_host, platform_info)
    else:
        print("✅ tmux already installed on remote")

    # Install uv (modern Python package manager)
    if 'uv' not in existing_deps:
        success &= install_uv_remote(target_host)
    else:
        print("✅ uv already installed on remote")

    # Install web backend
    if web_backend not in existing_deps:
        success &= install_web_backend_remote(target_host, web_backend, platform_info)
    else:
        print(f"✅ {web_backend} already installed on remote")

    if success:
        success &= verify_remote_installations(target_host, web_backend)

    if success:
        print(f"\\n🎉 All dependencies installed successfully on {target_host}!")
        print("💡 Next steps:")
        print(f"   1. Test remote access: ssh {target_host}")
        print("   2. Test Claude CLI: ssh {target_host} 'claude --version'")
        print(f"   3. Test {web_backend}: ssh {target_host} '{web_backend} --version'")
    else:
        print(f"\\n❌ Some dependencies failed to install on {target_host}")
        print("💡 Check error messages above for manual installation guidance")

    return success


# Claude CLI Installers
def install_claude_cli_local(platform_info):
    """Install Claude CLI locally"""
    print("📦 Installing Claude CLI...")

    commands = [
        'pip install claude-cli',
        'pip3 install claude-cli'
    ]

    for cmd in commands:
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print("✅ Claude CLI installed successfully")
                return True
            else:
                print(f"❌ {cmd} failed: {result.stderr}")
        except Exception as e:
            print(f"❌ {cmd} failed: {e}")

    print("💡 Manual installation: pip install claude-cli")
    return False


def install_claude_cli_remote(target_host, platform_info):
    """Install Claude CLI on remote host"""
    print("📦 Installing Claude CLI on remote...")

    commands = [
        'pip install claude-cli',
        'pip3 install claude-cli'
    ]

    for cmd in commands:
        try:
            result = subprocess.run(
                ['ssh', target_host, cmd],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("✅ Claude CLI installed on remote")
                return True
            else:
                print(f"❌ {cmd} failed: {result.stderr}")
        except Exception as e:
            print(f"❌ {cmd} failed: {e}")

    print(f"💡 Manual installation on remote:")
    print(f"   ssh {target_host} 'pip3 install --user claude-cli'")
    return False


# tmux Installers
def install_tmux_local(platform_info):
    """Install tmux locally"""
    print("📦 Installing tmux...")

    try:
        if platform_info['package_manager'] == 'brew':
            result = subprocess.run(['brew', 'install', 'tmux'],
                                  capture_output=True, text=True, timeout=300)
        elif platform_info['package_manager'] == 'apt-get':
            result = subprocess.run(['sudo', 'apt-get', 'update'],
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                result = subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tmux'],
                                      capture_output=True, text=True, timeout=300)
        elif platform_info['package_manager'] in ['dnf', 'yum']:
            result = subprocess.run(['sudo', platform_info['package_manager'], 'install', '-y', 'tmux'],
                                  capture_output=True, text=True, timeout=300)
        elif platform_info['package_manager'] == 'pacman':
            result = subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'tmux'],
                                  capture_output=True, text=True, timeout=300)
        else:
            print(f"❌ Unsupported package manager for tmux: {platform_info['package_manager']}")
            return False

        if result.returncode == 0:
            print("✅ tmux installed successfully")
            return True
        else:
            print(f"❌ tmux installation failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ tmux installation failed: {e}")
        return False


def install_tmux_remote(target_host, platform_info):
    """Install tmux on remote host"""
    print("📦 Installing tmux on remote...")

    try:
        if platform_info['package_manager'] == 'apt-get':
            cmd = 'sudo apt-get update && sudo apt-get install -y tmux'
        elif platform_info['package_manager'] in ['dnf', 'yum']:
            cmd = f"sudo {platform_info['package_manager']} install -y tmux"
        elif platform_info['package_manager'] == 'pacman':
            cmd = 'sudo pacman -S --noconfirm tmux'
        else:
            print(f"❌ Unsupported package manager for tmux: {platform_info['package_manager']}")
            return False

        result = subprocess.run(
            ['ssh', target_host, cmd],
            capture_output=True, text=True, timeout=300
        )

        if result.returncode == 0:
            print("✅ tmux installed on remote")
            return True
        else:
            print(f"❌ tmux installation failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ tmux installation failed: {e}")
        return False


# uv Installers
def install_uv_local(platform_info):
    """Install uv (fast Python package manager) locally"""
    print("🦀 Installing uv...")

    try:
        # Install uv using the official installer
        cmd = 'curl -LsSf https://astral.sh/uv/install.sh | sh'
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True, timeout=120
        )

        if result.returncode == 0:
            print("✅ uv installed successfully")
            return True
        else:
            print(f"❌ uv installation failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ uv installation failed: {e}")
        return False


def install_uv_remote(target_host):
    """Install uv (fast Python package manager) on remote host"""
    print("🦀 Installing uv on remote...")

    try:
        # Install uv using the official installer
        cmd = 'curl -LsSf https://astral.sh/uv/install.sh | sh'
        result = subprocess.run(
            ['ssh', target_host, cmd],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode == 0:
            print("✅ uv installed successfully")
            # Source the shell to make uv available
            source_cmd = 'source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null || true'
            subprocess.run(['ssh', target_host, source_cmd], timeout=10)
            return True
        else:
            print(f"❌ uv installation failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ uv installation failed: {e}")
        return False


# Web Backend Installers
def install_web_backend_local(web_backend, platform_info):
    """Install web backend locally with proper platform support"""
    print(f"📺 Installing {web_backend}...")

    if web_backend == 'gotty':
        return install_gotty_local(platform_info)
    elif web_backend == 'ttyd':
        return install_ttyd_local(platform_info)
    else:
        print(f"❌ Unsupported web backend: {web_backend}")
        return False


def install_web_backend_remote(target_host, web_backend, platform_info):
    """Install web backend on remote host using uv > pipx > system packages"""
    print(f"📺 Installing {web_backend} on remote...")

    # Strategy: Try uv first, then pipx, then system packages
    strategies = [
        ('uv', f'source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null || true; uv tool install {web_backend}'),
        ('pipx', f'pipx install {web_backend}'),
        ('pip', f'pip install --break-system-packages {web_backend}'),
    ]

    # Add system package fallback for ttyd only (gotty isn't in repos)
    if web_backend == 'ttyd':
        if platform_info['package_manager'] == 'apt-get':
            strategies.append(('apt', 'sudo apt-get update && sudo apt-get install -y ttyd'))
        elif platform_info['package_manager'] in ['dnf', 'yum']:
            strategies.append(('yum/dnf', f"sudo {platform_info['package_manager']} install -y ttyd"))

    for strategy_name, cmd in strategies:
        try:
            print(f"🔧 Trying {strategy_name}...")
            result = subprocess.run(
                ['ssh', target_host, cmd],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                print(f"✅ {web_backend} installed via {strategy_name}")
                return True
            else:
                print(f"❌ {strategy_name} failed: {result.stderr.strip()[:100]}")

        except subprocess.TimeoutExpired:
            print(f"❌ {strategy_name} timed out")
        except Exception as e:
            print(f"❌ {strategy_name} error: {e}")

    # Last resort: GitHub binary for gotty
    if web_backend == 'gotty':
        print("🔧 Trying GitHub binary download...")
        try:
            arch_result = subprocess.run(
                ['ssh', target_host, 'uname -m'],
                capture_output=True, text=True, timeout=10
            )

            if 'x86_64' in arch_result.stdout or 'amd64' in arch_result.stdout:
                arch = 'amd64'
            elif 'aarch64' in arch_result.stdout or 'arm64' in arch_result.stdout:
                arch = 'arm64'
            else:
                print(f"❌ Unsupported architecture for gotty binary")
                return False

            binary_cmd = f"""
            cd /tmp && \\
            wget -O gotty_linux_{arch}.tar.gz https://github.com/yudai/gotty/releases/latest/download/gotty_linux_{arch}.tar.gz && \\
            tar -xzf gotty_linux_{arch}.tar.gz && \\
            sudo mv gotty /usr/local/bin/ && \\
            sudo chmod +x /usr/local/bin/gotty && \\
            rm gotty_linux_{arch}.tar.gz
            """

            result = subprocess.run(
                ['ssh', target_host, binary_cmd],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                print(f"✅ {web_backend} installed via GitHub binary")
                return True

        except Exception as e:
            print(f"❌ GitHub binary installation failed: {e}")

    print(f"❌ All installation methods failed for {web_backend}")
    return False


def install_gotty_local(platform_info):
    """Install gotty locally"""
    import urllib.request
    import json
    import tarfile
    from pathlib import Path

    try:
        if platform_info['package_manager'] == 'brew':
            # Use Homebrew on macOS
            result = subprocess.run(['brew', 'install', 'gotty'],
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print("✅ gotty installed via Homebrew")
                return True
            else:
                print(f"❌ Homebrew gotty installation failed: {result.stderr}")

        # Fallback to binary installation for all platforms
        print("📦 Installing gotty from GitHub releases...")

        # Get latest release info
        response = urllib.request.urlopen("https://api.github.com/repos/yudai/gotty/releases/latest")
        release_info = json.loads(response.read())

        # Determine architecture
        machine = plt.machine().lower()
        if machine in ['x86_64', 'amd64']:
            arch = 'amd64'
        elif machine in ['aarch64', 'arm64']:
            arch = 'arm64'
        else:
            print(f"❌ Unsupported architecture: {machine}")
            return False

        # Find appropriate asset
        asset_name = f"gotty_linux_{arch}.tar.gz"
        asset_url = None

        for asset in release_info['assets']:
            if asset['name'] == asset_name:
                asset_url = asset['browser_download_url']
                break

        if not asset_url:
            print(f"❌ Could not find {asset_name} in latest release")
            return False

        # Download and extract
        temp_dir = Path("/tmp/gotty_install")
        temp_dir.mkdir(exist_ok=True)

        archive_path = temp_dir / asset_name
        urllib.request.urlretrieve(asset_url, archive_path)

        with tarfile.open(archive_path) as tar:
            tar.extractall(temp_dir)

        # Find gotty binary
        gotty_path = temp_dir / "gotty"
        if gotty_path.exists():
            # Install to /usr/local/bin
            result = subprocess.run(
                ['sudo', 'mv', str(gotty_path), '/usr/local/bin/gotty'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                result = subprocess.run(
                    ['sudo', 'chmod', '+x', '/usr/local/bin/gotty'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    print("✅ gotty installed successfully")
                    return True
                else:
                    print(f"❌ Failed to set permissions: {result.stderr}")
                    return False
            else:
                print(f"❌ Failed to install gotty: {result.stderr}")
                return False

        print("❌ gotty binary not found in archive")
        return False

    except Exception as e:
        print(f"❌ gotty installation failed: {e}")
        print("💡 Manual installation:")
        print("   Visit: https://github.com/yudai/gotty/releases")
        return False


def install_ttyd_local(platform_info):
    """Install ttyd locally"""
    try:
        if platform_info['package_manager'] == 'brew':
            result = subprocess.run(['brew', 'install', 'ttyd'],
                                  capture_output=True, text=True, timeout=300)
        elif platform_info['package_manager'] == 'apt-get':
            result = subprocess.run(['sudo', 'apt-get', 'update'],
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                result = subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ttyd'],
                                      capture_output=True, text=True, timeout=300)
        elif platform_info['package_manager'] in ['dnf', 'yum']:
            result = subprocess.run(['sudo', platform_info['package_manager'], 'install', '-y', 'ttyd'],
                                  capture_output=True, text=True, timeout=300)
        elif platform_info['package_manager'] == 'pacman':
            result = subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'ttyd'],
                                  capture_output=True, text=True, timeout=300)
        else:
            print(f"❌ Unsupported package manager for ttyd: {platform_info['package_manager']}")
            return False

        if result.returncode == 0:
            print("✅ ttyd installed successfully")
            return True
        else:
            print(f"❌ ttyd installation failed: {result.stderr}")
            print(f"💡 Manual installation: sudo {platform_info['package_manager']} install ttyd")
            return False

    except subprocess.TimeoutExpired:
        print("❌ ttyd installation timed out")
        return False
    except Exception as e:
        print(f"❌ ttyd installation failed: {e}")
        return False