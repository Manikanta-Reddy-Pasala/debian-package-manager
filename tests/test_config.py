"""Tests for configuration management."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from debian_metapackage_manager.config.config import (
    Config, PackagePrefixes, VersionPinning, RemovablePackages
)


class TestConfig:
    """Test suite for main Config class."""

    def test_config_initialization_with_path(self, temp_config_dir):
        """Test config initialization with custom path."""
        config_path = Path(temp_config_dir) / 'custom_config.json'
        config = Config(str(config_path))
        
        assert config.config_path == str(config_path)
        assert isinstance(config.package_prefixes, PackagePrefixes)
        assert isinstance(config.version_pinning, VersionPinning)
        assert isinstance(config.removable_packages, RemovablePackages)

    def test_config_initialization_without_path(self):
        """Test config initialization with default path."""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path('/tmp/test_home')
            with patch('pathlib.Path.mkdir'):
                config = Config()
                expected_path = '/tmp/test_home/.config/debian-package-manager/config.json'
                assert config.config_path == expected_path

    def test_config_load_existing_file(self, temp_config_dir):
        """Test loading existing configuration file."""
        config_path = Path(temp_config_dir) / 'config.json'
        test_config = {
            'custom_prefixes': ['test-', 'dev-'],
            'offline_mode': True,
            'pinned_versions': {'pkg1': '1.0.0'},
            'removable_packages': ['removable-pkg']
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        config = Config(str(config_path))
        
        assert config.get_custom_prefixes() == ['test-', 'dev-']
        assert config.is_offline_mode() == True
        assert config.get_pinned_version('pkg1') == '1.0.0'
        assert 'removable-pkg' in config.get_removable_packages()

    def test_config_load_malformed_file(self, temp_config_dir):
        """Test loading malformed JSON file falls back to defaults."""
        config_path = Path(temp_config_dir) / 'bad_config.json'
        
        with open(config_path, 'w') as f:
            f.write('invalid json {')
        
        config = Config(str(config_path))
        
        # Should fall back to default config
        assert isinstance(config.get_custom_prefixes(), list)
        assert 'mycompany-' in config.get_custom_prefixes()

    def test_config_create_default_config(self):
        """Test creating default configuration."""
        config = Config()
        default_prefixes = config.get_custom_prefixes()
        
        assert 'mycompany-' in default_prefixes
        assert 'internal-' in default_prefixes
        assert 'custom-' in default_prefixes
        assert not config.is_offline_mode()

    def test_config_get_custom_prefixes(self, test_config):
        """Test getting custom prefixes."""
        prefixes = test_config.get_custom_prefixes()
        
        assert isinstance(prefixes, list)
        assert 'test-' in prefixes
        assert 'custom-' in prefixes

    def test_config_offline_mode_operations(self, test_config):
        """Test offline mode get/set operations."""
        # Initially should be False (from test fixture)
        assert not test_config.is_offline_mode()
        
        # Set to True
        test_config.set_offline_mode(True)
        assert test_config.is_offline_mode()
        
        # Set back to False
        test_config.set_offline_mode(False)
        assert not test_config.is_offline_mode()

    def test_config_add_custom_prefix(self, test_config):
        """Test adding custom prefix."""
        initial_count = len(test_config.get_custom_prefixes())
        
        test_config.add_custom_prefix('new-prefix-')
        
        prefixes = test_config.get_custom_prefixes()
        assert len(prefixes) == initial_count + 1
        assert 'new-prefix-' in prefixes

    def test_config_remove_custom_prefix(self, test_config):
        """Test removing custom prefix."""
        test_config.add_custom_prefix('temp-prefix-')
        assert 'temp-prefix-' in test_config.get_custom_prefixes()
        
        test_config.remove_custom_prefix('temp-prefix-')
        assert 'temp-prefix-' not in test_config.get_custom_prefixes()

    def test_config_pinned_version_operations(self, test_config):
        """Test pinned version operations."""
        # Set pinned version
        test_config.set_pinned_version('test-pkg', '2.0.0')
        assert test_config.get_pinned_version('test-pkg') == '2.0.0'
        
        # Non-existent package should return None
        assert test_config.get_pinned_version('non-existent') is None

    def test_config_add_removable_package(self, test_config):
        """Test adding removable package."""
        test_config.add_removable_package('safe-to-remove')
        
        removable_packages = test_config.get_removable_packages()
        assert 'safe-to-remove' in removable_packages

    def test_config_add_system_critical_package_fails(self, test_config):
        """Test that adding system-critical package fails."""
        with pytest.raises(ValueError, match="Cannot add system-critical package"):
            test_config.add_removable_package('libc6')

    def test_config_remove_removable_package(self, test_config):
        """Test removing removable package."""
        test_config.add_removable_package('temp-pkg')
        assert 'temp-pkg' in test_config.get_removable_packages()
        
        test_config.remove_removable_package('temp-pkg')
        assert 'temp-pkg' not in test_config.get_removable_packages()

    def test_config_can_remove_package_with_prefix(self, test_config):
        """Test can_remove_package with custom prefix."""
        # Package with test- prefix should be removable
        assert test_config.can_remove_package('test-myapp')
        
        # Package with custom- prefix should be removable
        assert test_config.can_remove_package('custom-tool')
        
        # System package should not be removable
        assert not test_config.can_remove_package('libc6')

    def test_config_can_remove_package_in_removable_list(self, test_config):
        """Test can_remove_package with package in removable list."""
        test_config.add_removable_package('special-pkg')
        
        # Should be removable even without custom prefix
        assert test_config.can_remove_package('special-pkg')

    def test_config_system_critical_packages_detection(self, test_config):
        """Test detection of system-critical packages."""
        critical_packages = [
            'libc6', 'bash', 'coreutils', 'systemd', 'apt', 'dpkg',
            'linux-image-5.4.0', 'grub-pc'
        ]
        
        for pkg in critical_packages:
            with pytest.raises(ValueError):
                test_config.add_removable_package(pkg)

    def test_config_save_config(self, temp_config_dir):
        """Test saving configuration."""
        config_path = Path(temp_config_dir) / 'save_test.json'
        config = Config(str(config_path))
        
        # Modify configuration
        config.add_custom_prefix('saved-prefix-')
        config.set_offline_mode(True)
        
        # Save should be called automatically, but test explicit save
        config.save_config()
        
        # Reload and verify
        new_config = Config(str(config_path))
        assert 'saved-prefix-' in new_config.get_custom_prefixes()
        assert new_config.is_offline_mode()


class TestPackagePrefixes:
    """Test suite for PackagePrefixes class."""

    def test_package_prefixes_initialization(self):
        """Test PackagePrefixes initialization."""
        prefixes = PackagePrefixes(['test-', 'dev-'])
        
        assert prefixes.get_prefixes() == ['test-', 'dev-']

    def test_package_prefixes_initialization_empty(self):
        """Test PackagePrefixes initialization with empty list."""
        prefixes = PackagePrefixes([])
        
        assert prefixes.get_prefixes() == []

    def test_package_prefixes_initialization_none(self):
        """Test PackagePrefixes initialization with None."""
        prefixes = PackagePrefixes(None)
        
        assert prefixes.get_prefixes() == []

    def test_package_prefixes_add_prefix(self):
        """Test adding prefix."""
        prefixes = PackagePrefixes(['existing-'])
        
        prefixes.add_prefix('new-')
        
        result = prefixes.get_prefixes()
        assert 'existing-' in result
        assert 'new-' in result
        assert len(result) == 2

    def test_package_prefixes_add_duplicate_prefix(self):
        """Test adding duplicate prefix (should not duplicate)."""
        prefixes = PackagePrefixes(['test-'])
        
        prefixes.add_prefix('test-')
        
        result = prefixes.get_prefixes()
        assert result.count('test-') == 1

    def test_package_prefixes_remove_prefix(self):
        """Test removing prefix."""
        prefixes = PackagePrefixes(['test-', 'dev-'])
        
        prefixes.remove_prefix('test-')
        
        result = prefixes.get_prefixes()
        assert 'test-' not in result
        assert 'dev-' in result

    def test_package_prefixes_remove_nonexistent_prefix(self):
        """Test removing non-existent prefix (should not error)."""
        prefixes = PackagePrefixes(['test-'])
        
        # Should not raise error
        prefixes.remove_prefix('nonexistent-')
        
        assert prefixes.get_prefixes() == ['test-']

    def test_package_prefixes_is_custom_package(self):
        """Test custom package detection."""
        prefixes = PackagePrefixes(['mycompany-', 'dev-'])
        
        assert prefixes.is_custom_package('mycompany-app')
        assert prefixes.is_custom_package('dev-tool')
        assert not prefixes.is_custom_package('system-package')
        assert not prefixes.is_custom_package('apt')

    def test_package_prefixes_get_prefixes_returns_copy(self):
        """Test that get_prefixes returns a copy, not reference."""
        prefixes = PackagePrefixes(['test-'])
        
        result1 = prefixes.get_prefixes()
        result2 = prefixes.get_prefixes()
        
        # Should be equal but not same object
        assert result1 == result2
        assert result1 is not result2
        
        # Modifying returned list should not affect internal state
        result1.append('modified-')
        assert 'modified-' not in prefixes.get_prefixes()


class TestVersionPinning:
    """Test suite for VersionPinning class."""

    def test_version_pinning_initialization(self):
        """Test VersionPinning initialization."""
        versions = {'pkg1': '1.0.0', 'pkg2': '2.0.0'}
        pinning = VersionPinning(versions)
        
        assert pinning.get_pinned_version('pkg1') == '1.0.0'
        assert pinning.get_pinned_version('pkg2') == '2.0.0'

    def test_version_pinning_initialization_empty(self):
        """Test VersionPinning initialization with empty dict."""
        pinning = VersionPinning({})
        
        assert pinning.get_pinned_version('any-pkg') is None

    def test_version_pinning_initialization_none(self):
        """Test VersionPinning initialization with None."""
        pinning = VersionPinning(None)
        
        assert pinning.get_pinned_version('any-pkg') is None

    def test_version_pinning_set_version(self):
        """Test setting pinned version."""
        pinning = VersionPinning({})
        
        pinning.set_pinned_version('new-pkg', '3.0.0')
        
        assert pinning.get_pinned_version('new-pkg') == '3.0.0'

    def test_version_pinning_remove_version(self):
        """Test removing pinned version."""
        pinning = VersionPinning({'pkg1': '1.0.0'})
        
        pinning.remove_pinned_version('pkg1')
        
        assert pinning.get_pinned_version('pkg1') is None

    def test_version_pinning_remove_nonexistent_version(self):
        """Test removing non-existent pinned version."""
        pinning = VersionPinning({'pkg1': '1.0.0'})
        
        # Should not raise error
        pinning.remove_pinned_version('nonexistent')
        
        assert pinning.get_pinned_version('pkg1') == '1.0.0'

    def test_version_pinning_has_pinned_version(self):
        """Test checking if package has pinned version."""
        pinning = VersionPinning({'pkg1': '1.0.0'})
        
        assert pinning.has_pinned_version('pkg1')
        assert not pinning.has_pinned_version('pkg2')

    def test_version_pinning_get_all_pinned(self):
        """Test getting all pinned versions."""
        versions = {'pkg1': '1.0.0', 'pkg2': '2.0.0'}
        pinning = VersionPinning(versions)
        
        all_pinned = pinning.get_all_pinned()
        
        assert all_pinned == versions
        assert all_pinned is not versions  # Should be a copy

    def test_version_pinning_update_existing_version(self):
        """Test updating existing pinned version."""
        pinning = VersionPinning({'pkg1': '1.0.0'})
        
        pinning.set_pinned_version('pkg1', '2.0.0')
        
        assert pinning.get_pinned_version('pkg1') == '2.0.0'


class TestRemovablePackages:
    """Test suite for RemovablePackages class."""

    def test_removable_packages_initialization(self):
        """Test RemovablePackages initialization."""
        packages = ['pkg1', 'pkg2']
        removable = RemovablePackages(packages)
        
        assert removable.get_packages() == ['pkg1', 'pkg2']

    def test_removable_packages_initialization_empty(self):
        """Test RemovablePackages initialization with empty list."""
        removable = RemovablePackages([])
        
        assert removable.get_packages() == []

    def test_removable_packages_initialization_none(self):
        """Test RemovablePackages initialization with None."""
        removable = RemovablePackages(None)
        
        assert removable.get_packages() == []

    def test_removable_packages_add_package(self):
        """Test adding removable package."""
        removable = RemovablePackages(['existing'])
        
        removable.add_package('new-pkg')
        
        packages = removable.get_packages()
        assert 'existing' in packages
        assert 'new-pkg' in packages

    def test_removable_packages_add_duplicate_package(self):
        """Test adding duplicate package (should not duplicate)."""
        removable = RemovablePackages(['pkg1'])
        
        removable.add_package('pkg1')
        
        packages = removable.get_packages()
        assert packages.count('pkg1') == 1

    def test_removable_packages_remove_package(self):
        """Test removing removable package."""
        removable = RemovablePackages(['pkg1', 'pkg2'])
        
        removable.remove_package('pkg1')
        
        packages = removable.get_packages()
        assert 'pkg1' not in packages
        assert 'pkg2' in packages

    def test_removable_packages_remove_nonexistent_package(self):
        """Test removing non-existent package (should not error)."""
        removable = RemovablePackages(['pkg1'])
        
        # Should not raise error
        removable.remove_package('nonexistent')
        
        assert removable.get_packages() == ['pkg1']

    def test_removable_packages_is_removable(self):
        """Test checking if package is removable."""
        removable = RemovablePackages(['safe-pkg', 'temp-pkg'])
        
        assert removable.is_removable('safe-pkg')
        assert removable.is_removable('temp-pkg')
        assert not removable.is_removable('system-pkg')

    def test_removable_packages_clear_all(self):
        """Test clearing all removable packages."""
        removable = RemovablePackages(['pkg1', 'pkg2', 'pkg3'])
        
        removable.clear_all()
        
        assert removable.get_packages() == []

    def test_removable_packages_get_packages_returns_copy(self):
        """Test that get_packages returns a copy, not reference."""
        removable = RemovablePackages(['pkg1'])
        
        result1 = removable.get_packages()
        result2 = removable.get_packages()
        
        # Should be equal but not same object
        assert result1 == result2
        assert result1 is not result2
        
        # Modifying returned list should not affect internal state
        result1.append('modified')
        assert 'modified' not in removable.get_packages()


class TestConfigIntegration:
    """Integration tests for Config components."""

    def test_config_integration_all_components(self, temp_config_dir):
        """Test integration of all config components."""
        config_path = Path(temp_config_dir) / 'integration_test.json'
        config = Config(str(config_path))
        
        # Test prefixes
        config.add_custom_prefix('integration-')
        assert config.can_remove_package('integration-test')
        
        # Test version pinning
        config.set_pinned_version('integration-pkg', '1.5.0')
        assert config.get_pinned_version('integration-pkg') == '1.5.0'
        
        # Test removable packages
        config.add_removable_package('safe-integration-pkg')
        assert config.can_remove_package('safe-integration-pkg')
        
        # Test offline mode
        config.set_offline_mode(True)
        assert config.is_offline_mode()
        
        # Reload config and verify persistence
        new_config = Config(str(config_path))
        assert 'integration-' in new_config.get_custom_prefixes()
        assert new_config.get_pinned_version('integration-pkg') == '1.5.0'
        assert 'safe-integration-pkg' in new_config.get_removable_packages()
        assert new_config.is_offline_mode()

    def test_config_complex_package_removal_logic(self, temp_config_dir):
        """Test complex package removal logic."""
        config_path = Path(temp_config_dir) / 'removal_test.json'
        config = Config(str(config_path))
        
        # Add custom prefixes
        config.add_custom_prefix('company-')
        config.add_custom_prefix('dev-')
        
        # Add specific removable packages
        config.add_removable_package('special-system-pkg')
        
        # Test various scenarios
        assert config.can_remove_package('company-app')      # Has custom prefix
        assert config.can_remove_package('dev-tool')        # Has custom prefix  
        assert config.can_remove_package('special-system-pkg')  # Explicitly removable
        assert not config.can_remove_package('libc6')       # System critical
        assert not config.can_remove_package('random-pkg')  # No prefix, not removable

    def test_config_error_handling_file_operations(self, temp_config_dir):
        """Test config error handling during file operations."""
        # Test with unwritable directory
        config_path = Path(temp_config_dir) / 'nonexistent' / 'config.json'
        
        # Should still work by falling back to defaults
        config = Config(str(config_path))
        
        # Basic operations should still work
        assert isinstance(config.get_custom_prefixes(), list)
        
        # Save operations should handle errors gracefully
        config.add_custom_prefix('error-test-')
        # Should not raise exception even if save fails

    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_config_handle_save_error(self, mock_file, temp_config_dir):
        """Test handling of save errors."""
        config_path = Path(temp_config_dir) / 'save_error_test.json'
        config = Config(str(config_path))
        
        # Should handle save error gracefully
        config.add_custom_prefix('test-error-')
        
        # Operation should complete without exception
        # (error is logged but not raised)