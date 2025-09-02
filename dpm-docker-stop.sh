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
