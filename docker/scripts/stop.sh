#!/bin/bash
# Stop DPM Docker Environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🛑 Stopping DPM Docker Environment..."
docker-compose down

echo "✅ DPM Docker environment stopped"