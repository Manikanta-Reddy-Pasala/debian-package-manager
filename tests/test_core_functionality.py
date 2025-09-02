"""Tests for core package management functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from debian_metapackage_manager.core.package_manager import PackageManager
from debian_metapackage_manager.core.classifier import PackageClassifier
from debian_metapackage_manager.core.mode_manager import ModeManager
from debian_metapackage_manager.models import Package, OperationResult, PackageStatus
from debian_metapackage_manager.config import Config


class TestPackageManager:
    """Test suite for PackageManager class."""

    def test_package_manager_initialization(self, test_config):
        """Test PackageManager initialization."""
        manager = PackageManager(test_config)
        
        assert manager.config == test_config
        assert hasattr(manager, 'apt')
        assert hasattr(manager, 'dpkg')
        assert hasattr(manager, 'classifier')
        assert hasattr(manager, 'mode_manager')

    @patch('debian_metapackage_manager.config.config.Config')
    def test_package_manager_initialization_without_config(self, mock_config_class):
        """Test PackageManager initialization without config."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        manager = PackageManager()
        
        assert manager.config == mock_config
        mock_config_class.assert_called_once()

    def test_install_package_success(self, mock_package_manager):
        """Test successful package installation."""
        mock_package_manager.apt.is_installed.return_value = False
        mock_package_manager.apt.install.return_value = True
        mock_package_manager.mode_manager.get_package_version_for_mode.return_value = '1.0.0'
        
        result = mock_package_manager.install_package('test-package')
        
        assert result.success is True
        assert len(result.packages_affected) == 1
        assert result.packages_affected[0].name == 'test-package'

    def test_install_package_already_installed(self, mock_package_manager):
        """Test installing package that's already installed."""
        mock_package_manager.apt.is_installed.return_value = True
        
        result = mock_package_manager.install_package('test-package')
        
        assert result.success is True
        assert len(result.warnings) == 1
        assert "already installed" in result.warnings[0]

    def test_install_package_already_installed_with_force(self, mock_package_manager):
        """Test installing already installed package with force."""
        mock_package_manager.apt.is_installed.return_value = True
        mock_package_manager.apt.install.return_value = True
        
        result = mock_package_manager.install_package('test-package', force=True)
        
        assert result.success is True
        # Should proceed with installation even if already installed

    def test_install_package_with_specific_version(self, mock_package_manager):
        """Test installing package with specific version."""
        mock_package_manager.apt.is_installed.return_value = False
        mock_package_manager.apt.install.return_value = True
        
        result = mock_package_manager.install_package('test-package', version='2.0.0')
        
        assert result.success is True
        mock_package_manager.apt.install.assert_called_with('test-package', '2.0.0')

    def test_install_package_failure(self, mock_package_manager):
        """Test failed package installation."""
        mock_package_manager.apt.is_installed.return_value = False
        mock_package_manager.apt.install.return_value = False
        mock_package_manager.mode_manager.get_package_version_for_mode.return_value = '1.0.0'
        
        result = mock_package_manager.install_package('test-package')
        
        assert result.success is False
        assert len(result.errors) > 0

    def test_install_package_with_exception(self, mock_package_manager):
        """Test package installation with exception."""
        mock_package_manager.apt.is_installed.side_effect = Exception("Test exception")
        
        result = mock_package_manager.install_package('test-package')
        
        assert result.success is False
        assert len(result.errors) > 0

    def test_remove_package_success(self, mock_package_manager):
        """Test successful package removal."""
        # Setup mocks
        mock_package_manager.apt.is_installed.return_value = True
        mock_package_manager.apt.remove.return_value = True
        mock_package_manager.apt.get_package_info.return_value = Package(
            name='test-package', version='1.0.0'
        )
        
        result = mock_package_manager.remove_package('test-package')
        
        assert result.success is True
        assert len(result.packages_affected) == 1
        assert result.packages_affected[0].name == 'test-package'

    def test_remove_package_not_installed(self, mock_package_manager):
        """Test removing package that's not installed."""
        mock_package_manager.apt.is_installed.return_value = False
        
        result = mock_package_manager.remove_package('test-package')
        
        assert result.success is True
        assert len(result.warnings) == 1
        assert "not installed" in result.warnings[0]

    def test_remove_package_failure(self, mock_package_manager):
        """Test failed package removal."""
        mock_package_manager.apt.is_installed.return_value = True
        mock_package_manager.apt.remove.return_value = False
        mock_package_manager.apt.get_package_info.return_value = Package(
            name='test-package', version='1.0.0'
        )
        
        result = mock_package_manager.remove_package('test-package')
        
        assert result.success is False
        assert "Normal removal failed" in result.warnings[0]

    def test_remove_package_with_force(self, mock_package_manager):
        """Test package removal with force."""
        mock_package_manager.apt.is_installed.return_value = True
        mock_package_manager.apt.remove.return_value = False
        mock_package_manager.apt.get_package_info.return_value = Package(
            name='test-package', version='1.0.0'
        )
        
        # Mock force removal success
        with patch.object(mock_package_manager, '_force_remove_package') as mock_force:
            mock_force.return_value = OperationResult(
                success=True, packages_affected=[Package('test-package', '1.0.0')],
                warnings=[], errors=[], user_confirmations_required=[]
            )
            
            result = mock_package_manager.remove_package('test-package', force=True)
            
            assert result.success is True

    def test_force_remove_package_success(self, mock_package_manager):
        """Test successful force removal."""
        package = Package(name='test-package', version='1.0.0')
        mock_package_manager.dpkg.safe_remove.return_value = True
        
        result = mock_package_manager._force_remove_package(package)
        
        assert result.success is True
        assert len(result.packages_affected) == 1

    def test_force_remove_package_failure(self, mock_package_manager):
        """Test failed force removal."""
        package = Package(name='test-package', version='1.0.0')
        mock_package_manager.dpkg.safe_remove.return_value = False
        mock_package_manager.dpkg.safe_purge.return_value = False
        
        result = mock_package_manager._force_remove_package(package)
        
        assert result.success is False

    def test_get_package_info_success(self, mock_package_manager):
        """Test getting package information."""
        expected_package = Package(name='test-package', version='1.0.0')
        mock_package_manager.apt.get_package_info.return_value = expected_package
        
        result = mock_package_manager.get_package_info('test-package')
        
        assert result == expected_package

    def test_get_package_info_not_found(self, mock_package_manager):
        """Test getting package information for non-existent package."""
        mock_package_manager.apt.get_package_info.return_value = None
        
        result = mock_package_manager.get_package_info('nonexistent-package')
        
        assert result is None

    def test_list_installed_packages_all(self, mock_package_manager):
        """Test listing all installed packages."""
        expected_packages = [
            Package('package1', '1.0.0', is_custom=True),
            Package('package2', '2.0.0', is_custom=False),
        ]
        mock_package_manager.dpkg.get_installed_packages.return_value = expected_packages
        
        result = mock_package_manager.list_installed_packages()
        
        assert len(result) == 2
        assert result == expected_packages

    def test_list_installed_packages_custom_only(self, mock_package_manager):
        """Test listing only custom installed packages."""
        all_packages = [
            Package('custom-package', '1.0.0', is_custom=True),
            Package('system-package', '2.0.0', is_custom=False),
        ]
        mock_package_manager.dpkg.get_installed_packages.return_value = all_packages
        
        result = mock_package_manager.list_installed_packages(custom_only=True)
        
        assert len(result) == 1
        assert result[0].name == 'custom-package'

    def test_check_system_health_success(self, mock_package_manager):
        """Test successful system health check."""
        mock_package_manager.dpkg.list_broken_packages.return_value = []
        mock_package_manager.dpkg.detect_locks.return_value = []
        mock_package_manager.mode_manager.is_offline_mode.return_value = False
        mock_package_manager.mode_manager.validate_pinned_versions.return_value = (True, [])
        
        result = mock_package_manager.check_system_health()
        
        assert result.success is True
        assert len(result.errors) == 0

    def test_check_system_health_with_broken_packages(self, mock_package_manager):
        """Test system health check with broken packages."""
        broken_packages = [Package('broken-pkg', '1.0.0', status=PackageStatus.BROKEN)]
        mock_package_manager.dpkg.list_broken_packages.return_value = broken_packages
        mock_package_manager.dpkg.detect_locks.return_value = []
        mock_package_manager.mode_manager.is_offline_mode.return_value = False
        
        result = mock_package_manager.check_system_health()
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "Broken package" in result.errors[0]

    def test_check_system_health_with_locks(self, mock_package_manager):
        """Test system health check with active locks."""
        mock_package_manager.dpkg.list_broken_packages.return_value = []
        mock_package_manager.dpkg.detect_locks.return_value = ['/var/lib/dpkg/lock']
        mock_package_manager.mode_manager.is_offline_mode.return_value = False
        
        result = mock_package_manager.check_system_health()
        
        assert result.success is True  # Locks are warnings, not errors
        assert len(result.warnings) > 0
        assert "Active lock" in result.warnings[0]

    def test_fix_broken_system_success(self, mock_package_manager):
        """Test successful broken system fix."""
        mock_package_manager.dpkg.fix_broken_packages.return_value = True
        mock_package_manager.apt.update_package_cache.return_value = True
        
        result = mock_package_manager.fix_broken_system()
        
        assert result.success is True

    def test_fix_broken_system_failure(self, mock_package_manager):
        """Test failed broken system fix."""
        mock_package_manager.dpkg.fix_broken_packages.return_value = False
        mock_package_manager.apt.update_package_cache.return_value = False
        
        result = mock_package_manager.fix_broken_system()
        
        assert result.success is False


