#!/bin/bash
#
# CDP Ninja - Linux/macOS Setup Script
# Lightweight Chrome DevTools Protocol bridge installation
#
# Usage:
#   ./setup_unix.sh [options]
#
# Options:
#   --install-dir DIR     Installation directory (default: ~/cdp-ninja)
#   --cdp-port PORT       Chrome DevTools port (default: 9222)
#   --bridge-port PORT    HTTP API bridge port (default: 8888)
#   --skip-chrome         Skip Chrome setup and configuration
#   --global-python       Use global Python instead of virtual environment
#   --python-path PATH    Explicit path to Python executable
#   --start-url URL       URL to open when Chrome starts
#   --help               Show this help message

set -e  # Exit on any error

# Default configuration
INSTALL_DIR="$HOME/cdp-ninja"
CDP_PORT=9222
BRIDGE_PORT=8888
SKIP_CHROME=false
GLOBAL_PYTHON=false
PYTHON_PATH=""
START_URL="http://localhost:3690"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')] [INFO] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] [SUCCESS] $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] [WARNING] $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] [ERROR] $1${NC}"
}

# Help function
show_help() {
    cat << EOF
Debug Ninja - Linux/macOS Setup Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --install-dir DIR     Installation directory (default: ~/cdp-ninja)
    --cdp-port PORT       Chrome DevTools port (default: 9222)
    --bridge-port PORT    HTTP API bridge port (default: 8888)
    --skip-chrome         Skip Chrome setup and configuration
    --global-python       Use global Python instead of virtual environment
    --python-path PATH    Explicit path to Python executable
    --start-url URL       URL to open when Chrome starts
    --help               Show this help message

EXAMPLES:
    # Standard installation
    ./setup_unix.sh

    # Custom installation directory
    ./setup_unix.sh --install-dir /opt/cdp-ninja

    # Skip Chrome setup (manual Chrome start required)
    ./setup_unix.sh --skip-chrome

    # Use specific Python version
    ./setup_unix.sh --python-path /usr/bin/python3.9

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --cdp-port)
            CDP_PORT="$2"
            shift 2
            ;;
        --bridge-port)
            BRIDGE_PORT="$2"
            shift 2
            ;;
        --skip-chrome)
            SKIP_CHROME=true
            shift
            ;;
        --global-python)
            GLOBAL_PYTHON=true
            shift
            ;;
        --python-path)
            PYTHON_PATH="$2"
            shift 2
            ;;
        --start-url)
            START_URL="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Find Chrome executable
find_chrome() {
    local os=$(detect_os)
    local chrome_paths=()

    case $os in
        "linux")
            chrome_paths=(
                "/usr/bin/google-chrome"
                "/usr/bin/google-chrome-stable"
                "/usr/bin/chromium-browser"
                "/usr/bin/chromium"
                "/snap/bin/chromium"
                "/opt/google/chrome/chrome"
            )
            ;;
        "macos")
            chrome_paths=(
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                "/Applications/Chromium.app/Contents/MacOS/Chromium"
            )
            ;;
    esac

    for path in "${chrome_paths[@]}"; do
        if [[ -f "$path" ]]; then
            echo "$path"
            return 0
        fi
    done

    return 1
}

# Find Python executable
find_python() {
    local python_commands=("python3" "python" "python3.8" "python3.9" "python3.10" "python3.11" "python3.12")

    if [[ -n "$PYTHON_PATH" ]] && [[ -x "$PYTHON_PATH" ]]; then
        local version=$($PYTHON_PATH --version 2>&1)
        if [[ $version =~ Python\ 3\.([89]|1[0-9]) ]]; then
            echo "$PYTHON_PATH"
            return 0
        fi
    fi

    for cmd in "${python_commands[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            local version=$($cmd --version 2>&1)
            if [[ $version =~ Python\ 3\.([89]|1[0-9]) ]]; then
                echo "$cmd"
                return 0
            fi
        fi
    done

    return 1
}

