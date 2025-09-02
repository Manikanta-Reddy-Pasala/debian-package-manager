"""System-related exceptions."""

from .base import DPMError


class SystemError(DPMError):
    """Base system error."""
    pass


class NetworkError(SystemError):
    """Network-related error."""
    pass


class PermissionError(SystemError):
    """Permission-related error."""
    
    def __init__(self, operation: str, resource: str = ""):
        """Initialize permission error."""
        message = f"Permission denied for operation: {operation}"
        if resource:
            message += f" on {resource}"
        super().__init__(message)
        self.operation = operation
        self.resource = resource