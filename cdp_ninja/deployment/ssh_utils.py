"""
CDP Ninja SSH Utilities
Handles SSH operations for remote installations and setup
"""

import subprocess


def verify_ssh_access_remote(target_host):
    """Verify SSH key access to remote host"""
    try:
        result = subprocess.run(
            ['ssh', '-o', 'PasswordAuthentication=no', '-o', 'ConnectTimeout=10',
             target_host, 'echo "SSH connection test"'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print("❌ SSH key authentication failed")
            print("🔧 Setup required:")
            print(f"   1. Generate SSH key: ssh-keygen -t ed25519")
            print(f"   2. Copy to remote: ssh-copy-id {target_host}")
            print(f"   3. Test connection: ssh {target_host}")
            return False

        print("✅ SSH connection verified")
        return True

    except subprocess.TimeoutExpired:
        print(f"❌ SSH connection timeout to {target_host}")
        return False
    except FileNotFoundError:
        print("❌ SSH client not found")
        return False


def check_remote_dependencies(target_host):
    """Check which dependencies are already installed on remote host"""
    existing = []
    tools = ['claude', 'tmux', 'gotty', 'ttyd', 'uv']

    for tool in tools:
        try:
            # Source shell environment to find tools in PATH (like nvm-installed claude)
            result = subprocess.run(
                ['ssh', target_host, f'source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null || true; which {tool}'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                existing.append(tool)
        except Exception:
            pass  # Tool not found, which is expected

    return existing


def setup_ssh_tunnel(target_host, cdp_port=8888, web_port=7979, instruct_only=False):
    """Setup SSH tunnels for remote access"""
    if instruct_only:
        show_tunnel_instructions(target_host, cdp_port, web_port)
        return True

    print(f"🔧 Setting up SSH tunnels to {target_host}...")

    # Check if tunnels already exist
    try:
        result = subprocess.run(
            ['pgrep', '-f', f'ssh.*-L.*{cdp_port}.*{target_host}'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"⚠️  SSH tunnel for port {cdp_port} already exists")
            return True
    except Exception:
        pass

    try:
        # Create SSH tunnel
        tunnel_cmd = [
            'ssh', '-fN',
            '-L', f'{cdp_port}:localhost:{cdp_port}',
            '-L', f'{web_port}:localhost:{web_port}',
            target_host
        ]

        result = subprocess.run(tunnel_cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"✅ SSH tunnels established:")
            print(f"   • {cdp_port} → CDP Bridge")
            print(f"   • {web_port} → Web Terminal")
            print(f"   Local access: http://localhost:{cdp_port}")

            # Test connection
            import requests
            try:
                response = requests.get(f'http://localhost:{cdp_port}/system/status', timeout=5)
                if response.status_code == 200:
                    print("✅ Tunnel verification successful")
                else:
                    print("⚠️  Tunnel created but service not responding")
            except Exception as e:
                print(f"⚠️  Tunnel created but verification failed: {e} (service may not be running)")

            print(f"\n🔧 To kill tunnel later: pkill -f 'ssh.*-L.*{cdp_port}'")
            return True
        else:
            print(f"❌ Failed to create tunnel: {result.stderr}")
            show_tunnel_instructions(target_host, cdp_port, web_port)
            return False

    except subprocess.TimeoutExpired:
        print("❌ SSH tunnel setup timed out")
        return False
    except Exception as e:
        print(f"❌ SSH tunnel setup failed: {e}")
        return False


def show_tunnel_instructions(target_host, cdp_port=8888, web_port=7979):
    """Show manual instructions for SSH tunnel setup"""
    print("\n📖 Manual SSH Tunnel Setup Instructions")
    print("=" * 50)
    print(f"\n🔧 Create tunnels to {target_host}:")
    print(f"   ssh -fN \\")
    print(f"       -L {cdp_port}:localhost:{cdp_port} \\")
    print(f"       -L {web_port}:localhost:{web_port} \\")
    print(f"       {target_host}")
    print(f"\n🌐 Local access:")
    print(f"   • CDP Bridge: http://localhost:{cdp_port}")
    print(f"   • Web Terminal: http://localhost:{web_port}")
    print(f"\n🔧 Kill tunnels:")
    print(f"   pkill -f 'ssh.*-L.*{cdp_port}'")
    print(f"\n🔍 Check tunnels:")
    print(f"   ps aux | grep 'ssh.*-L.*{cdp_port}'")
    print(f"\n📊 Port usage:")
    print(f"   • {cdp_port} → CDP Bridge (gotty/ttyd)")
    print(f"   • {web_port} → Web Terminal (gotty/ttyd)")
    print(f"\n🧪 Test connection:")
    print(f"   curl http://localhost:{cdp_port}/system/status")


def start_claude_interface(target_host, web_backend, web_port=7979, instruct_only=False):
    """Start Claude interface in tmux with web terminal"""
    if instruct_only:
        show_invoke_claude_instructions(target_host, web_backend, web_port)
        return True

    print(f"🤖 Starting Claude interface on: {target_host}")
    print(f"📺 Web backend: {web_backend}")

    try:
        # Start tmux session with Claude
        remote_cmd = f"""
        tmux new-session -d -s claude 'claude' 2>/dev/null || tmux attach -t claude &
        """

        if web_backend == 'ttyd':
            remote_cmd += f"""
        ttyd -p {web_port} -t titleFixed='Claude CLI' -t disableLeaveAlert=true -W tmux attach -t claude &
        """
        else:  # gotty
            remote_cmd += f"""
        gotty -p {web_port} --permit-write --reconnect --reconnect-time 10 --max-connection 5 --title-format 'Claude CLI - {{.hostname}}' tmux attach -t claude &
        """

        result = subprocess.run(
            ['ssh', target_host, remote_cmd],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            print(f"✅ Claude interface started on {target_host}:{web_port}")
            print(f"🌐 Direct access: http://{target_host}:{web_port}")
            print(f"\n💡 Setup local tunnel for localhost access:")
            print(f"   ssh -fN -L {web_port}:localhost:{web_port} {target_host}")
            print(f"   Then open: http://localhost:{web_port}")
            return True
        else:
            print(f"❌ Failed to start Claude interface: {result.stderr}")
            show_invoke_claude_instructions(target_host, web_backend, web_port)
            return False

    except subprocess.TimeoutExpired:
        print("❌ Claude interface startup timed out")
        return False
    except Exception as e:
        print(f"❌ Failed to start Claude interface: {e}")
        return False


def show_invoke_claude_instructions(target_host, web_backend, web_port=7979):
    """Show manual instructions for starting Claude interface"""
    print("\n📖 Manual Claude Interface Setup Instructions")
    print("=" * 55)
    print(f"\n🤖 Start Claude interface on {target_host}:")
    print(f"   ssh {target_host}")
    print(f"   tmux new-session -d -s claude 'claude'")

    if web_backend == 'ttyd':
        print(f"   ttyd -p {web_port} \\")
        print(f"     -t titleFixed='Claude CLI' \\")
        print(f"     -t disableLeaveAlert=true \\")
        print(f"     -W tmux attach -t claude")
    else:  # gotty
        print(f"   gotty -p {web_port} \\")
        print(f"     --permit-write \\")
        print(f"     --reconnect \\")
        print(f"     --title-format 'Claude CLI - {{.hostname}}' \\")
        print(f"     tmux attach -t claude")

    print(f"\n🌐 Access methods:")
    print(f"   • Direct: http://{target_host}:{web_port}")
    print(f"   • Via tunnel: ssh -fN -L {web_port}:localhost:{web_port} {target_host}")
    print(f"   • Then visit: http://localhost:{web_port}")
    print(f"\n🔧 Management:")
    print(f"   • Kill tmux: ssh {target_host} 'tmux kill-session -t claude'")
    print(f"   • Check status: ssh {target_host} 'tmux list-sessions'")
    print(f"   • Check web terminal: ssh {target_host} 'curl localhost:{web_port}'")