# Install Python if needed (package manager specific)
install_python_prompt() {
    local os=$(detect_os)

    log_warning "Python 3.8+ is required but not found on this system"

    echo "Would you like to install Python? (y/N)"
    read -r response
    if [[ $response =~ ^[Yy]$ ]]; then
        case $os in
            "linux")
                if command -v apt >/dev/null 2>&1; then
                    log_info "Installing Python using apt..."
                    sudo apt update
                    sudo apt install -y python3 python3-pip python3-venv
                elif command -v yum >/dev/null 2>&1; then
                    log_info "Installing Python using yum..."
                    sudo yum install -y python3 python3-pip
                elif command -v dnf >/dev/null 2>&1; then
                    log_info "Installing Python using dnf..."
                    sudo dnf install -y python3 python3-pip
                else
                    log_error "No supported package manager found. Please install Python 3.8+ manually."
                    exit 1
                fi
                ;;
            "macos")
                if command -v brew >/dev/null 2>&1; then
                    log_info "Installing Python using Homebrew..."
                    brew install python@3.9
                else
                    log_error "Homebrew not found. Please install Python 3.8+ manually:"
                    log_info "  Option 1: Install Homebrew: https://brew.sh/"
                    log_info "  Option 2: Download from: https://www.python.org/downloads/"
                    exit 1
                fi
                ;;
        esac
    else
        log_error "Cannot proceed without Python 3.8+"
        exit 1
    fi
}

# Setup virtual environment
setup_venv() {
    local python_cmd="$1"
    local install_dir="$2"

    log_info "Setting up Python virtual environment..."

    local venv_path="$install_dir/venv"

    if [[ ! -d "$venv_path" ]]; then
        log_info "Creating virtual environment..."
        "$python_cmd" -m venv "$venv_path"
        log_success "Virtual environment created"
    else
        log_success "Virtual environment already exists"
    fi

    # Return paths
    case $(detect_os) in
        "linux"|"macos")
            echo "$venv_path/bin/python"
            echo "$venv_path/bin/pip"
            echo "$venv_path/bin/activate"
            ;;
    esac
}

# Install Python dependencies
install_dependencies() {
    local pip_cmd="$1"
    local install_dir="$2"

    log_info "Installing Python dependencies..."

    # Create requirements.txt if it doesn't exist
    local requirements_file="$install_dir/requirements.txt"
    if [[ ! -f "$requirements_file" ]]; then
        cat > "$requirements_file" << 'EOF'
flask==3.0.0
flask-cors==4.0.0
websocket-client==1.7.0
psutil==5.9.6
requests==2.31.0
python-dotenv==1.0.0
EOF
        log_info "Created requirements.txt"
    fi

    # Upgrade pip
    log_info "Upgrading pip..."
    "$pip_cmd" install --upgrade pip --quiet

    # Install dependencies
    log_info "Installing packages from requirements.txt..."
    "$pip_cmd" install -r "$requirements_file" --quiet

    log_success "Python dependencies installed successfully"
}

# Create project structure
create_project_structure() {
    local install_dir="$1"

    log_info "Creating project structure..."

    local directories=("core" "api" "setup" "agent" "examples" "logs")

    for dir in "${directories[@]}"; do
        mkdir -p "$install_dir/$dir"
    done

    # Create __init__.py files
    touch "$install_dir/core/__init__.py"
    touch "$install_dir/api/__init__.py"

    log_success "Project structure created"
}

# Setup Chrome for debugging
setup_chrome() {
    local chrome_exe="$1"
    local port="$2"
    local url="$3"

    if [[ "$SKIP_CHROME" == true ]]; then
        log_warning "Skipping Chrome setup (--skip-chrome specified)"
        return 0
    fi

    log_info "Configuring Chrome for debugging..."

    # Kill existing Chrome debug instances
    log_info "Stopping existing Chrome debug instances..."
    case $(detect_os) in
        "linux")
            pkill -f "chrome.*remote-debugging" || true
            pkill -f "chromium.*remote-debugging" || true
            ;;
        "macos")
            pkill -f "Google Chrome.*remote-debugging" || true
            pkill -f "Chromium.*remote-debugging" || true
            ;;
    esac

    sleep 2

    # Create clean debug profile
    local debug_profile="/tmp/cdp-ninja-chrome-profile"
    if [[ -d "$debug_profile" ]]; then
        rm -rf "$debug_profile"
    fi
    mkdir -p "$debug_profile"

    # Chrome startup arguments
    local chrome_args=(
        "--remote-debugging-port=$port"
        "--user-data-dir=$debug_profile"
        "--no-first-run"
        "--no-default-browser-check"
        "--disable-background-timer-throttling"
        "--disable-renderer-backgrounding"
        "--disable-features=TranslateUI"
        "--disable-ipc-flooding-protection"
        "$url"
    )

    # Start Chrome with debugging
    log_info "Starting Chrome with debugging on port $port..."

    case $(detect_os) in
        "linux")
            nohup "$chrome_exe" "${chrome_args[@]}" > /dev/null 2>&1 &
            ;;
        "macos")
            nohup "$chrome_exe" "${chrome_args[@]}" > /dev/null 2>&1 &
            ;;
    esac

    # Wait for Chrome to start
    sleep 4

    # Verify Chrome DevTools is accessible
    local max_attempts=10
    local connected=false

    for ((i=1; i<=max_attempts; i++)); do
        if curl -s "http://localhost:$port/json" > /dev/null 2>&1; then
            connected=true
            local tabs=$(curl -s "http://localhost:$port/json" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
            log_success "Chrome DevTools verified - $tabs tab(s) available"
            break
        else
            if [[ $i -eq $max_attempts ]]; then
                log_warning "Chrome DevTools verification failed after $max_attempts attempts"
            else
                log_info "Attempt $i/$max_attempts - waiting for Chrome..."
                sleep 2
            fi
        fi
    done

    if [[ "$connected" == false ]]; then
        log_warning "Chrome DevTools may not be accessible on port $port"
        log_info "You may need to manually start Chrome with:"
        log_info "  $chrome_exe ${chrome_args[*]}"
    fi
}

