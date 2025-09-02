#!/bin/bash
# Unified Installation Script for Debian Package Manager
# Supports both local installation and Docker environment setup.

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

show_help() {
    echo "Debian Package Manager Installation Script"
    echo ""
    echo "Usage: ./install.sh [mode] [options]"
    echo ""
    echo "Modes:"
    echo "  --local        Install locally on the system (requires sudo)"
    echo "  --docker       Set up Docker development environment"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --uninstall    Uninstall the package manager (local mode only)"
    echo ""
    echo "Examples:"
    echo "  ./install.sh --local      # Install DPM locally"
    echo "  ./install.sh --docker     # Set up Docker environment"
    echo "  sudo ./install.sh --local --uninstall  # Uninstall local installation"
}

# LOCAL INSTALLATION FUNCTIONS

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Local installation requires root privileges (use sudo)"
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
    print_success "Local installation complete! Available commands:"
    echo ""
    echo "  dpm install <package>     # Install a package or metapackage"
    echo "  dpm remove <package>      # Remove a package"
    echo "  dpm info <package>        # Show package information"
    echo "  dpm list                  # List custom prefix packages"
    echo "  dpm list --all            # List all installed packages"
    echo "  dpm health                # Check system health"
    echo "  dpm fix                   # Fix broken packages"
    echo "  dpm mode --status         # Show mode status"
    echo "  dpm cleanup --all         # Clean up system"
    echo "  dpm connect <user> <host> # Connect to remote system"
    echo ""
    echo "For more information, run: dpm --help"
    echo ""
    echo "Configuration file: /etc/debian-package-manager/config.json"
    echo "Installation directory: $INSTALL_DIR"
}

install_local() {
    print_status "Starting local DPM installation..."
    
    check_root
    check_dependencies
    install_package
    create_config
    show_usage
    
    print_success "Local installation completed successfully!"
}

# DOCKER INSTALLATION FUNCTIONS

check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        print_status "Please install Docker first:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install docker.io docker-compose"
        echo "  Or visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check for Docker Compose
    COMPOSE_AVAILABLE=false
    COMPOSE_CMD=""
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_AVAILABLE=true
        COMPOSE_CMD="docker-compose"
        print_status "Found Docker Compose (standalone version)"
    elif docker compose version &> /dev/null; then
        COMPOSE_AVAILABLE=true
        COMPOSE_CMD="docker compose"
        print_status "Found Docker Compose (plugin version)"
    fi
    
    if [ "$COMPOSE_AVAILABLE" = false ]; then
        print_error "Docker Compose is required but not installed"
        print_status "Please install Docker Compose:"
        echo "  Ubuntu/Debian: sudo apt install docker-compose"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        print_status "Please start Docker service:"
        echo "  sudo systemctl start docker"
        exit 1
    fi
    
    print_success "Docker is available and running"
}

check_docker_structure() {
    print_status "Checking Docker environment structure..."
    
    if [ ! -d "docker" ]; then
        print_error "Docker directory not found"
        print_status "Please ensure you're running this script from the project root"
        exit 1
    fi
    
    if [ ! -f "docker/Dockerfile" ]; then
        print_error "docker/Dockerfile not found"
        exit 1
    fi
    
    if [ ! -f "docker/docker-compose.yml" ]; then
        print_error "docker/docker-compose.yml not found"
        exit 1
    fi
    
    print_success "Docker structure is valid"
}

build_docker_environment() {
    print_status "Building Docker environment..."
    
    cd docker
    
    # Build the Docker image
    print_status "Building Docker image (this may take a few minutes)..."
    if $COMPOSE_CMD build; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
    
    cd ..
}

create_wrapper_scripts() {
    print_status "Creating Docker wrapper scripts..."
    
    # Create main start script
    cat > dpm-docker-start.sh << 'EOF'
#!/bin/bash
# Start DPM Docker Environment

set -e

echo "🐳 Starting DPM Docker Environment..."

# Detect Docker Compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

# Change to docker directory
cd docker

# Check if container is already running
if $COMPOSE_CMD ps | grep -q "dpm-dev.*Up"; then
    echo "✅ Container is already running"
else
    echo "🚀 Starting container..."
    $COMPOSE_CMD up -d
    
    # Wait for container to be ready
    echo "⏳ Waiting for container to be ready..."
    sleep 3
fi

echo "🔗 Connecting to DPM environment..."
echo "   Use 'exit' to leave the container (it will keep running)"
echo "   Use './dpm-docker-stop.sh' to fully stop the environment"
echo ""

$COMPOSE_CMD exec dpm-environment /bin/bash

echo "👋 Exited DPM environment"
EOF

    # Create stop script
    cat > dpm-docker-stop.sh << 'EOF'
#!/bin/bash
# Stop DPM Docker Environment

set -e

echo "🛑 Stopping DPM Docker Environment..."

# Detect Docker Compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

cd docker
$COMPOSE_CMD down

echo "✅ DPM Docker environment stopped"
EOF

    # Make scripts executable
    chmod +x dpm-docker-start.sh
    chmod +x dpm-docker-stop.sh
    
    print_success "Wrapper scripts created"
}

show_docker_usage() {
    print_success "Docker environment setup complete!"
    echo ""
    echo "🚀 Quick Start:"
    echo "  ./dpm-docker-start.sh     # Start and enter Docker environment"
    echo "  ./dpm-docker-stop.sh      # Stop Docker environment"
    echo ""
    echo "📦 Inside the Docker container, you can use:"
    echo "  dpm install <package>     # Install a package"
    echo "  dpm remove <package>      # Remove a package"
    echo "  dpm list                  # List custom packages"
    echo "  dpm list --all            # List all packages"
    echo "  dpm health                # Check system health"
    echo "  dpm mode --status         # Check current mode"
    echo "  dpm connect <user> <host> # Test remote connections"
    echo ""
    echo "🔧 Development Features:"
    echo "  - Live code editing (changes reflected immediately)"
    echo "  - Pre-built example packages for testing"
    echo "  - SSH keys pre-configured for remote testing"
    echo "  - Persistent data and configuration"
    echo ""
    echo "For more information, see docker/README.md"
}

install_docker() {
    print_status "Starting Docker environment setup..."
    
    check_docker
    check_docker_structure
    build_docker_environment
    create_wrapper_scripts
    show_docker_usage
    
    print_success "Docker environment setup completed successfully!"
}

uninstall_local() {
    print_status "Uninstalling Debian Package Manager..."
    
    check_root
    
    rm -rf "$INSTALL_DIR"
    rm -f "$BIN_DIR/dpm"
    rm -f "$BIN_DIR/debian-package-manager"
    
    print_success "Local uninstallation completed!"
}

# MAIN SCRIPT LOGIC

# Handle command line arguments
case "${1:-}" in
    --local)
        if [[ "${2:-}" == "--uninstall" ]]; then
            uninstall_local
        else
            install_local
        fi
        ;;
    --docker)
        install_docker
        ;;
    --help|-h)
        show_help
        exit 0
        ;;
    --uninstall)
        print_error "--uninstall must be used with --local mode"
        echo "Usage: sudo ./install.sh --local --uninstall"
        exit 1
        ;;
    "")
        print_error "Please specify installation mode"
        echo ""
        show_help
        exit 1
        ;;
    *)
        print_error "Unknown option: $1"
        echo ""
        show_help
        exit 1
        ;;
esac