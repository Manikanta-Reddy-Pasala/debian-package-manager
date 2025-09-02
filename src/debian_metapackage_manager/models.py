"""Core data models for the Debian Metapackage Manager."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class PackageStatus(Enum):
    """Package installation status."""
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    UPGRADABLE = "upgradable"
    BROKEN = "broken"


class PackageType(Enum):
    """Package type classification."""
    CUSTOM = "custom"
    SYSTEM = "system"
    METAPACKAGE = "metapackage"


@dataclass
class Package:
    """Represents a Debian package with its metadata."""
    name: str
    version: str
    is_metapackage: bool = False
    is_custom: bool = False
    dependencies: List['Package'] = None
    conflicts: List['Package'] = None
    status: PackageStatus = PackageStatus.NOT_INSTALLED
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.conflicts is None:
            self.conflicts = []


@dataclass
class Conflict:
    """Represents a package conflict."""
    package: Package
    conflicting_package: Package
    reason: str


@dataclass
class DependencyPlan:
    """Plan for dependency resolution operations."""
    to_install: List[Package]
    to_remove: List[Package]
    to_upgrade: List[Package]
    conflicts: List[Conflict]
    requires_user_confirmation: bool = False
    
    def __post_init__(self):
        if self.to_install is None:
            self.to_install = []
        if self.to_remove is None:
            self.to_remove = []
        if self.to_upgrade is None:
            self.to_upgrade = []
        if self.conflicts is None:
            self.conflicts = []


@dataclass
class OperationResult:
    """Result of a package operation."""
    success: bool
    packages_affected: List[Package]
    warnings: List[str]
    errors: List[str]
    user_confirmations_required: List[str]
    
    def __post_init__(self):
        if self.packages_affected is None:
            self.packages_affected = []
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
        if self.user_confirmations_required is None:
            self.user_confirmations_required = []