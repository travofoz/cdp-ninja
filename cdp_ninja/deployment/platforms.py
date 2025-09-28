"""
CDP Ninja Platform Detection
Detects local and remote platform information for dependency installation
"""

import platform
import shutil
import subprocess


def detect_local_platform():
    """Detect local platform and available package manager"""
    system = platform.system()

    if system == 'Windows':
        print("❌ Windows is not supported for dependency installation")
        print("💡 Use WSL2 with Ubuntu for CDP Ninja development")
        return None

    elif system == 'Darwin':  # macOS
        if shutil.which('brew'):
            return {
                'os': 'macOS',
                'system': 'Darwin',
                'package_manager': 'brew',
                'sudo_required': False
            }
        else:
            print("❌ Homebrew not found on macOS")
            print("💡 Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return None

    elif system == 'Linux':
        # Detect Linux distribution
        distro_info = detect_linux_distro()
        if not distro_info:
            return None

        # Find available package manager
        if distro_info['family'] in ['ubuntu', 'debian'] and shutil.which('apt-get'):
            return {
                'os': f"Linux ({distro_info['name']})",
                'system': 'Linux',
                'distro_family': distro_info['family'],
                'package_manager': 'apt-get',
                'sudo_required': True
            }
        elif distro_info['family'] in ['centos', 'rhel', 'fedora']:
            if shutil.which('dnf'):
                return {
                    'os': f"Linux ({distro_info['name']})",
                    'system': 'Linux',
                    'distro_family': distro_info['family'],
                    'package_manager': 'dnf',
                    'sudo_required': True
                }
            elif shutil.which('yum'):
                return {
                    'os': f"Linux ({distro_info['name']})",
                    'system': 'Linux',
                    'distro_family': distro_info['family'],
                    'package_manager': 'yum',
                    'sudo_required': True
                }
        elif distro_info['family'] == 'arch' and shutil.which('pacman'):
            return {
                'os': f"Linux ({distro_info['name']})",
                'system': 'Linux',
                'distro_family': distro_info['family'],
                'package_manager': 'pacman',
                'sudo_required': True
            }

        print(f"❌ Unsupported Linux distribution or missing package manager")
        return None

    else:
        print(f"❌ Unsupported operating system: {system}")
        return None


def detect_linux_distro():
    """Detect Linux distribution from /etc/os-release"""
    try:
        with open('/etc/os-release', 'r') as f:
            lines = f.readlines()

        distro_info = {}
        for line in lines:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                distro_info[key] = value.strip('"')

        name = distro_info.get('NAME', '').lower()
        id_like = distro_info.get('ID_LIKE', '').lower()
        distro_id = distro_info.get('ID', '').lower()

        # Determine distribution family
        if 'ubuntu' in name or 'ubuntu' in id_like or distro_id == 'ubuntu':
            family = 'ubuntu'
        elif 'debian' in name or 'debian' in id_like or distro_id == 'debian':
            family = 'debian'
        elif 'centos' in name or 'centos' in id_like or distro_id == 'centos':
            family = 'centos'
        elif 'rhel' in name or 'red hat' in name or 'rhel' in id_like:
            family = 'rhel'
        elif 'fedora' in name or 'fedora' in id_like or distro_id == 'fedora':
            family = 'fedora'
        elif 'arch' in name or 'arch' in id_like or distro_id == 'arch':
            family = 'arch'
        else:
            family = 'unknown'

        return {
            'name': distro_info.get('PRETTY_NAME', name),
            'family': family,
            'id': distro_id
        }

    except Exception as e:
        print(f"❌ Could not detect Linux distribution: {e}")
        return None


def detect_remote_platform(target_host):
    """Detect platform and package manager on remote host"""
    try:
        # Get OS information
        result = subprocess.run(
            ['ssh', target_host, 'cat /etc/os-release 2>/dev/null || echo "UNKNOWN"'],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0 or 'UNKNOWN' in result.stdout:
            print("❌ Could not detect remote OS")
            return None

        # Parse os-release
        distro_info = {}
        for line in result.stdout.split('\n'):
            if '=' in line:
                key, value = line.strip().split('=', 1)
                distro_info[key] = value.strip('"')

        name = distro_info.get('NAME', '').lower()
        id_like = distro_info.get('ID_LIKE', '').lower()
        distro_id = distro_info.get('ID', '').lower()

        # Determine distribution family
        if 'ubuntu' in name or 'ubuntu' in id_like or distro_id == 'ubuntu':
            family = 'ubuntu'
        elif 'debian' in name or 'debian' in id_like or distro_id == 'debian':
            family = 'debian'
        elif 'centos' in name or 'centos' in id_like or distro_id == 'centos':
            family = 'centos'
        elif 'rhel' in name or 'red hat' in name or 'rhel' in id_like:
            family = 'rhel'
        elif 'fedora' in name or 'fedora' in id_like or distro_id == 'fedora':
            family = 'fedora'
        elif 'arch' in name or 'arch' in id_like or distro_id == 'arch':
            family = 'arch'
        else:
            family = 'unknown'

        # Check available package managers
        if family in ['ubuntu', 'debian']:
            pkg_mgr_check = subprocess.run(
                ['ssh', target_host, 'which apt-get'],
                capture_output=True, text=True, timeout=10
            )
            if pkg_mgr_check.returncode == 0:
                return {
                    'os': f"Linux ({distro_info.get('PRETTY_NAME', name)})",
                    'system': 'Linux',
                    'distro_family': family,
                    'package_manager': 'apt-get',
                    'sudo_required': True
                }

        elif family in ['centos', 'rhel', 'fedora']:
            # Try dnf first, then yum
            for pkg_mgr in ['dnf', 'yum']:
                pkg_mgr_check = subprocess.run(
                    ['ssh', target_host, f'which {pkg_mgr}'],
                    capture_output=True, text=True, timeout=10
                )
                if pkg_mgr_check.returncode == 0:
                    return {
                        'os': f"Linux ({distro_info.get('PRETTY_NAME', name)})",
                        'system': 'Linux',
                        'distro_family': family,
                        'package_manager': pkg_mgr,
                        'sudo_required': True
                    }

        elif family == 'arch':
            pkg_mgr_check = subprocess.run(
                ['ssh', target_host, 'which pacman'],
                capture_output=True, text=True, timeout=10
            )
            if pkg_mgr_check.returncode == 0:
                return {
                    'os': f"Linux ({distro_info.get('PRETTY_NAME', name)})",
                    'system': 'Linux',
                    'distro_family': family,
                    'package_manager': 'pacman',
                    'sudo_required': True
                }

        print(f"❌ Unsupported remote platform or package manager not found")
        return None

    except Exception as e:
        print(f"❌ Failed to detect remote platform: {e}")
        return None


def check_existing_dependencies():
    """Check which dependencies are already installed locally"""
    existing = []

    # Check Claude CLI
    if shutil.which('claude'):
        existing.append('claude')

    # Check tmux
    if shutil.which('tmux'):
        existing.append('tmux')

    # Check gotty
    if shutil.which('gotty'):
        existing.append('gotty')

    # Check ttyd
    if shutil.which('ttyd'):
        existing.append('ttyd')

    # Check uv
    if shutil.which('uv'):
        existing.append('uv')

    return existing