# Create startup scripts
create_startup_scripts() {
    local install_dir="$1"
    local venv_activate="$2"
    local bridge_port="$3"

    log_info "Creating startup scripts..."

    # Shell script for easy startup
    cat > "$install_dir/start_bridge.sh" << EOF
#!/bin/bash
cd "$install_dir"
echo "Starting Debug Ninja..."
echo "Bridge URL: http://localhost:$bridge_port"
echo "Press Ctrl+C to stop"
echo ""

# Activate virtual environment if it exists
if [[ -f "$venv_activate" ]]; then
    source "$venv_activate"
    echo "Virtual environment activated"
fi

python -m api.server
EOF

    chmod +x "$install_dir/start_bridge.sh"

    # Create desktop entry for Linux
    if [[ $(detect_os) == "linux" ]] && [[ -d "$HOME/.local/share/applications" ]]; then
        cat > "$HOME/.local/share/applications/cdp-ninja.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Debug Ninja
Comment=Lightweight Chrome DevTools Protocol Bridge
Exec=$install_dir/start_bridge.sh
Icon=web-browser
Terminal=true
Categories=Development;Debugger;
EOF
        log_success "Desktop entry created"
    fi

    log_success "Startup scripts created"
}

# Create configuration file
create_config() {
    local install_dir="$1"
    local cdp_port="$2"
    local bridge_port="$3"

    cat > "$install_dir/config.json" << EOF
{
    "cdp": {
        "port": $cdp_port,
        "host": "localhost",
        "auto_reconnect": true,
        "max_events": 1000
    },
    "bridge": {
        "port": $bridge_port,
        "host": "0.0.0.0",
        "debug": false
    },
    "chrome": {
        "profile_dir": "/tmp/cdp-ninja-chrome-profile",
        "additional_args": []
    },
    "logging": {
        "level": "INFO",
        "file": "logs/cdp-ninja.log"
    }
}
EOF

    log_success "Configuration file created: config.json"
}

# Show installation summary
show_summary() {
    local install_dir="$1"
    local bridge_port="$2"
    local cdp_port="$3"
    local chrome_configured="$4"

    # Get local IP
    local local_ip
    case $(detect_os) in
        "linux")
            local_ip=$(ip route get 1 | awk '{print $7}' | head -n1)
            ;;
        "macos")
            local_ip=$(route get default | grep interface | awk '{print $2}' | xargs ifconfig | grep inet | grep -v inet6 | awk '{print $2}' | head -n1)
            ;;
    esac

    cat << EOF

${GREEN}========================================
🥷 Debug Ninja Installation Complete!
========================================${NC}

Installation Directory: $install_dir
Bridge URL: http://localhost:$bridge_port
Chrome DevTools: http://localhost:$cdp_port

${CYAN}🚀 Quick Start:${NC}
$install_dir/start_bridge.sh

${CYAN}🔗 For Remote Access (SSH Tunnel):${NC}
${YELLOW}# Option A: Access remote Debug Ninja${NC}
ssh -L $bridge_port:localhost:$bridge_port user@remote-machine

