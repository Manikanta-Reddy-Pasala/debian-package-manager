<!-- @format -->

# Debian Package Manager

Intelligent package management for custom Debian package systems with offline/online mode support and advanced dependency resolution.

## Features

- **Dual Mode Operation**: Support for both offline (pinned versions) and online/artifactory modes
- **Intelligent Dependency Resolution**: Advanced conflict detection and resolution with user confirmation
- **Custom Package Recognition**: Configurable prefixes for identifying custom packages
- **Enhanced System Cleanup**: Comprehensive cleanup functionality for APT cache, offline repositories, and artifactory
- **Remote System Execution**: SSH-based remote package management across multiple systems
- **Force Operations**: Safe force installation/removal with comprehensive protection strategies
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

### 🐳 Docker Installation (Development/Testing)

Set up a complete DPM environment in Docker for development and testing:

```bash
# Build and start Docker environment
sudo ./install.sh --docker

# Stop Docker environment
sudo ./install.sh --docker --stop

# Remove Docker environment completely
sudo ./install.sh --docker --remove
```

**Features included:**
- Complete isolated environment
- Pre-built example packages
- All DPM functionality in a container
- Easy development and testing workflow

## Available Commands

### 📦 Package Management

#### `dpm install <package-name> [--version <version>] [--force]`
Install a package or specific version of a package.

```bash
# Install latest version
dpm install mycompany-webserver

# Install specific version
dpm install mycompany-webserver --version 1.2.3

# Force install with intelligent protection strategies
dpm install mycompany-webserver --force
```

**Force Installation Protection:**
- Automatically analyzes impact before proceeding
- Marks dependent custom packages as manually installed to prevent auto-removal
- Tries multiple safe installation methods before showing user confirmation
- Only shows confirmation for significant impacts as a last resort
- Uses table format for clear impact visualization

#### `dpm remove <package-name> [--force] [--purge]`
Remove a package or metapackage.

```bash
# Remove package
dpm remove mycompany-webserver

# Force remove with intelligent protection strategies
dpm remove mycompany-webserver --force

# Remove package and purge configuration files
dpm remove mycompany-webserver --purge
```

**Force Removal Protection:**
- Analyzes dependencies and reverse dependencies before proceeding
- Marks dependent custom packages as manually installed to prevent cascade removal
- Tries multiple safe removal methods before showing user confirmation
- Only shows confirmation for significant impacts as a last resort
- Uses table format for clear impact visualization

### 🔄 Mode Management

#### `dpm mode`
Show current mode status (online/offline).

```bash
dpm mode
```

#### `dpm mode --offline`
Switch to offline mode using pinned versions.

```bash
dpm mode --offline
```

#### `dpm mode --online`
Switch to online mode using latest available versions.

```bash
dpm mode --online
```

### 📋 Package Information

#### `dpm list [--all] [--broken] [--metapackages] [--simple] [--table]`
List installed packages with filtering options.

```bash
# List custom packages only (default)
dpm list

# List all installed packages
dpm list --all

# List broken packages
dpm list --broken

# List metapackages only
dpm list --metapackages

# Simple list format (package names only)
dpm list --simple

# Table format with detailed information
dpm list --table
```

#### `dpm info <package-name> [--dependencies]`
Show detailed information about a package.

```bash
# Basic package information
dpm info mycompany-webserver

# Include dependency information
dpm info mycompany-webserver --dependencies
```

### 🔧 System Maintenance

#### `dpm health`
Check system package health status.

```bash
dpm health
```

#### `dpm fix`
Attempt to fix broken package states.

```bash
dpm fix
```

#### `dpm cleanup [--apt-cache] [--offline-repo] [--artifactory]`
Clean up system resources.

```bash
# Clean all resources
dpm cleanup

# Clean APT cache only
dpm cleanup --apt-cache

# Clean offline repository only
dpm cleanup --offline-repo

# Clean artifactory cache only
dpm cleanup --artifactory
```

### 🔗 Remote Management

#### `dpm connect <host> [--port <port>] [--user <user>]`
Connect to a remote system for package management.

```bash
# Connect with default settings
dpm connect 192.168.1.100

# Connect with custom port and user
dpm connect 192.168.1.100 --port 2222 --user admin
```

#### `dpm connect --disconnect`
Disconnect from remote system.

```bash
dpm connect --disconnect
```

## Configuration

DPM uses JSON configuration files to manage settings. The default configuration includes:

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
  "offline_mode": false,
  "force_confirmation_required": true,
  "auto_resolve_conflicts": true
}
```

### Custom Prefixes
Only packages with configured prefixes can be safely removed to prevent accidental system package removal.

## Force Operations Behavior

DPM's force operations are designed with safety as the top priority:

### Force Installation (`dpm install --force`)
1. **Impact Analysis**: Analyzes what packages would be removed or installed
2. **Protection Strategy**: Marks dependent custom packages as manually installed
3. **Safe Methods First**: Tries `--no-remove`, `--only-upgrade`, and other safe flags
4. **Intelligent Fallback**: Only shows user confirmation for significant impacts
5. **Multiple Strategies**: Uses various APT/DPKG flags as needed
6. **Clear Visualization**: Shows impacts in table format when confirmation is required

### Force Removal (`dpm remove --force`)
1. **Dependency Analysis**: Identifies what dependencies would be removed
2. **Reverse Dependency Check**: Finds packages that depend on the target
3. **Protection Strategy**: Marks dependent custom packages as manually installed
4. **Safe Removal First**: Tries standard removal before force methods
5. **Intelligent Fallback**: Only shows user confirmation for significant impacts
6. **Multiple Strategies**: Uses various APT/DPKG force flags as needed
7. **Clear Visualization**: Shows impacts in table format when confirmation is required

## Quick Start Examples

### Local Installation
```bash
# Install DPM locally
sudo ./install.sh --local

# Install a package
dpm install mycompany-webserver

# List installed custom packages
dpm list

# Check system health
dpm health
```

### Docker Environment
```bash
# Set up Docker environment
sudo ./install.sh --docker

# The environment will automatically start and show available commands
# All example packages are pre-built and ready to install
```

## Development

### Building Example Packages
Example packages are automatically built during Docker setup. To manually build:

```bash
./docker/scripts/build-examples.sh
```

### Running Tests
Execute the test suite:

```bash
python -m pytest tests/ -v
```

## License
MIT License - See [LICENSE](LICENSE) file for details.