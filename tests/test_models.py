"""Tests for core data models."""

import pytest
from debian_metapackage_manager.models import (
    Package, PackageStatus, PackageType, Conflict, 
    DependencyPlan, OperationResult
)


def test_package_creation():
    """Test Package model creation and defaults."""
    package = Package(name="test-package", version="1.0.0")
    
    assert package.name == "test-package"
    assert package.version == "1.0.0"
    assert package.is_metapackage is False
    assert package.is_custom is False
    assert package.dependencies == []
    assert package.conflicts == []
    assert package.status == PackageStatus.NOT_INSTALLED


def test_package_with_dependencies():
    """Test Package with dependencies."""
    dep1 = Package(name="dep1", version="1.0.0")
    dep2 = Package(name="dep2", version="2.0.0")
    
    package = Package(
        name="main-package", 
        version="1.0.0",
        dependencies=[dep1, dep2]
    )
    
    assert len(package.dependencies) == 2
    assert package.dependencies[0].name == "dep1"
    assert package.dependencies[1].name == "dep2"


def test_conflict_creation():
    """Test Conflict model creation."""
    pkg1 = Package(name="package1", version="1.0.0")
    pkg2 = Package(name="package2", version="2.0.0")
    
    conflict = Conflict(
        package=pkg1,
        conflicting_package=pkg2,
        reason="Version conflict"
    )
    
    assert conflict.package.name == "package1"
    assert conflict.conflicting_package.name == "package2"
    assert conflict.reason == "Version conflict"


def test_dependency_plan_creation():
    """Test DependencyPlan model creation."""
    pkg1 = Package(name="install-pkg", version="1.0.0")
    pkg2 = Package(name="remove-pkg", version="1.0.0")
    
    plan = DependencyPlan(
        to_install=[pkg1],
        to_remove=[pkg2],
        to_upgrade=[],
        conflicts=[]
    )
    
    assert len(plan.to_install) == 1
    assert len(plan.to_remove) == 1
    assert len(plan.to_upgrade) == 0
    assert len(plan.conflicts) == 0
    assert plan.requires_user_confirmation is False


def test_operation_result_creation():
    """Test OperationResult model creation."""
    pkg = Package(name="test-pkg", version="1.0.0")
    
    result = OperationResult(
        success=True,
        packages_affected=[pkg],
        warnings=["Warning message"],
        errors=[],
        user_confirmations_required=[]
    )
    
    assert result.success is True
    assert len(result.packages_affected) == 1
    assert result.packages_affected[0].name == "test-pkg"
    assert len(result.warnings) == 1
    assert result.warnings[0] == "Warning message"