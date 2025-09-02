#!/bin/bash
# Build example packages for Docker environment

set -e

echo "📦 Building example packages..."

cd /docker-setup/packages

# Check if packages directory exists and has content
if [ ! -d "." ] || [ -z "$(ls -A .)" ]; then
    echo "⚠️  No packages found to build"
    exit 0
fi

# Build all package directories
for pkg_dir in */; do
    if [ -d "$pkg_dir" ] && [ -f "$pkg_dir/DEBIAN/control" ]; then
        echo "Building package: $pkg_dir"
        
        # Validate control file has proper format
        if ! grep -q "^Package:" "$pkg_dir/DEBIAN/control"; then
            echo "❌ Invalid control file in $pkg_dir"
            continue
        fi
        
        # Build the package
        if dpkg-deb --build "$pkg_dir"; then
            echo "✅ Built: ${pkg_dir%/}.deb"
        else
            echo "❌ Failed to build: $pkg_dir"
        fi
    else
        echo "⚠️  Skipping $pkg_dir (missing DEBIAN/control)"
    fi
done

echo "✅ Example package building complete!"