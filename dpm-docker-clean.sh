#!/bin/bash
# Clean DPM Docker Environment

set -e

echo "🧹 Cleaning DPM Docker Environment..."
echo "This will remove containers, images, and volumes"
read -p "Are you sure? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
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
    $COMPOSE_CMD down -v
    
    echo "🗑️  Removing Docker image..."
    docker rmi dpm-environment 2>/dev/null || true
    
    echo "🧹 Running Docker system cleanup..."
    docker system prune -f
    
    echo "✅ Cleanup completed"
else
    echo "❌ Cleanup cancelled"
fi
