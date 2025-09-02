# DPM Docker Environment

This document explains how to use the Debian Package Manager (DPM) in a Docker environment for development, testing, and isolated package management.

## Quick Start

### 1. Install Docker Environment
```bash
# Create Docker environment with DPM pre-installed
./install-docker.sh

# Start and enter the environment
./dpm-docker-start.sh
```

### 2. Use DPM Commands
Once inside the container, all DPM commands work normally:
```bash
# Check system health
dpm health

# List installed packages
dpm list --custom

# View example package
dpm info docker-example

# Show configuration
dpm config --show

# Test cleanup functionality
dpm cleanup --apt-cache
```

## Docker Environment Features

### 🐳 **Pre-configured Environment**
- Ubuntu 22.04 base with all dependencies
- DPM installed and ready to use
- Example packages for testing
- SSH keys pre-generated for remote testing
- Development tools (vim, nano, git, etc.)

### 📦 **Example Packages**
- `docker-example` - Sample package for testing DPM functionality
- Custom prefixes configured including `docker-` for container-specific packages
- Removable packages list with example entries

### 🔧 **Development Ready**
- Source code mounted from host (live editing)
- Python development tools (pytest, black, isort, mypy)
- Non-root user setup for security
- Persistent volumes for user data and package cache

### 🌐 **Remote Testing**
- SSH client and keys pre-configured
- Test remote connections with `dpm connect user host`
- Full remote execution capabilities

## Management Scripts

### `./dpm-docker-start.sh`
Starts the Docker environment and drops you into an interactive shell:
```bash
./dpm-docker-start.sh
# You're now inside the container with DPM ready to use
dpm health
```

### `./dpm-docker-stop.sh`
Stops the Docker environment:
```bash
./dpm-docker-stop.sh
```

### `./dpm-docker-clean.sh`
Removes all Docker containers, images, and volumes:
```bash
./dpm-docker-clean.sh
# Confirms before deletion
```

### `./dpm-docker-rebuild.sh`
Rebuilds the Docker environment from scratch:
```bash
./dpm-docker-rebuild.sh
```

## Usage Examples

### Basic Package Management
```bash
# Inside the container
dpm list --custom                    # List custom packages
dpm info docker-example             # Show package details
dpm health --verbose                # Detailed system health
dpm config --add-prefix "test-"     # Add custom prefix
```

### Testing Remote Connections
```bash
# Connect to a remote system (if available)
dpm connect user remote-host.com --key ~/.ssh/id_rsa

# All commands now execute remotely
dpm health                          # Check remote system
dpm list --custom                   # List remote packages

# Disconnect and return to local
dpm connect --disconnect
```

### System Cleanup Testing
```bash
# Test various cleanup operations
dpm cleanup --apt-cache             # Clean APT cache
dpm cleanup --all                   # Comprehensive cleanup
dpm cleanup --all --aggressive      # Aggressive cleanup
```

### Configuration Management
```bash
# Manage removable packages
dpm config --add-removable "old-package"
dpm config --list-removable
dpm config --remove-removable "old-package"

# Manage custom prefixes
dpm config --add-prefix "company-"
dpm config --show
```

## Development Workflow

### 1. **Live Development**
- Source code is mounted from the host directory
- Changes to Python files are immediately available
- No need to rebuild container for code changes

### 2. **Testing Changes**
```bash
# Make changes to source code on host
# Inside container, test immediately:
dpm health
python3 -m pytest tests/
```

### 3. **Package Testing**
```bash
# Create test packages
mkdir -p /tmp/test-pkg/DEBIAN
# ... create package structure
dpkg-deb --build /tmp/test-pkg
dpm install /tmp/test-pkg.deb
```

## Docker Compose Configuration

The environment uses Docker Compose with:
- **Persistent volumes** for user data and APT cache
- **Network isolation** with custom bridge network
- **Environment variables** for proper terminal support
- **Volume mounts** for live development

## Troubleshooting

### Container Won't Start
```bash
# Check Docker status
docker ps -a
docker-compose logs

# Rebuild if needed
./dpm-docker-rebuild.sh
```

### Permission Issues
```bash
# The container runs as 'dpmuser' (non-root)
# For privileged operations, use sudo (no password required)
sudo dpm install some-package
```

### Network Issues
```bash
# Test network connectivity
ping google.com
curl -I https://archive.ubuntu.com

# Check DNS
nslookup archive.ubuntu.com
```

### SSH Key Issues
```bash
# SSH keys are pre-generated
ls -la ~/.ssh/
ssh-keygen -t rsa -b 2048 -f ~/.ssh/new_key -N ""
```

## Advanced Usage

### Custom Package Creation
```bash
# Create a custom package for testing
mkdir -p /tmp/my-package-1.0.0/DEBIAN
cat > /tmp/my-package-1.0.0/DEBIAN/control << EOF
Package: docker-my-package
Version: 1.0.0
Architecture: all
Maintainer: Test User
Description: My custom test package
EOF

# Build and install
dpkg-deb --build /tmp/my-package-1.0.0
sudo dpm install /tmp/my-package-1.0.0.deb
```

### Multi-Container Testing
```bash
# Start multiple containers for remote testing
docker run -d --name dpm-remote -p 2222:22 dpm-environment
# Configure SSH and test remote connections
```

### Performance Testing
```bash
# Test with large package lists
time dpm list
time dpm health --verbose
```

## Benefits of Docker Environment

1. **🔒 Isolation**: No impact on host system
2. **🔄 Reproducible**: Consistent environment across machines
3. **🧪 Safe Testing**: Test dangerous operations safely
4. **🚀 Quick Setup**: Ready to use in minutes
5. **🔧 Development**: Live code editing with immediate testing
6. **🌐 Remote Testing**: Test SSH connections without real servers
7. **📦 Package Testing**: Create and test packages safely

## Cleanup

To completely remove the Docker environment:
```bash
./dpm-docker-clean.sh
rm -f Dockerfile.dpm docker-compose.yml dpm-docker-*.sh
```

This removes all containers, images, volumes, and helper scripts.