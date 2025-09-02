# Debian Package Manager

Intelligent package management for custom Debian package systems with offline/online mode support and advanced dependency resolution.

## Features

- **Dual Mode Operation**: Support for both offline (pinned versions) and online/artifactory modes
- **Intelligent Dependency Resolution**: Advanced conflict detection and resolution with user confirmation
- **Custom Package Recognition**: Configurable prefixes for identifying custom/metapackages
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

## Quick Start

```bash
# Basic package operations
dpm install mycompany-dev-tools     # Install a metapackage
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
dpm install <package-name> --force           # Force install with conflicts
dpm install <package-name> --offline         # Use offline mode
dpm install <package-name> --version 1.2.3   # Install specific version

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

# Mode settings
dpm config --set-offline                    # Enable offline mode
dpm config --set-online                     # Enable online mode
```

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
- **System Config**: `/etc/debian-metapackage-manager/config.json`
- **User Config**: `~/.config/debian-metapackage-manager/config.json`

### Configuration Options
```json
{
    "package_prefixes": {
        "custom_prefixes": [
            "mycompany-",
            "custom-",
            "meta-"
        ]
    },
    "offline_mode": false,
    "version_pinning": {
        "mycompany-dev-tools": "1.2.3",
        "custom-database": "2.1.0"
    }
}
```

### Custom Package Prefixes
Configure prefixes to identify your organization's packages:
```bash
# Add prefixes for your packages
dpm config --add-prefix "acme-"
dpm config --add-prefix "internal-"

# These packages will now be recognized as custom:
# acme-dev-tools, internal-database, etc.
```

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