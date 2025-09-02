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
