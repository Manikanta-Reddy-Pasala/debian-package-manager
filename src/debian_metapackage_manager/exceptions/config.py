"""Configuration-related exceptions."""

from .base import DPMError


class ConfigError(DPMError):
    """Base configuration error."""
    pass


class ConfigValidationError(ConfigError):
    """Configuration validation error."""
    
    def __init__(self, field: str, value: str, reason: str = ""):
        """Initialize config validation error."""
        message = f"Invalid configuration for '{field}': {value}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)
        self.field = field
        self.value = value
        self.reason = reason