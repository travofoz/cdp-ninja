"""
CDP Ninja CLI Command Handlers
Handles deployment and operational CLI commands
"""

from pathlib import Path
import platform
from .ssh_utils import setup_ssh_tunnel, start_claude_interface, show_tunnel_instructions, show_invoke_claude_instructions
from .verification import verify_remote_installations, verify_local_installations
from .installers import install_deps_local, install_deps_remote

# Global flag for shell execution
SHELL_ENABLED = False


def handle_usage():
    """Output API documentation overview and domain guide"""
    try:
        usage_path = Path(__file__).parent.parent.parent / "docs" / "usage" / "readme.md"
        if not usage_path.exists():
            print("❌ API documentation not found at expected location")
            print(f"   Expected: {usage_path}")
            return

        print("🥷 CDP Ninja API Documentation")
        print("=" * 50)
        print()

        with open(usage_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse and format the markdown content for CLI display
        lines = content.split('\n')
        in_code_block = False
        in_table = False

        for line in lines:
            # Handle code blocks
            if line.startswith('```'):
                in_code_block = not in_code_block
                print("─" * 40)
                continue

            # Handle tables
            if '|' in line and not in_code_block:
                in_table = True
                # Format table rows
                if line.startswith('|'):
                    formatted_line = line.replace('|', '│').strip()
                    print(f"   {formatted_line}")
                continue
            elif in_table and not '|' in line:
                in_table = False
                print()

            # Format headers
            if line.startswith('# '):
                print(f"\n🔥 {line[2:]}")
                print("=" * len(line))
            elif line.startswith('## '):
                print(f"\n💠 {line[3:]}")
                print("─" * len(line))
            elif line.startswith('### '):
                print(f"\n⚡ {line[4:]}")
            # Format code blocks with indentation
            elif in_code_block:
                print(f"   {line}")
            # Format list items
            elif line.startswith('- '):
                print(f"  • {line[2:]}")
            # Regular lines
            elif line.strip():
                print(line)
            else:
                print()

        print("\n📁 Full documentation files:")
        docs_dir = Path(__file__).parent.parent.parent / "docs" / "usage"
        if docs_dir.exists():
            for doc_file in sorted(docs_dir.glob("*.md")):
                if doc_file.name != "readme.md":
                    print(f"   • {doc_file.name}")

    except Exception as e:
        print(f"❌ Error reading API documentation: {e}")
        return 1

    return 0


def handle_install_agents(target_path, instruct_only=False):
    """Install agents locally or remotely with conflict resolution"""
    if instruct_only:
        show_install_agents_instructions(target_path)
        return True

    print(f"🥷 Installing CDP Ninja agents to: {target_path}")

    try:
        agents_dir = Path(__file__).parent.parent.parent / "agents"
        if not agents_dir.exists():
            print(f"❌ Agents directory not found: {agents_dir}")
            print("💡 Expected location: /agents (relative to cdp_ninja package)")
            show_install_agents_instructions(target_path)
            return False

        agent_files = list(agents_dir.glob("*.md"))
        if not agent_files:
            print(f"❌ No agent files found in: {agents_dir}")
            show_install_agents_instructions(target_path)
            return False

        print(f"📁 Found {len(agent_files)} agent files")

        # Parse target (local vs remote)
        if ':' in target_path:
            # Remote installation via SCP
            print("🌐 Remote installation detected")
            host, remote_path = target_path.split(':', 1)
            success = install_agents_remote(host, remote_path, agents_dir)
        else:
            # Local installation
            print("💻 Local installation detected")
            success = install_agents_local(target_path, agents_dir)

        if success:
            print("\n🎉 Agent installation completed successfully!")
            print("💡 Next steps:")
            print("   1. Verify agents are accessible in your Claude Code environment")
            print("   2. Test with: Task(subagent_type='cdp-ninja-hidden-door', ...)")
        else:
            print("\n❌ Agent installation failed or no files were installed")
            show_install_agents_instructions(target_path)

        return success

    except Exception as e:
        print(f"❌ Agent installation failed: {e}")
        show_install_agents_instructions(target_path)
        return False


def handle_install_deps(target_host, web_backend, instruct_only=False):
    """Install dependencies (Claude CLI, tmux, gotty/ttyd) on target system"""
    if instruct_only:
        show_install_deps_instructions(target_host, web_backend)
        return True

    print(f"🛠️  Installing dependencies on: {target_host}")
    print(f"📺 Web backend: {web_backend}")

    if target_host == 'localhost':
        print("💻 Installing locally...")
        success = install_deps_local(web_backend)
    else:
        print(f"🌐 Installing remotely on {target_host}...")
        success = install_deps_remote(target_host, web_backend)

    if not success:
        print("\n💡 Installation failed - showing manual instructions:")
        show_install_deps_instructions(target_host, web_backend)

    return success


def handle_tunnel(target_host, instruct_only=False):
    """Setup reverse SSH tunnel for remote access to local CDP Ninja"""
    if instruct_only:
        show_tunnel_instructions(target_host)
        return True

    print(f"🚇 Setting up reverse SSH tunnel to: {target_host}")
    print("   This will expose your local CDP Ninja on the remote server")

    # Only tunnel the bridge port - Chrome DevTools stays local
    bridge_port = 8888

    success = setup_ssh_tunnel(target_host, bridge_port)

    if not success:
        print("\n💡 Tunnel setup failed - showing manual instructions:")
        show_tunnel_instructions(target_host, bridge_port)

    return success


def handle_invoke_claude(target_host, web_backend, instruct_only=False):
    """Start Claude interface in tmux with web terminal"""
    if instruct_only:
        show_invoke_claude_instructions(target_host, web_backend)
        return True

    print(f"🤖 Starting Claude interface on: {target_host}")
    print(f"📺 Web backend: {web_backend}")

    success = start_claude_interface(target_host, web_backend)

    if not success:
        print("\n💡 Claude setup failed - showing manual instructions:")
        show_invoke_claude_instructions(target_host, web_backend)

    return success


def handle_shell():
    """Enable shell execution capabilities on the bridge"""
    global SHELL_ENABLED
    from cdp_ninja.config import config

    print("🐚 Enabling shell execution endpoint...")
    print("⚠️  Warning: Remote shell execution will be enabled")
    print("📡 Shell endpoint: POST /system/execute")

    # Set global flag to enable shell routes
    SHELL_ENABLED = True

    # Directly enable shell execution in config
    config.enable_shell_execution = True

    print("✅ Shell execution enabled - starting server")
    return 'start_server_with_shell'  # Signal to start server with shell enabled


def handle_kill_tunnels():
    """Kill all active SSH tunnels for CDP Ninja (both local and remote sides)"""
    import subprocess
    import platform
    import re

    print("🔪 Killing all active SSH tunnels...")

    killed_count = 0
    remote_hosts = set()  # Track which hosts we need to clean up

    try:
        if platform.system() == "Windows":
            # Find SSH tunnel processes on Windows using PowerShell (more reliable than wmic)
            powershell_cmd = [
                'powershell', '-Command',
                'Get-WmiObject Win32_Process | Where-Object {$_.Name -eq "ssh.exe" -and $_.CommandLine -like "*-R*" -and $_.CommandLine -like "*127.0.0.1*"} | Select-Object ProcessId,CommandLine | ConvertTo-Json'
            ]

            result = subprocess.run(powershell_cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    # Parse JSON output from PowerShell
                    processes = json.loads(result.stdout.strip())

                    # Handle single process (not in array) vs multiple processes (in array)
                    if isinstance(processes, dict):
                        processes = [processes]

                    tunnel_pids = []
                    for process in processes:
                        pid = str(process.get('ProcessId', ''))
                        command = process.get('CommandLine', '')
                        if pid.isdigit():
                            tunnel_pids.append(pid)
                            print(f"🎯 Found CDP tunnel: PID {pid}")
                            print(f"   Command: {command[:80]}...")

                            # Extract remote host from command for cleanup
                            # Pattern: ssh [flags] user@host or ssh [flags] host (hostname is always last)
                            parts = command.split()
                            if len(parts) >= 2:
                                # Hostname is typically the last argument
                                hostname = parts[-1]
                                # Keep user@host format for proper authentication
                                remote_hosts.add(hostname)

                    for pid in tunnel_pids:
                        try:
                            kill_result = subprocess.run(
                                ['taskkill', '/F', '/PID', pid],
                                capture_output=True, text=True, timeout=5
                            )
                            if kill_result.returncode == 0:
                                print(f"✅ Killed SSH tunnel (PID {pid})")
                                killed_count += 1
                            else:
                                print(f"❌ Failed to kill PID {pid}: {kill_result.stderr}")
                        except Exception as e:
                            print(f"❌ Error killing PID {pid}: {e}")

                    if not tunnel_pids:
                        print("💡 No CDP Ninja SSH tunnels found")

                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing PowerShell output: {e}")
                    print("💡 No CDP Ninja SSH tunnels found")
            else:
                print("💡 No CDP Ninja SSH tunnels found")

        else:
            # Find SSH tunnel processes on Linux/Mac
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                tunnel_pids = []
                for line in result.stdout.split('\n'):
                    # Look for SSH processes with CDP Ninja reverse tunnel pattern (-R port:127.0.0.1:port)
                    if 'ssh' in line and '-R' in line and '127.0.0.1' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[1]
                            tunnel_pids.append(pid)

                            # Extract remote host from command for cleanup
                            parts = line.split()
                            # Find hostname (usually after ssh command and flags)
                            for i, part in enumerate(parts):
                                if 'ssh' in parts[i-1] if i > 0 else False:
                                    continue
                                if not part.startswith('-') and ('.' in part or '@' in part):
                                    # Keep user@host format for proper authentication
                                    remote_hosts.add(part)
                                    break

                for pid in tunnel_pids:
                    try:
                        kill_result = subprocess.run(
                            ['kill', pid],
                            capture_output=True, text=True, timeout=5
                        )
                        if kill_result.returncode == 0:
                            print(f"✅ Killed SSH tunnel (PID {pid})")
                            killed_count += 1
                        else:
                            print(f"❌ Failed to kill PID {pid}: {kill_result.stderr}")
                    except Exception as e:
                        print(f"❌ Error killing PID {pid}: {e}")

                if not tunnel_pids:
                    print("💡 No SSH tunnels found")

    except subprocess.TimeoutExpired:
        print("❌ Timeout while searching for SSH tunnels")
        return False
    except Exception as e:
        print(f"❌ Error searching for SSH tunnels: {e}")
        return False

    # Clean up remote SSH daemons that might be holding ports
    if remote_hosts:
        print(f"\n🧹 Cleaning up remote SSH daemons on {len(remote_hosts)} host(s)...")
        for host in remote_hosts:
            try:
                print(f"   🎯 Cleaning {host}...")
                # Find PIDs bound to tunnel ports and kill them
                cleanup_cmd = [
                    'ssh', host,
                    'for port in $(seq 8888 8899); do ss -tlnp | grep ":$port " | sed -n "s/.*pid=\\([0-9]*\\).*/\\1/p" | xargs -r kill 2>/dev/null || true; done'
                ]
                result = subprocess.run(cleanup_cmd, capture_output=True, text=True, timeout=15)

                if result.returncode == 0:
                    print(f"   ✅ Remote cleanup completed for {host}")
                else:
                    print(f"   ⚠️  Remote cleanup warning for {host}: {result.stderr.strip()}")

            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Remote cleanup timeout for {host}")
            except Exception as e:
                print(f"   ⚠️  Remote cleanup failed for {host}: {e}")

    if killed_count > 0:
        print(f"\n🎉 Successfully killed {killed_count} local SSH tunnel(s)")
        if remote_hosts:
            print(f"🧹 Cleaned up remote SSH daemons on {len(remote_hosts)} host(s)")
    else:
        print("\n💡 No SSH tunnels were running")

    return True


def handle_start_browser():
    """Start Chromium browser with CDP debugging enabled"""
    import subprocess
    import platform
    import os
    from pathlib import Path

    print("🌐 Starting Chromium browser with CDP debugging...")

    # Common browser executable names and paths
    browser_candidates = []

    if platform.system() == "Windows":
        # Windows browser paths
        browser_candidates = [
            # Chrome
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),

            # Edge
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",

            # Brave
            os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),

            # Chromium
            os.path.expanduser(r"~\AppData\Local\Chromium\Application\chrome.exe"),
        ]
    elif platform.system() == "Darwin":
        # macOS browser paths
        browser_candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    else:
        # Linux browser commands (check PATH)
        browser_candidates = [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "microsoft-edge",
            "brave-browser",
        ]

    # Find available browser
    browser_path = None
    browser_name = None

    for candidate in browser_candidates:
        if platform.system() == "Linux":
            # For Linux, check if command exists in PATH
            try:
                result = subprocess.run(['which', candidate], capture_output=True, timeout=5)
                if result.returncode == 0:
                    browser_path = candidate
                    browser_name = candidate
                    break
            except:
                continue
        else:
            # For Windows/macOS, check if file exists
            if os.path.exists(candidate):
                browser_path = candidate
                browser_name = Path(candidate).stem
                break

    if not browser_path:
        print("❌ No Chromium-based browser found!")
        print("💡 Supported browsers:")
        print("   • Google Chrome")
        print("   • Microsoft Edge")
        print("   • Brave Browser")
        print("   • Chromium")
        print("\n💡 Manual command:")
        print('   chrome --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="C:\\temp\\chrome-debug"')
        return False

    print(f"✅ Found browser: {browser_name}")
    print(f"   Path: {browser_path}")

    # Create temp directory for user data
    if platform.system() == "Windows":
        user_data_dir = r"C:\temp\chrome-debug"
    else:
        user_data_dir = "/tmp/chrome-debug"

    # Ensure temp directory exists
    try:
        os.makedirs(user_data_dir, exist_ok=True)
    except Exception as e:
        print(f"⚠️  Couldn't create temp directory {user_data_dir}: {e}")
        user_data_dir = None

    # Build browser command
    browser_cmd = [browser_path]
    browser_cmd.extend([
        '--remote-debugging-port=9222',
        '--remote-allow-origins=*',
    ])

    if user_data_dir:
        browser_cmd.append(f'--user-data-dir={user_data_dir}')

    # Keep it clean - just the essential CDP flags

    print(f"🚀 Launching browser...")
    print(f"   Command: {' '.join(browser_cmd)}")

    try:
        # Start browser in background
        if platform.system() == "Windows":
            # On Windows, use CREATE_NEW_PROCESS_GROUP to detach
            process = subprocess.Popen(
                browser_cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # On Unix, use nohup-like approach
            process = subprocess.Popen(
                browser_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )

        print(f"✅ Browser started successfully!")
        print(f"   • Process PID: {process.pid}")
        print(f"   • Debug Port: 9222")
        if user_data_dir:
            print(f"   • Profile: {user_data_dir}")

        print(f"\n🧪 Test CDP connection:")
        print(f"   curl http://localhost:9222/json")

        print(f"\n💡 Start CDP Ninja bridge:")
        print(f"   uv run cdp-ninja")

        return True

    except Exception as e:
        print(f"❌ Failed to start browser: {e}")
        return False


# Helper functions for agent installation
def install_agents_local(target_path, agents_dir):
    """Install agents to local path with conflict resolution"""
    import shutil

    target = Path(target_path).expanduser().resolve()

    try:
        target.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"❌ Permission denied creating directory: {target}")
        return False

    installed_count = 0
    skipped_count = 0

    for agent_file in agents_dir.glob("*.md"):
        target_file = target / agent_file.name

        if target_file.exists() and not getattr(install_agents_local, 'overwrite_all', False):
            choice = prompt_file_conflict(agent_file, target_file)
            if choice == 'skip':
                print(f"⏭️  Skipped: {agent_file.name}")
                skipped_count += 1
                continue
            elif choice == 'all':
                # Set flag to overwrite all remaining files
                install_agents_local.overwrite_all = True

        try:
            shutil.copy2(agent_file, target_file)
            print(f"✅ Installed: {agent_file.name}")
            installed_count += 1
        except Exception as e:
            print(f"❌ Failed to copy {agent_file.name}: {e}")

    print(f"\n📊 Installation Summary:")
    print(f"   • Installed: {installed_count} agents")
    if skipped_count > 0:
        print(f"   • Skipped: {skipped_count} agents (already existed)")

    return installed_count > 0


