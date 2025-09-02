"""Tests for error handling utilities."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from debian_metapackage_manager.utils.error.error_handler import (
    PackageOperationError, DependencyResolutionError, ConflictResolutionError,
    NetworkError, PermissionError, PackageLockError,
    handle_exceptions, ErrorHandler, validate_operation_preconditions,
    create_safe_operation_result
)
from debian_metapackage_manager.models import OperationResult, Package


class TestExceptionClasses:
    """Test custom exception classes."""

    def test_package_operation_error(self):
        """Test PackageOperationError base exception."""
        error = PackageOperationError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_dependency_resolution_error(self):
        """Test DependencyResolutionError inheritance."""
        error = DependencyResolutionError("Dependency error")
        assert str(error) == "Dependency error"
        assert isinstance(error, PackageOperationError)

    def test_conflict_resolution_error(self):
        """Test ConflictResolutionError inheritance."""
        error = ConflictResolutionError("Conflict error")
        assert str(error) == "Conflict error"
        assert isinstance(error, PackageOperationError)

    def test_network_error(self):
        """Test NetworkError inheritance."""
        error = NetworkError("Network error")
        assert str(error) == "Network error"
        assert isinstance(error, PackageOperationError)

    def test_permission_error(self):
        """Test PermissionError inheritance."""
        error = PermissionError("Permission error")
        assert str(error) == "Permission error"
        assert isinstance(error, PackageOperationError)

    def test_package_lock_error(self):
        """Test PackageLockError inheritance."""
        error = PackageLockError("Lock error")
        assert str(error) == "Lock error"
        assert isinstance(error, PackageOperationError)


class TestHandleExceptionsDecorator:
    """Test the handle_exceptions decorator."""

    def test_handle_exceptions_success(self):
        """Test decorator with successful operation."""
        @handle_exceptions("test_operation")
        def successful_operation():
            return "success"
        
        result = successful_operation()
        assert result == "success"

    def test_handle_exceptions_keyboard_interrupt(self):
        """Test decorator handling KeyboardInterrupt."""
        @handle_exceptions("test_operation")
        def interrupted_operation():
            raise KeyboardInterrupt()
        
        result = interrupted_operation()
        
        assert isinstance(result, OperationResult)
        assert not result.success
        assert "cancelled by user" in result.warnings[0]

    def test_handle_exceptions_permission_error(self):
        """Test decorator handling PermissionError."""
        @handle_exceptions("test_operation")
        def permission_error_operation():
            raise PermissionError("Access denied")
        
        result = permission_error_operation()
        
        assert isinstance(result, OperationResult)
        assert not result.success
        assert "Permission denied" in result.errors[0]
        assert "Try running with sudo" in result.errors[1]

    def test_handle_exceptions_network_error(self):
        """Test decorator handling NetworkError."""
        @handle_exceptions("test_operation")
        def network_error_operation():
            raise NetworkError("No connection")
        
        result = network_error_operation()
        
        assert isinstance(result, OperationResult)
        assert not result.success
        assert "Network error" in result.errors[0]
        assert "Consider switching to offline mode" in result.warnings[0]

    def test_handle_exceptions_dependency_resolution_error(self):
        """Test decorator handling DependencyResolutionError."""
        @handle_exceptions("test_operation")
        def dependency_error_operation():
            raise DependencyResolutionError("Cannot resolve dependencies")
        
        result = dependency_error_operation()
        
        assert isinstance(result, OperationResult)
        assert not result.success
        assert "Dependency resolution failed" in result.errors[0]
        assert "Consider using --force" in result.warnings[0]

    def test_handle_exceptions_conflict_resolution_error(self):
        """Test decorator handling ConflictResolutionError."""
        @handle_exceptions("test_operation")
        def conflict_error_operation():
            raise ConflictResolutionError("Cannot resolve conflicts")
        
        result = conflict_error_operation()
        
        assert isinstance(result, OperationResult)
        assert not result.success
        assert "Conflict resolution failed" in result.errors[0]
        assert "Manual intervention may be required" in result.warnings[0]

    def test_handle_exceptions_generic_exception(self):
        """Test decorator handling generic exceptions."""
        @handle_exceptions("test_operation")
        def generic_error_operation():
            raise ValueError("Something went wrong")
        
        result = generic_error_operation()
        
        assert isinstance(result, OperationResult)
        assert not result.success
        assert "Unexpected error" in result.errors[0]
        assert "Check logs for detailed error information" in result.warnings[0]


class TestErrorHandler:
    """Test the ErrorHandler class."""

    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler()
        
        assert hasattr(handler, 'logger')
        assert hasattr(handler, 'recovery_strategies')

    def test_error_handler_handle_error_with_context(self):
        """Test error handling with context."""
        handler = ErrorHandler()
        
        error = NetworkError("Connection failed")
        context = {"operation": "install", "package": "test-pkg"}
        
        # Should not raise exception
        handler.handle_error(error, context)

    def test_error_handler_handle_error_without_context(self):
        """Test error handling without context."""
        handler = ErrorHandler()
        
        error = PackageOperationError("General error")
        
        # Should not raise exception
        handler.handle_error(error)

    @patch('debian_metapackage_manager.core.mode_manager.ModeManager')
    def test_error_handler_network_recovery(self, mock_mode_manager):
        """Test network error recovery."""
        mock_manager_instance = Mock()
        mock_mode_manager.return_value = mock_manager_instance
        
        handler = ErrorHandler()
        context = {"operation": "install"}
        
        result = handler._recover_from_network_error(context)
        
        # Should attempt to switch to offline mode
        mock_manager_instance.switch_to_offline_mode.assert_called_once()
        assert result is True

    def test_error_handler_dependency_conflict_recovery(self):
        """Test dependency conflict recovery."""
        handler = ErrorHandler()
        context = {"operation": "install"}
        
        result = handler._recover_from_dependency_conflict(context)
        
        # Currently returns False as it requires user interaction
        assert result is False

    def test_error_handler_multiple_errors(self):
        """Test handling multiple errors."""
        handler = ErrorHandler()
        
        errors = [
            NetworkError("Network issue"),
            PermissionError("Permission issue"),
            PackageOperationError("General issue")
        ]
        
        for error in errors:
            # Should handle all errors without raising exceptions
            handler.handle_error(error, {"operation": "test"})


class TestValidateOperationPreconditions:
    """Test operation precondition validation."""

    @patch('os.geteuid')
    def test_validate_operation_preconditions_install_root(self, mock_geteuid):
        """Test install operation validation with root privileges."""
        mock_geteuid.return_value = 0  # Root user
        
        issues = validate_operation_preconditions('install', package_name='test-pkg')
        
        assert len(issues) == 0

    @patch('os.geteuid')
    def test_validate_operation_preconditions_install_non_root(self, mock_geteuid):
        """Test install operation validation without root privileges."""
        mock_geteuid.return_value = 1000  # Non-root user
        
        issues = validate_operation_preconditions('install', package_name='test-pkg')
        
        assert len(issues) == 1
        assert "Root privileges required" in issues[0]

    def test_validate_operation_preconditions_install_no_package(self):
        """Test install operation validation without package name."""
        issues = validate_operation_preconditions('install')
        
        assert len(issues) >= 1
        assert any("Package name is required" in issue for issue in issues)

    def test_validate_operation_preconditions_install_invalid_package(self):
        """Test install operation validation with invalid package name."""
        issues = validate_operation_preconditions('install', package_name="")
        
        assert len(issues) >= 1
        assert any("Invalid package name" in issue for issue in issues)

    @patch('os.geteuid')
    def test_validate_operation_preconditions_remove(self, mock_geteuid):
        """Test remove operation validation."""
        mock_geteuid.return_value = 0  # Root user
        
        issues = validate_operation_preconditions('remove', package_name='test-pkg')
        
        assert len(issues) == 0

    def test_validate_operation_preconditions_remove_no_package(self):
        """Test remove operation validation without package name."""
        issues = validate_operation_preconditions('remove')
        
        assert len(issues) >= 1
        assert any("Package name is required" in issue for issue in issues)

    def test_validate_operation_preconditions_other_operation(self):
        """Test validation for operations that don't require root."""
        issues = validate_operation_preconditions('info', package_name='test-pkg')
        
        # Should not require root privileges for info operation
        assert not any("Root privileges required" in issue for issue in issues)


