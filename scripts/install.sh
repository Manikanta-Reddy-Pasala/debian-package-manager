#!/bin/bash
# Installation script for Debian Metapackage Manager

set -e

echo "Installing Debian Metapackage Manager..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if running on Ubuntu/Debian
if ! command -v apt-get &> /dev/null; then
    echo "Warning: This tool is designed for Ubuntu/Debian systems"
fi

# Install the package
echo "Installing with uv..."
uv tool install debian-metapackage-manager

# Verify installation
if command -v dpm &> /dev/null; then
    echo "✅ Installation successful!"
    echo "You can now use 'dpm' command"
    echo ""
    echo "Examples:"
    echo "  dpm install mycompany-dev-tools"
    echo "  dpm remove old-package --force"
    echo "  dpm health"
    echo "  dpm --help"
else
    echo "❌ Installation failed. Please check the output above for errors."
    exit 1
fi