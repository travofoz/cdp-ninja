"""
CDP Ninja Verification
Verifies remote installations and tool availability
"""

import subprocess


def verify_remote_installations(target_host, web_backend):
    """Verify all dependencies are working on remote host (binary pass/fail)"""
    print("🔍 Verifying remote installations...")

    # Just check if tools exist in PATH - don't worry about version flags
    tools = ['claude', 'tmux', web_backend]

    working_tools = []
    failed_tools = []

    for tool in tools:
        try:
            # Source shell environment to find tools in PATH (like nvm-installed claude)
            cmd = f'source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null || true; which {tool}'
            result = subprocess.run(
                ['ssh', target_host, cmd],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"✅ {tool} verification passed on remote")
                working_tools.append(tool)
            else:
                print(f"❌ {tool} verification failed on remote")
                failed_tools.append(tool)
        except Exception:
            print(f"❌ {tool} verification failed on remote")
            failed_tools.append(tool)

    if failed_tools:
        print(f"\n⚠️  Partially successful - {', '.join(working_tools)} installed; failed: {', '.join(failed_tools)}")
        return False
    else:
        return True


def verify_local_installations(web_backend):
    """Verify all dependencies are working on local host"""
    import shutil
    print("🔍 Verifying local installations...")

    tools = ['claude', 'tmux', web_backend]
    working_tools = []
    failed_tools = []

    for tool in tools:
        if shutil.which(tool):
            print(f"✅ {tool} verification passed locally")
            working_tools.append(tool)
        else:
            print(f"❌ {tool} verification failed locally")
            failed_tools.append(tool)

    if failed_tools:
        print(f"\n⚠️  Partially successful - {', '.join(working_tools)} installed; failed: {', '.join(failed_tools)}")
        return False
    else:
        return True