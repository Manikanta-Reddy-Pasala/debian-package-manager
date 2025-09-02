"""Tests for APT interface wrapper."""

import os
import sys
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.apt_interface import APTInterface
from debian_metapackage_manager.models import PackageStatus


class MockSubprocessResult:
    """Mock subprocess result."""
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_apt_interface_creation():
    """Test APT interface can be created."""
    apt = APTInterface()
    assert apt is not None


@patch('subprocess.run')
def test_is_installed_true(mock_run):
    """Test package installation check - installed package."""
    mock_run.return_value = MockSubprocessResult(
        returncode=0,
        stdout="ii  vim  2:8.2.3458-2ubuntu2.2  amd64  Vi IMproved - enhanced vi editor"
    )
    
    apt = APTInterface()
    assert apt.is_installed('vim') is True
    
    mock_run.assert_called_with(['dpkg', '-l', 'vim'], capture_output=True, text=True)


@patch('subprocess.run')
def test_is_installed_false(mock_run):
    """Test package installation check - not installed package."""
    mock_run.return_value = MockSubprocessResult(returncode=1)
    
    apt = APTInterface()
    assert apt.is_installed('nonexistent-package') is False


@patch('subprocess.run')
def test_get_package_info(mock_run):
    """Test getting package information."""
    mock_run.return_value = MockSubprocessResult(
        returncode=0,
        stdout="""Package: vim
Version: 2:8.2.3458-2ubuntu2.2
Architecture: amd64
Description: Vi IMproved - enhanced vi editor
 Vim is an almost compatible version of the UNIX editor Vi."""
    )
    
    apt = APTInterface()
    
    # Mock is_installed to return True
    with patch.object(apt, 'is_installed', return_value=True):
        package_info = apt.get_package_info('vim')
    
    assert package_info is not None
    assert package_info.name == 'vim'
    assert package_info.version == '2:8.2.3458-2ubuntu2.2'


@patch('subprocess.run')
def test_get_dependencies(mock_run):
    """Test getting package dependencies."""
    mock_run.return_value = MockSubprocessResult(
        returncode=0,
        stdout="""vim
  Depends: vim-common (= 2:8.2.3458-2ubuntu2.2)
  Depends: vim-runtime (= 2:8.2.3458-2ubuntu2.2)
  Depends: libacl1 (>= 2.2.23)
  Depends: libc6 (>= 2.29)"""
    )
    
    apt = APTInterface()
    
    # Mock _get_package_status
    with patch.object(apt, '_get_package_status', return_value=PackageStatus.INSTALLED):
        dependencies = apt.get_dependencies('vim')
    
    assert len(dependencies) >= 4
    dep_names = [dep.name for dep in dependencies]
    assert 'vim-common' in dep_names
    assert 'vim-runtime' in dep_names
    assert 'libacl1' in dep_names
    assert 'libc6' in dep_names


@patch('subprocess.run')
def test_check_conflicts(mock_run):
    """Test checking for package conflicts."""
    mock_run.return_value = MockSubprocessResult(
        returncode=1,
        stdout="""Reading package lists...
Building dependency tree...
The following packages will be REMOVED:
  old-package conflicting-package
The following NEW packages will be installed:
  new-package"""
    )
    
    apt = APTInterface()
    conflicts = apt.check_conflicts('new-package')
    
    assert len(conflicts) == 2
    conflict_names = [conflict.conflicting_package.name for conflict in conflicts]
    assert 'old-package' in conflict_names
    assert 'conflicting-package' in conflict_names


@patch('subprocess.run')
def test_get_available_versions(mock_run):
    """Test getting available package versions."""
    mock_run.return_value = MockSubprocessResult(
        returncode=0,
        stdout="""vim:
  Installed: 2:8.2.3458-2ubuntu2.2
  Candidate: 2:8.2.3458-2ubuntu2.3
  Version table:
 *** 2:8.2.3458-2ubuntu2.3 500
        500 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 Packages
     2:8.2.3458-2ubuntu2.2 100
        100 /var/lib/dpkg/status"""
    )
    
    apt = APTInterface()
    versions = apt.get_available_versions('vim')
    
    assert len(versions) >= 1
    assert '2:8.2.3458-2ubuntu2.3' in versions or '2:8.2.3458-2ubuntu2.2' in versions


@patch('subprocess.run')
def test_search_packages(mock_run):
    """Test searching for packages."""
    mock_run.return_value = MockSubprocessResult(
        returncode=0,
        stdout="""vim - Vi IMproved - enhanced vi editor
vim-common - Vi IMproved - Common files
vim-runtime - Vi IMproved - Runtime files"""
    )
    
    apt = APTInterface()
    packages = apt.search_packages('vim')
    
    assert len(packages) == 3
    assert 'vim' in packages
    assert 'vim-common' in packages
    assert 'vim-runtime' in packages


@patch('subprocess.run')
def test_install_package(mock_run):
    """Test package installation."""
    mock_run.return_value = MockSubprocessResult(returncode=0)
    
    apt = APTInterface()
    result = apt.install('test-package')
    
    assert result is True
    mock_run.assert_called_with(
        ['sudo', 'apt-get', 'install', '-y', 'test-package'],
        capture_output=True, text=True
    )


@patch('subprocess.run')
def test_install_package_with_version(mock_run):
    """Test package installation with specific version."""
    mock_run.return_value = MockSubprocessResult(returncode=0)
    
    apt = APTInterface()
    result = apt.install('test-package', '1.0.0')
    
    assert result is True
    mock_run.assert_called_with(
        ['sudo', 'apt-get', 'install', '-y', 'test-package=1.0.0'],
        capture_output=True, text=True
    )


@patch('subprocess.run')
def test_remove_package(mock_run):
    """Test package removal."""
    mock_run.return_value = MockSubprocessResult(returncode=0)
    
    apt = APTInterface()
    result = apt.remove('test-package')
    
    assert result is True
    mock_run.assert_called_with(
        ['sudo', 'apt-get', 'remove', '-y', 'test-package'],
        capture_output=True, text=True
    )


@patch('subprocess.run')
def test_remove_package_force(mock_run):
    """Test forced package removal."""
    mock_run.return_value = MockSubprocessResult(returncode=0)
    
    apt = APTInterface()
    result = apt.remove('test-package', force=True)
    
    assert result is True
    expected_cmd = ['sudo', 'apt-get', 'remove', '-y', '--force-yes', '--allow-remove-essential', 'test-package']
    mock_run.assert_called_with(expected_cmd, capture_output=True, text=True)


if __name__ == "__main__":
    test_apt_interface_creation()
    test_is_installed_true()
    test_is_installed_false()
    test_get_package_info()
    test_get_dependencies()
    test_check_conflicts()
    test_get_available_versions()
    test_search_packages()
    test_install_package()
    test_install_package_with_version()
    test_remove_package()
    test_remove_package_force()
    print("All APT interface tests passed!")