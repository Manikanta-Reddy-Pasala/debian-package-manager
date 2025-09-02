"""Tests for APT interface."""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock

from debian_metapackage_manager.interfaces.apt.interface import APTInterface
from debian_metapackage_manager.models import Package, Conflict, PackageStatus


class TestAPTInterface:
    """Test suite for APT interface."""

    def test_apt_interface_initialization(self):
        """Test APT interface initialization."""
        interface = APTInterface()
        
        assert interface.config is None
        assert interface._cache_info == {}

    def test_apt_interface_initialization_with_config(self):
        """Test APT interface initialization with config."""
        mock_config = Mock()
        interface = APTInterface(config=mock_config)
        
        assert interface.config == mock_config

    @patch('subprocess.run')
    def test_install_package_success(self, mock_run):
        """Test successful package installation."""
        mock_run.return_value.returncode = 0
        
        interface = APTInterface()
        result = interface.install('test-package')
        
        assert result is True
        mock_run.assert_called_once()
        
        # Verify correct command was called
        call_args = mock_run.call_args[0][0]
        assert call_args == ['sudo', 'apt-get', 'install', '-y', 'test-package']

    @patch('subprocess.run')
    def test_install_package_with_version(self, mock_run):
        """Test package installation with specific version."""
        mock_run.return_value.returncode = 0
        
        interface = APTInterface()
        result = interface.install('test-package', version='1.2.3')
        
        assert result is True
        
        # Verify correct command with version was called
        call_args = mock_run.call_args[0][0]
        assert call_args == ['sudo', 'apt-get', 'install', '-y', 'test-package=1.2.3']

    @patch('subprocess.run')
    def test_install_package_failure(self, mock_run):
        """Test failed package installation."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Package not found"
        
        interface = APTInterface()
        result = interface.install('nonexistent-package')
        
        assert result is False

    @patch('subprocess.run')
    def test_install_package_exception(self, mock_run):
        """Test package installation with exception."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'apt-get')
        
        interface = APTInterface()
        result = interface.install('test-package')
        
        assert result is False

    @patch('subprocess.run')
    def test_remove_package_success(self, mock_run):
        """Test successful package removal."""
        mock_run.return_value.returncode = 0
        
        interface = APTInterface()
        result = interface.remove('test-package')
        
        assert result is True
        mock_run.assert_called_once()
        
        # Verify correct command was called
        call_args = mock_run.call_args[0][0]
        assert call_args == ['sudo', 'apt-get', 'remove', '-y', 'test-package']

    @patch('subprocess.run')
    def test_remove_package_with_force(self, mock_run):
        """Test package removal with force option."""
        mock_run.return_value.returncode = 0
        
        interface = APTInterface()
        result = interface.remove('test-package', force=True)
        
        assert result is True
        
        # Verify force options were added
        call_args = mock_run.call_args[0][0]
        assert '--force-yes' in call_args or '--allow-remove-essential' in call_args

    @patch('subprocess.run')
    def test_remove_package_failure(self, mock_run):
        """Test failed package removal."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Package not installed"
        
        interface = APTInterface()
        result = interface.remove('test-package')
        
        assert result is False

    @patch('subprocess.run')
    def test_get_dependencies_success(self, mock_run):
        """Test getting package dependencies."""
        mock_output = """test-package
  Depends: libssl1.1
  Depends: libc6 (>= 2.17)
  Depends: zlib1g
  Recommends: ca-certificates
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        dependencies = interface.get_dependencies('test-package')
        
        assert len(dependencies) == 3  # Only Depends, not Recommends
        dep_names = [dep.name for dep in dependencies]
        assert 'libssl1.1' in dep_names
        assert 'libc6' in dep_names
        assert 'zlib1g' in dep_names

    @patch('subprocess.run')
    def test_get_dependencies_no_deps(self, mock_run):
        """Test getting dependencies for package with no dependencies."""
        mock_output = """test-package
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        dependencies = interface.get_dependencies('test-package')
        
        assert dependencies == []

    @patch('subprocess.run')
    def test_get_dependencies_failure(self, mock_run):
        """Test getting dependencies when command fails."""
        mock_run.return_value.returncode = 1
        
        interface = APTInterface()
        dependencies = interface.get_dependencies('nonexistent-package')
        
        assert dependencies == []

    @patch('subprocess.run')
    def test_check_conflicts_success(self, mock_run):
        """Test checking package conflicts."""
        mock_output = """The following packages will be REMOVED:
  old-package conflicting-package
