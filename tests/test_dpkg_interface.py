"""Tests for DPKG interface."""

import os
import sys
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.dpkg_interface import DPKGInterface
from debian_metapackage_manager.models import PackageStatus


class MockSubprocessResult:
    """Mock subprocess result."""
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_dpkg_interface_creation():
    """Test DPKG interface can be created."""
    dpkg = DPKGInterface()
    assert dpkg is not None
    assert len(dpkg.lock_files) > 0


@patch('subprocess.run')
@patch.object(DPKGInterface, '_handle_locks', return_value=True)
def test_force_remove_success(mock_handle_locks, mock_run):
    """Test successful force removal."""
    mock_run.return_value = MockSubprocessResult(returncode=0)
    
    dpkg = DPKGInterface()
    result = dpkg.force_remove('test-package')
    
    assert result is True
    mock_run.assert_called_with(
        ['sudo', 'dpkg', '--remove', '--force-depends', '--force-remove-essential', 'test-package'],
        capture_output=True, text=True
    )


@patch('subprocess.run')
@patch.object(DPKGInterface, '_handle_locks', return_value=True)
@patch.object(DPKGInterface, '_force_remove_aggressive', return_value=True)
def test_force_remove_fallback(mock_aggressive, mock_handle_locks, mock_run):
    """Test force removal with fallback to aggressive mode."""
    mock_run.return_value = MockSubprocessResult(returncode=1)
    
    dpkg = DPKGInterface()
    result = dpkg.force_remove('test-package')
    
    assert result is True
    mock_aggressive.assert_called_once_with('test-package')


@patch('subprocess.run')
def test_purge_package(mock_run):
    """Test package purging."""
    mock_run.return_value = MockSubprocessResult(returncode=0)
    
    dpkg = DPKGInterface()
    result = dpkg.purge_package('test-package', force=True)
    
    assert result is True
    expected_cmd = [
        'sudo', 'dpkg', '--purge',
        '--force-depends', '--force-remove-essential', '--force-confmiss',
        'test-package'
    ]
    mock_run.assert_called_with(expected_cmd, capture_output=True, text=True)


@patch('subprocess.run')
def test_fix_broken_packages_dpkg_success(mock_run):
    """Test fixing broken packages with dpkg success."""
    mock_run.return_value = MockSubprocessResult(returncode=0)
    
    dpkg = DPKGInterface()
    result = dpkg.fix_broken_packages()
    
    assert result is True
    mock_run.assert_called_with(['sudo', 'dpkg', '--configure', '-a'], capture_output=True, text=True)


@patch('subprocess.run')
def test_fix_broken_packages_apt_fallback(mock_run):
    """Test fixing broken packages with apt fallback."""
    # First call (dpkg) fails, second call (apt) succeeds
    mock_run.side_effect = [
        MockSubprocessResult(returncode=1),  # dpkg fails
        MockSubprocessResult(returncode=0)   # apt succeeds
    ]
    
    dpkg = DPKGInterface()
    result = dpkg.fix_broken_packages()
    
    assert result is True
    assert mock_run.call_count == 2


@patch('os.path.exists')
@patch('os.stat')
def test_detect_locks(mock_stat, mock_exists):
    """Test lock detection."""
    # Mock some lock files existing
    mock_exists.side_effect = lambda path: path in ['/var/lib/dpkg/lock', '/var/cache/apt/archives/lock']
    
    # Mock stat to return non-zero size
    mock_stat_result = Mock()
    mock_stat_result.st_size = 100
    mock_stat.return_value = mock_stat_result
    
    dpkg = DPKGInterface()
    locks = dpkg.detect_locks()
    
    assert len(locks) == 2
    assert '/var/lib/dpkg/lock' in locks
    assert '/var/cache/apt/archives/lock' in locks


@patch('subprocess.run')
def test_get_package_status_detailed_installed(mock_run):
    """Test getting detailed package status for installed package."""
    mock_run.return_value = MockSubprocessResult(
        returncode=0,
        stdout="""Package: test-package
Status: install ok installed
Priority: optional
Section: utils"""
    )
    
    dpkg = DPKGInterface()
    status, message = dpkg.get_package_status_detailed('test-package')
    
    assert status == PackageStatus.INSTALLED
    assert "installed" in message.lower()


