"""Tests for operation data models."""

import pytest
from debian_metapackage_manager.models.operations import (
    Conflict, DependencyPlan, OperationResult
)
from debian_metapackage_manager.models.package import Package, PackageStatus


class TestConflict:
    """Test suite for Conflict model."""

    def test_conflict_creation(self):
        """Test basic conflict creation."""
        pkg1 = Package(name="app-v1", version="1.0.0")
        pkg2 = Package(name="app-v2", version="2.0.0")
        reason = "Version conflict"
        
        conflict = Conflict(package=pkg1, conflicting_package=pkg2, reason=reason)
        
        assert conflict.package == pkg1
        assert conflict.conflicting_package == pkg2
        assert conflict.reason == reason

    def test_conflict_string_representation(self):
        """Test conflict string representation."""
        pkg1 = Package(name="app-v1", version="1.0.0")
        pkg2 = Package(name="app-v2", version="2.0.0")
        conflict = Conflict(
            package=pkg1, 
            conflicting_package=pkg2, 
            reason="Version conflict"
        )
        
        expected = "app-v1 conflicts with app-v2: Version conflict"
        assert str(conflict) == expected

    def test_conflict_with_empty_reason(self):
        """Test conflict with empty reason."""
        pkg1 = Package(name="pkg1", version="1.0.0")
        pkg2 = Package(name="pkg2", version="1.0.0")
        conflict = Conflict(package=pkg1, conflicting_package=pkg2, reason="")
        
        expected = "pkg1 conflicts with pkg2: "
        assert str(conflict) == expected


class TestDependencyPlan:
    """Test suite for DependencyPlan model."""

    def test_dependency_plan_creation_empty(self):
        """Test creating empty dependency plan."""
        plan = DependencyPlan(
            to_install=[],
            to_remove=[],
            to_upgrade=[],
            conflicts=[]
        )
        
        assert plan.to_install == []
        assert plan.to_remove == []
        assert plan.to_upgrade == []
        assert plan.conflicts == []
        assert not plan.requires_user_confirmation

    def test_dependency_plan_creation_with_data(self):
        """Test creating dependency plan with data."""
        pkg_install = Package(name="new-pkg", version="1.0.0")
        pkg_remove = Package(name="old-pkg", version="0.9.0")
        pkg_upgrade = Package(name="existing-pkg", version="1.1.0")
        
        conflict = Conflict(
            package=pkg_install,
            conflicting_package=pkg_remove,
            reason="Test conflict"
        )
        
        plan = DependencyPlan(
            to_install=[pkg_install],
            to_remove=[pkg_remove],
            to_upgrade=[pkg_upgrade],
            conflicts=[conflict],
            requires_user_confirmation=True
        )
        
        assert len(plan.to_install) == 1
        assert len(plan.to_remove) == 1
        assert len(plan.to_upgrade) == 1
        assert len(plan.conflicts) == 1
        assert plan.requires_user_confirmation

    def test_dependency_plan_total_operations(self):
        """Test total operations calculation."""
        pkg1 = Package(name="pkg1", version="1.0.0")
        pkg2 = Package(name="pkg2", version="1.0.0")
        pkg3 = Package(name="pkg3", version="1.0.0")
        
        plan = DependencyPlan(
            to_install=[pkg1, pkg2],
            to_remove=[pkg3],
            to_upgrade=[],
            conflicts=[]
        )
        
        assert plan.total_operations == 3

    def test_dependency_plan_has_conflicts_true(self):
        """Test has_conflicts property when conflicts exist."""
        conflict = Conflict(
            package=Package(name="pkg1", version="1.0.0"),
            conflicting_package=Package(name="pkg2", version="1.0.0"),
            reason="Test"
        )
        
        plan = DependencyPlan(
            to_install=[],
            to_remove=[],
            to_upgrade=[],
            conflicts=[conflict]
        )
        
        assert plan.has_conflicts

    def test_dependency_plan_has_conflicts_false(self):
        """Test has_conflicts property when no conflicts."""
        plan = DependencyPlan(
            to_install=[],
            to_remove=[],
            to_upgrade=[],
            conflicts=[]
        )
        
        assert not plan.has_conflicts

    def test_dependency_plan_string_representation(self):
        """Test dependency plan string representation."""
        pkg1 = Package(name="pkg1", version="1.0.0")
        pkg2 = Package(name="pkg2", version="1.0.0")
        
        conflict = Conflict(
            package=pkg1,
            conflicting_package=pkg2,
            reason="Test"
        )
        
        plan = DependencyPlan(
            to_install=[pkg1],
            to_remove=[pkg2],
            to_upgrade=[],
            conflicts=[conflict]
        )
        
        expected = "DependencyPlan(install=1, remove=1, upgrade=0, conflicts=1)"
        assert str(plan) == expected

    def test_dependency_plan_post_init_none_values(self):
        """Test __post_init__ with None values."""
        plan = DependencyPlan(
            to_install=None,
            to_remove=None,
            to_upgrade=None,
            conflicts=None
        )
        
        assert plan.to_install == []
        assert plan.to_remove == []
        assert plan.to_upgrade == []
        assert plan.conflicts == []


