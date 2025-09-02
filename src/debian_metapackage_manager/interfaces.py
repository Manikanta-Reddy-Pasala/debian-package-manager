"""Base interfaces for package management operations."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Package, Conflict, OperationResult


class PackageInterface(ABC):
    """Base interface for package management operations."""
    
    @abstractmethod
    def install(self, package: str, version: Optional[str] = None) -> bool:
        """Install a package with optional version specification."""
        pass
    
    @abstractmethod
    def remove(self, package: str, force: bool = False) -> bool:
        """Remove a package with optional force flag."""
        pass
    
    @abstractmethod
    def get_dependencies(self, package: str) -> List[Package]:
        """Get dependencies for a package."""
        pass
    
    @abstractmethod
    def check_conflicts(self, package: str) -> List[Conflict]:
        """Check for conflicts when installing a package."""
        pass
    
    @abstractmethod
    def is_installed(self, package: str) -> bool:
        """Check if a package is installed."""
        pass
    
    @abstractmethod
    def get_package_info(self, package: str) -> Optional[Package]:
        """Get detailed information about a package."""
        pass


class DependencyResolverInterface(ABC):
    """Interface for dependency resolution."""
    
    @abstractmethod
    def resolve_dependencies(self, package: Package) -> 'DependencyPlan':
        """Resolve dependencies for a package installation."""
        pass
    
    @abstractmethod
    def resolve_conflicts(self, conflicts: List[Conflict]) -> 'DependencyPlan':
        """Resolve package conflicts."""
        pass


class ConfigInterface(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def get_custom_prefixes(self) -> List[str]:
        """Get list of custom package prefixes."""
        pass
    
    @abstractmethod
    def is_offline_mode(self) -> bool:
        """Check if operating in offline mode."""
        pass
    
    @abstractmethod
    def get_pinned_version(self, package: str) -> Optional[str]:
        """Get pinned version for a package in offline mode."""
        pass