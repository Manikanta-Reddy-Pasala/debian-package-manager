"""Tests for core package engine."""

import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.engine import PackageEngine
from debian_metapackage_manager.models import Package, DependencyPlan, OperationResult, PackageStatus
from debian_metapackage_manager.config import Config


def create_mock_components():
    """Create mock components for testing."""
    mocks = {}
    
    # Mock APT interface
    mocks['apt'] = Mock()
    mocks['apt'].is_installed.return_value = False
    mocks['apt'].get_package_info.return_value = Package(name="test", version="1.0.0")
    mocks['apt'].install.return_value = True
    mocks['apt'].remove.return_value = True
    
    # Mock DPKG interface
    mocks['dpkg'] = Mock()
    mocks['dpkg'].force_remove.return_value = True
    mocks['dpkg'].fix_broken_packages.return_value = True
    mocks['dpkg'].list_broken_packages.return_value = []
    mocks['dpkg'].detect_locks.return_value = []
    mocks['dpkg'].get_installed_packages.return_value = []
    
    # Mock classifier
    mocks['classifier'] = Mock()
    mocks['classifier'].is_custom_package.return_value = False
    mocks['classifier'].is_metapackage.return_value = False
    mocks['classifier'].get_removal_risk_level.return_value = "LOW"
    
    # Mock mode manager
    mocks['mode_manager'] = Mock()
    mocks['mode_manager'].get_package_version_for_mode.return_value = "1.0.0"
    mocks['mode_manager'].is_offline_mode.return_value = False
    mocks['mode_manager'].validate_pinned_versions.return_value = (True, [])
    
    # Mock dependency resolver
    mocks['dependency_resolver'] = Mock()
    mocks['dependency_resolver'].resolve_dependencies.return_value = DependencyPlan(
        to_install=[Package(name="test", version="1.0.0")],
        to_remove=[],
        to_upgrade=[],
        conflicts=[]
    )
    mocks['dependency_resolver'].validate_resolution_plan.return_value = (True, [])
    mocks['dependency_resolver'].create_installation_order.return_value = [Package(name="test", version="1.0.0")]
    
    # Mock conflict handler
    mocks['conflict_handler'] = Mock()
    mocks['conflict_handler'].handle_conflicts.return_value = (True, DependencyPlan(
        to_install=[Package(name="test", version="1.0.0")],
        to_remove=[],
        to_upgrade=[],
        conflicts=[]
    ))
    mocks['conflict_handler']._prompt_for_removals.return_value = True
    mocks['conflict_handler'].prompt_for_force_mode.return_value = True
    
    return mocks