@patch('subprocess.run')
def test_get_package_status_detailed_broken(mock_run):
    """Test getting detailed package status for broken package."""
    mock_run.return_value = MockSubprocessResult(
        returncode=0,
        stdout="""Package: test-package
Status: install ok half-configured
Priority: optional
Section: utils"""
    )
    
    dpkg = DPKGInterface()
    status, message = dpkg.get_package_status_detailed('test-package')
    
    assert status == PackageStatus.BROKEN
    assert "half-configured" in message


@patch('subprocess.run')
def test_get_package_status_detailed_not_installed(mock_run):
    """Test getting detailed package status for non-installed package."""
    mock_run.return_value = MockSubprocessResult(returncode=1)
    
    dpkg = DPKGInterface()
    status, message = dpkg.get_package_status_detailed('test-package')
    
    assert status == PackageStatus.NOT_INSTALLED
    assert "not installed" in message.lower()


@patch('subprocess.run')
def test_list_broken_packages(mock_run):
    """Test listing broken packages."""
    mock_run.return_value = MockSubprocessResult(
        returncode=0,
        stdout="""Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version      Architecture Description
+++-==============-============-============-=================================
ii  good-package   1.0.0        amd64        A good package
iU  broken-pkg1    1.0.0        amd64        A broken package (unpacked)
iF  broken-pkg2    2.0.0        amd64        A broken package (half-configured)"""
    )
    
    dpkg = DPKGInterface()
    broken_packages = dpkg.list_broken_packages()
    
    assert len(broken_packages) == 2
    broken_names = [pkg.name for pkg in broken_packages]
    assert 'broken-pkg1' in broken_names
    assert 'broken-pkg2' in broken_names
    
    for pkg in broken_packages:
        assert pkg.status == PackageStatus.BROKEN


@patch('subprocess.run')
def test_reconfigure_package(mock_run):
    """Test package reconfiguration."""
    mock_run.return_value = MockSubprocessResult(returncode=0)
    
    dpkg = DPKGInterface()
    result = dpkg.reconfigure_package('test-package')
    
    assert result is True
    mock_run.assert_called_with(['sudo', 'dpkg-reconfigure', 'test-package'], capture_output=True, text=True)


@patch('os.path.exists', return_value=True)
@patch('subprocess.run')
def test_force_install_deb(mock_run, mock_exists):
    """Test force installing DEB file."""
    mock_run.return_value = MockSubprocessResult(returncode=0)
    
    dpkg = DPKGInterface()
    result = dpkg.force_install_deb('/path/to/package.deb')
    
    assert result is True
    expected_cmd = [
        'sudo', 'dpkg', '-i',
        '--force-depends', '--force-conflicts',
        '/path/to/package.deb'
    ]
    mock_run.assert_called_with(expected_cmd, capture_output=True, text=True)


@patch('os.path.exists', return_value=False)
def test_force_install_deb_file_not_found(mock_exists):
    """Test force installing non-existent DEB file."""
    dpkg = DPKGInterface()
    result = dpkg.force_install_deb('/path/to/nonexistent.deb')
    
    assert result is False


@patch('subprocess.run')
def test_get_installed_packages(mock_run):
    """Test getting list of installed packages."""
    mock_run.return_value = MockSubprocessResult(
        returncode=0,
        stdout="""Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version      Architecture Description
+++-==============-============-============-=================================
ii  package1       1.0.0        amd64        First package
ii  package2       2.0.0        amd64        Second package
rc  removed-pkg    1.0.0        amd64        Removed package"""
    )
    
    dpkg = DPKGInterface()
    packages = dpkg.get_installed_packages()
    
    assert len(packages) == 2  # Only 'ii' status packages
    package_names = [pkg.name for pkg in packages]
    assert 'package1' in package_names
    assert 'package2' in package_names
    assert 'removed-pkg' not in package_names
    
    for pkg in packages:
        assert pkg.status == PackageStatus.INSTALLED


if __name__ == "__main__":
    test_dpkg_interface_creation()
    test_force_remove_success()
    test_force_remove_fallback()
    test_purge_package()
    test_fix_broken_packages_dpkg_success()
    test_fix_broken_packages_apt_fallback()
    test_detect_locks()
    test_get_package_status_detailed_installed()
    test_get_package_status_detailed_broken()
    test_get_package_status_detailed_not_installed()
    test_list_broken_packages()
    test_reconfigure_package()
    test_force_install_deb()
    test_force_install_deb_file_not_found()
    test_get_installed_packages()
    print("All DPKG interface tests passed!")