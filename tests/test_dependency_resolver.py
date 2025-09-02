"""Tests for dependency resolution engine."""

import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.dependency_resolver import DependencyResolver
from debian_metapackage_manager.models import Package, Conflict, PackageStatus, PackageType
from debian_metapackage_manager.apt_interface import APTInterface
from debian_metapackage_manager.classifier import PackageClassifier
from debian_metapackage_manager.config import Config


def create_mock_apt():
    """Create a mock APT interface."""
    mock_apt = Mock(spec=APTInterface)
    mock_apt.is_installed.return_value = False
    mock_apt.get_dependencies.return_value = []
    mock_apt.check_conflicts.return_value = []
    mock_apt.get_package_info.return_value = None
    return mock_apt


def create_mock_classifier():
    """Create a mock package classifier."""
    mock_classifier = Mock(spec=PackageClassifier)
    mock_classifier.is_custom_package.return_value = False
    mock_classifier.is_metapackage.return_value = False
    mock_classifier.should_prioritize_preservation.return_value = False
    mock_classifier.get_removal_risk_level.return_value = "LOW"
    mock_classifier.get_package_category_summary.return_value = "test packages"
    return mock_classifier


def test_dependency_resolver_creation():
    """Test dependency resolver can be created."""
    resolver = DependencyResolver()
    assert resolver is not None


def test_resolve_dependencies_simple():
    """Test simple dependency resolution."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    # Mock dependencies
    dep1 = Package(name="dep1", version="1.0.0")
    dep2 = Package(name="dep2", version="2.0.0")
    mock_apt.get_dependencies.return_value = [dep1, dep2]
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    
    main_package = Package(name="main-package", version="1.0.0")
    plan = resolver.resolve_dependencies(main_package)
    
    assert len(plan.to_install) == 3  # main package + 2 dependencies
    assert main_package in plan.to_install
    assert dep1 in plan.to_install
    assert dep2 in plan.to_install


def test_resolve_dependencies_with_conflicts():
    """Test dependency resolution with conflicts."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    # Mock a conflict
    main_package = Package(name="main-package", version="1.0.0")
    conflicting_package = Package(name="conflicting-package", version="1.0.0")
    conflict = Conflict(
        package=main_package,
        conflicting_package=conflicting_package,
        reason="Version conflict"
    )
    
    mock_apt.check_conflicts.return_value = [conflict]
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    plan = resolver.resolve_dependencies(main_package)
    
    assert len(plan.conflicts) == 1
    assert plan.requires_user_confirmation is True
    assert len(plan.to_remove) >= 1


def test_resolve_conflicts():
    """Test conflict resolution."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    pkg1 = Package(name="package1", version="1.0.0")
    pkg2 = Package(name="package2", version="2.0.0")
    conflict = Conflict(package=pkg1, conflicting_package=pkg2, reason="Test conflict")
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    plan = resolver.resolve_conflicts([conflict])
    
    assert len(plan.conflicts) == 1
    assert plan.requires_user_confirmation is True
    assert len(plan.to_remove) >= 1


def test_choose_removal_candidate_system_vs_custom():
    """Test removal candidate selection prioritizing system packages."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    # Mock system package preservation
    def mock_preserve(name):
        return name == "system-package"
    
    mock_classifier.should_prioritize_preservation.side_effect = mock_preserve
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    
    system_pkg = Package(name="system-package", version="1.0.0")
    custom_pkg = Package(name="custom-package", version="1.0.0")
    
    # System package should be preserved, custom should be removed
    candidate = resolver._choose_removal_candidate(system_pkg, custom_pkg)
    assert candidate == custom_pkg
    
    candidate = resolver._choose_removal_candidate(custom_pkg, system_pkg)
    assert candidate == custom_pkg


def test_choose_removal_candidate_custom_vs_regular():
    """Test removal candidate selection between custom and regular packages."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    # Mock custom package detection
    def mock_custom(name):
        return name == "custom-package"
    
    mock_classifier.is_custom_package.side_effect = mock_custom
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    
    custom_pkg = Package(name="custom-package", version="1.0.0")
    regular_pkg = Package(name="regular-package", version="1.0.0")
    
    # Custom package should be removed over regular package
    candidate = resolver._choose_removal_candidate(custom_pkg, regular_pkg)
    assert candidate == custom_pkg
    
    candidate = resolver._choose_removal_candidate(regular_pkg, custom_pkg)
    assert candidate == custom_pkg


def test_create_installation_order():
    """Test creation of installation order."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    # Mock dependencies: pkg1 depends on pkg2, pkg2 depends on pkg3
    def mock_get_deps(name):
        if name == "pkg1":
            return [Package(name="pkg2", version="1.0.0")]
        elif name == "pkg2":
            return [Package(name="pkg3", version="1.0.0")]
        else:
            return []
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    resolver._get_all_dependencies = mock_get_deps
    
    packages = [
        Package(name="pkg1", version="1.0.0"),
        Package(name="pkg2", version="1.0.0"),
        Package(name="pkg3", version="1.0.0")
    ]
    
    ordered = resolver.create_installation_order(packages)
    
    # pkg3 should come first (no dependencies), then pkg2, then pkg1
    pkg_names = [pkg.name for pkg in ordered]
    assert pkg_names.index("pkg3") < pkg_names.index("pkg2")
    assert pkg_names.index("pkg2") < pkg_names.index("pkg1")


