"""Tests for mode management system."""

import os
import sys
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.mode_manager import ModeManager
from debian_metapackage_manager.config import Config
from debian_metapackage_manager.apt_interface import APTInterface
from debian_metapackage_manager.models import Package


def create_mock_config():
    """Create a mock configuration."""
    mock_config = Mock(spec=Config)
    mock_config.is_offline_mode.return_value = False
    mock_config.get_pinned_version.return_value = None
    mock_config.set_offline_mode = Mock()
    mock_config.set_pinned_version = Mock()
    mock_config.version_pinning = Mock()
    mock_config.version_pinning.get_all_pinned.return_value = {}
    mock_config.version_pinning.has_pinned_version.return_value = False
    return mock_config


def create_mock_apt():
    """Create a mock APT interface."""
    mock_apt = Mock(spec=APTInterface)
    mock_apt.is_installed.return_value = False
    mock_apt.get_package_info.return_value = None
    mock_apt.get_available_versions.return_value = []
    mock_apt.get_dependencies.return_value = []
    mock_apt.update_package_cache.return_value = True
    return mock_apt


def test_mode_manager_creation():
    """Test mode manager can be created."""
    manager = ModeManager()
    assert manager is not None


def test_is_offline_mode_config_setting():
    """Test offline mode detection from config."""
    mock_config = create_mock_config()
    mock_config.is_offline_mode.return_value = True
    
    manager = ModeManager(mock_config)
    assert manager.is_offline_mode() is True


@patch('subprocess.run')
def test_is_network_available_success(mock_run):
    """Test network availability check - success."""
    mock_run.return_value = Mock(returncode=0)
    
    manager = ModeManager()
    assert manager.is_network_available() is True


@patch('subprocess.run')
def test_is_network_available_failure(mock_run):
    """Test network availability check - failure."""
    mock_run.return_value = Mock(returncode=1)
    
    manager = ModeManager()
    assert manager.is_network_available() is False


@patch('subprocess.run')
def test_is_network_available_timeout(mock_run):
    """Test network availability check - timeout."""
    mock_run.side_effect = subprocess.TimeoutExpired('ping', 5)
    
    manager = ModeManager()
    assert manager.is_network_available() is False


@patch('subprocess.run')
def test_are_repositories_accessible_success(mock_run):
    """Test repository accessibility check - success."""
    mock_run.return_value = Mock(returncode=0)
    
    manager = ModeManager()
    assert manager.are_repositories_accessible() is True


@patch('subprocess.run')
def test_are_repositories_accessible_failure(mock_run):
    """Test repository accessibility check - failure."""
    mock_run.return_value = Mock(returncode=1)
    
    manager = ModeManager()
    assert manager.are_repositories_accessible() is False


def test_switch_to_offline_mode():
    """Test switching to offline mode."""
    mock_config = create_mock_config()
    
    manager = ModeManager(mock_config)
    manager.switch_to_offline_mode()
    
    mock_config.set_offline_mode.assert_called_once_with(True)


@patch.object(ModeManager, 'is_network_available', return_value=True)
@patch.object(ModeManager, 'are_repositories_accessible', return_value=True)
def test_switch_to_online_mode_success(mock_repos, mock_network):
    """Test switching to online mode - success."""
    mock_config = create_mock_config()
    
    manager = ModeManager(mock_config)
    manager.switch_to_online_mode()
    
    mock_config.set_offline_mode.assert_called_once_with(False)


@patch.object(ModeManager, 'is_network_available', return_value=False)
@patch.object(ModeManager, 'are_repositories_accessible', return_value=False)
def test_switch_to_online_mode_failure(mock_repos, mock_network):
    """Test switching to online mode - failure."""
    mock_config = create_mock_config()
    
    manager = ModeManager(mock_config)
    manager.switch_to_online_mode()
    
    # Should not call set_offline_mode(False) when network unavailable
    mock_config.set_offline_mode.assert_not_called()


def test_get_pinned_version():
    """Test getting pinned version."""
    mock_config = create_mock_config()
    mock_config.get_pinned_version.return_value = "1.0.0"
    
    manager = ModeManager(mock_config)
    version = manager._get_pinned_version("test-package")
    
    assert version == "1.0.0"
    mock_config.get_pinned_version.assert_called_once_with("test-package")


