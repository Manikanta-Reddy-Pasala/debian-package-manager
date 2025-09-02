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

The Debian Package Manager supports two installation modes through a unified installer:

### 🖥️ Local Installation (Production)

Install DPM directly on your system for production use:

```bash
# Install locally (requires sudo)
sudo ./install.sh --local

# Uninstall if needed
sudo ./install.sh --local --uninstall
```

**Features included:**
- System-wide `dpm` command
- Bash autocomplete for all commands and arguments
- Default configuration
- Full package management capabilities

**Requirements:**
- Ubuntu 18.04+ or Debian 10+
- Python 3.8+
- Root privileges (sudo)
- `apt`, `dpkg`, `python3-apt`

### 🐳 Docker Environment (Development)

Set up an isolated Docker environment for development and testing:

```bash
# Set up Docker environment (auto-starts container)
./install.sh --docker

# Connect to running environment
./dpm-docker-start.sh

# Stop the environment when done
./dpm-docker-stop.sh
```

**Features included:**
- Isolated development environment
- Bash autocomplete pre-configured
- Example packages for testing
- SSH keys for remote testing
- Live code editing support

**Requirements:**
- Docker and Docker Compose
- No root privileges needed
- Isolated from host system

**Benefits of Docker Mode:**
- 🔒 **Safe Testing**: Isolated environment with no impact on host
- 🧪 **Development Ready**: Live code editing with immediate testing
- 📦 **Pre-configured**: Example packages and SSH keys included
- 🚀 **Quick Setup**: Ready to use in minutes
- ⚡ **Auto-start**: Container starts automatically during setup

### ⌨️ Autocomplete Support

Both installation modes include comprehensive bash autocomplete:

- **Commands**: Tab completion for all DPM commands (`install`, `remove`, `list`, etc.)
- **Options**: Tab completion for command-line flags (`--version`, `--force`, `--all`, etc.)
- **Package Names**: Tab completion for available and installed packages
- **SSH Options**: Tab completion for connection parameters

```bash
# Try autocomplete after installation
dpm <TAB><TAB>              # Shows all available commands
dpm install <TAB><TAB>      # Shows available packages
dpm remove <TAB><TAB>       # Shows installed packages
dpm list --<TAB><TAB>       # Shows available options
```

### Installation Help

```bash
# Show installation options
./install.sh --help

# Quick help
./install.sh              # Shows usage information
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

## Available Commands

After installation, DPM provides the following commands:

### Package Management
```bash
dpm install <package>              # Install a package  
dpm install <package> --version X  # Install specific version
dpm install <package> --force      # Force installation
dpm remove <package>               # Remove a package
dpm info <package>                 # Show package information
```

### Package Listing
```bash
dpm list                          # List custom packages (default)
dpm list --all                    # List all installed packages
dpm list --metapackages          # List only metapackages
dpm list --broken                # List broken packages
dpm list --simple                # Simple list format
```

### System Management
```bash
dpm health                        # Check system health
dpm fix                          # Fix broken packages
dpm cleanup --all                # Clean up system
dpm mode --status                # Check current mode
dpm mode --offline|--online      # Switch modes (enables/disables Artifactory)
```

### Remote Management
```bash
dpm connect <user> <host>        # Connect to remote system
dpm connect                      # Show connection status
dpm connect --disconnect         # Disconnect from remote
```

### Help and Information
```bash
dpm --help                       # Show all available commands
dpm <command> --help             # Show help for specific command
```

## Quick Start

### Local Installation
```bash
# Install DPM locally
sudo ./install.sh --local

# Basic usage with autocomplete
dpm install mycompany-dev-tools   # Install custom package
dpm list                          # List custom packages  
dpm health                        # Check system health

# Use tab completion
dpm <TAB><TAB>                    # Show all commands
dpm install <TAB><TAB>            # Show available packages
```

### Docker Environment
```bash
# Set up Docker environment (auto-starts)
./install.sh --docker

# Connect to running container
./dpm-docker-start.sh

# Inside container - test DPM with autocomplete
dpm health                        # Check system
dpm list --all                    # List all packages
dpm mode --status                 # Check mode
dpm <TAB><TAB>                    # Try tab completion
```

## Detailed Usage

### Package Operations

```bash
# Install packages
dpm install <package-name>                    # Standard installation
dpm install <package-name> --version 1.2.3   # Install specific version
dpm install <package-name> --version 1.2.3 --force # Force install with impact analysis and confirmation