The following NEW packages will be installed:
  test-package
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        conflicts = interface.check_conflicts('test-package')
        
        assert len(conflicts) == 2
        conflict_names = [c.conflicting_package.name for c in conflicts]
        assert 'old-package' in conflict_names
        assert 'conflicting-package' in conflict_names

    @patch('subprocess.run')
    def test_check_conflicts_no_conflicts(self, mock_run):
        """Test checking conflicts when no conflicts exist."""
        mock_output = """The following NEW packages will be installed:
  test-package
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        conflicts = interface.check_conflicts('test-package')
        
        assert conflicts == []

    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        """Test checking if package is installed (installed)."""
        mock_output = """ii  test-package  1.0.0-1  amd64  Test package
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        result = interface.is_installed('test-package')
        
        assert result is True

    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        """Test checking if package is installed (not installed)."""
        mock_run.return_value.returncode = 1
        
        interface = APTInterface()
        result = interface.is_installed('test-package')
        
        assert result is False

    @patch('subprocess.run')
    def test_is_installed_partial_state(self, mock_run):
        """Test checking package with partial installation state."""
        mock_output = """rc  test-package  1.0.0-1  amd64  Test package (removed but config files remain)
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        result = interface.is_installed('test-package')
        
        assert result is False  # 'rc' state means not fully installed

    @patch('subprocess.run')
    def test_get_package_info_success(self, mock_run):
        """Test getting package information."""
        mock_output = """Package: test-package
Version: 1.2.3-1ubuntu1
Description: A test package for testing
 Extended description here
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        package_info = interface.get_package_info('test-package')
        
        assert package_info is not None
        assert package_info.name == 'test-package'
        assert package_info.version == '1.2.3-1ubuntu1'

    @patch('subprocess.run')
    def test_get_package_info_not_found(self, mock_run):
        """Test getting package information for non-existent package."""
        mock_run.return_value.returncode = 1
        
        interface = APTInterface()
        package_info = interface.get_package_info('nonexistent-package')
        
        assert package_info is None

    @patch('subprocess.run')
    def test_get_available_versions_success(self, mock_run):
        """Test getting available package versions."""
        mock_output = """test-package:
  Installed: 1.0.0-1
  Candidate: 1.2.0-1
  Version table:
 *** 1.2.0-1 500
        500 http://archive.ubuntu.com/ubuntu focal/universe amd64 Packages
     1.0.0-1 100
        100 /var/lib/dpkg/status
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        versions = interface.get_available_versions('test-package')
        
        assert len(versions) >= 1
        assert '1.2.0-1' in versions or '1.0.0-1' in versions

    @patch('subprocess.run')
    def test_get_available_versions_not_found(self, mock_run):
        """Test getting versions for non-existent package."""
        mock_run.return_value.returncode = 1
        
        interface = APTInterface()
        versions = interface.get_available_versions('nonexistent-package')
        
        assert versions == []

    @patch('subprocess.run')
    def test_update_package_cache_success(self, mock_run):
        """Test updating APT package cache."""
        mock_run.return_value.returncode = 0
        
        interface = APTInterface()
        result = interface.update_package_cache()
        
        assert result is True
        mock_run.assert_called_once()
        
        call_args = mock_run.call_args[0][0]
        assert call_args == ['sudo', 'apt-get', 'update']

    @patch('subprocess.run')
    def test_update_package_cache_failure(self, mock_run):
        """Test failed package cache update."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Failed to fetch"
        
        interface = APTInterface()
        result = interface.update_package_cache()
        
        assert result is False

    @patch('subprocess.run')
    def test_search_packages_success(self, mock_run):
        """Test searching for packages."""
        mock_output = """test-package - Test package description
test-dev - Test development package
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        packages = interface.search_packages('test')
        
        assert len(packages) == 2
        assert 'test-package' in packages
        assert 'test-dev' in packages

    @patch('subprocess.run')
    def test_search_packages_no_results(self, mock_run):
        """Test searching with no results."""
        mock_output = ""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        packages = interface.search_packages('nonexistent')
        
        assert packages == []

    def test_get_package_status_installed(self):
        """Test getting package status for installed package."""
        interface = APTInterface()
        
        with patch.object(interface, 'is_installed', return_value=True):
            with patch.object(interface, '_is_upgradable', return_value=False):
                status = interface._get_package_status('test-package')
                assert status == PackageStatus.INSTALLED

    def test_get_package_status_upgradable(self):
        """Test getting package status for upgradable package."""
        interface = APTInterface()
        
        with patch.object(interface, 'is_installed', return_value=True):
            with patch.object(interface, '_is_upgradable', return_value=True):
                status = interface._get_package_status('test-package')
                assert status == PackageStatus.UPGRADABLE

    def test_get_package_status_not_installed(self):
        """Test getting package status for not installed package."""
        interface = APTInterface()
        
        with patch.object(interface, 'is_installed', return_value=False):
            status = interface._get_package_status('test-package')
            assert status == PackageStatus.NOT_INSTALLED

    @patch('subprocess.run')
    def test_is_upgradable_true(self, mock_run):
        """Test checking if package is upgradable (true)."""
        mock_output = """test-package/focal-updates 1.2.0-1 amd64 [upgradable from: 1.0.0-1]
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        result = interface._is_upgradable('test-package')
        
        assert result is True

    @patch('subprocess.run')
    def test_is_upgradable_false(self, mock_run):
        """Test checking if package is upgradable (false)."""
        mock_output = ""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        result = interface._is_upgradable('test-package')
        
        assert result is False


