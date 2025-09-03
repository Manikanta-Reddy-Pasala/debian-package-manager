#!/bin/bash
# Start DPM Docker Environment

set -e

echo "Starting DPM Docker Environment..."

# Detect Docker Compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Docker Compose not found"
    exit 1
fi

# Change to docker directory
cd docker

# Check if container is already running
if $COMPOSE_CMD ps | grep -q "dpm-dev.*Up"; then
    echo "Container is already running"
else
    echo "Starting container..."
    $COMPOSE_CMD up -d
    
    # Wait for container to be ready
    echo "Waiting for container to be ready..."
    sleep 3
    
    echo "Container started successfully!"
fi

# Check if we should enter interactive mode or just start
if [[ "${1:-}" == "--start-only" ]]; then
    echo "DPM Docker environment is running!"
    echo "   Connect using: ./dpm-docker-start.sh"
    exit 0
fi

echo "Connecting to DPM environment..."
echo "   Use 'exit' to leave the container (it will keep running)"
echo "   Use './dpm-docker-stop.sh' to fully stop the environment"
echo ""
echo "Quick start commands:"
echo "   dpm health          # Check system status"
echo "   dpm mode --status   # Check current mode"
echo "   dpm list            # List custom packages"
echo "   dpm list --all      # List all packages"
echo "   Tab completion is available! Try: dpm <TAB><TAB>"
echo ""

$COMPOSE_CMD exec dpm-environment /bin/bash

echo "Exited DPM environment"