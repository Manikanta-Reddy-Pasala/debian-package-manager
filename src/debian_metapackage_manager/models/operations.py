"""Operation-related data models."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from .package import Package


@dataclass
class Conflict:
    """Represents a package conflict."""
    package: Package
    conflicting_package: Package
    reason: str
    
    def __str__(self) -> str:
        """String representation of the conflict."""
        return f"{self.package.name} conflicts with {self.conflicting_package.name}: {self.reason}"


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
    
    @property
    def total_operations(self) -> int:
        """Get total number of operations in the plan."""
        return len(self.to_install) + len(self.to_remove) + len(self.to_upgrade)
    
    @property
    def has_conflicts(self) -> bool:
        """Check if the plan has conflicts."""
        return len(self.conflicts) > 0
    
    def __str__(self) -> str:
        """String representation of the dependency plan."""
        return f"DependencyPlan(install={len(self.to_install)}, remove={len(self.to_remove)}, upgrade={len(self.to_upgrade)}, conflicts={len(self.conflicts)})"


@dataclass
class OperationResult:
    """Result of a package operation."""
    success: bool
    packages_affected: List[Package]
    warnings: List[str]
    errors: List[str]
    user_confirmations_required: List[str]
    details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.packages_affected is None:
            self.packages_affected = []
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
        if self.user_confirmations_required is None:
            self.user_confirmations_required = []
        if self.details is None:
            self.details = {}
    
    @property
    def has_warnings(self) -> bool:
        """Check if the result has warnings."""
        return len(self.warnings) > 0
    
    @property
    def has_errors(self) -> bool:
        """Check if the result has errors."""
        return len(self.errors) > 0
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the result."""
        self.warnings.append(warning)
    
    def add_error(self, error: str) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        self.success = False
    
    def __str__(self) -> str:
        """String representation of the operation result."""
        status = "SUCCESS" if self.success else "FAILED"
        return f"OperationResult({status}, packages={len(self.packages_affected)}, warnings={len(self.warnings)}, errors={len(self.errors)})"