def install_agents_remote(host, remote_path, agents_dir):
    """Install agents to remote host via SCP"""
    import subprocess

    try:
        # Create remote directory
        result = subprocess.run(
            ['ssh', host, f'mkdir -p {remote_path}'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"❌ Failed to create remote directory: {result.stderr}")
            return False

        # Copy all agent files
        agent_files = list(agents_dir.glob("*.md"))
        scp_cmd = ['scp'] + [str(f) for f in agent_files] + [f'{host}:{remote_path}/']

        result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print(f"✅ Copied {len(agent_files)} agent files to {host}:{remote_path}")

            # Verify installation
            result = subprocess.run(
                ['ssh', host, f'ls -la {remote_path}/*.md'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                print("📋 Remote agents:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 9:
                            filename = parts[-1].split('/')[-1]
                            print(f"   • {filename}")
                return True
            else:
                print("⚠️  Files copied but verification failed")
                return True
        else:
            print(f"❌ SCP failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Remote installation timed out")
        return False
    except Exception as e:
        print(f"❌ Remote installation failed: {e}")
        return False


def prompt_file_conflict(source_file, target_file):
    """Prompt user for file conflict resolution"""
    print(f"\n⚠️  File conflict: {target_file.name} already exists")
    print(f"   Source: {source_file} ({source_file.stat().st_size} bytes)")
    print(f"   Target: {target_file} ({target_file.stat().st_size} bytes)")

    while True:
        choice = input("   [o]verwrite, [s]kip, overwrite [a]ll, [q]uit? ").lower().strip()
        if choice in ['o', 'overwrite']:
            return 'overwrite'
        elif choice in ['s', 'skip']:
            return 'skip'
        elif choice in ['a', 'all']:
            return 'all'
        elif choice in ['q', 'quit']:
            print("❌ Installation cancelled by user")
            raise KeyboardInterrupt("User cancelled installation")
        else:
            print("   Invalid choice. Please enter o, s, a, or q.")


def show_install_agents_instructions(target_path):
    """Show manual instructions for installing agents"""
    print("\n📖 Manual Agent Installation Instructions")
    print("=" * 50)

    agents_dir = Path(__file__).parent.parent.parent / "agents"

    if ':' in target_path:
        # Remote installation instructions
        host, remote_path = target_path.split(':', 1)
        print(f"🌐 Remote Installation to {host}:{remote_path}")
        print("\n1. Setup SSH key authentication:")
        print(f"   ssh-keygen -t ed25519")
        print(f"   ssh-copy-id {host}")
        print(f"   ssh {host}  # Test connection")

        print(f"\n2. Create remote directory:")
        print(f"   ssh {host} 'mkdir -p {remote_path}'")

        print(f"\n3. Copy agent files:")
        print(f"   scp {agents_dir}/*.md {host}:{remote_path}/")

        print(f"\n4. Verify installation:")
        print(f"   ssh {host} 'ls -la {remote_path}/'")

    else:
        # Local installation instructions
        print(f"💻 Local Installation to {target_path}")
        print(f"\n1. Create target directory:")
        print(f"   mkdir -p {target_path}")

        print(f"\n2. Copy agent files:")
        print(f"   cp {agents_dir}/*.md {target_path}/")

        print(f"\n3. Verify installation:")
        print(f"   ls -la {target_path}/")

    print(f"\n📋 Agent Files to Install:")
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            print(f"   • {agent_file.name}")
    else:
        print(f"   ❌ Agents directory not found: {agents_dir}")

    print(f"\n🧪 Testing:")
    print(f"   Task(subagent_type='cdp-ninja-hidden-door', prompt='test')")


def show_install_deps_instructions(target_host, web_backend):
    """Show manual instructions for installing dependencies"""
    print("\n📖 Manual Dependency Installation Instructions")
    print("=" * 55)

    if target_host == 'localhost':
        print("💻 Local Installation")
        print("\n1. Install Claude CLI:")
        print("   pip3 install claude-cli")
        print("   # OR")
        print("   pip install claude-cli")

        print("\n2. Install tmux:")
        if platform.system() == 'Darwin':
            print("   brew install tmux")
        else:
            print("   # Ubuntu/Debian:")
            print("   sudo apt-get update && sudo apt-get install -y tmux")
            print("   # CentOS/RHEL/Fedora:")
            print("   sudo dnf install tmux")
            print("   # OR")
            print("   sudo yum install tmux")
            print("   # Arch Linux:")
            print("   sudo pacman -S tmux")

        print(f"\n3. Install {web_backend}:")
        if web_backend == 'ttyd':
            if platform.system() == 'Darwin':
                print("   brew install ttyd")
            else:
                print("   # Ubuntu/Debian:")
                print("   sudo apt-get install -y ttyd")
                print("   # CentOS/RHEL/Fedora:")
                print("   sudo dnf install ttyd")
                print("   # Arch Linux:")
                print("   sudo pacman -S ttyd")
        else:  # gotty
            if platform.system() == 'Darwin':
                print("   brew install gotty")
            else:
                print("   # Download from GitHub:")
                print("   wget https://github.com/yudai/gotty/releases/latest/download/gotty_linux_amd64.tar.gz")
                print("   tar -xzf gotty_linux_amd64.tar.gz")
                print("   sudo mv gotty /usr/local/bin/")
                print("   sudo chmod +x /usr/local/bin/gotty")

    else:
        print(f"🌐 Remote Installation on {target_host}")
        print("\n1. Setup SSH key authentication:")
        print("   ssh-keygen -t ed25519")
        print(f"   ssh-copy-id {target_host}")
        print(f"   ssh {target_host}  # Test connection")

        print("\n2. Install Claude CLI on remote:")
        print(f"   ssh {target_host} 'pip3 install claude-cli'")

        print("\n3. Install tmux on remote:")
        print(f"   # Ubuntu/Debian:")
        print(f"   ssh {target_host} 'sudo apt-get update && sudo apt-get install -y tmux'")
        print(f"   # CentOS/RHEL/Fedora:")
        print(f"   ssh {target_host} 'sudo dnf install -y tmux'")

        print(f"\n4. Install {web_backend} on remote:")
        if web_backend == 'ttyd':
            print(f"   ssh {target_host} 'sudo apt-get install -y ttyd'")
        else:  # gotty
            print(f"   ssh {target_host} 'cd /tmp && \\")
            print(f"   wget https://github.com/yudai/gotty/releases/latest/download/gotty_linux_amd64.tar.gz && \\")
            print(f"   tar -xzf gotty_linux_amd64.tar.gz && \\")
            print(f"   sudo mv gotty /usr/local/bin/ && \\")
            print(f"   sudo chmod +x /usr/local/bin/gotty'")

    print("\n🧪 Verification:")
    print("   claude --version")
    print("   tmux -V")
    print(f"   {web_backend} --version")


def configure_domain_manager(args):
    """Configure domain manager based on CLI arguments"""
    import sys
    import time
    from ..core.domain_manager import DomainRiskLevel, CDPDomain, initialize_domain_manager

    risk_level_map = {
        'safe': DomainRiskLevel.SAFE,
        'low': DomainRiskLevel.LOW,
        'medium': DomainRiskLevel.MEDIUM,
        'high': DomainRiskLevel.HIGH,
        'very_high': DomainRiskLevel.VERY_HIGH
    }

    if args.max_risk_level not in risk_level_map:
        print(f"❌ Invalid risk level: {args.max_risk_level}")
        sys.exit(1)

    max_risk = risk_level_map[args.max_risk_level]
    domain_manager = initialize_domain_manager(max_risk)

    # Handle domain loading strategy
    if args.eager_load_domains and args.lazy_load_domains:
        print("⚠️ Warning: Both --eager-load-domains and --lazy-load-domains specified")
        print("Using eager loading")

    if args.eager_load_domains:
        enabled_count = domain_manager.enable_all_allowed_domains()
        print(f"✅ Eager loading enabled {enabled_count} domains")

    if args.disable_auto_unload:
        domain_manager.set_auto_unload_enabled(False)
        print("🔒 Auto-unload disabled")

    if args.domain_timeout:
        domain_manager.set_default_timeout(args.domain_timeout)
        print(f"⏱️ Domain timeout set to {args.domain_timeout} minutes")

    if args.enable_domains:
        domain_names = [name.strip().upper() for name in args.enable_domains.split(',')]
        for domain_name in domain_names:
            try:
                domain = CDPDomain[domain_name]
                if domain_manager.ensure_domain(domain, "cli_explicit"):
                    print(f"✅ Enabled domain: {domain_name}")
                else:
                    print(f"❌ Failed to enable domain: {domain_name}")
            except KeyError:
                print(f"❌ Unknown domain: {domain_name}")

    return domain_manager


def handle_list_domains(args):
    """List all available domains with risk levels"""
    from ..core.domain_manager import CDPDomain, DomainManager, DomainRiskLevel

    print("🥷 Available CDP Domains:")
    print("=" * 50)

    for domain in CDPDomain:
        config = DomainManager.DOMAIN_CONFIGS.get(domain)
        if config:
            risk_color = {
                DomainRiskLevel.SAFE: "🟢",
                DomainRiskLevel.LOW: "🟡",
                DomainRiskLevel.MEDIUM: "🟠",
                DomainRiskLevel.HIGH: "🔴",
                DomainRiskLevel.VERY_HIGH: "🚨"
            }.get(config.risk_level, "❓")

            auto_unload = f" (auto-unload: {config.auto_unload_timeout}m)" if config.auto_unload_timeout else ""
            enable_req = "" if config.requires_enable else " (no enable required)"

            print(f"{risk_color} {domain.value:<15} - {config.risk_level.value}{auto_unload}{enable_req}")


def handle_domain_status(args):
    """Show current domain status"""
    import time
    from ..core.domain_manager import get_domain_manager

    domain_manager = get_domain_manager()
    status = domain_manager.get_domain_status()

    print("🥷 Current Domain Status:")
    print("=" * 50)
    print(f"Max Risk Level: {status['max_risk_level']}")
    print(f"Enabled Domains: {len(status['enabled_domains'])}")

    if status['enabled_domains']:
        print("\nEnabled:")
        for domain in status['enabled_domains']:
            details = status['domain_details'][domain]
            last_used = details['last_used']
            age = f"{(time.time() - last_used) / 60:.1f}m ago" if last_used > 0 else "never"
            enabled_by = ", ".join(details['enabled_by']) if details['enabled_by'] else "unknown"
            print(f"  ✅ {domain} - used {age} by {enabled_by}")

    disabled_count = len([d for d in status['domain_details'] if not status['domain_details'][d]['enabled']])
    if disabled_count > 0:
        print(f"\nDisabled: {disabled_count} domains")


def handle_health_check(args):
    """Perform health check on CDP bridge"""
    from ..core.cdp_pool import get_global_pool
    from ..core.domain_manager import get_domain_manager

    print("🏥 CDP Ninja Health Check")
    print("=" * 30)

    try:
        # Check CDP client connection
        global_pool = get_global_pool()
        if global_pool:
            print("✅ Global CDP pool: Available")

            # Try to get a connection
            conn = global_pool.acquire()
            if conn:
                print("✅ CDP connection: Active")
                global_pool.release(conn)
            else:
                print("❌ CDP connection: Failed to acquire")
        else:
            print("❌ Global CDP pool: Not initialized")

        # Check domain manager
        domain_manager = get_domain_manager()
        status = domain_manager.get_domain_status()
        enabled_count = len(status['enabled_domains'])
        print(f"✅ Domain manager: {enabled_count} domains enabled")

        print("\n🎯 Overall Status: Healthy")

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

    return True