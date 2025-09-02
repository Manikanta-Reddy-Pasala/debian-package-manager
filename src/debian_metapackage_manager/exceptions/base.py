"""Base exceptions for Debian Package Manager."""


class DPMError(Exception):
    """Base exception for all DPM errors."""
    
    def __init__(self, message: str, details: dict = None):
        """Initialize DPM error."""
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class DPMWarning(UserWarning):
    """Base warning for all DPM warnings."""
    
    def __init__(self, message: str, details: dict = None):
        """Initialize DPM warning."""
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation of the warning."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message