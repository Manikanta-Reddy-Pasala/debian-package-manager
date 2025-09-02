# Design Document

## Overview

The Debian Metapackage Manager is a Python CLI tool that provides intelligent package management for custom metapackage hierarchies. The tool uses `apt` and `dpkg` APIs to interact with the Debian package system, implements sophisticated dependency resolution algorithms, and provides a user-friendly interface for managing complex package relationships in both offline and online modes.

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │  Core Engine    │    │  Package Layer  │
│                 │    │                 │    │                 │
│ - Command Parser│────│ - Dependency    │────│ - APT Interface │
│ - User Prompts  │    │   Resolver      │    │ - DPKG Interface│
│ - Output Format │    │ - Conflict      │    │ - Package Query │
└─────────────────┘    │   Handler       │    └─────────────────┘
                       │ - Mode Manager  │
                       └─────────────────┘
                              │
                       ┌─────────────────┐
                       │ Configuration   │
                       │                 │
                       │ - Package       │
                       │   Prefixes      │
                       │ - Mode Settings │
                       │ - Pinned        │
                       │   Versions      │
                       └─────────────────┘
```

## Components and Interfaces

### 1. CLI Layer (`cli.py`)

**Purpose:** Handle user interaction and command parsing

**Key Classes:**
- `PackageManagerCLI`: Main CLI interface
- `UserPrompt`: Interactive confirmation dialogs
- `OutputFormatter`: Consistent output formatting

**Interfaces:**
```python
class PackageManagerCLI:
    def install(self, package_name: str, force: bool = False) -> bool
    def remove(self, package_name: str, force: bool = False) -> bool
    def prompt_user_confirmation(self, action: str, packages: List[str]) -> bool
```

### 2. Core Engine (`engine.py`)

**Purpose:** Central orchestration and business logic

**Key Classes:**
- `PackageEngine`: Main orchestration class
- `DependencyResolver`: Handles complex dependency resolution
- `ConflictHandler`: Manages package conflicts and removals
- `ModeManager`: Switches between offline/online modes

**Interfaces:**
```python
class PackageEngine:
    def install_package(self, name: str, force: bool) -> InstallResult
    def remove_package(self, name: str, force: bool) -> RemoveResult
    def resolve_dependencies(self, package: Package) -> DependencyPlan
    def handle_conflicts(self, conflicts: List[Conflict]) -> Resolution
```

### 3. Package Layer (`package.py`)

**Purpose:** Interface with Debian package system

**Key Classes:**
- `APTInterface`: Wrapper around apt-python library
- `DPKGInterface`: Direct dpkg operations for forced actions
- `PackageQuery`: Package information and status queries
- `PackageClassifier`: Identifies custom vs system packages

**Interfaces:**
```python
class APTInterface:
    def install(self, package: str, version: str = None) -> bool
    def remove(self, package: str, force: bool = False) -> bool
    def get_dependencies(self, package: str) -> List[Dependency]
    def check_conflicts(self, package: str) -> List[Conflict]

class PackageClassifier:
    def is_custom_package(self, package_name: str) -> bool
    def get_package_type(self, package_name: str) -> PackageType
```

### 4. Configuration (`config.py`)

**Purpose:** Manage configuration and settings

**Key Classes:**
- `Config`: Main configuration management
- `PackagePrefixes`: Custom package prefix management
- `VersionPinning`: Handle pinned versions for offline mode

## Data Models

### Package Model
```python
@dataclass
class Package:
    name: str
    version: str
    is_metapackage: bool
    is_custom: bool
    dependencies: List['Package']
    conflicts: List['Package']
    status: PackageStatus
```

### Dependency Resolution Model
```python
@dataclass
class DependencyPlan:
    to_install: List[Package]
    to_remove: List[Package]
    to_upgrade: List[Package]
    conflicts: List[Conflict]
    requires_user_confirmation: bool
```

### Operation Result Model
```python
@dataclass
class OperationResult:
    success: bool
    packages_affected: List[Package]
    warnings: List[str]
    errors: List[str]
    user_confirmations_required: List[str]
```

## Error Handling

### 1. Dependency Conflicts
- **Detection:** Use apt's dependency resolver to identify conflicts
- **Resolution:** Implement custom conflict resolution algorithm
- **User Interaction:** Present clear options with impact analysis
- **Fallback:** Force resolution with dpkg when apt fails

### 2. Package Lock Issues
- **Detection:** Monitor for dpkg lock files and apt lock states
- **Resolution:** Implement retry mechanism with exponential backoff
- **Force Resolution:** Direct dpkg operations to break locks when authorized
- **Recovery:** Ensure system consistency after forced operations

### 3. Network/Repository Issues
- **Offline Mode:** Use local package cache and pinned versions
- **Online Mode:** Implement retry logic for repository access
- **Fallback:** Switch to offline mode when repositories unavailable
- **Validation:** Verify package integrity before installation

### 4. Permission Issues
- **Detection:** Check for root privileges before operations
- **Guidance:** Provide clear instructions for privilege escalation
- **Sudo Integration:** Seamlessly handle sudo requirements
- **Security:** Validate operations before privilege escalation

## Testing Strategy

### 1. Unit Tests
- **Package Classification:** Test custom package prefix recognition
- **Dependency Resolution:** Test complex dependency scenarios
- **Conflict Handling:** Test various conflict resolution paths
- **Mode Switching:** Test offline/online mode transitions

### 2. Integration Tests
- **APT Integration:** Test with real apt operations in containers
- **DPKG Integration:** Test forced operations and lock handling
- **End-to-End Workflows:** Test complete install/remove scenarios
- **Error Recovery:** Test system recovery from failed operations

### 3. System Tests
- **Ubuntu Compatibility:** Test across Ubuntu LTS versions
- **Metapackage Scenarios:** Test with real metapackage hierarchies
- **Performance Testing:** Test with large dependency trees
- **Stress Testing:** Test concurrent operations and edge cases

### 4. User Acceptance Tests
- **CLI Usability:** Test command-line interface workflows
- **Prompt Clarity:** Test user confirmation dialogs
- **Error Messages:** Test error message clarity and actionability
- **Documentation:** Test installation and usage documentation

## Implementation Considerations

### 1. UV Package Distribution
- Use `pyproject.toml` with uv build system
- Include all dependencies in the package
- Create standalone executable with entry points
- Ensure no system Python dependencies

### 2. Privilege Management
- Detect when root privileges are required
- Provide clear sudo integration
- Validate operations before privilege escalation
- Maintain security best practices

### 3. Performance Optimization
- Cache package information for repeated queries
- Implement parallel dependency resolution where safe
- Optimize database queries for large package sets
- Use efficient data structures for dependency graphs

### 4. Robustness
- Implement comprehensive error recovery
- Provide detailed logging for troubleshooting
- Ensure atomic operations where possible
- Maintain system consistency even after failures