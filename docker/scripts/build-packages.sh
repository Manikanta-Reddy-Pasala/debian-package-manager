#!/bin/bash
# Build example packages for Docker environment

set -e

cd /tmp/example-packages

# Build docker-example package
if [ -d "docker-example-1.0.0" ]; then
    echo "Building docker-example package..."
    dpkg-deb --build docker-example-1.0.0
    echo "✅ docker-example package built successfully"
else
    echo "❌ docker-example source directory not found"
fi

# List built packages
echo ""
echo "📦 Available packages:"
ls -la *.deb 2>/dev/null || echo "No .deb packages found"