"""Custom exceptions for Debian Package Manager."""

from .base import DPMError, DPMWarning
from .cli import CLIError, ValidationError, CommandError
from .package import PackageError, PackageNotFoundError, DependencyError, ConflictError
from .system import SystemError, NetworkError, PermissionError as DPMPermissionError
from .config import ConfigError, ConfigValidationError

__all__ = [
    'DPMError', 'DPMWarning',
    'CLIError', 'ValidationError', 'CommandError',
    'PackageError', 'PackageNotFoundError', 'DependencyError', 'ConflictError',
    'SystemError', 'NetworkError', 'DPMPermissionError',
    'ConfigError', 'ConfigValidationError'
]