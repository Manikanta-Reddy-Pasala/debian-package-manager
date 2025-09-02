#!/bin/bash
# Docker Installation Script for Debian Package Manager
# This script sets up a Docker environment with DPM pre-installed and ready to use.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install docker.io docker-compose"
        echo "  Or visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check for Docker Compose (both standalone and plugin versions)
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
        echo "  Or install Docker Desktop which includes the plugin version"
        echo "  Or visit: https://docs.docker.com/compose/install/"
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
        COMPOSE_CMD="sudo $COMPOSE_CMD"
    else
        DOCKER_CMD="docker"
        # COMPOSE_CMD is already set above
    fi
    
    print_success "Docker is available and running"
    print_status "Using Docker Compose command: $COMPOSE_CMD"
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
    print_status "Creating wrapper scripts..."
    
    # Detect which Docker Compose command to use
    local compose_cmd=""
    if command -v docker-compose &> /dev/null; then
        compose_cmd="docker-compose"
    elif docker compose version &> /dev/null; then
        compose_cmd="docker compose"
    else
        compose_cmd="docker-compose"  # fallback
    fi
    
    # Create main start script
    cat > dpm-docker-start.sh << EOF
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
if \$COMPOSE_CMD ps | grep -q "dpm-dev.*Up"; then
    echo "✅ Container is already running"
else
    echo "🚀 Starting container..."
    \$COMPOSE_CMD up -d
    
    # Wait for container to be ready
    echo "⏳ Waiting for container to be ready..."
    sleep 3
fi

echo "🔗 Connecting to DPM environment..."
echo "   Use 'exit' to leave the container (it will keep running)"
echo "   Use './dpm-docker-stop.sh' to fully stop the environment"
echo ""

\$COMPOSE_CMD exec dpm-environment /bin/bash

echo "👋 Exited DPM environment"
EOF

    # Create stop script
    cat > dpm-docker-stop.sh << EOF
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
\$COMPOSE_CMD down

echo "✅ DPM Docker environment stopped"
EOF

    # Create clean script
    cat > dpm-docker-clean.sh << EOF
#!/bin/bash
# Clean DPM Docker Environment

set -e

echo "🧹 Cleaning DPM Docker Environment..."
echo "This will remove containers, images, and volumes"
read -p "Are you sure? (y/N): " -n 1 -r
echo

if [[ \$REPLY =~ ^[Yy]\$ ]]; then
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
    echo "🗑️  Removing containers and volumes..."
    \$COMPOSE_CMD down -v
    
    echo "🗑️  Removing Docker image..."
    docker rmi dpm-environment 2>/dev/null || true
    
    echo "🧹 Running Docker system cleanup..."
    docker system prune -f
    
    echo "✅ Cleanup completed"
else
    echo "❌ Cleanup cancelled"
fi
EOF

    # Create rebuild script
    cat > dpm-docker-rebuild.sh << EOF
#!/bin/bash
# Rebuild DPM Docker Environment

set -e

echo "🔄 Rebuilding DPM Docker Environment..."

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

echo "🛑 Stopping existing containers..."
\$COMPOSE_CMD down

echo "🗑️  Removing old image..."
docker rmi dpm-environment 2>/dev/null || true

echo "🔨 Building new image..."
\$COMPOSE_CMD build --no-cache

echo "🚀 Starting new environment..."
\$COMPOSE_CMD up -d

echo "✅ Rebuild completed"
echo "Use './dpm-docker-start.sh' to connect to the environment"
EOF

    # Make scripts executable
    chmod +x dpm-docker-*.sh
    
    print_success "Wrapper scripts created in project root"
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
    echo "  3. Try: dpm mode --status"
    echo "  4. Test: dpm install --online <package>"
    echo "  5. Test: dpm install --offline <package>"
    echo ""
    echo "🔧 Development workflow:"
    echo "  - Source code is mounted from current directory"
    echo "  - Changes are reflected immediately in container"
    echo "  - Use 'exit' to leave container (it keeps running)"
    echo "  - Use './dpm-docker-stop.sh' to fully stop"
    echo ""
    echo "🌐 Mode testing:"
    echo "  - Test online mode: dpm install --online <package>"
    echo "  - Test offline mode: dpm install --offline <package>"
    echo "  - Check status: dpm mode --status"
    echo "  - Auto-detect: dpm mode --auto"
    echo ""
    echo "🔗 Remote testing:"
    echo "  - SSH keys are pre-generated in container"
    echo "  - Test remote connections with: dpm connect user host"
    echo "  - Return to local: dpm connect --disconnect"
    echo ""
    echo "📦 Example packages:"
    echo "  - docker-example package is pre-built for testing"
    echo "  - Custom prefixes include 'docker-' for container-specific packages"
    echo ""
    print_success "Ready to use! Run './dpm-docker-start.sh' to begin."
}

main() {
    print_status "🐳 Setting up DPM Docker Environment..."
    
    check_docker
    check_docker_structure
    build_docker_environment
    create_wrapper_scripts
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
        echo ""
        echo "The Docker environment uses organized files from 'docker/' directory:"
        echo "  docker/Dockerfile           - Main container definition"
        echo "  docker/docker-compose.yml   - Container orchestration"
        echo "  docker/config/              - DPM configuration files"
        echo "  docker/packages/            - Example packages"
        echo "  docker/scripts/             - Setup and build scripts"
        echo "  docker/bashrc-additions     - Shell environment setup"
        exit 0
        ;;
    --clean)
        print_status "🧹 Cleaning up DPM Docker environment..."
        cd docker 2>/dev/null || true
        
        # Try both Docker Compose versions
        if command -v docker-compose &> /dev/null; then
            docker-compose down -v 2>/dev/null || true
        elif docker compose version &> /dev/null; then
            docker compose down -v 2>/dev/null || true
        fi
        
        docker rmi dpm-environment 2>/dev/null || true
        cd .. 2>/dev/null || true
        rm -f dpm-docker-*.sh
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