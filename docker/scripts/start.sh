#!/bin/bash
# Start DPM Docker Environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🐳 Starting DPM Docker Environment..."

# Check if container is already running
if docker-compose ps | grep -q "dpm-dev.*Up"; then
    echo "✅ Container is already running"
else
    echo "🚀 Starting container..."
    docker-compose up -d
    
    # Wait for container to be ready
    echo "⏳ Waiting for container to be ready..."
    sleep 3
    
    # Build example packages inside container
    echo "📦 Building example packages..."
    docker-compose exec dpm-environment bash -c "
        cd /tmp/example-packages && 
        dpkg-deb --build docker-example-1.0.0 && 
        dpkg -i docker-example-1.0.0.deb
    " || echo "⚠️  Package building failed, continuing..."
fi

echo "🔗 Connecting to DPM environment..."
echo "   Use 'exit' to leave the container (it will keep running)"
echo "   Use './stop.sh' to fully stop the environment"
echo ""

docker-compose exec dpm-environment /bin/bash

echo "👋 Exited DPM environment"