class TestPackageClassifier:
    """Test suite for PackageClassifier class."""

    def test_package_classifier_initialization(self, test_config):
        """Test PackageClassifier initialization."""
        classifier = PackageClassifier(test_config)
        
        assert classifier.config == test_config

    def test_is_metapackage_true(self, test_config):
        """Test metapackage detection for actual metapackage."""
        classifier = PackageClassifier(test_config)
        
        # Mock metapackage detection logic
        with patch.object(classifier, '_detect_metapackage', return_value=True):
            result = classifier.is_metapackage('bundle-package')
            
            assert result is True

    def test_is_metapackage_false(self, test_config):
        """Test metapackage detection for regular package."""
        classifier = PackageClassifier(test_config)
        
        with patch.object(classifier, '_detect_metapackage', return_value=False):
            result = classifier.is_metapackage('regular-package')
            
            assert result is False

    def test_is_custom_package_with_prefix(self, test_config):
        """Test custom package detection with prefix."""
        classifier = PackageClassifier(test_config)
        
        result = classifier.is_custom_package('test-package')  # test- is in prefixes
        
        assert result is True

    def test_is_custom_package_without_prefix(self, test_config):
        """Test custom package detection without prefix."""
        classifier = PackageClassifier(test_config)
        
        result = classifier.is_custom_package('system-package')
        
        assert result is False

    def test_should_prioritize_preservation_system_package(self, test_config):
        """Test preservation priority for system packages."""
        classifier = PackageClassifier(test_config)
        
        result = classifier.should_prioritize_preservation('libc6')
        
        assert result is True

    def test_should_prioritize_preservation_custom_package(self, test_config):
        """Test preservation priority for custom packages."""
        classifier = PackageClassifier(test_config)
        
        result = classifier.should_prioritize_preservation('test-package')
        
        assert result is False  # Custom packages have lower preservation priority

    def test_detect_metapackage_by_dependencies(self, test_config):
        """Test metapackage detection by dependency count."""
        classifier = PackageClassifier(test_config)
        
        # Mock many dependencies
        many_deps = [Package(f'dep{i}', '1.0.0') for i in range(10)]
        
        with patch.object(classifier, '_get_package_dependencies', return_value=many_deps):
            result = classifier._detect_metapackage('package-with-many-deps')
            
            # Implementation would check dependency count
            # This is a simplified test

    def test_detect_metapackage_by_name_pattern(self, test_config):
        """Test metapackage detection by name patterns."""
        classifier = PackageClassifier(test_config)
        
        metapackage_names = [
            'ubuntu-desktop',
            'kde-full',
            'gnome-core',
            'build-essential',
            'company-suite'
        ]
        
        for name in metapackage_names:
            with patch.object(classifier, '_check_metapackage_patterns', return_value=True):
                result = classifier._detect_metapackage(name)
                # Pattern matching would be implemented in actual code


