# Changelog

## [Latest] - 2025-02-09

### Fixed
- **CLI --online mode**: Fixed missing `--online` option in install command parser
- **Offline mode detection**: Improved logic in ModeManager to prevent false offline mode when internet is available
- **Mode switching**: Enhanced install command to properly handle both `--online` and `--offline` flags with validation
- **Docker structure**: Reorganized Docker environment with proper file organization

### Enhanced
- **Mode Manager**: Improved `is_offline_mode()` logic to respect explicit configuration while checking network availability
- **CLI validation**: Added validation to prevent specifying both `--online` and `--offline` modes simultaneously
- **Docker setup**: Restructured Docker files into organized directory structure with dedicated scripts
- **Installation process**: Simplified Docker installation with better file organization

### Added
- **Docker scripts**: Added `setup-dpm.sh` and `build-examples.sh` for organized Docker setup
- **Test script**: Added `test-online-mode.py` for verifying --online mode functionality
- **Enhanced documentation**: Updated README with recent fixes and improved Docker structure documentation

### Changed
- **Docker Dockerfile**: Updated to use organized file structure with proper script execution
- **docker-compose.yml**: Improved volume mounting and environment setup
- **install-docker.sh**: Simplified script using organized Docker file structure
- **bashrc-additions**: Enhanced with better aliases and mode testing examples

### Technical Details
- Fixed `is_offline_mode()` in ModeManager to only force offline when both network and repositories are unavailable
- Added proper `--online` flag handling in CLI install command
- Reorganized Docker files: scripts/, config/, packages/, bashrc-additions
- Enhanced error handling and user feedback for mode switching
- Improved network detection and repository accessibility checks

### Docker Structure
```
docker/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Orchestration config
├── config/                 # DPM configuration files
├── packages/               # Example packages
├── scripts/                # Setup and build scripts
│   ├── setup-dpm.sh       # Main setup script
│   └── build-examples.sh  # Package building script
└── bashrc-additions        # Shell environment setup
```

### Usage Examples
```bash
# New --online mode usage
dpm install --online package-name    # Force online mode
dpm install --offline package-name   # Force offline mode

# Mode management
dpm mode --status                     # Check current mode
dpm mode --online                     # Switch to online mode
dpm mode --offline                    # Switch to offline mode
dpm mode --auto                       # Auto-detect mode

# Docker usage
./install-docker.sh                  # Setup Docker environment
./dpm-docker-start.sh                # Start and enter container
./dpm-docker-stop.sh                 # Stop container
./dpm-docker-clean.sh                # Clean up environment
```