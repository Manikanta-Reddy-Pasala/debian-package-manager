# Debian Metapackage Manager

Intelligent package management for custom Debian metapackage systems.

## Features

- Support for both offline (pinned versions) and online/artifactory modes
- Intelligent dependency resolution with conflict handling
- Custom package recognition using configurable prefixes
- Force installation/removal with user confirmation
- Standalone uv package with no system Python dependencies

## Installation

```bash
# Install using uv
uv tool install debian-metapackage-manager

# Or install from source
git clone <repository>
cd debian-metapackage-manager
uv pip install -e .
```

## Usage

```bash
# Install a package or metapackage
dpm install <package-name>

# Remove a package or metapackage
dpm remove <package-name>

# Force operations (with confirmation)
dpm install --force <package-name>
dpm remove --force <package-name>
```

## Configuration

The tool uses configuration files to manage:
- Custom package prefixes
- Offline/online mode settings
- Pinned versions for offline mode

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