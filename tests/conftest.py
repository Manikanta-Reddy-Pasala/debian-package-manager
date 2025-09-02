"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.config import Config
from debian_metapackage_manager.models import Package, OperationResult, PackageStatus
from debian_metapackage_manager.interfaces.apt import APTInterface
from debian_metapackage_manager.interfaces.dpkg import DPKGInterface
from debian_metapackage_manager.core import PackageManager
from debian_metapackage_manager.core.managers import PackageEngine


@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_config_dir):
    """Create a test configuration."""
    config_path = Path(temp_config_dir) / 'config.json'
    test_config_data = {
        'custom_prefixes': ['test-', 'custom-', 'dev-'],
        'offline_mode': False,
        'pinned_versions': {'test-package': '1.0.0'},
        'removable_packages': ['test-removable'],
        'force_confirmation_required': True,
        'auto_resolve_conflicts': True
    }
    
    with open(config_path, 'w') as f:
        json.dump(test_config_data, f, indent=2)
    
    return Config(str(config_path))


@pytest.fixture
def mock_apt_interface():
    """Create a mock APT interface."""
    mock = Mock(spec=APTInterface)
    mock.is_installed.return_value = False
    mock.install.return_value = True
    mock.remove.return_value = True
    mock.get_dependencies.return_value = []
    mock.check_conflicts.return_value = []
    mock.get_package_info.return_value = None
    mock.get_available_versions.return_value = ['1.0.0', '2.0.0']
    return mock


@pytest.fixture
def mock_dpkg_interface():
    """Create a mock DPKG interface."""
    mock = Mock(spec=DPKGInterface)
    mock.safe_remove.return_value = True
    mock.safe_purge.return_value = True
    mock.fix_broken_packages.return_value = True
    mock.list_broken_packages.return_value = []
    mock.detect_locks.return_value = []
    mock.get_installed_packages.return_value = []
    mock.reconfigure_package.return_value = True
    mock._handle_locks.return_value = True
    mock.get_package_status_detailed.return_value = (PackageStatus.INSTALLED, "Package is installed")
    return mock


@pytest.fixture
def test_package():
    """Create a test package."""
    return Package(
        name='test-package',
        version='1.0.0',
        is_metapackage=False,
        is_custom=True,
        status=PackageStatus.NOT_INSTALLED
    )


@pytest.fixture
def test_system_package():
    """Create a test system package."""
    return Package(
        name='libc6',
        version='2.31-0ubuntu9.7',
        is_metapackage=False,
        is_custom=False,
        status=PackageStatus.INSTALLED
    )


@pytest.fixture
def test_metapackage():
    """Create a test metapackage."""
    return Package(
        name='custom-bundle',
        version='1.0.0',
        is_metapackage=True,
        is_custom=True,
        status=PackageStatus.NOT_INSTALLED
    )


@pytest.fixture
def successful_operation_result(test_package):
    """Create a successful operation result."""
    return OperationResult(
        success=True,
        packages_affected=[test_package],
        warnings=[],
        errors=[],
        user_confirmations_required=[]
    )


@pytest.fixture
def failed_operation_result():
    """Create a failed operation result."""
    return OperationResult(
        success=False,
        packages_affected=[],
        warnings=['Test warning'],
        errors=['Test error'],
        user_confirmations_required=[]
    )


@pytest.fixture
def mock_package_manager(mock_apt_interface, mock_dpkg_interface, test_config):
    """Create a mock package manager with dependencies."""
    package_manager = PackageManager(test_config)
    package_manager.apt = mock_apt_interface
    package_manager.dpkg = mock_dpkg_interface
    return package_manager


@pytest.fixture
def mock_package_engine(mock_package_manager):
    """Create a mock package engine."""
    engine = PackageEngine(mock_package_manager.config)
    engine.package_manager = mock_package_manager
    engine.apt = mock_package_manager.apt
    engine.dpkg = mock_package_manager.dpkg
    return engine


# Test data fixtures
@pytest.fixture
def sample_packages():
    """Provide sample packages for testing."""
    return [
        Package('test-app1', '1.0.0', is_custom=True),
        Package('test-app2', '2.0.0', is_custom=True),
        Package('libc6', '2.31-0ubuntu9.7', is_custom=False),
        Package('custom-bundle', '1.0.0', is_metapackage=True, is_custom=True),
    ]


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for command execution tests."""
    with pytest.mock.patch('subprocess.run') as mock:
        mock.return_value.returncode = 0
        mock.return_value.stdout = ""
        mock.return_value.stderr = ""
        yield mock


@pytest.fixture
def mock_network_available():
    """Mock network as available."""
    with pytest.mock.patch('debian_metapackage_manager.utils.network.NetworkChecker.is_network_available') as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_network_unavailable():
    """Mock network as unavailable."""
    with pytest.mock.patch('debian_metapackage_manager.utils.network.NetworkChecker.is_network_available') as mock:
        mock.return_value = False
        yield mock


# CLI testing fixtures
@pytest.fixture
def mock_cli_args():
    """Create mock CLI arguments."""
    class MockArgs:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    return MockArgs


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests."""
    # Clear any cached instances
    yield
    # Cleanup code here if needed


class TestHelpers:
    """Helper methods for tests."""
    
    @staticmethod
    def create_package(**kwargs) -> Package:
        """Create a package with default values."""
        defaults = {
            'name': 'test-package',
            'version': '1.0.0',
            'is_metapackage': False,
            'is_custom': True,
            'status': PackageStatus.NOT_INSTALLED
        }
        defaults.update(kwargs)
        return Package(**defaults)
    
    @staticmethod
    def create_operation_result(success: bool = True, **kwargs) -> OperationResult:
        """Create an operation result with default values."""
        defaults = {
            'success': success,
            'packages_affected': [],
            'warnings': [],
            'errors': [],
            'user_confirmations_required': []
        }
        defaults.update(kwargs)
        return OperationResult(**defaults)


@pytest.fixture
def helpers():
    """Provide test helpers."""
    return TestHelpers()