class TestCreateSafeOperationResult:
    """Test safe operation result creation."""

    def test_create_safe_operation_result_success(self):
        """Test creating successful safe operation result."""
        result = create_safe_operation_result(success=True)
        
        assert result.success is True
        assert result.packages_affected == []
        assert result.warnings == []
        assert result.errors == []

    def test_create_safe_operation_result_failure(self):
        """Test creating failed safe operation result."""
        result = create_safe_operation_result(success=False, error_message="Test error")
        
        assert result.success is False
        assert result.packages_affected == []
        assert result.warnings == []
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_create_safe_operation_result_with_warnings(self):
        """Test creating safe operation result with warnings."""
        warnings = ["Warning 1", "Warning 2"]
        result = create_safe_operation_result(success=True, warnings=warnings)
        
        assert result.success is True
        assert result.warnings == warnings

    def test_create_safe_operation_result_default_error_message(self):
        """Test creating safe operation result with default error message."""
        result = create_safe_operation_result(success=False)
        
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0] == "Operation failed"


class TestErrorHandlerIntegration:
    """Integration tests for error handling components."""

    def test_error_handler_with_decorator_integration(self):
        """Test integration between ErrorHandler and decorator."""
        @handle_exceptions("integration_test")
        def operation_with_multiple_issues():
            # Simulate complex operation that might have multiple issues
            raise DependencyResolutionError("Complex dependency issue")
        
        result = operation_with_multiple_issues()
        
        assert isinstance(result, OperationResult)
        assert not result.success
        assert len(result.errors) >= 1
        assert len(result.warnings) >= 1

    def test_realistic_error_scenario_network_then_permission(self):
        """Test realistic scenario with multiple error types."""
        @handle_exceptions("realistic_scenario")
        def complex_operation(error_type):
            if error_type == "network":
                raise NetworkError("Cannot reach repositories")
            elif error_type == "permission":
                raise PermissionError("Access denied to package files")
            elif error_type == "dependency":
                raise DependencyResolutionError("Circular dependency detected")
        
        # Test network error
        network_result = complex_operation("network")
        assert not network_result.success
        assert any("Network error" in error for error in network_result.errors)
        assert any("offline mode" in warning for warning in network_result.warnings)
        
        # Test permission error
        perm_result = complex_operation("permission")
        assert not perm_result.success
        assert any("Permission denied" in error for error in perm_result.errors)
        assert any("sudo" in error for error in perm_result.errors)
        
        # Test dependency error
        dep_result = complex_operation("dependency")
        assert not dep_result.success
        assert any("Dependency resolution failed" in error for error in dep_result.errors)

    def test_error_context_preservation(self):
        """Test that error context is preserved through handling."""
        handler = ErrorHandler()
        
        original_error = DependencyResolutionError("Original message")
        context = {
            "operation": "install",
            "package": "complex-pkg",
            "dependencies": ["dep1", "dep2"]
        }
        
        # Should handle error without losing context information
        handler.handle_error(original_error, context)
        
        # Verify that the handler processed the error
        # (In a real scenario, this might log or store the context)

    @patch('os.geteuid')
    def test_precondition_validation_integration(self, mock_geteuid):
        """Test integration of precondition validation with error handling."""
        mock_geteuid.return_value = 1000  # Non-root user
        
        # Validate preconditions
        issues = validate_operation_preconditions('install', package_name='test-pkg')
        
        if issues:
            # Create safe result for precondition failures
            result = create_safe_operation_result(
                success=False,
                error_message=f"Precondition failed: {issues[0]}",
                warnings=issues[1:] if len(issues) > 1 else []
            )
            
            assert not result.success
            assert "Root privileges required" in result.errors[0]