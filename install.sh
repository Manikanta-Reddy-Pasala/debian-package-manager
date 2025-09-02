#!/bin/bash
"""
Installation script for Debian Package Manager
This script installs the package manager system-wide or in a virtual environment.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/debian-package-manager"
BIN_DIR="/usr/local/bin"
VENV_DIR="$INSTALL_DIR/venv"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_dependencies() {
    print_status "Checking system dependencies..."
    
    # Check for Python 3.8+
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_error "Python 3.8+ is required, found Python $python_version"
        exit 1
    fi
    
    # Check for apt and dpkg
    if ! command -v apt &> /dev/null; then
        print_error "apt is required but not found"
        exit 1
    fi
    
    if ! command -v dpkg &> /dev/null; then
        print_error "dpkg is required but not found"
        exit 1
    fi
    
    # Check for python3-venv
    if ! python3 -c "import venv" 2>/dev/null; then
        print_warning "python3-venv not found, attempting to install..."
        apt update && apt install -y python3-venv
    fi
    
    # Check for python3-apt
    if ! python3 -c "import apt" 2>/dev/null; then
        print_warning "python3-apt not found, attempting to install..."
        apt update && apt install -y python3-apt
    fi
    
    print_success "All dependencies satisfied"
}

install_package() {
    print_status "Installing Debian Package Manager..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Copy source files
    cp -r src/ "$INSTALL_DIR/"
    cp -r bin/ "$INSTALL_DIR/"
    cp pyproject.toml "$INSTALL_DIR/"
    cp README.md "$INSTALL_DIR/"
    
    # Create virtual environment
    print_status "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    # Install package in virtual environment
    print_status "Installing package dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -e "$INSTALL_DIR"
    
    # Create system-wide executable
    print_status "Creating system executable..."
    cat > "$BIN_DIR/dpm" << EOF
#!/bin/bash
# Debian Package Manager system executable
export PYTHONPATH="$INSTALL_DIR/src:\$PYTHONPATH"
exec "$VENV_DIR/bin/python" -m debian_metapackage_manager.cli "\$@"
EOF
    
    chmod +x "$BIN_DIR/dpm"
    
    # Create alternative executable name
    ln -sf "$BIN_DIR/dpm" "$BIN_DIR/debian-package-manager"
    
    print_success "Installation completed successfully!"
}

create_config() {
    print_status "Creating default configuration..."
    
    # Create system config directory
    mkdir -p /etc/debian-package-manager
    
    # Create default config if it doesn't exist
    if [[ ! -f /etc/debian-package-manager/config.json ]]; then
        cat > /etc/debian-package-manager/config.json << EOF
{
    "package_prefixes": {
        "custom_prefixes": [
            "mycompany-",
            "custom-"
        ]
    },
    "offline_mode": false,
    "version_pinning": {}
}
EOF
        print_success "Created default configuration at /etc/debian-package-manager/config.json"
    else
        print_status "Configuration already exists, skipping..."
    fi
}

show_usage() {
    print_success "Installation complete! You can now use the following commands:"
    echo ""
    echo "  dpm install <package>     # Install a package or metapackage"
    echo "  dpm remove <package>      # Remove a package"
    echo "  dpm info <package>        # Show package information"
    echo "  dpm list                  # List installed packages"
    echo "  dpm health                # Check system health"
    echo "  dpm fix                   # Fix broken packages"
    echo "  dpm config --show         # Show configuration"
    echo "  dpm mode --status         # Show mode status"
    echo ""
    echo "For more information, run: dpm --help"
    echo ""
    echo "Configuration file: /etc/debian-package-manager/config.json"
    echo "Installation directory: $INSTALL_DIR"
}

main() {
    print_status "Starting Debian Package Manager installation..."
    
    check_root
    check_dependencies
    install_package
    create_config
    show_usage
    
    print_success "Installation completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Debian Package Manager Installation Script"
        echo ""
        echo "Usage: sudo ./install.sh [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --uninstall    Uninstall the package manager"
        echo ""
        exit 0
        ;;
    --uninstall)
        print_status "Uninstalling Debian Package Manager..."
        rm -rf "$INSTALL_DIR"
        rm -f "$BIN_DIR/dpm"
        rm -f "$BIN_DIR/debian-package-manager"
        print_success "Uninstallation completed!"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac