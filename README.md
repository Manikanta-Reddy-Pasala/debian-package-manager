<!-- @format -->

# Debian Package Manager

Intelligent package management for custom Debian package systems with offline/online mode support and advanced dependency resolution.

## Features

- **Dual Mode Operation**: Support for both offline (pinned versions) and online/artifactory modes
- **Intelligent Dependency Resolution**: Advanced conflict detection and resolution with user confirmation
- **Custom Package Recognition**: Configurable prefixes for identifying custom packages
- **Removable Packages Management**: JSON-based configuration for packages that can be safely removed during conflicts
- **Enhanced System Cleanup**: Comprehensive cleanup functionality for APT cache, offline repositories, and artifactory
- **Remote System Execution**: SSH-based remote package management across multiple systems
- **Force Operations**: Safe force installation/removal with comprehensive user confirmation
- **System Health Monitoring**: Built-in health checks and automatic system repair
- **Standalone Executable**: Works without system Python dependencies
- **Comprehensive CLI**: Full-featured command-line interface with detailed help

## Installation

### Quick Install (Recommended)

```bash
# Download and run the installation script
sudo ./install.sh
```

### Docker Environment (Isolated Testing)

```bash
# Create Docker environment with DPM pre-installed
./install-docker.sh

# Start and use DPM in container
./dpm-docker-start.sh
```

**Benefits of Docker Installation:**

- 🔒 **Isolated Environment**: No impact on host system
- 🧪 **Safe Testing**: Test dangerous operations safely
- 🚀 **Quick Setup**: Ready to use in minutes with example packages
- 🔧 **Development Ready**: Live code editing with immediate testing
- 🌐 **Remote Testing**: Test SSH connections in controlled environment
- 📦 **Organized Structure**: All Docker files properly organized in docker/ directory

**Docker Structure:**

```
docker/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Orchestration config
├── config/                 # DPM configuration files
├── packages/               # Example packages
├── scripts/                # Setup and build scripts
└── bashrc-additions        # Shell environment setup
```

See [DOCKER.md](DOCKER.md) for detailed Docker usage instructions.

### Manual Installation from Source

```bash
# Clone the repository
git clone https://github.com/example/debian-package-manager.git
cd debian-package-manager

# Install system dependencies
sudo apt update
sudo apt install python3-venv python3-apt

# Run installation script
sudo ./install.sh
```

### Development Installation

```bash
# Clone and install in development mode
git clone https://github.com/example/debian-package-manager.git
cd debian-package-manager

# Create virtual environment and install
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### System Requirements

- **Operating System**: Ubuntu 18.04+ or Debian 10+
- **Python**: 3.8 or higher
- **Privileges**: Root access required for package operations
- **Dependencies**: `apt`, `dpkg`, `python3-apt`

## Recent Fixes & Improvements

### Fixed Issues

- ✅ **--online mode**: Fixed missing `--online` option in install command
- ✅ **Offline mode detection**: Improved logic to prevent false offline mode when internet is available
- ✅ **Docker structure**: Reorganized Docker files into proper directory structure
- ✅ **Mode switching**: Enhanced mode switching with proper validation and user feedback

### Enhanced Features

- 🔧 **Mode Management**: Better online/offline mode detection and switching
- 📦 **Docker Environment**: Organized file structure with dedicated scripts and configuration
- 🌐 **Network Detection**: Improved network and repository accessibility checks
- 🚀 **Installation Options**: Both `--online` and `--offline` flags now work correctly

## Quick Start

```bash
# Basic package operations
dpm install mycompany-dev-tools     # Install a custom package
dpm remove old-package              # Remove a package
dpm info vim                        # Show package information
dpm list --custom                   # List custom packages

# System maintenance
dpm health                          # Check system health
dpm fix                            # Fix broken packages

# Configuration
dpm config --show                   # Show current settings
dpm mode --status                   # Check offline/online mode
```

## Detailed Usage

### Package Operations

```bash
# Install packages
dpm install <package-name>                    # Standard installation
dpm install <package-name> --version 1.2.3   # Install specific version
dpm install <package-name> --version 1.2.3 --force # Force install specific version with conflicts

# Remove packages
dpm remove <package-name>                     # Standard removal
dpm remove <package-name> --force            # Force remove with dependencies
dpm remove <package-name> --purge            # Remove with config files

# Package information
dpm info <package-name>                       # Basic package info
dpm info <package-name> --dependencies       # Include dependency tree
```

### System Management

```bash
# List packages
dpm list                           # All installed packages
dpm list --custom                  # Only custom packages
dpm list --metapackages           # Only metapackages
dpm list --broken                 # Only broken packages

# System health and maintenance
dpm health                        # Basic health check
dpm health --verbose              # Detailed health information
dpm fix                          # Fix broken packages
dpm fix --force                  # Aggressive fixing methods
```

### Configuration Management

```bash
# View configuration
dpm config --show                           # Show all settings

# Manage custom prefixes
dpm config --add-prefix "newcompany-"       # Add custom prefix
dpm config --remove-prefix "oldcompany-"    # Remove prefix

# Manage removable packages
dpm config --add-removable "old-library"    # Add package to removable list
dpm config --remove-removable "old-lib"     # Remove from removable list
dpm config --list-removable                 # List all removable packages

