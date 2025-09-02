"""Comprehensive error handling for package operations."""

import traceback
from typing import List, Optional, Callable, Any
from functools import wraps
from ...utils.logging.logger import get_logger
from ...models import OperationResult


logger = get_logger('error_handler')


class PackageOperationError(Exception):
    """Base exception for package operations."""
    pass


class DependencyResolutionError(PackageOperationError):
    """Exception for dependency resolution failures."""
    pass


class ConflictResolutionError(PackageOperationError):
    """Exception for conflict resolution failures."""
    pass


class NetworkError(PackageOperationError):
    """Exception for network-related failures."""
    pass


class PermissionError(PackageOperationError):
    """Exception for permission-related failures."""
    pass


class PackageLockError(PackageOperationError):
    """Exception for package lock issues."""
    pass


def handle_exceptions(operation_name: str):
    """Decorator for handling exceptions in package operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                logger.info(f"Starting operation: {operation_name}")
                result = func(*args, **kwargs)
                logger.info(f"Operation completed successfully: {operation_name}")
                return result
                
            except KeyboardInterrupt:
                logger.warning(f"Operation cancelled by user: {operation_name}")
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=["Operation cancelled by user"],
                    errors=[],
                    user_confirmations_required=[]
                )
                
            except PermissionError as e:
                error_msg = f"Permission denied: {str(e)}"
                logger.error(f"Permission error in {operation_name}: {error_msg}")
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=[],
                    errors=[error_msg, "Try running with sudo or as root"],
                    user_confirmations_required=[]
                )
                
            except NetworkError as e:
                error_msg = f"Network error: {str(e)}"
                logger.error(f"Network error in {operation_name}: {error_msg}")
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=["Consider switching to offline mode"],
                    errors=[error_msg],
                    user_confirmations_required=[]
                )
                
            except PackageLockError as e:
                error_msg = f"Package lock error: {str(e)}"
                logger.error(f"Lock error in {operation_name}: {error_msg}")
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=["Try again in a few moments or use --force"],
                    errors=[error_msg],
                    user_confirmations_required=[]
                )
                
            except DependencyResolutionError as e:
                error_msg = f"Dependency resolution failed: {str(e)}"
                logger.error(f"Dependency error in {operation_name}: {error_msg}")
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=["Consider using --force to override"],
                    errors=[error_msg],
                    user_confirmations_required=[]
                )
                
            except ConflictResolutionError as e:
                error_msg = f"Conflict resolution failed: {str(e)}"
                logger.error(f"Conflict error in {operation_name}: {error_msg}")
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=["Manual intervention may be required"],
                    errors=[error_msg],
                    user_confirmations_required=[]
                )
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error in {operation_name}: {error_msg}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=["Check logs for detailed error information"],
                    errors=[error_msg],
                    user_confirmations_required=[]
                )
        
        return wrapper
    return decorator


class ErrorHandler:
    """Main error handler for the package manager."""
    
    def __init__(self):
        """Initialize error handler."""
        self.logger = get_logger('error_handler')
        self.recovery = ErrorRecovery()
        self.recovery_strategies = {
            'network': self.recovery._recover_from_network_error,
            'locks': self.recovery._recover_from_lock_error,
            'broken': self.recovery._recover_from_broken_packages
        }
    
    def handle_error(self, error: Exception, context: dict = None) -> None:
        """Handle an error with optional context."""
        if context is None:
            context = {}
        
        self.logger.error(f"Handling error: {type(error).__name__}: {str(error)}")
        
        # Log context if provided
        if context:
            self.logger.debug(f"Error context: {context}")
        
        # Attempt recovery based on error type
        error_type = type(error).__name__.lower()
        if 'network' in error_type:
            self.recovery.attempt_recovery('network_timeout', context)
        elif 'lock' in error_type:
            self.recovery.attempt_recovery('package_lock', context)
        elif 'broken' in error_type:
            self.recovery.attempt_recovery('broken_packages', context)


class ErrorRecovery:
    """Handles error recovery and system restoration."""
    
    def __init__(self):
        self.logger = get_logger('error_recovery')
    
    def attempt_recovery(self, error_type: str, context: dict) -> bool:
        """Attempt to recover from an error."""
        self.logger.info(f"Attempting recovery for error type: {error_type}")
        
        try:
            if error_type == "package_lock":
                return self._recover_from_lock_error(context)
            elif error_type == "broken_packages":
                return self._recover_from_broken_packages(context)
            elif error_type == "network_timeout":
                return self._recover_from_network_error(context)
            elif error_type == "dependency_conflict":
                return self._recover_from_dependency_conflict(context)
            else:
                self.logger.warning(f"No recovery method for error type: {error_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Recovery attempt failed: {str(e)}")
            return False
    
    def _recover_from_lock_error(self, context: dict) -> bool:
        """Recover from package lock errors."""
        try:
            from ...interfaces.dpkg import DPKGInterface
            dpkg = DPKGInterface()
            
            # Wait and retry
            import time
            time.sleep(5)
            
            # Try to handle locks
            if dpkg._handle_locks():
                self.logger.info("Successfully recovered from lock error")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Lock recovery failed: {str(e)}")
            return False
    
    def _recover_from_broken_packages(self, context: dict) -> bool:
        """Recover from broken package states."""
        try:
            from ...interfaces.dpkg import DPKGInterface
            dpkg = DPKGInterface()
            
            if dpkg.fix_broken_packages():
                self.logger.info("Successfully fixed broken packages")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Broken package recovery failed: {str(e)}")
            return False
    
    def _recover_from_network_error(self, context: dict) -> bool:
        """Recover from network errors."""
        try:
            # Switch to offline mode
            from ...core.mode_manager import ModeManager
            mode_manager = ModeManager()
            mode_manager.switch_to_offline_mode()
            
            self.logger.info("Switched to offline mode due to network error")
            return True
            
        except Exception as e:
            self.logger.error(f"Network error recovery failed: {str(e)}")
            return False
    
    def _recover_from_dependency_conflict(self, context: dict) -> bool:
        """Recover from dependency conflicts."""
        try:
            # This would typically involve user interaction
            # For now, just log the attempt
            self.logger.info("Dependency conflict recovery would require user interaction")
            return False
            
        except Exception as e:
            self.logger.error(f"Dependency conflict recovery failed: {str(e)}")
            return False


def validate_operation_preconditions(operation: str, **kwargs) -> List[str]:
    """Validate preconditions for an operation."""
    issues = []
    
    if operation in ['install', 'remove']:
        # Check for root privileges
        import os
        if os.geteuid() != 0:
            issues.append("Root privileges required for package operations")
    
    if operation == 'install':
        package_name = kwargs.get('package_name')
        if not package_name:
            issues.append("Package name is required for installation")
        elif not isinstance(package_name, str) or not package_name.strip():
            issues.append("Invalid package name provided")
    
    if operation == 'remove':
        package_name = kwargs.get('package_name')
        if not package_name:
            issues.append("Package name is required for removal")
    
    return issues


def create_safe_operation_result(success: bool = False, 
                                error_message: str = "Operation failed",
                                warnings: Optional[List[str]] = None) -> OperationResult:
    """Create a safe operation result for error conditions."""
    return OperationResult(
        success=success,
        packages_affected=[],
        warnings=warnings or [],
        errors=[error_message] if not success else [],
        user_confirmations_required=[]
    )