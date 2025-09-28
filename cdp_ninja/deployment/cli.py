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
    """Output complete API documentation from USAGE.md"""
    try:
        usage_path = Path(__file__).parent.parent.parent / "USAGE.md"
        if not usage_path.exists():
            print("❌ USAGE.md not found at expected location")
            return

        print("🥷 CDP Ninja API Documentation")
        print("=" * 50)
        print()

        with open(usage_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse and format the markdown content for CLI display
        lines = content.split('\n')
        in_code_block = False

        for line in lines:
            # Handle code blocks
            if line.startswith('```'):
                in_code_block = not in_code_block
                print("─" * 40)
                continue

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

    print("🐚 Enabling shell execution endpoint...")
    print("⚠️  Warning: Remote shell execution will be enabled")
    print("📡 Shell endpoint: POST /system/execute")

    # Set global flag to enable shell routes
    SHELL_ENABLED = True

    print("✅ Shell execution enabled - starting server")
    return 'start_server_with_shell'  # Signal to start server with shell enabled


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