class TestOperationResult:
    """Test suite for OperationResult model."""

    def test_operation_result_success(self):
        """Test successful operation result."""
        pkg = Package(name="test-pkg", version="1.0.0")
        
        result = OperationResult(
            success=True,
            packages_affected=[pkg],
            warnings=[],
            errors=[],
            user_confirmations_required=[]
        )
        
        assert result.success
        assert len(result.packages_affected) == 1
        assert result.packages_affected[0] == pkg
        assert not result.has_warnings
        assert not result.has_errors

    def test_operation_result_failure(self):
        """Test failed operation result."""
        result = OperationResult(
            success=False,
            packages_affected=[],
            warnings=["Warning message"],
            errors=["Error message"],
            user_confirmations_required=["Confirm action"]
        )
        
        assert not result.success
        assert len(result.packages_affected) == 0
        assert result.has_warnings
        assert result.has_errors
        assert len(result.warnings) == 1
        assert len(result.errors) == 1
        assert len(result.user_confirmations_required) == 1

    def test_operation_result_has_warnings_property(self):
        """Test has_warnings property."""
        result_no_warnings = OperationResult(
            success=True,
            packages_affected=[],
            warnings=[],
            errors=[],
            user_confirmations_required=[]
        )
        
        result_with_warnings = OperationResult(
            success=True,
            packages_affected=[],
            warnings=["Warning"],
            errors=[],
            user_confirmations_required=[]
        )
        
        assert not result_no_warnings.has_warnings
        assert result_with_warnings.has_warnings

    def test_operation_result_has_errors_property(self):
        """Test has_errors property."""
        result_no_errors = OperationResult(
            success=True,
            packages_affected=[],
            warnings=[],
            errors=[],
            user_confirmations_required=[]
        )
        
        result_with_errors = OperationResult(
            success=False,
            packages_affected=[],
            warnings=[],
            errors=["Error"],
            user_confirmations_required=[]
        )
        
        assert not result_no_errors.has_errors
        assert result_with_errors.has_errors

    def test_operation_result_add_warning(self):
        """Test adding warnings to result."""
        result = OperationResult(
            success=True,
            packages_affected=[],
            warnings=[],
            errors=[],
            user_confirmations_required=[]
        )
        
        assert not result.has_warnings
        
        result.add_warning("First warning")
        assert result.has_warnings
        assert len(result.warnings) == 1
        assert result.warnings[0] == "First warning"
        
        result.add_warning("Second warning")
        assert len(result.warnings) == 2

    def test_operation_result_add_error(self):
        """Test adding errors to result."""
        result = OperationResult(
            success=True,
            packages_affected=[],
            warnings=[],
            errors=[],
            user_confirmations_required=[]
        )
        
        assert result.success
        assert not result.has_errors
        
        result.add_error("First error")
        assert not result.success  # Should set success to False
        assert result.has_errors
        assert len(result.errors) == 1
        assert result.errors[0] == "First error"
        
        result.add_error("Second error")
        assert len(result.errors) == 2

    def test_operation_result_string_representation(self):
        """Test operation result string representation."""
        pkg = Package(name="test-pkg", version="1.0.0")
        
        success_result = OperationResult(
            success=True,
            packages_affected=[pkg],
            warnings=["Warning"],
            errors=[],
            user_confirmations_required=[]
        )
        
        failure_result = OperationResult(
            success=False,
            packages_affected=[],
            warnings=[],
            errors=["Error1", "Error2"],
            user_confirmations_required=[]
        )
        
        assert str(success_result) == "OperationResult(SUCCESS, packages=1, warnings=1, errors=0)"
        assert str(failure_result) == "OperationResult(FAILED, packages=0, warnings=0, errors=2)"

    def test_operation_result_with_details(self):
        """Test operation result with details dictionary."""
        result = OperationResult(
            success=True,
            packages_affected=[],
            warnings=[],
            errors=[],
            user_confirmations_required=[],
            details={"space_freed": 1024, "time_taken": 30}
        )
        
        assert result.details["space_freed"] == 1024
        assert result.details["time_taken"] == 30

    def test_operation_result_post_init_none_values(self):
        """Test __post_init__ with None values."""
        result = OperationResult(
            success=True,
            packages_affected=None,
            warnings=None,
            errors=None,
            user_confirmations_required=None
        )
        
        assert result.packages_affected == []
        assert result.warnings == []
        assert result.errors == []
        assert result.user_confirmations_required == []
        assert result.details == {}


