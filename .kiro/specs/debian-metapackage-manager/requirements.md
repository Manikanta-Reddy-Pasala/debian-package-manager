# Requirements Document

## Introduction

The Debian Metapackage Manager is a Python-based CLI tool that provides intelligent package management for custom metapackage systems. It supports both offline mode (with pinned versions) and online/artifactory mode (with latest versions), while handling complex dependency resolution and providing developers flexibility to install individual packages even when they belong to metapackages. The tool ensures reproducible operations and handles dependency conflicts gracefully with user confirmation.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to install individual packages that belong to metapackages without breaking the system, so that I can have flexibility in development environments.

#### Acceptance Criteria

1. WHEN a user installs an individual package THEN the system SHALL succeed even if the package belongs to a metapackage
2. WHEN installing a package causes dependency conflicts THEN the system SHALL resolve conflicts automatically without breaking unrelated packages
3. WHEN dependency resolution requires removing packages THEN the system SHALL prompt the user with a list of packages to be removed
4. IF the user confirms removal THEN the system SHALL proceed with forced removal if necessary
5. WHEN a package installation is requested THEN the system SHALL recognize custom packages using 6-7 known prefixes

### Requirement 2

**User Story:** As a system administrator, I want to install metapackages with all their dependencies at pinned versions, so that I can maintain consistent environments.

#### Acceptance Criteria

1. WHEN a metapackage is installed THEN the system SHALL pull all its dependencies with pinned versions
2. WHEN operating in offline mode THEN the system SHALL use pinned versions for all metapackages
3. WHEN operating in online/artifactory mode THEN the system SHALL use latest versions when requested
4. WHEN metapackage installation encounters conflicts THEN the system SHALL resolve dependencies at any cost
5. IF critical packages need removal for metapackage installation THEN the system SHALL prompt user for confirmation

### Requirement 3

**User Story:** As a developer, I want to remove packages or metapackages reliably, so that I can clean up my development environment without system issues.

#### Acceptance Criteria

1. WHEN a package removal is requested THEN the system SHALL remove it at any cost
2. WHEN removal encounters dependency locks THEN the system SHALL force removal after user confirmation
3. WHEN removal requires removing other packages THEN the system SHALL prompt user with removal list
4. IF user confirms forced removal THEN the system SHALL proceed even with critical packages
5. WHEN removal encounters any Debian locking issues THEN the system SHALL resolve them automatically

### Requirement 4

**User Story:** As a developer, I want a standalone CLI tool that doesn't depend on system Python, so that I can use it across different Ubuntu environments.

#### Acceptance Criteria

1. WHEN the tool is distributed THEN it SHALL be packaged as a standalone uv package
2. WHEN the tool is installed THEN it SHALL NOT depend on system Python versions
3. WHEN the tool runs THEN it SHALL work on Ubuntu systems
4. WHEN the tool is executed THEN it SHALL provide CLI commands for install and remove operations
5. WHEN the tool is invoked THEN it SHALL support both `install <package|metapackage>` and `remove <package|metapackage>` commands

### Requirement 5

**User Story:** As a system administrator, I want the tool to automatically fix dependency issues while keeping me informed, so that I can maintain control over critical system changes.

#### Acceptance Criteria

1. WHEN dependency issues are detected THEN the system SHALL fix them automatically
2. WHEN critical packages need removal THEN the system SHALL prompt user before proceeding
3. WHEN the system resolves conflicts THEN it SHALL provide strict, reproducible commands
4. WHEN operating in either mode THEN the system SHALL maintain reproducible install/remove behavior
5. IF automatic resolution fails THEN the system SHALL provide forced resolution options with user confirmation

### Requirement 6

**User Story:** As a developer, I want the tool to distinguish between custom and system packages, so that it can make intelligent decisions about package management.

#### Acceptance Criteria

1. WHEN analyzing packages THEN the system SHALL recognize custom packages using 6-7 configurable prefixes
2. WHEN making removal decisions THEN the system SHALL treat custom packages differently from system packages
3. WHEN resolving conflicts THEN the system SHALL prioritize preserving system packages over custom packages
4. WHEN prompting for confirmations THEN the system SHALL clearly indicate which packages are custom vs system
5. WHEN operating in development mode THEN the system SHALL allow more aggressive operations on custom packages