# Mode settings
dpm config --set-offline                    # Enable offline mode
dpm config --set-online                     # Enable online mode
dpm mode --status                           # Check current mode status
dpm mode --online                           # Switch to online mode
dpm mode --offline                          # Switch to offline mode
dpm mode --auto                             # Auto-detect appropriate mode
```

### System Cleanup and Maintenance

```bash
# Comprehensive cleanup
dpm cleanup --all                           # Full system cleanup
dpm cleanup --all --aggressive              # Aggressive cleanup

# Specific cleanup operations
dpm cleanup --apt-cache                     # Clean APT package cache
dpm cleanup --offline-repos                 # Clean offline repository caches
dpm cleanup --artifactory                   # Clean artifactory cache
```

### Remote System Management

```bash
# Connect to remote system (all subsequent commands execute remotely)
dpm connect user 10.0.1.5                  # Connect via SSH
dpm connect user host.com --key ~/.ssh/id_rsa --port 2222

# Check connection status
dpm connect                                 # Show current connection status

# All regular DPM commands now execute on the remote system
dpm install my-package                      # Install on remote system
dpm remove old-package                      # Remove from remote system
dpm list --custom                           # List remote packages
dpm health                                  # Check remote system health
dpm config --add-prefix "company-"         # Configure remote system
dpm cleanup --all                           # Clean remote system

# Disconnect and return to local execution
dpm connect --disconnect                    # Return to local execution
```

**Key Benefits of Connection State Approach:**

- **Seamless Experience**: No need to prefix every command with `remote exec`
- **Consistent Interface**: All DPM commands work the same way locally and remotely
- **Clear Context**: Always know if you're operating locally or remotely
- **Simple Switching**: Easy to switch between local and remote execution

### Mode Management

```bash
# Check current mode
dpm mode --status                  # Show detailed mode status

# Switch modes
dpm mode --offline                 # Switch to offline mode (pinned versions)
dpm mode --online                  # Switch to online mode (latest versions)
dpm mode --auto                    # Auto-detect appropriate mode
```

## Configuration

The system uses a hierarchical configuration approach:

### Configuration Files

- **System Config**: `/etc/debian-package-manager/config.json`
- **User Config**: `~/.config/debian-package-manager/config.json`

### Configuration Options

```json
{
  "custom_prefixes": [
    "mycompany-",
    "internal-",
    "custom-",
    "dev-",
    "local-",
    "meta-",
    "bundle-"
  ],
  "removable_packages": [
    "old-library",
    "deprecated-tool",
    "temp-package",
    "test-package"
  ],
  "offline_mode": false,
  "pinned_versions": {
    "mycompany-core": "1.2.3",
    "internal-utils": "2.1.0"
  },
  "force_confirmation_required": true,
  "auto_resolve_conflicts": true
}
```

### Removable Packages Configuration

The `removable_packages` list allows you to specify packages that can be safely removed during conflict resolution, even if they don't match your custom prefixes:

```bash
# Add packages that can be removed during conflicts
dpm config --add-removable "old-library"
dpm config --add-removable "deprecated-service"

# View all removable packages
dpm config --list-removable

# Remove from removable list
dpm config --remove-removable "old-library"
```

**Important**: System-critical packages (like `libc6`, `bash`, `systemd`, etc.) cannot be added to the removable list for safety.

### Custom Package Prefixes

Configure prefixes to identify your organization's packages:

```bash
# Add prefixes for your packages
dpm config --add-prefix "acme-"
dpm config --add-prefix "internal-"

# These packages will now be recognized as custom:
# acme-dev-tools, internal-database, etc.
```

### Conflict Resolution Policy

Configure how the system handles package conflicts:

```bash
# View current conflict resolution settings
dpm config --show

# Block system package removal (SAFE - recommended)
dpm config --block-system-removal

# Allow system package removal (DANGEROUS - use with caution)
dpm config --allow-system-removal

# Add packages to protected list (never removed)
dpm config --add-protected "critical-service"
dpm config --add-protected "mycompany-database"

# Remove packages from protected list
dpm config --remove-protected "old-package"
```

### Safety Features

The system includes several safety features to protect your system:

- **System Package Protection**: By default, system packages cannot be removed during conflict resolution
- **Custom Package Preference**: When resolving conflicts, custom packages are preferred for removal over system packages
- **Protected Package List**: Critical packages are protected from removal
- **Risk Assessment**: All operations are categorized by risk level with appropriate warnings

## Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

## A

dvanced Usage

### Configuration

```bash
# Show current configuration
dpm config --show

# Add custom package prefix
dpm config --add-prefix "mycompany-"

# Switch to offline mode
dpm config --set-offline
```

### Mode Management

```bash
# Check current mode
dpm mode --status

# Switch modes
dpm mode --offline    # Use pinned versions
dpm mode --online     # Use latest versions
dpm mode --auto       # Auto-detect best mode
```

### System Maintenance

```bash
# Check system health
dpm health --verbose

# Fix broken packages
dpm fix --force

# List packages by type
dpm list --custom      # Show only custom packages
dpm list --broken      # Show broken packages
```

## Architecture

The tool consists of several key components:

- **CLI Layer**: User interface and command parsing
- **Package Engine**: Core orchestration and business logic
- **Dependency Resolver**: Complex dependency resolution with conflict handling
- **Mode Manager**: Offline/online mode switching and version management
- **Conflict Handler**: User interaction for conflict resolution
- **APT/DPKG Interfaces**: Low-level package system interaction

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `python -m pytest`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Report issues: [GitHub Issues](https://github.com/example/debian-package-manager/issues)
- Documentation: [Wiki](https://github.com/example/debian-package-manager/wiki)
- Discussions: [GitHub Discussions](https://github.com/example/debian-package-manager/discussions)