def test_get_pinned_version_fallback_installed():
    """Test getting pinned version with fallback to installed version."""
    mock_config = create_mock_config()
    mock_config.get_pinned_version.return_value = None
    
    mock_apt = create_mock_apt()
    mock_apt.is_installed.return_value = True
    mock_apt.get_package_info.return_value = Package(name="test-package", version="2.0.0")
    
    manager = ModeManager(mock_config, mock_apt)
    version = manager._get_pinned_version("test-package")
    
    assert version == "2.0.0"


def test_get_pinned_version_fallback_available():
    """Test getting pinned version with fallback to available versions."""
    mock_config = create_mock_config()
    mock_config.get_pinned_version.return_value = None
    
    mock_apt = create_mock_apt()
    mock_apt.is_installed.return_value = False
    mock_apt.get_available_versions.return_value = ["3.0.0", "2.0.0"]
    
    manager = ModeManager(mock_config, mock_apt)
    version = manager._get_pinned_version("test-package")
    
    assert version == "3.0.0"


def test_get_latest_version():
    """Test getting latest version."""
    mock_apt = create_mock_apt()
    mock_apt.get_package_info.return_value = Package(name="test-package", version="4.0.0")
    
    manager = ModeManager(apt_interface=mock_apt)
    version = manager._get_latest_version("test-package")
    
    assert version == "4.0.0"
    mock_apt.update_package_cache.assert_called_once()


@patch.object(ModeManager, 'is_offline_mode', return_value=True)
def test_get_package_version_for_mode_offline(mock_offline):
    """Test getting package version in offline mode."""
    mock_config = create_mock_config()
    mock_config.get_pinned_version.return_value = "1.0.0"
    
    manager = ModeManager(mock_config)
    version = manager.get_package_version_for_mode("test-package")
    
    assert version == "1.0.0"


@patch.object(ModeManager, 'is_offline_mode', return_value=False)
def test_get_package_version_for_mode_online(mock_offline):
    """Test getting package version in online mode."""
    mock_apt = create_mock_apt()
    mock_apt.get_package_info.return_value = Package(name="test-package", version="2.0.0")
    
    manager = ModeManager(apt_interface=mock_apt)
    version = manager.get_package_version_for_mode("test-package")
    
    assert version == "2.0.0"


def test_resolve_metapackage_versions():
    """Test resolving versions for metapackage."""
    mock_apt = create_mock_apt()
    mock_apt.get_dependencies.return_value = [
        Package(name="dep1", version="1.0.0"),
        Package(name="dep2", version="2.0.0")
    ]
    
    manager = ModeManager(apt_interface=mock_apt)
    
    # Mock get_package_version_for_mode
    def mock_version(name):
        versions = {"meta-package": "1.0.0", "dep1": "1.0.0", "dep2": "2.0.0"}
        return versions.get(name)
    
    manager.get_package_version_for_mode = mock_version
    
    versions = manager.resolve_metapackage_versions("meta-package")
    
    assert len(versions) == 3
    assert versions["meta-package"] == "1.0.0"
    assert versions["dep1"] == "1.0.0"
    assert versions["dep2"] == "2.0.0"


def test_validate_pinned_versions_success():
    """Test validation of pinned versions - success."""
    mock_config = create_mock_config()
    mock_config.version_pinning.get_all_pinned.return_value = {
        "package1": "1.0.0",
        "package2": "2.0.0"
    }
    
    mock_apt = create_mock_apt()
    mock_apt.get_available_versions.side_effect = [
        ["1.0.0", "1.1.0"],  # package1 versions
        ["2.0.0", "2.1.0"]   # package2 versions
    ]
    
    manager = ModeManager(mock_config, mock_apt)
    is_valid, issues = manager.validate_pinned_versions()
    
    assert is_valid is True
    assert len(issues) == 0


def test_validate_pinned_versions_missing_package():
    """Test validation of pinned versions - missing package."""
    mock_config = create_mock_config()
    mock_config.version_pinning.get_all_pinned.return_value = {
        "missing-package": "1.0.0"
    }
    
    mock_apt = create_mock_apt()
    mock_apt.get_available_versions.return_value = []  # No versions available
    
    manager = ModeManager(mock_config, mock_apt)
    is_valid, issues = manager.validate_pinned_versions()
    
    assert is_valid is False
    assert len(issues) == 1
    assert "missing-package" in issues[0]
    assert "not found" in issues[0]