class TestOperationResultEdgeCases:
    """Test edge cases for OperationResult."""

    def test_operation_result_multiple_warnings_and_errors(self):
        """Test result with multiple warnings and errors."""
        result = OperationResult(
            success=False,
            packages_affected=[],
            warnings=["Warning 1", "Warning 2", "Warning 3"],
            errors=["Error 1", "Error 2"],
            user_confirmations_required=[]
        )
        
        assert len(result.warnings) == 3
        assert len(result.errors) == 2
        assert result.has_warnings
        assert result.has_errors
        assert not result.success

    def test_operation_result_empty_strings(self):
        """Test result with empty string messages."""
        result = OperationResult(
            success=True,
            packages_affected=[],
            warnings=[""],
            errors=[""],
            user_confirmations_required=[""]
        )
        
        assert result.has_warnings  # Empty string still counts as a warning
        assert result.has_errors    # Empty string still counts as an error

    def test_operation_result_large_package_list(self):
        """Test result with many packages."""
        packages = [
            Package(name=f"pkg-{i}", version="1.0.0") 
            for i in range(100)
        ]
        
        result = OperationResult(
            success=True,
            packages_affected=packages,
            warnings=[],
            errors=[],
            user_confirmations_required=[]
        )
        
        assert len(result.packages_affected) == 100
        expected_str = "OperationResult(SUCCESS, packages=100, warnings=0, errors=0)"
        assert str(result) == expected_str


class TestModelsIntegration:
    """Integration tests between different model classes."""

    def test_conflict_in_dependency_plan(self):
        """Test conflict within a dependency plan."""
        pkg1 = Package(name="app-old", version="1.0.0")
        pkg2 = Package(name="app-new", version="2.0.0")
        
        conflict = Conflict(
            package=pkg2,
            conflicting_package=pkg1,
            reason="Version incompatibility"
        )
        
        plan = DependencyPlan(
            to_install=[pkg2],
            to_remove=[pkg1],
            to_upgrade=[],
            conflicts=[conflict]
        )
        
        assert plan.has_conflicts
        assert plan.total_operations == 2
        assert len(plan.conflicts) == 1
        assert plan.conflicts[0].reason == "Version incompatibility"

    def test_complex_dependency_plan_in_operation_result(self):
        """Test complex scenario with plan and result."""
        # Setup packages
        new_pkg = Package(name="new-feature", version="1.0.0", is_custom=True)
        old_pkg = Package(name="old-feature", version="0.9.0", is_custom=True)
        upgrade_pkg = Package(name="core-lib", version="2.0.0")
        
        # Create conflict
        conflict = Conflict(
            package=new_pkg,
            conflicting_package=old_pkg,
            reason="Feature replacement"
        )
        
        # Create dependency plan
        plan = DependencyPlan(
            to_install=[new_pkg],
            to_remove=[old_pkg],
            to_upgrade=[upgrade_pkg],
            conflicts=[conflict],
            requires_user_confirmation=True
        )
        
        # Create operation result
        result = OperationResult(
            success=True,
            packages_affected=[new_pkg, upgrade_pkg],  # old_pkg was removed
            warnings=["Replaced old-feature with new-feature"],
            errors=[],
            user_confirmations_required=["Confirm feature replacement"],
            details={"dependency_plan": plan}
        )
        
        # Verify integration
        assert result.success
        assert len(result.packages_affected) == 2
        assert result.has_warnings
        assert not result.has_errors
        assert len(result.user_confirmations_required) == 1
        
        # Verify embedded plan
        embedded_plan = result.details["dependency_plan"]
        assert embedded_plan.total_operations == 3
        assert embedded_plan.has_conflicts
        assert embedded_plan.requires_user_confirmation