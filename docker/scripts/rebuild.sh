#!/bin/bash
# Rebuild DPM Docker Environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🔄 Rebuilding DPM Docker Environment..."

echo "🛑 Stopping existing containers..."
docker-compose down

echo "🗑️  Removing old image..."
docker rmi dpm-environment 2>/dev/null || true

echo "🔨 Building new image..."
docker-compose build --no-cache

echo "🚀 Starting new environment..."
docker-compose up -d

echo "✅ Rebuild completed"
echo "Use './start.sh' to connect to the environment"