${YELLOW}# Option B: Expose local Debug Ninja${NC}
ssh -R $bridge_port:localhost:$bridge_port user@claude-code-vps

${CYAN}📚 Usage Examples:${NC}
• Health Check: curl http://localhost:$bridge_port/health
• Take Screenshot: curl http://localhost:$bridge_port/cdp/screenshot > screenshot.png
• Execute JavaScript: curl -X POST http://localhost:$bridge_port/cdp/execute \\
    -H "Content-Type: application/json" \\
    -d '{"code":"document.title"}'

${CYAN}🔧 Configuration:${NC}
Edit $install_dir/config.json to customize settings

${CYAN}📖 Documentation:${NC}
See $install_dir/README.md for complete API reference

EOF

    if [[ "$chrome_configured" != true ]]; then
        echo -e "${YELLOW}⚠️  Chrome Setup Skipped:${NC}"
        echo "To enable Chrome debugging manually:"
        echo "  google-chrome --remote-debugging-port=$cdp_port --user-data-dir=/tmp/cdp-ninja-chrome-profile $START_URL"
        echo ""
    fi
}

# Test installation
test_installation() {
    local venv_python="$1"
    local install_dir="$2"

    log_info "Testing installation..."

    # Test Python imports
    local test_script="$install_dir/test_install.py"
    cat > "$test_script" << 'EOF'
try:
    import flask
    import websocket
    import psutil
    import requests
    print("SUCCESS: All required packages available")
except ImportError as e:
    print(f"ERROR: Missing package - {e}")
    exit(1)
EOF

    if "$venv_python" "$test_script" 2>/dev/null; then
        log_success "Package imports verified"
    else
        log_warning "Package import test failed"
    fi

    rm -f "$test_script"
}

# Main installation flow
main() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  DEBUG NINJA - LINUX/MACOS INSTALLATION${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""

    # Step 1: Find Chrome
    log_info "Checking Chrome installation..."
    local chrome=""
    if chrome=$(find_chrome); then
        log_success "Chrome executable found: $chrome"
    elif [[ "$SKIP_CHROME" == false ]]; then
        log_error "Chrome not found. Install Chrome/Chromium first or use --skip-chrome"
        log_info "Install Chrome from: https://www.google.com/chrome/"
        exit 1
    else
        log_warning "Chrome not found, but --skip-chrome specified"
    fi

    # Step 2: Find Python
    log_info "Checking Python installation..."
    local python=""
    if python=$(find_python); then
        log_success "Python found: $python"
    else
        install_python_prompt
        if ! python=$(find_python); then
            log_error "Cannot proceed without Python 3.8+"
            exit 1
        fi
    fi

    # Step 3: Create installation directory
    log_info "Creating installation directory..."
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    log_success "Installation directory: $INSTALL_DIR"

    # Step 4: Create project structure
    create_project_structure "$INSTALL_DIR"

    # Step 5: Setup Python environment
    local venv_python="$python"
    local venv_pip="pip"
    local venv_activate=""

    if [[ "$GLOBAL_PYTHON" == false ]]; then
        local venv_info
        venv_info=$(setup_venv "$python" "$INSTALL_DIR")
        local venv_paths=($venv_info)
        venv_python="${venv_paths[0]}"
        venv_pip="${venv_paths[1]}"
        venv_activate="${venv_paths[2]}"
    else
        log_warning "Using global Python installation (not recommended)"
    fi

    # Step 6: Install dependencies
    install_dependencies "$venv_pip" "$INSTALL_DIR"

    # Step 7: Create configuration
    create_config "$INSTALL_DIR" "$CDP_PORT" "$BRIDGE_PORT"

    # Step 8: Create startup scripts
    create_startup_scripts "$INSTALL_DIR" "$venv_activate" "$BRIDGE_PORT"

    # Step 9: Setup Chrome debugging
    local chrome_configured=false
    if [[ -n "$chrome" ]]; then
        setup_chrome "$chrome" "$CDP_PORT" "$START_URL"
        chrome_configured=true
    fi

    # Step 10: Test installation
    if [[ "$GLOBAL_PYTHON" == false ]]; then
        test_installation "$venv_python" "$INSTALL_DIR"
    fi

    # Step 11: Show completion summary
    show_summary "$INSTALL_DIR" "$BRIDGE_PORT" "$CDP_PORT" "$chrome_configured"

    log_success "Installation completed successfully! 🎉"
}

# Run main function
main "$@"