#!/bin/bash
# Build script for Debian Metapackage Manager

set -e

echo "Building Debian Metapackage Manager..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Building with uv..."
    uv build
else
    echo "uv not found, using pip and build..."
    python3 -m pip install build
    python3 -m build
fi

echo "✅ Build completed!"
echo "Distribution files are in the 'dist/' directory"

# List the built files
echo ""
echo "Built files:"
ls -la dist/