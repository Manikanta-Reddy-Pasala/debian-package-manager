"""Package-related data models."""

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
    
    @property
    def package_type(self) -> PackageType:
        """Get the package type."""
        if self.is_metapackage:
            return PackageType.METAPACKAGE
        elif self.is_custom:
            return PackageType.CUSTOM
        else:
            return PackageType.SYSTEM
    
    def __str__(self) -> str:
        """String representation of the package."""
        return f"{self.name} (v{self.version})"
    
    def __repr__(self) -> str:
        """Detailed representation of the package."""
        return f"Package(name='{self.name}', version='{self.version}', type={self.package_type.value})"