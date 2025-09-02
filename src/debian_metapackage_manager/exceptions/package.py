"""Package-related exceptions."""

from .base import DPMError


class PackageError(DPMError):
    """Base package error."""
    pass


class PackageNotFoundError(PackageError):
    """Package not found error."""
    
    def __init__(self, package_name: str):
        """Initialize package not found error."""
        super().__init__(f"Package '{package_name}' not found")
        self.package_name = package_name


class DependencyError(PackageError):
    """Dependency resolution error."""
    pass


class ConflictError(PackageError):
    """Package conflict error."""
    
    def __init__(self, package1: str, package2: str, reason: str = ""):
        """Initialize conflict error."""
        message = f"Conflict between '{package1}' and '{package2}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.package1 = package1
        self.package2 = package2
        self.reason = reason