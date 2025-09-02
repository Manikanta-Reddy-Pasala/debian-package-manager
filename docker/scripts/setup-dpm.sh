#!/bin/bash
# Setup script for DPM in Docker container

set -e

echo "🔧 Setting up DPM environment..."

# Install DPM in development mode
cd /workspace
pip install -e .

# Create necessary directories
mkdir -p /root/.dpm
mkdir -p /var/cache/dpm

# Copy configuration files
cp -r /docker-setup/config/* /root/.dpm/ 2>/dev/null || true

# Set up SSH for remote testing
mkdir -p /root/.ssh
ssh-keygen -t rsa -b 2048 -f /root/.ssh/id_rsa -N "" -q
chmod 600 /root/.ssh/id_rsa
chmod 644 /root/.ssh/id_rsa.pub

# Install example packages
if [ -d "/docker-setup/packages" ]; then
    echo "📦 Installing example packages..."
    for deb in /docker-setup/packages/*.deb; do
        if [ -f "$deb" ]; then
            dpkg -i "$deb" 2>/dev/null || true
        fi
    done
fi

# Fix any broken packages
apt-get install -f -y 2>/dev/null || true

echo "✅ DPM environment setup complete!"
echo "🚀 Ready to use DPM commands"