def test_package_engine_creation():
    """Test package engine can be created."""
    engine = PackageEngine()
    assert engine is not None


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_install_package_success(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test successful package installation."""
    mocks = create_mock_components()
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.install_package("test-package")
    
    assert result.success is True
    assert len(result.packages_affected) > 0
    assert result.packages_affected[0].name == "test"


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_install_package_already_installed(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test installing already installed package."""
    mocks = create_mock_components()
    mocks['apt'].is_installed.return_value = True
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.install_package("test-package")
    
    assert result.success is True
    assert len(result.warnings) > 0
    assert "already installed" in result.warnings[0]


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_install_package_validation_failure(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test package installation with validation failure."""
    mocks = create_mock_components()
    mocks['dependency_resolver'].validate_resolution_plan.return_value = (False, ["Validation error"])
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.install_package("test-package")
    
    assert result.success is False
    assert len(result.errors) > 0
    assert "Validation error" in result.errors


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_install_package_user_cancellation(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test package installation cancelled by user."""
    mocks = create_mock_components()
    
    # Create a plan with conflicts to trigger conflict handling
    plan_with_conflicts = DependencyPlan(
        to_install=[Package(name="test", version="1.0.0")],
        to_remove=[Package(name="conflict", version="1.0.0")],
        to_upgrade=[],
        conflicts=[]
    )
    mocks['dependency_resolver'].resolve_dependencies.return_value = plan_with_conflicts
    mocks['conflict_handler'].handle_conflicts.return_value = (False, plan_with_conflicts)
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.install_package("test-package")
    
    assert result.success is False
    assert len(result.warnings) > 0
    assert "cancelled by user" in result.warnings[0]


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_remove_package_success(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test successful package removal."""
    mocks = create_mock_components()
    mocks['apt'].is_installed.return_value = True
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.remove_package("test-package")
    
    assert result.success is True
    assert len(result.packages_affected) > 0


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_remove_package_not_installed(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test removing package that's not installed."""
    mocks = create_mock_components()
    mocks['apt'].is_installed.return_value = False
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.remove_package("test-package")
    
    assert result.success is True
    assert len(result.warnings) > 0
    assert "not installed" in result.warnings[0]


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_remove_package_high_risk(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test removing high-risk package."""
    mocks = create_mock_components()
    mocks['apt'].is_installed.return_value = True
    mocks['classifier'].get_removal_risk_level.return_value = "HIGH"
    mocks['conflict_handler']._prompt_for_removals.return_value = False  # User declines
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.remove_package("critical-package")
    
    assert result.success is False
    assert len(result.warnings) > 0
    assert "cancelled by user" in result.warnings[0]


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_remove_package_force_mode(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test force removal when normal removal fails."""
    mocks = create_mock_components()
    mocks['apt'].is_installed.return_value = True
    mocks['apt'].remove.return_value = False  # Normal removal fails
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.remove_package("test-package", force=True)
    
    assert result.success is True
    assert len(result.warnings) > 0
    assert "force methods" in result.warnings[0]


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_get_package_info(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test getting package information."""
    mocks = create_mock_components()
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    package_info = engine.get_package_info("test-package")
    
    assert package_info is not None
    assert package_info.name == "test"
    assert package_info.version == "1.0.0"


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_list_installed_packages(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test listing installed packages."""
    mocks = create_mock_components()
    mocks['dpkg'].get_installed_packages.return_value = [
        Package(name="package1", version="1.0.0"),
        Package(name="package2", version="2.0.0")
    ]
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    packages = engine.list_installed_packages()
    
    assert len(packages) == 2
    assert packages[0].name == "package1"
    assert packages[1].name == "package2"


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_check_system_health_healthy(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test system health check - healthy system."""
    mocks = create_mock_components()
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.check_system_health()
    
    assert result.success is True
    assert len(result.errors) == 0


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_check_system_health_broken_packages(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test system health check - broken packages."""
    mocks = create_mock_components()
    mocks['dpkg'].list_broken_packages.return_value = [
        Package(name="broken-pkg", version="1.0.0", status=PackageStatus.BROKEN)
    ]
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.check_system_health()
    
    assert result.success is False
    assert len(result.errors) > 0
    assert "Broken package" in result.errors[0]


@patch('debian_metapackage_manager.engine.APTInterface')
@patch('debian_metapackage_manager.engine.DPKGInterface')
@patch('debian_metapackage_manager.engine.PackageClassifier')
@patch('debian_metapackage_manager.engine.ModeManager')
@patch('debian_metapackage_manager.engine.DependencyResolver')
@patch('debian_metapackage_manager.engine.ConflictHandler')
def test_fix_broken_system(mock_conflict, mock_resolver, mock_mode, mock_classifier, mock_dpkg, mock_apt):
    """Test fixing broken system."""
    mocks = create_mock_components()
    mocks['dpkg'].list_broken_packages.return_value = [
        Package(name="broken-pkg", version="1.0.0", status=PackageStatus.BROKEN)
    ]
    mocks['dpkg'].reconfigure_package.return_value = True
    
    # Setup mocks
    mock_apt.return_value = mocks['apt']
    mock_dpkg.return_value = mocks['dpkg']
    mock_classifier.return_value = mocks['classifier']
    mock_mode.return_value = mocks['mode_manager']
    mock_resolver.return_value = mocks['dependency_resolver']
    mock_conflict.return_value = mocks['conflict_handler']
    
    engine = PackageEngine()
    result = engine.fix_broken_system()
    
    assert result.success is True
    assert len(result.packages_affected) > 0
    assert result.packages_affected[0].name == "broken-pkg"


if __name__ == "__main__":
    test_package_engine_creation()
    test_install_package_success()
    test_install_package_already_installed()
    test_install_package_validation_failure()
    test_install_package_user_cancellation()
    test_remove_package_success()
    test_remove_package_not_installed()
    test_remove_package_high_risk()
    test_remove_package_force_mode()
    test_get_package_info()
    test_list_installed_packages()
    test_check_system_health_healthy()
    test_check_system_health_broken_packages()
    test_fix_broken_system()
    print("All package engine tests passed!")