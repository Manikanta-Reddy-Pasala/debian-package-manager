"""CLI-related exceptions."""

from .base import DPMError


class CLIError(DPMError):
    """Base CLI error."""
    pass


class ValidationError(CLIError):
    """Validation error in CLI arguments."""
    pass


class CommandError(CLIError):
    """Error executing a command."""
    
    def __init__(self, command: str, message: str, exit_code: int = 1):
        """Initialize command error."""
        super().__init__(f"Command '{command}' failed: {message}")
        self.command = command
        self.exit_code = exit_code