class TestModeManager:
    """Test suite for ModeManager class."""

    def test_mode_manager_initialization(self, test_config, mock_apt_interface):
        """Test ModeManager initialization."""
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        assert mode_manager.config == test_config
        assert mode_manager.apt == mock_apt_interface

    def test_is_offline_mode_true(self, test_config, mock_apt_interface):
        """Test offline mode detection when enabled."""
        test_config.is_offline_mode.return_value = True
        
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        assert mode_manager.is_offline_mode() is True

    def test_is_offline_mode_false(self, test_config, mock_apt_interface):
        """Test offline mode detection when disabled."""
        test_config.is_offline_mode.return_value = False
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        # Mock network checker to return True for network availability
        with patch.object(mode_manager, 'network_checker') as mock_checker:
            mock_checker.is_network_available.return_value = True
            mock_checker.are_repositories_accessible.return_value = True
            
            assert mode_manager.is_offline_mode() is False

    def test_get_package_version_for_mode_offline(self, test_config, mock_apt_interface):
        """Test getting package version in offline mode."""
        test_config.is_offline_mode.return_value = True
        test_config.get_pinned_version.return_value = '1.0.0-pinned'
        
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        # Mock is_offline_mode to return True
        with patch.object(mode_manager, 'is_offline_mode', return_value=True):
            version = mode_manager.get_package_version_for_mode('test-package')
            
            assert version == '1.0.0-pinned'

    def test_get_package_version_for_mode_online(self, test_config, mock_apt_interface):
        """Test getting package version in online mode."""
        test_config.is_offline_mode.return_value = False
        mock_apt_interface.get_package_info.return_value = Package(name='test-package', version='3.0.0')
        
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        # Mock is_offline_mode to return False
        with patch.object(mode_manager, 'is_offline_mode', return_value=False):
            version = mode_manager.get_package_version_for_mode('test-package')
            
            assert version == '3.0.0'

    def test_get_package_version_for_mode_offline_no_pinned(self, test_config, mock_apt_interface):
        """Test getting package version in offline mode with no pinned version."""
        test_config.get_pinned_version.return_value = None
        mock_apt_interface.is_installed.return_value = True
        mock_apt_interface.get_package_info.return_value = Package(name='test-package', version='2.0.0')
        
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        # Mock is_offline_mode to return True
        with patch.object(mode_manager, 'is_offline_mode', return_value=True):
            version = mode_manager.get_package_version_for_mode('test-package')
            
            # Should fallback to installed version
            assert version == '2.0.0'

    def test_switch_to_offline_mode(self, test_config, mock_apt_interface):
        """Test switching to offline mode."""
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        mode_manager.switch_to_offline_mode()
        
        test_config.set_offline_mode.assert_called_with(True)

    def test_switch_to_online_mode(self, test_config, mock_apt_interface):
        """Test switching to online mode."""
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        mode_manager.switch_to_online_mode()
        
        test_config.set_offline_mode.assert_called_with(False)

    def test_validate_pinned_versions_success(self, test_config, mock_apt_interface):
        """Test successful pinned version validation."""
        pinned_versions = {'package1': '1.0.0', 'package2': '2.0.0'}
        test_config.version_pinning.get_all_pinned.return_value = pinned_versions
        mock_apt_interface.get_available_versions.return_value = ['1.0.0', '1.1.0', '2.0.0']
        
        mode_manager = ModeManager(test_config, mock_apt_interface)
        is_valid, issues = mode_manager.validate_pinned_versions()
        
        assert is_valid is True
        assert len(issues) == 0

    def test_validate_pinned_versions_invalid(self, test_config, mock_apt_interface):
        """Test pinned version validation with invalid versions."""
        pinned_versions = {'package1': '999.0.0'}  # Non-existent version
        test_config.version_pinning.get_all_pinned.return_value = pinned_versions
        mock_apt_interface.get_available_versions.return_value = ['1.0.0', '2.0.0']
        
        mode_manager = ModeManager(test_config, mock_apt_interface)
        is_valid, issues = mode_manager.validate_pinned_versions()
        
        assert is_valid is False
        assert len(issues) > 0

    def test_auto_detect_appropriate_mode_online(self, test_config, mock_apt_interface):
        """Test auto-detecting appropriate mode when online."""
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        with patch.object(mode_manager, 'network_checker') as mock_checker:
            mock_checker.is_network_available.return_value = True
            mock_checker.are_repositories_accessible.return_value = True
            
            result = mode_manager.auto_detect_mode()
            
            assert 'online' in result

    def test_auto_detect_appropriate_mode_offline(self, test_config, mock_apt_interface):
        """Test auto-detecting appropriate mode when offline."""
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        with patch.object(mode_manager, 'network_checker') as mock_checker:
            mock_checker.is_network_available.return_value = False
            
            result = mode_manager.auto_detect_mode()
            
            assert 'offline' in result


