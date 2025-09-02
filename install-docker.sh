#!/bin/bash
"""
Docker Installation Script for Debian Package Manager
This script creates a Docker environment with DPM pre-installed and ready to use.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE_NAME="dpm-environment"
DOCKER_CONTAINER_NAME="dpm-dev"
DOCKERFILE_NAME="Dockerfile.dpm"

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

check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        print_status "Please install Docker first:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install docker.io"
        echo "  Or visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        print_status "Please start Docker service:"
        echo "  sudo systemctl start docker"
        echo "  sudo systemctl enable docker"
        exit 1
    fi
    
    # Check if user can run Docker commands
    if ! docker ps &> /dev/null; then
        print_warning "Current user cannot run Docker commands"
        print_status "You may need to add your user to the docker group:"
        echo "  sudo usermod -aG docker \$USER"
        echo "  Then log out and log back in"
        print_status "Continuing with sudo..."
        DOCKER_CMD="sudo docker"
    else
        DOCKER_CMD="docker"
    fi
    
    print_success "Docker is available and running"
}

create_dockerfile() {
    print_status "Creating Dockerfile for DPM environment..."
    
    cat > "$DOCKERFILE_NAME" << 'EOF'
# Debian Package Manager Docker Environment
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-apt \
    apt-utils \
    dpkg-dev \
    curl \
    wget \
    git \
    ssh \
    sudo \
    vim \
    nano \
    htop \
    tree \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for development
RUN useradd -m -s /bin/bash -G sudo dpmuser && \
    echo "dpmuser:dpmuser" | chpasswd && \
    echo "dpmuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set up working directory
WORKDIR /opt/debian-package-manager

# Copy DPM source code
COPY . .

# Install DPM in development mode
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -e . && \
    python3 -m pip install pytest black isort mypy

# Create system-wide DPM executable
RUN ln -sf /usr/local/bin/dpm /usr/bin/dpm

# Create default configuration
RUN mkdir -p /etc/debian-package-manager && \
    cat > /etc/debian-package-manager/config.json << 'EOFCONFIG'
{
    "custom_prefixes": [
        "mycompany-",
        "internal-",
        "custom-",
        "dev-",
        "local-",
        "meta-",
        "bundle-",
        "docker-"
    ],
    "removable_packages": [
        "example-old-package",
        "test-package",
        "demo-service"
    ],
    "offline_mode": false,
    "pinned_versions": {
        "docker-example": "1.0.0"
    },
    "force_confirmation_required": true,
    "auto_resolve_conflicts": true
}
EOFCONFIG

# Create user config directory
RUN mkdir -p /home/dpmuser/.config/debian-package-manager && \
    chown -R dpmuser:dpmuser /home/dpmuser/.config

# Create some example packages for testing
RUN mkdir -p /tmp/example-packages && \
    cd /tmp/example-packages && \
    # Create a simple example package structure
    mkdir -p docker-example-1.0.0/DEBIAN && \
    cat > docker-example-1.0.0/DEBIAN/control << 'EOFCONTROL'
Package: docker-example
Version: 1.0.0
Architecture: all
Maintainer: DPM Docker Environment
Description: Example package for DPM testing
 This is an example package created for testing DPM functionality
 in the Docker environment.
EOFCONTROL
    # Create package content
    mkdir -p docker-example-1.0.0/usr/local/bin && \
    echo '#!/bin/bash\necho "Hello from docker-example package!"' > docker-example-1.0.0/usr/local/bin/docker-example && \
    chmod +x docker-example-1.0.0/usr/local/bin/docker-example && \
    # Build the package
    dpkg-deb --build docker-example-1.0.0 && \
    # Install it for testing
    dpkg -i docker-example-1.0.0.deb || true

# Set up SSH for remote testing (optional)
RUN mkdir -p /home/dpmuser/.ssh && \
    ssh-keygen -t rsa -b 2048 -f /home/dpmuser/.ssh/id_rsa -N "" && \
    chown -R dpmuser:dpmuser /home/dpmuser/.ssh

# Create helpful aliases and environment setup
RUN cat >> /home/dpmuser/.bashrc << 'EOFBASHRC'

# DPM Environment Setup
export PATH="/usr/local/bin:$PATH"
export PYTHONPATH="/opt/debian-package-manager/src:$PYTHONPATH"

# Helpful aliases
alias ll='ls -la'
alias dpm-status='dpm connect && dpm health --verbose'
alias dpm-test='dpm list --custom && dpm info docker-example'

# Welcome message
echo "🐳 Welcome to DPM Docker Environment!"
echo "📦 Debian Package Manager is ready to use"
echo ""
echo "Quick start commands:"
echo "  dpm --help              # Show all available commands"
echo "  dpm health              # Check system health"
echo "  dpm list --custom       # List custom packages"
echo "  dpm info docker-example # Show example package info"
echo "  dpm config --show       # Show current configuration"
echo ""
echo "Example workflows:"
echo "  dpm install <package>   # Install a package"
echo "  dpm remove <package>    # Remove a package"
echo "  dpm cleanup --all       # Clean system"
echo ""
echo "Remote testing:"
echo "  dpm connect user host   # Connect to remote system"
echo "  dpm connect --disconnect # Return to local"
echo ""
EOFBASHRC

# Switch to non-root user
USER dpmuser
WORKDIR /home/dpmuser

# Set default command to bash
CMD ["/bin/bash"]
EOF

    print_success "Dockerfile created: $DOCKERFILE_NAME"
}

build_docker_image() {
    print_status "Building Docker image: $DOCKER_IMAGE_NAME"
    print_status "This may take a few minutes..."
    
    if $DOCKER_CMD build -f "$DOCKERFILE_NAME" -t "$DOCKER_IMAGE_NAME" .; then
        print_success "Docker image built successfully: $DOCKER_IMAGE_NAME"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

create_docker_compose() {
    print_status "Creating docker-compose.yml for easy management..."
    
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  dpm-environment:
    image: $DOCKER_IMAGE_NAME
    container_name: $DOCKER_CONTAINER_NAME
    hostname: dpm-docker
    stdin_open: true
    tty: true
    volumes:
      # Mount current directory for development
      - .:/opt/debian-package-manager
      # Persist user data
      - dpm-user-data:/home/dpmuser
      # Persist package cache
      - dpm-apt-cache:/var/cache/apt
    environment:
      - TERM=xterm-256color
    networks:
      - dpm-network
    # Keep container running
    command: tail -f /dev/null

volumes:
  dpm-user-data:
  dpm-apt-cache:

networks:
  dpm-network:
    driver: bridge
EOF

    print_success "docker-compose.yml created"
}

create_helper_scripts() {
    print_status "Creating helper scripts..."
    
    # Create start script
    cat > dpm-docker-start.sh << EOF
#!/bin/bash
# Start DPM Docker Environment

echo "🐳 Starting DPM Docker Environment..."

if docker-compose ps | grep -q "$DOCKER_CONTAINER_NAME.*Up"; then
    echo "✅ Container is already running"
else
    echo "🚀 Starting container..."
    docker-compose up -d
    sleep 2
fi

echo "🔗 Connecting to DPM environment..."
docker-compose exec dpm-environment /bin/bash

echo "👋 Exited DPM environment"
EOF

    # Create stop script
    cat > dpm-docker-stop.sh << EOF
#!/bin/bash
# Stop DPM Docker Environment

echo "🛑 Stopping DPM Docker Environment..."
docker-compose down

echo "✅ DPM Docker environment stopped"
EOF

    # Create clean script
    cat > dpm-docker-clean.sh << EOF
#!/bin/bash
# Clean DPM Docker Environment

echo "🧹 Cleaning DPM Docker Environment..."
echo "This will remove containers, images, and volumes"
read -p "Are you sure? (y/N): " -n 1 -r
echo
if [[ \$REPLY =~ ^[Yy]\$ ]]; then
    docker-compose down -v
    $DOCKER_CMD rmi $DOCKER_IMAGE_NAME 2>/dev/null || true
    $DOCKER_CMD system prune -f
    echo "✅ Cleanup completed"
else
    echo "❌ Cleanup cancelled"
fi
EOF

    # Create rebuild script
    cat > dpm-docker-rebuild.sh << EOF
#!/bin/bash
# Rebuild DPM Docker Environment

echo "🔄 Rebuilding DPM Docker Environment..."
docker-compose down
$DOCKER_CMD rmi $DOCKER_IMAGE_NAME 2>/dev/null || true
$DOCKER_CMD build -f $DOCKERFILE_NAME -t $DOCKER_IMAGE_NAME .
docker-compose up -d
echo "✅ Rebuild completed"
EOF

    # Make scripts executable
    chmod +x dpm-docker-*.sh
    
    print_success "Helper scripts created:"
    echo "  ./dpm-docker-start.sh   - Start and enter DPM environment"
    echo "  ./dpm-docker-stop.sh    - Stop DPM environment"
    echo "  ./dpm-docker-clean.sh   - Clean up everything"
    echo "  ./dpm-docker-rebuild.sh - Rebuild and restart"
}

show_usage() {
    print_success "🐳 DPM Docker Environment Setup Complete!"
    echo ""
    echo "📋 Available commands:"
    echo "  ./dpm-docker-start.sh   - Start and enter the DPM environment"
    echo "  ./dpm-docker-stop.sh    - Stop the DPM environment"
    echo "  ./dpm-docker-clean.sh   - Clean up containers and images"
    echo "  ./dpm-docker-rebuild.sh - Rebuild the environment"
    echo ""
    echo "🚀 Quick start:"
    echo "  1. Run: ./dpm-docker-start.sh"
    echo "  2. Inside container: dpm health"
    echo "  3. Try: dpm list --custom"
    echo "  4. Test: dpm info docker-example"
    echo ""
    echo "🔧 Development workflow:"
    echo "  - Source code is mounted from current directory"
    echo "  - Changes are reflected immediately"
    echo "  - Use 'exit' to leave container (it keeps running)"
    echo "  - Use './dpm-docker-stop.sh' to fully stop"
    echo ""
    echo "🌐 Remote testing:"
    echo "  - SSH keys are pre-generated in container"
    echo "  - Test remote connections with: dpm connect user host"
    echo ""
    echo "📦 Example packages:"
    echo "  - docker-example package is pre-installed for testing"
    echo "  - Custom prefixes include 'docker-' for container-specific packages"
    echo ""
    print_success "Ready to use! Run './dpm-docker-start.sh' to begin."
}

cleanup_on_error() {
    print_error "Installation failed. Cleaning up..."
    rm -f "$DOCKERFILE_NAME" docker-compose.yml dpm-docker-*.sh
    $DOCKER_CMD rmi "$DOCKER_IMAGE_NAME" 2>/dev/null || true
}

main() {
    print_status "🐳 Setting up DPM Docker Environment..."
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    check_docker
    create_dockerfile
    build_docker_image
    create_docker_compose
    create_helper_scripts
    show_usage
    
    print_success "🎉 DPM Docker Environment is ready!"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "DPM Docker Environment Installation Script"
        echo ""
        echo "Usage: ./install-docker.sh [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --clean        Clean up existing Docker environment"
        echo "  --rebuild      Rebuild the Docker environment"
        echo ""
        echo "This script creates a Docker environment with DPM pre-installed."
        echo "You can then use all DPM commands directly in the container."
        exit 0
        ;;
    --clean)
        print_status "🧹 Cleaning up DPM Docker environment..."
        docker-compose down -v 2>/dev/null || true
        $DOCKER_CMD rmi "$DOCKER_IMAGE_NAME" 2>/dev/null || true
        rm -f "$DOCKERFILE_NAME" docker-compose.yml dpm-docker-*.sh
        print_success "✅ Cleanup completed!"
        exit 0
        ;;
    --rebuild)
        print_status "🔄 Rebuilding DPM Docker environment..."
        ./install-docker.sh --clean
        main
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