def test_validate_resolution_plan_success():
    """Test validation of a good resolution plan."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    
    # Create a simple plan with no issues
    from debian_metapackage_manager.models import DependencyPlan
    plan = DependencyPlan(
        to_install=[Package(name="safe-package", version="1.0.0")],
        to_remove=[],
        to_upgrade=[],
        conflicts=[]
    )
    
    # Mock no circular dependencies
    resolver._has_circular_dependency = Mock(return_value=False)
    
    is_valid, issues = resolver.validate_resolution_plan(plan)
    
    assert is_valid is True
    assert len(issues) == 0


def test_validate_resolution_plan_high_risk_removal():
    """Test validation with high-risk package removal."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    # Mock high-risk package
    def mock_preserve(name):
        return name == "critical-system-package"
    
    def mock_risk_level(name):
        return "HIGH" if name == "critical-system-package" else "LOW"
    
    mock_classifier.should_prioritize_preservation.side_effect = mock_preserve
    mock_classifier.get_removal_risk_level.side_effect = mock_risk_level
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    
    from debian_metapackage_manager.models import DependencyPlan
    plan = DependencyPlan(
        to_install=[],
        to_remove=[Package(name="critical-system-package", version="1.0.0")],
        to_upgrade=[],
        conflicts=[]
    )
    
    resolver._has_circular_dependency = Mock(return_value=False)
    
    is_valid, issues = resolver.validate_resolution_plan(plan)
    
    assert is_valid is False
    assert len(issues) > 0
    assert "High-risk removal" in issues[0]


def test_get_resolution_summary():
    """Test generation of resolution summary."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    # Mock category summary
    mock_classifier.get_package_category_summary.return_value = "2 custom packages"
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    
    from debian_metapackage_manager.models import DependencyPlan
    plan = DependencyPlan(
        to_install=[
            Package(name="pkg1", version="1.0.0"),
            Package(name="pkg2", version="1.0.0")
        ],
        to_remove=[Package(name="old-pkg", version="1.0.0")],
        to_upgrade=[],
        conflicts=[]
    )
    
    summary = resolver.get_resolution_summary(plan)
    
    assert "Install:" in summary
    assert "Remove:" in summary
    assert "2 custom packages" in summary


def test_get_all_dependencies_recursive():
    """Test recursive dependency resolution."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    # Mock recursive dependencies
    def mock_get_deps(name):
        if name == "main":
            return [Package(name="dep1", version="1.0.0")]
        elif name == "dep1":
            return [Package(name="dep2", version="1.0.0")]
        else:
            return []
    
    mock_apt.get_dependencies.side_effect = mock_get_deps
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    deps = resolver._get_all_dependencies("main")
    
    dep_names = [dep.name for dep in deps]
    assert "dep1" in dep_names
    assert "dep2" in dep_names


def test_get_all_dependencies_circular():
    """Test handling of circular dependencies."""
    mock_apt = create_mock_apt()
    mock_classifier = create_mock_classifier()
    
    # Mock circular dependencies: A -> B -> A
    def mock_get_deps(name):
        if name == "pkgA":
            return [Package(name="pkgB", version="1.0.0")]
        elif name == "pkgB":
            return [Package(name="pkgA", version="1.0.0")]
        else:
            return []
    
    mock_apt.get_dependencies.side_effect = mock_get_deps
    
    resolver = DependencyResolver(mock_apt, mock_classifier)
    deps = resolver._get_all_dependencies("pkgA")
    
    # Should not get stuck in infinite loop
    assert len(deps) >= 1
    dep_names = [dep.name for dep in deps]
    assert "pkgB" in dep_names


if __name__ == "__main__":
    test_dependency_resolver_creation()
    test_resolve_dependencies_simple()
    test_resolve_dependencies_with_conflicts()
    test_resolve_conflicts()
    test_choose_removal_candidate_system_vs_custom()
    test_choose_removal_candidate_custom_vs_regular()
    test_create_installation_order()
    test_validate_resolution_plan_success()
    test_validate_resolution_plan_high_risk_removal()
    test_get_resolution_summary()
    test_get_all_dependencies_recursive()
    test_get_all_dependencies_circular()
    print("All dependency resolver tests passed!")