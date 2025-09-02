# DPM Docker Environment

This directory contains all the files needed to create a Docker-based development and testing environment for the Debian Package Manager (DPM).

## Directory Structure

```
docker/
├── Dockerfile              # Main container definition
├── docker-compose.yml      # Container orchestration
├── README.md              # This file
├── config/                # DPM configuration files
│   └── config.json        # System-wide DPM configuration
├── packages/              # Example packages for testing
│   └── docker-example-1.0.0/  # Example package source
│       ├── DEBIAN/
│       │   └── control    # Package metadata
│       └── usr/local/bin/
│           └── docker-example  # Example executable
└── scripts/               # Helper scripts for container management
    ├── build-packages.sh  # Build example packages
    ├── start.sh          # Start container and enter shell
    ├── stop.sh           # Stop container
    ├── clean.sh          # Clean up everything
    └── rebuild.sh        # Rebuild container
```

## Quick Start

From the project root directory:

```bash
# Build and start the Docker environment
./install-docker.sh

# Start and enter the container
./dpm-docker-start.sh

# Inside the container, test DPM
dpm health
dpm mode --status
dpm list --custom
dpm info docker-example
```

## Container Features

### 🐳 **Base Environment**
- **Ubuntu 22.04** with all DPM dependencies
- **Python 3.10+** with pip and venv
- **Development tools**: vim, nano, git, htop, tree, jq
- **Package tools**: apt, dpkg, dpkg-dev

### 👤 **User Setup**
- **Non-root user**: `dpmuser` with sudo privileges
- **Home directory**: `/home/dpmuser`
- **SSH keys**: Pre-generated for remote testing
- **Shell**: Bash with helpful aliases and welcome message

### 📦 **DPM Installation**
- **Source code**: Mounted from host at `/opt/debian-package-manager`
- **Installation**: DPM installed in development mode
- **Executable**: Available as `dpm` system-wide
- **Configuration**: Pre-configured with example settings

### 🔧 **Development Features**
- **Live editing**: Source code changes reflected immediately
- **Testing tools**: pytest, black, isort, mypy included
- **Persistent data**: User data and package cache preserved
- **Network access**: Full internet connectivity for online mode testing

## Configuration Files

### `config/config.json`
System-wide DPM configuration with:
- Custom prefixes including `docker-` for container-specific packages
- Removable packages list with examples
- Online mode enabled by default
- Example pinned versions

### `packages/docker-example-1.0.0/`
Example package demonstrating:
- Proper Debian package structure
- Custom prefix usage (`docker-`)
- Simple executable for testing
- Package metadata in `DEBIAN/control`

## Usage Examples

### Basic DPM Testing
```bash
# Inside container
dpm health --verbose          # Check system health
dpm mode --status            # Check current mode
dpm mode --online            # Switch to online mode
dpm mode --offline           # Switch to offline mode
dpm list --custom            # List custom packages
dpm info docker-example      # Show example package info
```

### Package Management Testing
```bash
# Test package operations
dpm remove docker-example    # Remove example package
dpm install /tmp/example-packages/docker-example-1.0.0.deb  # Reinstall
```

### Remote Connection Testing
```bash
# Test remote connection functionality
dpm connect                  # Show connection status
# dpm connect user remote-host.com --key ~/.ssh/id_rsa  # Connect to remote
# dpm health                 # Execute on remote
# dpm connect --disconnect   # Return to local
```

### Cleanup Testing
```bash
# Test cleanup functionality
dpm cleanup --apt-cache      # Clean APT cache
dpm cleanup --all           # Comprehensive cleanup
```

## Development Workflow

### 1. **Edit Code on Host**
```bash
# On host machine
vim src/debian_metapackage_manager/cli.py
```

### 2. **Test Immediately in Container**
```bash
# Inside container
dpm health  # Uses updated code immediately
```

### 3. **Run Tests**
```bash
# Inside container
python3 -m pytest tests/
black src/
isort src/
mypy src/
```

### 4. **Create Test Packages**
```bash
# Inside container
mkdir -p /tmp/test-pkg/DEBIAN
cat > /tmp/test-pkg/DEBIAN/control << EOF
Package: docker-test-pkg
Version: 1.0.0
Architecture: all
Description: Test package
EOF

dpkg-deb --build /tmp/test-pkg
dpm install /tmp/test-pkg.deb
```

## Container Management

### Using Docker Compose (from docker/ directory)
```bash
cd docker

# Start container
docker-compose up -d

# Enter container
docker-compose exec dpm-environment /bin/bash

# Stop container
docker-compose down

# View logs
docker-compose logs

# Rebuild
docker-compose build --no-cache
```

### Using Helper Scripts (from project root)
```bash
# Start and enter
./dpm-docker-start.sh

# Stop
./dpm-docker-stop.sh

# Clean up everything
./dpm-docker-clean.sh

# Rebuild
./dpm-docker-rebuild.sh
```

## Troubleshooting

### Container Won't Start
```bash
# Check Docker status
docker ps -a
cd docker && docker-compose logs

# Rebuild if needed
./dpm-docker-rebuild.sh
```

### Package Installation Issues
```bash
# Inside container, check package status
dpkg -l | grep docker-example
apt list --installed | grep docker

# Rebuild example package
cd /tmp/example-packages
dpkg-deb --build docker-example-1.0.0
dpkg -i docker-example-1.0.0.deb
```

### Network/Mode Issues
```bash
# Test network connectivity
ping google.com
curl -I https://archive.ubuntu.com

# Check DPM mode detection
dpm mode --status
dpm mode --online
dpm health --verbose
```

### Permission Issues
```bash
# Inside container, use sudo for privileged operations
sudo dpm install some-package
sudo apt update
```

## Customization

### Adding Custom Packages
1. Create package structure in `packages/`
2. Build with `dpkg-deb --build`
3. Copy to container or rebuild image

### Modifying Configuration
1. Edit `config/config.json`
2. Rebuild container to apply changes
3. Or modify inside running container for testing

### Adding Development Tools
1. Edit `Dockerfile` to add packages
2. Rebuild image with `./dpm-docker-rebuild.sh`

## Benefits

- **🔒 Isolation**: No impact on host system
- **🧪 Safe Testing**: Test dangerous operations safely
- **🚀 Quick Setup**: Ready in minutes
- **🔄 Reproducible**: Consistent across machines
- **🔧 Development**: Live code editing
- **🌐 Network Testing**: Test online/offline modes
- **📦 Package Testing**: Create and test packages safely