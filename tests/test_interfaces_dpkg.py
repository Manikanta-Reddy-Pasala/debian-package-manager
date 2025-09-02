"""Tests for DPKG interface."""

import pytest
import subprocess
import os
import time
from unittest.mock import Mock, patch, mock_open

from debian_metapackage_manager.interfaces.dpkg.interface import DPKGInterface
from debian_metapackage_manager.models import Package, PackageStatus


class TestDPKGInterface:
    """Test suite for DPKG interface."""

    def test_dpkg_interface_initialization(self, test_config):
        """Test DPKG interface initialization."""
        interface = DPKGInterface(test_config)
        
        assert interface.config == test_config
        assert len(interface.lock_files) == 3
        assert '/var/lib/dpkg/lock' in interface.lock_files

    def test_dpkg_interface_initialization_without_config(self):
        """Test DPKG interface initialization without config."""
        with patch('debian_metapackage_manager.config.Config') as mock_config_class:
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            interface = DPKGInterface()
            
            assert interface.config == mock_config

    def test_safe_remove_with_custom_prefix(self, test_config):
        """Test safe removal of package with custom prefix."""
        interface = DPKGInterface(test_config)
        
        with patch.object(interface, '_handle_locks', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                
                result = interface.safe_remove('test-package')  # test- is in custom prefixes
                
                assert result is True
                mock_run.assert_called()

    def test_safe_remove_system_package_denied(self, test_config):
        """Test that system packages cannot be safely removed."""
        interface = DPKGInterface(test_config)
        
        result = interface.safe_remove('libc6')  # System package
        
        assert result is False

    def test_safe_remove_non_custom_package_denied(self, test_config):
        """Test that non-custom packages cannot be safely removed."""
        interface = DPKGInterface(test_config)
        
        result = interface.safe_remove('random-package')  # No custom prefix
        
        assert result is False

    @patch('subprocess.run')
    def test_safe_remove_with_locks_handled(self, mock_run, test_config):
        """Test safe removal when locks are handled successfully."""
        interface = DPKGInterface(test_config)
        
        # Mock successful lock handling and removal
        with patch.object(interface, '_handle_locks', return_value=True):
            mock_run.return_value.returncode = 0
            
            result = interface.safe_remove('test-package')
            
            assert result is True

    @patch('subprocess.run')
    def test_safe_remove_with_lock_handling_failure(self, mock_run, test_config):
        """Test safe removal when lock handling fails."""
        interface = DPKGInterface(test_config)
        
        # Mock failed lock handling
        with patch.object(interface, '_handle_locks', return_value=False):
            result = interface.safe_remove('test-package')
            
            assert result is False

    @patch('subprocess.run')
    def test_purge_package_success(self, mock_run, test_config):
        """Test successful package purging."""
        interface = DPKGInterface(test_config)
        
        # Mock successful purge
        mock_run.return_value.returncode = 0
        
        with patch.object(interface.config, 'can_remove_package', return_value=True):
            result = interface.purge_package('test-package')
            
            assert result is True
            mock_run.assert_called_once()
            
            call_args = mock_run.call_args[0][0]
            assert call_args == ['sudo', 'dpkg', '--purge', 'test-package']

    @patch('subprocess.run')
    def test_purge_package_failure(self, mock_run, test_config):
        """Test failed package purging."""
        interface = DPKGInterface(test_config)
        
        # Mock failed purge
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Package not found"
        
        with patch.object(interface.config, 'can_remove_package', return_value=True):
            result = interface.purge_package('test-package')
            
            assert result is False

    def test_purge_package_system_package_denied(self, test_config):
        """Test that system packages cannot be purged."""
        interface = DPKGInterface(test_config)
        
        result = interface.purge_package('libc6')
        
        assert result is False

    @patch('subprocess.run')
    def test_fix_broken_packages_success_dpkg(self, mock_run):
        """Test successful broken package fix using dpkg."""
        interface = DPKGInterface()
        
        # Mock successful dpkg configure
        mock_run.return_value.returncode = 0
        
        result = interface.fix_broken_packages()
        
        assert result is True
        mock_run.assert_called_once()
        
        call_args = mock_run.call_args[0][0]
        assert call_args == ['sudo', 'dpkg', '--configure', '-a']

    @patch('subprocess.run')
    def test_fix_broken_packages_fallback_to_apt(self, mock_run):
        """Test broken package fix fallback to apt-get."""
        interface = DPKGInterface()
        
        # Mock dpkg failure, apt-get success
        side_effects = [
            Mock(returncode=1),  # dpkg configure fails
            Mock(returncode=0)   # apt-get fix succeeds
        ]
        mock_run.side_effect = side_effects
        
        result = interface.fix_broken_packages()
        
        assert result is True
        assert mock_run.call_count == 2
        
        # Check that both commands were called
        calls = mock_run.call_args_list
        assert calls[0][0][0] == ['sudo', 'dpkg', '--configure', '-a']
        assert calls[1][0][0] == ['sudo', 'apt-get', 'install', '-f', '-y']

    @patch('subprocess.run')
    def test_fix_broken_packages_all_fail(self, mock_run):
        """Test broken package fix when all methods fail."""
        interface = DPKGInterface()
        
        # Mock all methods failing
        mock_run.return_value.returncode = 1
        
        result = interface.fix_broken_packages()
        
        assert result is False

    @patch('subprocess.run')
    def test_list_broken_packages_success(self, mock_run):
        """Test listing broken packages."""
        mock_output = """Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version      Architecture Description
+++-==============-============-============-=================================
iF  broken-pkg     1.0.0-1      amd64        A broken package
ii  good-pkg       2.0.0-1      amd64        A good package
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = DPKGInterface()
        broken_packages = interface.list_broken_packages()
        
        assert len(broken_packages) == 1
        assert broken_packages[0].name == 'broken-pkg'
        assert broken_packages[0].status == PackageStatus.BROKEN

    @patch('subprocess.run')
    def test_list_broken_packages_none_broken(self, mock_run):
        """Test listing broken packages when none are broken."""
        mock_output = """Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version      Architecture Description
+++-==============-============-============-=================================
ii  good-pkg1      1.0.0-1      amd64        A good package
ii  good-pkg2      2.0.0-1      amd64        Another good package
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = DPKGInterface()
        broken_packages = interface.list_broken_packages()
        
        assert len(broken_packages) == 0

    @patch('os.path.exists')
    def test_detect_locks_with_locks_present(self, mock_exists):
        """Test detecting locks when lock files are present."""
        # Mock that all lock files exist
        mock_exists.return_value = True
        
        interface = DPKGInterface()
        locks = interface.detect_locks()
        
        assert len(locks) == 3
        assert all(lock in interface.lock_files for lock in locks)

    @patch('os.path.exists')
    def test_detect_locks_no_locks_present(self, mock_exists):
        """Test detecting locks when no lock files are present."""
        # Mock that no lock files exist
        mock_exists.return_value = False
        
        interface = DPKGInterface()
        locks = interface.detect_locks()
        
        assert len(locks) == 0

    @patch('os.path.exists')
    def test_detect_locks_partial_locks(self, mock_exists):
        """Test detecting locks when some lock files are present."""
        # Mock that only some lock files exist
        def exists_side_effect(path):
            return path == '/var/lib/dpkg/lock'
        
        mock_exists.side_effect = exists_side_effect
        
        interface = DPKGInterface()
        locks = interface.detect_locks()
        
        assert len(locks) == 1
        assert locks[0] == '/var/lib/dpkg/lock'

    def test_handle_locks_no_locks(self):
        """Test lock handling when no locks are present."""
        interface = DPKGInterface()
        
        with patch.object(interface, 'detect_locks', return_value=[]):
            result = interface._handle_locks()
            
            assert result is True

    @patch('time.sleep')
    def test_handle_locks_temporary_locks(self, mock_sleep):
        """Test handling temporary locks that disappear."""
        interface = DPKGInterface()
        
        # Mock locks present initially, then gone
        lock_states = [
            ['/var/lib/dpkg/lock'],  # First check: locks present
            []                       # Second check: locks gone
        ]
        
        with patch.object(interface, 'detect_locks', side_effect=lock_states):
            result = interface._handle_locks()
            
            assert result is True
            mock_sleep.assert_called()

    @patch('time.sleep')
    def test_handle_locks_persistent_locks(self, mock_sleep):
        """Test handling persistent locks that don't disappear."""
        interface = DPKGInterface()
        
        # Mock locks always present
        with patch.object(interface, 'detect_locks', return_value=['/var/lib/dpkg/lock']):
            with patch.object(interface, '_force_remove_locks', return_value=True):
                result = interface._handle_locks()
                
                assert result is True

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_force_remove_locks_success(self, mock_exists, mock_run):
        """Test successful force removal of lock files."""
        interface = DPKGInterface()
        
        # Mock lock files exist
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        
        lock_files = ['/var/lib/dpkg/lock']
        result = interface._force_remove_locks(lock_files)
        
        assert result is True
        mock_run.assert_called()

    @patch('subprocess.run')
    def test_force_remove_locks_failure(self, mock_run):
        """Test failed force removal of lock files."""
        interface = DPKGInterface()
        
        # Mock removal failure
        mock_run.side_effect = subprocess.CalledProcessError(1, 'rm')
        
        lock_files = ['/var/lib/dpkg/lock']
        result = interface._force_remove_locks(lock_files)
        
        assert result is False

    @patch('subprocess.run')
    def test_get_package_status_detailed_installed(self, mock_run):
        """Test getting detailed package status for installed package."""
        mock_output = """Package: test-package
Status: install ok installed
Version: 1.0.0-1
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = DPKGInterface()
        status, info = interface.get_package_status_detailed('test-package')
        
        assert status == PackageStatus.INSTALLED
        assert 'install ok installed' in info

    @patch('subprocess.run')
    def test_get_package_status_detailed_broken(self, mock_run):
        """Test getting detailed package status for broken package."""
        mock_output = """Package: broken-package
Status: install reinst-required half-configured
Version: 1.0.0-1
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = DPKGInterface()
        status, info = interface.get_package_status_detailed('broken-package')
        
        assert status == PackageStatus.BROKEN
        assert 'reinstall required' in info

    @patch('subprocess.run')
    def test_get_package_status_detailed_not_found(self, mock_run):
        """Test getting detailed package status for non-existent package."""
        mock_run.return_value.returncode = 1
        
        interface = DPKGInterface()
        status, info = interface.get_package_status_detailed('nonexistent-package')
        
        assert status == PackageStatus.NOT_INSTALLED
        assert 'not found' in info

    @patch('subprocess.run')
    def test_force_remove_success(self, mock_run):
        """Test successful force removal."""
        mock_run.return_value.returncode = 0
        
        interface = DPKGInterface()
        result = interface.force_remove('test-package')
        
        assert result is True
        mock_run.assert_called_once()
        
        call_args = mock_run.call_args[0][0]
        assert '--force-remove-reinstreq' in call_args
        assert '--force-remove-essential' in call_args

    @patch('subprocess.run')
    def test_force_remove_failure(self, mock_run):
        """Test failed force removal."""
        mock_run.return_value.returncode = 1
        
        interface = DPKGInterface()
        result = interface.force_remove('test-package')
        
        assert result is False

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_force_install_deb_success(self, mock_exists, mock_run):
        """Test successful force installation of DEB file."""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        
        interface = DPKGInterface()
        result = interface.force_install_deb('/path/to/package.deb')
        
        assert result is True
        mock_run.assert_called_once()
        
        call_args = mock_run.call_args[0][0]
        assert '--force-depends' in call_args
        assert '--force-conflicts' in call_args
        assert '/path/to/package.deb' in call_args

    @patch('os.path.exists')
    def test_force_install_deb_file_not_found(self, mock_exists):
        """Test force installation when DEB file doesn't exist."""
        mock_exists.return_value = False
        
        interface = DPKGInterface()
        result = interface.force_install_deb('/nonexistent/package.deb')
        
        assert result is False

    @patch('subprocess.run')
    def test_get_installed_packages_success(self, mock_run):
        """Test getting list of installed packages."""
        mock_output = """Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version      Architecture Description
+++-==============-============-============-=================================
ii  package1       1.0.0-1      amd64        First package
ii  package2       2.0.0-1      amd64        Second package
rc  package3       1.5.0-1      amd64        Removed package (config remains)
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = DPKGInterface()
        packages = interface.get_installed_packages()
        
        assert len(packages) == 2  # Only 'ii' status packages
        package_names = [pkg.name for pkg in packages]
        assert 'package1' in package_names
        assert 'package2' in package_names
        assert 'package3' not in package_names  # 'rc' status excluded

    @patch('subprocess.run')
    def test_get_installed_packages_empty(self, mock_run):
        """Test getting installed packages when none are installed."""
        mock_output = """Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version      Architecture Description
+++-==============-============-============-=================================
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = DPKGInterface()
        packages = interface.get_installed_packages()
        
        assert len(packages) == 0


class TestDPKGInterfaceIntegration:
    """Integration tests for DPKG interface."""

    @patch('subprocess.run')
    def test_safe_removal_workflow(self, mock_run, test_config):
        """Test complete safe removal workflow."""
        interface = DPKGInterface(test_config)
        
        # Mock no locks and successful removal
        with patch.object(interface, 'detect_locks', return_value=[]):
            mock_run.return_value.returncode = 0
            
            # Test removal of custom package
            result = interface.safe_remove('test-package')
            
            assert result is True

    @patch('subprocess.run')
    def test_broken_package_recovery_workflow(self, mock_run):
        """Test broken package detection and recovery workflow."""
        interface = DPKGInterface()
        
        # Mock broken package detection
        broken_output = """iF  broken-pkg     1.0.0-1      amd64        A broken package"""
        
        # Mock fix success
        fix_outputs = [
            Mock(returncode=0, stdout=broken_output),  # list broken
            Mock(returncode=0)                         # fix broken
        ]
        mock_run.side_effect = fix_outputs
        
        # Detect broken packages
        broken_packages = interface.list_broken_packages()
        assert len(broken_packages) == 1
        
        # Fix broken packages
        fix_result = interface.fix_broken_packages()
        assert fix_result is True

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('time.sleep')
    def test_lock_handling_workflow(self, mock_sleep, mock_exists, mock_run):
        """Test complete lock handling workflow."""
        interface = DPKGInterface()
        
        # Mock persistent lock that needs force removal
        lock_file = '/var/lib/dpkg/lock'
        
        # Mock lock detection and force removal
        def exists_side_effect(path):
            return path == lock_file
        
        mock_exists.side_effect = exists_side_effect
        mock_run.return_value.returncode = 0
        
        # Test lock handling
        with patch.object(interface, 'detect_locks', return_value=[lock_file]):
            with patch.object(interface, '_force_remove_locks', return_value=True):
                result = interface._handle_locks()
                
                assert result is True


class TestDPKGInterfaceEdgeCases:
    """Test edge cases and error conditions."""

    def test_safe_remove_empty_package_name(self, test_config):
        """Test safe removal with empty package name."""
        interface = DPKGInterface(test_config)
        
        result = interface.safe_remove('')
        
        assert result is False

    def test_safe_remove_none_package_name(self, test_config):
        """Test safe removal with None package name."""
        interface = DPKGInterface(test_config)
        
        result = interface.safe_remove(None)
        
        assert result is False

    @patch('subprocess.run')
    def test_subprocess_timeout_handling(self, mock_run):
        """Test handling of subprocess timeouts."""
        mock_run.side_effect = subprocess.TimeoutExpired('dpkg', 30)
        
        interface = DPKGInterface()
        result = interface.fix_broken_packages()
        
        assert result is False

    @patch('subprocess.run')
    def test_permission_denied_handling(self, mock_run):
        """Test handling of permission denied errors."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'dpkg', stderr='Permission denied'
        )
        
        interface = DPKGInterface()
        result = interface.fix_broken_packages()
        
        assert result is False

    @patch('os.path.exists')
    def test_lock_detection_with_permission_error(self, mock_exists):
        """Test lock detection when permission is denied."""
        mock_exists.side_effect = PermissionError("Permission denied")
        
        interface = DPKGInterface()
        
        # Should handle permission error gracefully
        locks = interface.detect_locks()
        assert isinstance(locks, list)

    @patch('subprocess.run')
    def test_malformed_dpkg_output_handling(self, mock_run):
        """Test handling of malformed dpkg output."""
        mock_output = """Corrupted output that doesn't match expected format
Random lines
Invalid data
"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        interface = DPKGInterface()
        
        # Should handle malformed output gracefully
        packages = interface.get_installed_packages()
        assert isinstance(packages, list)
        
        broken_packages = interface.list_broken_packages()
        assert isinstance(broken_packages, list)

    @patch('subprocess.run')
    def test_unicode_in_package_names(self, mock_run):
        """Test handling of Unicode characters in package names."""
        mock_run.return_value.returncode = 0
        
        interface = DPKGInterface()
        
        # Should handle Unicode gracefully
        result = interface.force_remove('test-packageñ')
        assert isinstance(result, bool)

    @patch('subprocess.run')
    def test_very_large_package_lists(self, mock_run):
        """Test handling of very large package lists."""
        # Generate large output
        large_output = "Desired=Unknown/Install/Remove/Purge/Hold\n"
        large_output += "| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend\n"
        large_output += "|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)\n"
        large_output += "||/ Name           Version      Architecture Description\n"
        large_output += "+++-==============-============-============-=================================\n"
        
        # Add 1000 packages
        for i in range(1000):
            large_output += f"ii  package{i:<7} 1.0.0-1      amd64        Package {i}\n"
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = large_output
        
        interface = DPKGInterface()
        packages = interface.get_installed_packages()
        
        assert len(packages) == 1000
        
    @patch('time.sleep')
    def test_lock_handling_timeout(self, mock_sleep):
        """Test lock handling with timeout scenario."""
        interface = DPKGInterface()
        
        # Mock locks that never disappear
        with patch.object(interface, 'detect_locks', return_value=['/var/lib/dpkg/lock']):
            with patch.object(interface, '_force_remove_locks', return_value=False):
                result = interface._handle_locks()
                
                assert result is False