"""
CDP Ninja Deployment Module
Handles deployment, installation, and setup operations
"""

from .cli import (
    handle_usage, handle_install_agents, handle_install_deps,
    handle_tunnel, handle_invoke_claude, handle_shell,
    SHELL_ENABLED
)

from .platforms import detect_local_platform, detect_remote_platform
from .ssh_utils import verify_ssh_access_remote, check_remote_dependencies, setup_ssh_tunnel, start_claude_interface
from .verification import verify_remote_installations, verify_local_installations
from .installers import install_deps_local, install_deps_remote

__all__ = [
    'handle_usage', 'handle_install_agents', 'handle_install_deps',
    'handle_tunnel', 'handle_invoke_claude', 'handle_shell',
    'SHELL_ENABLED',
    'detect_local_platform', 'detect_remote_platform',
    'verify_ssh_access_remote', 'check_remote_dependencies',
    'setup_ssh_tunnel', 'start_claude_interface',
    'verify_remote_installations', 'verify_local_installations',
    'install_deps_local', 'install_deps_remote'
]