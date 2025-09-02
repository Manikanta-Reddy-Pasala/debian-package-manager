#!/bin/bash
# Build example packages for Docker environment

set -e

echo "📦 Building example packages..."

cd /docker-setup/packages

# Build all package directories
for pkg_dir in */; do
    if [ -d "$pkg_dir" ] && [ -f "$pkg_dir/DEBIAN/control" ]; then
        echo "Building package: $pkg_dir"
        dpkg-deb --build "$pkg_dir"
        echo "✅ Built: ${pkg_dir%/}.deb"
    fi
done

echo "✅ All example packages built!"