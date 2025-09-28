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


def setup_ssh_tunnel(target_host, bridge_port=8888, instruct_only=False):
    """Setup reverse SSH tunnel for remote access to local CDP Ninja

    Creates reverse tunnel (-R) so VPS can access Windows laptop's CDP bridge
    """
    if instruct_only:
        show_tunnel_instructions(target_host, bridge_port)
        return True

    print(f"🔧 Creating reverse SSH tunnel to {target_host}...")
    print(f"   Exposing localhost:{bridge_port} → {target_host}:localhost:{bridge_port}")

    try:
        # Create reverse SSH tunnel (Windows laptop → VPS)
        tunnel_cmd = [
            'ssh', '-N',  # Remove -f flag for better Windows compatibility
            '-4',  # Force IPv4 to match CDP bridge binding
            '-R', f'{bridge_port}:127.0.0.1:{bridge_port}',
            target_host
        ]

        print(f"🚇 Executing: {' '.join(tunnel_cmd)}")

        # Use Popen for background process instead of run()
        process = subprocess.Popen(
            tunnel_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give it a moment to establish or fail
        import time
        time.sleep(3)

        # Check if process is still running (good sign)
        if process.poll() is None:
            # Process is still running = tunnel likely established
            result_code = 0
            stderr_output = ""
        else:
            # Process exited = tunnel failed
            result_code = process.returncode
            _, stderr_output = process.communicate()

        if result_code == 0:
            print(f"✅ Reverse SSH tunnel established!")
            print(f"   • localhost:{bridge_port} → {target_host}:localhost:{bridge_port}")
            print(f"   • Process PID: {process.pid}")

            print(f"\n🧪 Testing tunnel from {target_host}...")
            # Test tunnel by attempting connection from remote side
            test_cmd = [
                'ssh', target_host,
                f'curl -s http://127.0.0.1:{bridge_port}/health'
            ]

            try:
                test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
                if test_result.returncode == 0 and '"status":"healthy"' in test_result.stdout:
                    print("✅ Tunnel verification successful - CDP Ninja accessible from remote!")
                    print(f"\n💡 Tunnel is running in background (PID {process.pid})")
                    print(f"💡 Kill with: taskkill /F /PID {process.pid}")
                    return True
                else:
                    print("⚠️  Tunnel created but remote access test failed")
                    print(f"   Test output: {test_result.stdout}")
                    print(f"\n💡 Tunnel is running in background (PID {process.pid})")
                    return True  # Tunnel exists, but service might not be ready
            except Exception as e:
                print(f"⚠️  Tunnel created but verification failed: {e}")
                print(f"\n💡 Tunnel is running in background (PID {process.pid})")
                return True  # Tunnel exists, verification failed

        else:
            print(f"❌ Failed to create tunnel: {stderr_output}")
            show_tunnel_instructions(target_host, bridge_port)
            return False

    except subprocess.TimeoutExpired:
        print("❌ SSH tunnel setup timed out")
        return False
    except Exception as e:
        print(f"❌ SSH tunnel setup failed: {e}")
        return False


def show_tunnel_instructions(target_host, bridge_port=8888):
    """Show manual instructions for reverse SSH tunnel setup"""
    print("\n📖 Manual Reverse SSH Tunnel Setup Instructions")
    print("=" * 50)
    print(f"\n🔧 Create reverse tunnel to {target_host}:")
    print(f"   ssh -4 -fN -R {bridge_port}:127.0.0.1:{bridge_port} {target_host}")

    print(f"\n🌐 Access from {target_host}:")
    print(f"   curl http://127.0.0.1:{bridge_port}/health")
    print(f"   curl http://127.0.0.1:{bridge_port}/cdp/status")

    print(f"\n🔧 Kill tunnel (Windows):")
    print(f"   tasklist | findstr ssh")
    print(f"   taskkill /F /PID <tunnel_pid>")

    print(f"\n🔧 Kill tunnel (Linux/Mac):")
    print(f"   pkill -f 'ssh.*-R.*{bridge_port}'")

    print(f"\n🔍 Check tunnel (Windows):")
    print(f"   Get-WmiObject Win32_Process | Where-Object {{$_.Name -eq \"ssh.exe\"}} | Select-Object ProcessId,CommandLine")

    print(f"\n🔍 Check tunnel (Linux/Mac):")
    print(f"   ps aux | grep 'ssh.*-R.*{bridge_port}'")

    print(f"\n🧪 Test from {target_host}:")
    print(f"   ssh {target_host} 'curl http://127.0.0.1:{bridge_port}/health'")

    print(f"\n📊 How it works:")
    print(f"   • Your laptop runs CDP Ninja on localhost:{bridge_port}")
    print(f"   • Reverse tunnel exposes it on {target_host}:localhost:{bridge_port}")
    print(f"   • You can access CDP Ninja from {target_host} via localhost:{bridge_port}")


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