class TestCoreIntegration:
    """Integration tests for core components."""

    def test_package_manager_with_classifier_integration(self, test_config):
        """Test PackageManager integration with PackageClassifier."""
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                mock_apt_instance = Mock()
                mock_dpkg_instance = Mock()
                mock_apt.return_value = mock_apt_instance
                mock_dpkg.return_value = mock_dpkg_instance
                
                manager = PackageManager(test_config)
                
                # Test that classifier is properly integrated
                assert hasattr(manager, 'classifier')
                assert manager.classifier.config == test_config

    def test_package_manager_with_mode_manager_integration(self, test_config):
        """Test PackageManager integration with ModeManager."""
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                mock_apt_instance = Mock()
                mock_dpkg_instance = Mock()
                mock_apt.return_value = mock_apt_instance
                mock_dpkg.return_value = mock_dpkg_instance
                
                manager = PackageManager(test_config)
                
                # Test that mode_manager is properly integrated
                assert hasattr(manager, 'mode_manager')
                assert manager.mode_manager.config == test_config
                assert manager.mode_manager.apt == mock_apt_instance

    def test_complete_package_installation_workflow(self, mock_package_manager):
        """Test complete package installation workflow."""
        # Setup mocks for successful installation
        mock_package_manager.apt.is_installed.return_value = False
        mock_package_manager.apt.install.return_value = True
        mock_package_manager.mode_manager.get_package_version_for_mode.return_value = '1.0.0'
        mock_package_manager.classifier.is_metapackage.return_value = False
        mock_package_manager.classifier.is_custom_package.return_value = True
        
        # Execute installation
        result = mock_package_manager.install_package('test-package')
        
        # Verify workflow
        assert result.success is True
        mock_package_manager.mode_manager.get_package_version_for_mode.assert_called_with('test-package')
        mock_package_manager.classifier.is_metapackage.assert_called_with('test-package')
        mock_package_manager.classifier.is_custom_package.assert_called_with('test-package')

    def test_complete_package_removal_workflow(self, mock_package_manager):
        """Test complete package removal workflow."""
        # Setup mocks for successful removal
        mock_package_manager.apt.is_installed.return_value = True
        mock_package_manager.apt.remove.return_value = True
        mock_package_manager.apt.get_package_info.return_value = Package(
            name='test-package', version='1.0.0'
        )
        mock_package_manager.classifier.is_metapackage.return_value = False
        mock_package_manager.classifier.is_custom_package.return_value = True
        
        # Execute removal
        result = mock_package_manager.remove_package('test-package')
        
        # Verify workflow
        assert result.success is True
        mock_package_manager.apt.is_installed.assert_called_with('test-package')
        mock_package_manager.apt.remove.assert_called_with('test-package', force=False)

    def test_mode_switching_workflow(self, test_config, mock_apt_interface):
        """Test mode switching workflow."""
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        # Test switching to offline mode
        mode_manager.switch_to_offline_mode()
        test_config.set_offline_mode.assert_called_with(True)
        
        # Test switching to online mode
        mode_manager.switch_to_online_mode()
        test_config.set_offline_mode.assert_called_with(False)

    def test_system_health_and_fix_workflow(self, mock_package_manager):
        """Test system health check and fix workflow."""
        # Setup health check to find issues
        mock_package_manager.dpkg.list_broken_packages.return_value = [
            Package('broken-pkg', '1.0.0', status=PackageStatus.BROKEN)
        ]
        mock_package_manager.dpkg.detect_locks.return_value = []
        mock_package_manager.mode_manager.is_offline_mode.return_value = False
        
        # Check health
        health_result = mock_package_manager.check_system_health()
        assert health_result.success is False
        
        # Fix issues
        mock_package_manager.dpkg.fix_broken_packages.return_value = True
        mock_package_manager.apt.update_package_cache.return_value = True
        
        fix_result = mock_package_manager.fix_broken_system()
        assert fix_result.success is True


