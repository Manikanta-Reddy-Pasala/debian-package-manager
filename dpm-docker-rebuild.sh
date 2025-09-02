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
$COMPOSE_CMD down

echo "🗑️  Removing old image..."
docker rmi dpm-environment 2>/dev/null || true

echo "🔨 Building new image..."
$COMPOSE_CMD build --no-cache

echo "🚀 Starting new environment..."
$COMPOSE_CMD up -d

echo "✅ Rebuild completed"
echo "Use './dpm-docker-start.sh' to connect to the environment"
