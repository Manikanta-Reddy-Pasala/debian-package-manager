#!/bin/bash
# Clean DPM Docker Environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🧹 Cleaning DPM Docker Environment..."
echo "This will remove containers, images, and volumes"
read -p "Are you sure? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing containers and volumes..."
    docker-compose down -v
    
    echo "🗑️  Removing Docker image..."
    docker rmi dpm-environment 2>/dev/null || true
    
    echo "🧹 Running Docker system cleanup..."
    docker system prune -f
    
    echo "✅ Cleanup completed"
else
    echo "❌ Cleanup cancelled"
fi