class TestAPTInterfaceIntegration:
    """Integration tests for APT interface."""

    @patch('subprocess.run')
    def test_install_check_status_workflow(self, mock_run):
        """Test complete install and status check workflow."""
        interface = APTInterface()
        
        # Mock installation success
        mock_run.return_value.returncode = 0
        install_result = interface.install('test-package')
        assert install_result is True
        
        # Mock status check - now installed
        mock_run.return_value.stdout = "ii  test-package  1.0.0-1  amd64  Test package"
        is_installed = interface.is_installed('test-package')
        assert is_installed is True

    @patch('subprocess.run')
    def test_dependency_resolution_workflow(self, mock_run):
        """Test dependency resolution workflow."""
        interface = APTInterface()
        
        # Mock dependency check
        mock_output = """test-package
  Depends: libssl1.1
  Depends: libc6 (>= 2.17)
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        dependencies = interface.get_dependencies('test-package')
        assert len(dependencies) == 2
        
        # Check that each dependency can be processed
        for dep in dependencies:
            assert isinstance(dep, Package)
            assert dep.name in ['libssl1.1', 'libc6']

    @patch('subprocess.run')
    def test_conflict_resolution_workflow(self, mock_run):
        """Test conflict resolution workflow."""
        interface = APTInterface()
        
        # Mock conflict simulation
        mock_output = """The following packages will be REMOVED:
  old-package
The following NEW packages will be installed:
  test-package
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        conflicts = interface.check_conflicts('test-package')
        assert len(conflicts) == 1
        assert conflicts[0].conflicting_package.name == 'old-package'

    @patch('subprocess.run')
    def test_version_management_workflow(self, mock_run):
        """Test version management workflow."""
        interface = APTInterface()
        
        # Mock available versions
        mock_output = """test-package:
  Candidate: 2.0.0-1
  Version table:
     2.0.0-1 500
     1.0.0-1 100
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        versions = interface.get_available_versions('test-package')
        assert len(versions) >= 1
        
        # Test installing specific version
        mock_run.reset_mock()
        mock_run.return_value.returncode = 0
        
        result = interface.install('test-package', version='1.0.0-1')
        assert result is True
        
        # Verify version was specified in command
        call_args = mock_run.call_args[0][0]
        assert 'test-package=1.0.0-1' in call_args


class TestAPTInterfaceEdgeCases:
    """Test edge cases and error conditions."""

    @patch('subprocess.run')
    def test_network_timeout_handling(self, mock_run):
        """Test handling of network timeouts."""
        mock_run.side_effect = subprocess.TimeoutExpired('apt-get', 30)
        
        interface = APTInterface()
        result = interface.install('test-package')
        
        assert result is False

    @patch('subprocess.run')
    def test_permission_denied_handling(self, mock_run):
        """Test handling of permission denied errors."""
        mock_run.side_effect = subprocess.CalledProcessError(
            100, 'apt-get', stderr='Permission denied'
        )
        
        interface = APTInterface()
        result = interface.install('test-package')
        
        assert result is False

    @patch('subprocess.run')
    def test_corrupted_cache_handling(self, mock_run):
        """Test handling of corrupted package cache."""
        mock_run.return_value.returncode = 100
        mock_run.return_value.stderr = "E: The package cache file is corrupted"
        
        interface = APTInterface()
        result = interface.update_package_cache()
        
        assert result is False

    @patch('subprocess.run')
    def test_disk_full_handling(self, mock_run):
        """Test handling of disk full errors."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "E: You don't have enough free space"
        
        interface = APTInterface()
        result = interface.install('large-package')
        
        assert result is False

    @patch('subprocess.run')
    def test_broken_package_handling(self, mock_run):
        """Test handling of broken packages."""
        mock_output = """test-package is broken
"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = mock_output
        
        interface = APTInterface()
        result = interface.install('broken-package')
        
        assert result is False

    def test_empty_package_name_handling(self):
        """Test handling of empty package names."""
        interface = APTInterface()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            
            result = interface.install('')
            assert result is False
            
            result = interface.remove('')
            assert result is False

    @patch('subprocess.run')
    def test_unicode_package_names(self, mock_run):
        """Test handling of Unicode in package names."""
        mock_run.return_value.returncode = 0
        
        interface = APTInterface()
        
        # Should handle Unicode gracefully
        result = interface.install('test-package-ñáme')
        assert result is True

    @patch('subprocess.run') 
    def test_very_long_package_names(self, mock_run):
        """Test handling of very long package names."""
        mock_run.return_value.returncode = 0
        
        interface = APTInterface()
        long_name = 'a' * 1000
        
        result = interface.install(long_name)
        # Should either succeed or fail gracefully
        assert isinstance(result, bool)