# Remove packages
dpm remove <package-name>                     # Standard removal
dpm remove <package-name> --force            # Force remove with impact analysis and confirmation
dpm remove <package-name> --purge            # Remove with config files

# Package information
dpm info <package-name>                       # Basic package info
dpm info <package-name> --dependencies       # Include dependency tree
```

### Package Listing

```bash
# List packages (custom prefixes by default)
dpm list                          # Custom packages only (default)
dpm list --all                    # All installed packages
dpm list --metapackages          # Only metapackages
dpm list --broken                # Only broken packages
dpm list --simple                # Simple list format (no table)
```

### System Health and Maintenance

```bash
# System health checks
dpm health                        # Basic health check
dpm health --verbose              # Detailed health information

# System repair
dpm fix                          # Fix broken packages
dpm fix --force                  # Aggressive fixing methods

# System cleanup
dpm cleanup --all                # Comprehensive cleanup
dpm cleanup --apt-cache          # Clean APT cache only
dpm cleanup --offline-repos      # Clean offline repositories
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
dpm cleanup --all                           # Clean remote system

# Disconnect and return to local execution
dpm connect --disconnect                    # Return to local execution
```

**Key Benefits of Connection State Approach:**

- **Seamless Experience**: No need to prefix every command with `remote exec`
- **Consistent Interface**: All DPM commands work the same way locally and remotely
- **Clear Context**: Always know if you're operating locally or remotely
- **Simple Switching**: Easy to switch between local and remote execution

## Configuration

DPM uses JSON configuration files for system settings:

- **System Config**: `/etc/debian-package-manager/config.json`
- **User Config**: `~/.config/debian-package-manager/config.json`

### Autocomplete Configuration

Bash autocomplete is automatically installed and configured:

- **Local Installation**: Installed to `/etc/bash_completion.d/dpm`
- **Docker Environment**: Pre-configured in container
- **Manual Setup**: Source the completion script in your `~/.bashrc`

```bash
# Manual autocomplete setup (if needed)
source /etc/bash_completion.d/dpm

# Or add to ~/.bashrc for permanent setup
echo "source /etc/bash_completion.d/dpm" >> ~/.bashrc
```

**Autocomplete Features:**
- ✅ Command completion (`dpm <TAB><TAB>`)
- ✅ Option completion (`dpm install --<TAB><TAB>`)
- ✅ Package name completion for available packages
- ✅ Installed package completion for remove operations
- ✅ SSH key file completion for connect operations
- ✅ Context-aware suggestions based on command

### Configuration Example

```
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
  "offline_mode": false,
  "pinned_versions": {
    "mycompany-core": "1.2.3",
    "internal-utils": "2.1.0"
  },
  "force_confirmation_required": true,
  "auto_resolve_conflicts": true
}
```

### Editing Configuration

```bash
# Edit system configuration
sudo nano /etc/debian-package-manager/config.json

# Edit user configuration
nano ~/.config/debian-package-manager/config.json
```

### Enhanced Force Operations

DPM provides intelligent force operations that analyze impact before proceeding:

**Force Installation (`--force`)**:
- Shows detailed impact analysis in table format
- Lists packages that will be removed due to conflicts
- Identifies custom packages at risk
- Applies protection strategies to preserve custom packages
- Requires explicit user confirmation (type "YES")

**Force Removal (`--force`)**:
- Shows dependency impact analysis in table format
- Lists dependencies that will be removed
- Identifies packages that depend on the target (may break)
- Applies protection strategies to preserve custom packages
- Requires explicit user confirmation (type "YES")

Both operations use advanced dependency analysis to minimize system impact while achieving the desired outcome.

### Artifactory Mode Management

DPM automatically manages Artifactory integration when switching between offline and online modes:

**Offline Mode (`dpm mode --offline`)**:
- Enables Artifactory repository configuration
- Sets up offline package cache
- Enables pinned version resolution
- Prepares offline dependencies

**Online Mode (`dpm mode --online`)**:
- Restores default repository configuration
- Disables offline package cache
- Enables latest version resolution
- Cleans offline dependencies

Mode switching automatically executes the appropriate Artifactory scripts to ensure proper configuration.

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