def test_validate_pinned_versions_missing_version():
    """Test validation of pinned versions - missing version."""
    mock_config = create_mock_config()
    mock_config.version_pinning.get_all_pinned.return_value = {
        "package1": "1.0.0"
    }
    
    mock_apt = create_mock_apt()
    mock_apt.get_available_versions.return_value = ["2.0.0", "2.1.0"]  # 1.0.0 not available
    
    manager = ModeManager(mock_config, mock_apt)
    is_valid, issues = manager.validate_pinned_versions()
    
    assert is_valid is False
    assert len(issues) == 1
    assert "1.0.0" in issues[0]
    assert "not available" in issues[0]


def test_create_offline_snapshot():
    """Test creating offline snapshot."""
    mock_config = create_mock_config()
    mock_apt = create_mock_apt()
    
    # Mock installed packages
    def mock_is_installed(name):
        return name in ["package1", "package2"]
    
    def mock_get_info(name):
        versions = {"package1": "1.0.0", "package2": "2.0.0"}
        if name in versions:
            return Package(name=name, version=versions[name])
        return None
    
    mock_apt.is_installed.side_effect = mock_is_installed
    mock_apt.get_package_info.side_effect = mock_get_info
    
    manager = ModeManager(mock_config, mock_apt)
    snapshot = manager.create_offline_snapshot(["package1", "package2", "package3"])
    
    assert len(snapshot) == 2
    assert snapshot["package1"] == "1.0.0"
    assert snapshot["package2"] == "2.0.0"
    assert "package3" not in snapshot  # Not installed


def test_get_mode_status():
    """Test getting mode status."""
    mock_config = create_mock_config()
    mock_config.version_pinning.get_all_pinned.return_value = {"pkg1": "1.0.0"}
    
    manager = ModeManager(mock_config)
    
    # Mock methods
    manager.is_offline_mode = Mock(return_value=True)
    manager.is_network_available = Mock(return_value=False)
    manager.are_repositories_accessible = Mock(return_value=False)
    
    status = manager.get_mode_status()
    
    assert status['offline_mode'] is True
    assert status['network_available'] is False
    assert status['repositories_accessible'] is False
    assert status['pinned_packages_count'] == 1
    assert status['config_offline_setting'] is False


@patch.object(ModeManager, 'is_network_available', return_value=False)
def test_auto_detect_mode_no_network(mock_network):
    """Test auto-detect mode with no network."""
    mock_config = create_mock_config()
    
    manager = ModeManager(mock_config)
    mode = manager.auto_detect_mode()
    
    assert mode == "offline (no network)"
    mock_config.set_offline_mode.assert_called_once_with(True)


@patch.object(ModeManager, 'is_network_available', return_value=True)
@patch.object(ModeManager, 'are_repositories_accessible', return_value=False)
def test_auto_detect_mode_no_repos(mock_repos, mock_network):
    """Test auto-detect mode with no repository access."""
    mock_config = create_mock_config()
    
    manager = ModeManager(mock_config)
    mode = manager.auto_detect_mode()
    
    assert mode == "offline (repositories unavailable)"
    mock_config.set_offline_mode.assert_called_once_with(True)


def test_clear_network_cache():
    """Test clearing network cache."""
    manager = ModeManager()
    
    # Set some cached values
    manager._network_available = True
    manager._repository_accessible = True
    
    manager.clear_network_cache()
    
    assert manager._network_available is None
    assert manager._repository_accessible is None


if __name__ == "__main__":
    test_mode_manager_creation()
    test_is_offline_mode_config_setting()
    test_is_network_available_success()
    test_is_network_available_failure()
    test_is_network_available_timeout()
    test_are_repositories_accessible_success()
    test_are_repositories_accessible_failure()
    test_switch_to_offline_mode()
    test_switch_to_online_mode_success()
    test_switch_to_online_mode_failure()
    test_get_pinned_version()
    test_get_pinned_version_fallback_installed()
    test_get_pinned_version_fallback_available()
    test_get_latest_version()
    test_get_package_version_for_mode_offline()
    test_get_package_version_for_mode_online()
    test_resolve_metapackage_versions()
    test_validate_pinned_versions_success()
    test_validate_pinned_versions_missing_package()
    test_validate_pinned_versions_missing_version()
    test_create_offline_snapshot()
    test_get_mode_status()
    test_auto_detect_mode_no_network()
    test_auto_detect_mode_no_repos()
    test_clear_network_cache()
    print("All mode manager tests passed!")