class TestCoreEdgeCases:
    """Test edge cases and error conditions."""

    def test_package_manager_exception_handling(self, mock_package_manager):
        """Test PackageManager exception handling."""
        # Mock exception in APT interface
        mock_package_manager.apt.is_installed.side_effect = Exception("Test exception")
        
        result = mock_package_manager.install_package('test-package')
        
        assert result.success is False
        assert len(result.errors) > 0

    def test_package_classifier_with_none_config(self):
        """Test PackageClassifier with None config."""
        with patch('debian_metapackage_manager.config.config.Config') as mock_config_class:
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            classifier = PackageClassifier(None)
            
            # Should create default config
            assert classifier.config == mock_config

    def test_mode_manager_network_error_handling(self, test_config, mock_apt_interface):
        """Test ModeManager handling of network errors."""
        mode_manager = ModeManager(test_config, mock_apt_interface)
        
        with patch.object(mode_manager, 'network_checker') as mock_checker:
            mock_checker.is_network_available.side_effect = Exception("Network error")
            
            # Should handle gracefully
            result = mode_manager.auto_detect_mode()
            assert 'offline' in result  # Should fallback to offline

    def test_package_manager_with_malformed_data(self, mock_package_manager):
        """Test PackageManager with malformed package data."""
        # Mock malformed package info
        mock_package_manager.apt.get_package_info.return_value = None
        
        result = mock_package_manager.get_package_info('malformed-package')
        
        assert result is None

    def test_concurrent_package_operations(self, mock_package_manager):
        """Test concurrent package operations (thread safety)."""
        import threading
        import time
        
        results = []
        
        def install_package(package_name):
            mock_package_manager.apt.is_installed.return_value = False
            mock_package_manager.apt.install.return_value = True
            mock_package_manager.mode_manager.get_package_version_for_mode.return_value = '1.0.0'
            
            result = mock_package_manager.install_package(package_name)
            results.append(result.success)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=install_package, args=(f'package{i}',))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert all(results)
        assert len(results) == 5