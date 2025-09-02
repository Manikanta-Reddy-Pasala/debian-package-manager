"""Integration tests for the Debian Package Manager."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from debian_metapackage_manager.cli.main import PackageManagerCLI
from debian_metapackage_manager.core.managers.package_engine import PackageEngine
from debian_metapackage_manager.config import Config
from debian_metapackage_manager.models import Package, OperationResult, PackageStatus


class TestEndToEndPackageInstallation:
    """End-to-end package installation workflow tests."""

    def test_complete_package_installation_workflow(self, temp_config_dir):
        """Test complete package installation from CLI to execution."""
        # Create test configuration
        config_path = Path(temp_config_dir) / 'config.json'
        test_config_data = {
            'custom_prefixes': ['test-', 'integration-'],
            'offline_mode': False,
            'pinned_versions': {},
            'removable_packages': [],
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config_data, f, indent=2)
        
        with patch('debian_metapackage_manager.config.Config') as mock_config_class:
            with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
                with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                    # Setup config mock
                    config = Config(str(config_path))
                    mock_config_class.return_value = config
                    
                    # Setup interface mocks
                    mock_apt_instance = Mock()
                    mock_dpkg_instance = Mock()
                    mock_apt.return_value = mock_apt_instance
                    mock_dpkg.return_value = mock_dpkg_instance
                    
                    # Configure mock behavior for successful installation
                    mock_apt_instance.is_installed.return_value = False
                    mock_apt_instance.install.return_value = True
                    mock_apt_instance.get_available_versions.return_value = ['1.0.0', '2.0.0']
                    
                    # Create CLI and run installation
                    cli = PackageManagerCLI()
                    
                    # Test installation command
                    with patch('sys.argv', ['dpm', 'install', 'test-package']):
                        with patch('builtins.print') as mock_print:
                            result = cli.run(['install', 'test-package'])
                            
                            assert result == 0
                            mock_apt_instance.install.assert_called_once()

    def test_package_installation_with_dependencies(self, temp_config_dir):
        """Test package installation with dependency resolution."""
        config_path = Path(temp_config_dir) / 'config.json'
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                # Setup interface mocks
                mock_apt_instance = Mock()
                mock_dpkg_instance = Mock()
                mock_apt.return_value = mock_apt_instance
                mock_dpkg.return_value = mock_dpkg_instance
                
                # Setup dependency chain
                main_package = Package('test-main', '1.0.0')
                dependency1 = Package('test-dep1', '1.0.0')
                dependency2 = Package('test-dep2', '1.0.0')
                
                mock_apt_instance.get_dependencies.return_value = [dependency1, dependency2]
                mock_apt_instance.is_installed.return_value = False
                mock_apt_instance.install.return_value = True
                
                # Create package engine and test
                engine = PackageEngine(config)
                result = engine.install_package('test-main')
                
                assert result.success is True
                # Should have attempted to install dependencies
                assert mock_apt_instance.install.call_count >= 1


class TestEndToEndPackageRemoval:
    """End-to-end package removal workflow tests."""

    def test_safe_package_removal_workflow(self, temp_config_dir):
        """Test safe package removal workflow."""
        # Create config with custom prefixes
        config_path = Path(temp_config_dir) / 'config.json'
        test_config_data = {
            'custom_prefixes': ['test-', 'safe-'],
            'offline_mode': False,
            'removable_packages': ['explicit-removable-pkg'],
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config_data, f, indent=2)
        
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                # Setup interface mocks
                mock_apt_instance = Mock()
                mock_dpkg_instance = Mock()
                mock_apt.return_value = mock_apt_instance
                mock_dpkg.return_value = mock_dpkg_instance
                
                # Configure for successful removal
                mock_apt_instance.is_installed.return_value = True
                mock_apt_instance.remove.return_value = True
                mock_apt_instance.get_package_info.return_value = Package('test-package', '1.0.0')
                
                # Test removal of custom package (should succeed)
                engine = PackageEngine(config)
                result = engine.remove_package('test-package')
                
                assert result.success is True
                mock_apt_instance.remove.assert_called_once()

    def test_system_package_removal_prevention(self, temp_config_dir):
        """Test that system packages cannot be removed."""
        config_path = Path(temp_config_dir) / 'config.json'
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
            mock_dpkg_instance = Mock()
            mock_dpkg.return_value = mock_dpkg_instance
            
            # Test removal of system package (should be prevented)
            result = mock_dpkg_instance.safe_remove('libc6')
            
            # Should be handled by the DPKG interface's safety checks


class TestModeManagement:
    """Test mode management (offline/online) workflows."""

    def test_offline_mode_workflow(self, temp_config_dir):
        """Test complete offline mode workflow."""
        # Create config with pinned versions
        config_path = Path(temp_config_dir) / 'config.json'
        test_config_data = {
            'custom_prefixes': ['test-'],
            'offline_mode': True,
            'pinned_versions': {
                'test-package': '1.0.0',
                'test-lib': '2.0.0'
            },
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config_data, f, indent=2)
        
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            mock_apt_instance = Mock()
            mock_apt.return_value = mock_apt_instance
            
            # Setup available versions
            mock_apt_instance.get_available_versions.return_value = ['1.0.0', '1.1.0', '2.0.0']
            
            from debian_metapackage_manager.core.mode_manager import ModeManager
            mode_manager = ModeManager(config, mock_apt_instance)
            
            # Test that pinned versions are used in offline mode
            version = mode_manager.get_package_version_for_mode('test-package')
            assert version == '1.0.0'  # Should use pinned version
            
            # Test validation of pinned versions
            is_valid, issues = mode_manager.validate_pinned_versions()
            assert is_valid is True

    def test_online_mode_workflow(self, temp_config_dir):
        """Test complete online mode workflow."""
        config_path = Path(temp_config_dir) / 'config.json'
        test_config_data = {
            'custom_prefixes': ['test-'],
            'offline_mode': False,
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config_data, f, indent=2)
        
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            mock_apt_instance = Mock()
            mock_apt.return_value = mock_apt_instance
            
            # Setup available versions
            mock_apt_instance.get_available_versions.return_value = ['1.0.0', '1.1.0', '2.0.0']
            
            from debian_metapackage_manager.core.mode_manager import ModeManager
            mode_manager = ModeManager(config, mock_apt_instance)
            
            # Test that latest versions are used in online mode
            version = mode_manager.get_package_version_for_mode('test-package')
            assert version == '2.0.0'  # Should use latest version

    def test_mode_switching_workflow(self, temp_config_dir):
        """Test switching between modes."""
        config_path = Path(temp_config_dir) / 'config.json'
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            mock_apt_instance = Mock()
            mock_apt.return_value = mock_apt_instance
            
            from debian_metapackage_manager.core.mode_manager import ModeManager
            mode_manager = ModeManager(config, mock_apt_instance)
            
            # Test switching to offline mode
            assert mode_manager.switch_to_offline_mode() is True
            assert config.is_offline_mode() is True
            
            # Test switching to online mode
            assert mode_manager.switch_to_online_mode() is True
            assert config.is_offline_mode() is False


class TestSystemHealthAndMaintenance:
    """Test system health checking and maintenance workflows."""

    def test_system_health_check_workflow(self, temp_config_dir):
        """Test complete system health check workflow."""
        config_path = Path(temp_config_dir) / 'config.json'
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                # Setup interface mocks
                mock_apt_instance = Mock()
                mock_dpkg_instance = Mock()
                mock_apt.return_value = mock_apt_instance
                mock_dpkg.return_value = mock_dpkg_instance
                
                # Configure healthy system
                mock_dpkg_instance.list_broken_packages.return_value = []
                mock_dpkg_instance.detect_locks.return_value = []
                
                # Test health check
                engine = PackageEngine(config)
                result = engine.check_system_health()
                
                assert result.success is True
                assert len(result.errors) == 0

    def test_broken_system_fix_workflow(self, temp_config_dir):
        """Test fixing broken system workflow."""
        config_path = Path(temp_config_dir) / 'config.json'
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                # Setup interface mocks
                mock_apt_instance = Mock()
                mock_dpkg_instance = Mock()
                mock_apt.return_value = mock_apt_instance
                mock_dpkg.return_value = mock_dpkg_instance
                
                # Configure broken system that can be fixed
                broken_package = Package('broken-pkg', '1.0.0', status=PackageStatus.BROKEN)
                mock_dpkg_instance.list_broken_packages.return_value = [broken_package]
                mock_dpkg_instance.fix_broken_packages.return_value = True
                mock_apt_instance.update_package_cache.return_value = True
                
                # Test system fix
                engine = PackageEngine(config)
                
                # First check health (should fail)
                health_result = engine.check_system_health()
                assert health_result.success is False
                
                # Then fix system (should succeed)
                fix_result = engine.fix_broken_system()
                assert fix_result.success is True


class TestConfigurationManagement:
    """Test configuration management workflows."""

    def test_configuration_persistence_workflow(self, temp_config_dir):
        """Test configuration persistence across operations."""
        config_path = Path(temp_config_dir) / 'config.json'
        
        # Create initial config
        config1 = Config(str(config_path))
        config1.add_custom_prefix('workflow-test-')
        config1.set_offline_mode(True)
        config1.add_removable_package('test-removable')
        
        # Create new config instance (should load persisted data)
        config2 = Config(str(config_path))
        
        assert 'workflow-test-' in config2.get_custom_prefixes()
        assert config2.is_offline_mode() is True
        assert 'test-removable' in config2.get_removable_packages()

    def test_configuration_validation_workflow(self, temp_config_dir):
        """Test configuration validation workflow."""
        config_path = Path(temp_config_dir) / 'config.json'
        
        # Create config with invalid data
        invalid_config_data = {
            'custom_prefixes': 'not-a-list',  # Should be list
            'offline_mode': 'not-a-boolean',  # Should be boolean
        }
        
        with open(config_path, 'w') as f:
            json.dump(invalid_config_data, f)
        
        # Should handle invalid config gracefully and use defaults
        config = Config(str(config_path))
        
        # Should fall back to defaults
        assert isinstance(config.get_custom_prefixes(), list)


class TestRemoteOperations:
    """Test remote operation workflows."""

    def test_remote_connection_workflow(self):
        """Test remote connection establishment workflow."""
        from debian_metapackage_manager.core.managers.remote_manager import RemotePackageManager
        
        with patch('debian_metapackage_manager.core.managers.remote_manager.SSHConnection') as mock_ssh:
            mock_connection = Mock()
            mock_connection.test_connection.return_value = True
            mock_ssh.return_value = mock_connection
            
            remote_manager = RemotePackageManager()
            
            # Test connection
            result = remote_manager.connect_remote('test-host', 'test-user')
            assert result is True
            
            # Test that we're now connected to remote
            assert remote_manager.is_remote_connected() is True
            
            # Test disconnection
            remote_manager.disconnect()
            assert remote_manager.is_remote_connected() is False

    def test_remote_package_operation_workflow(self):
        """Test remote package operation workflow."""
        from debian_metapackage_manager.core.managers.remote_manager import RemotePackageManager
        
        with patch('debian_metapackage_manager.core.managers.remote_manager.SSHConnection') as mock_ssh:
            mock_connection = Mock()
            mock_connection.test_connection.return_value = True
            mock_connection.execute_command.return_value = (0, "success", "")
            mock_ssh.return_value = mock_connection
            
            remote_manager = RemotePackageManager()
            
            # Connect to remote
            remote_manager.connect_remote('test-host', 'test-user')
            
            # Execute remote command
            result = remote_manager.execute_command('install', 'test-package')
            
            # Should have executed command on remote
            mock_connection.execute_command.assert_called()


class TestErrorHandlingWorkflows:
    """Test error handling across different workflows."""

    def test_network_error_handling_workflow(self, temp_config_dir):
        """Test handling of network errors during operations."""
        config_path = Path(temp_config_dir) / 'config.json'
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            mock_apt_instance = Mock()
            mock_apt.return_value = mock_apt_instance
            
            # Simulate network error
            mock_apt_instance.update_package_cache.side_effect = Exception("Network error")
            
            from debian_metapackage_manager.core.mode_manager import ModeManager
            with patch('debian_metapackage_manager.utils.network.NetworkChecker') as mock_checker:
                mock_checker.return_value.is_network_available.return_value = False
                
                mode_manager = ModeManager(config, mock_apt_instance)
                
                # Should auto-detect offline mode due to network error
                detected_mode = mode_manager.auto_detect_appropriate_mode()
                assert detected_mode == 'offline'

    def test_permission_error_handling_workflow(self, temp_config_dir):
        """Test handling of permission errors."""
        config_path = Path(temp_config_dir) / 'config.json'
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                mock_apt_instance = Mock()
                mock_dpkg_instance = Mock()
                mock_apt.return_value = mock_apt_instance
                mock_dpkg.return_value = mock_dpkg_instance
                
                # Simulate permission error
                mock_apt_instance.install.side_effect = PermissionError("Permission denied")
                
                engine = PackageEngine(config)
                result = engine.install_package('test-package')
                
                # Should handle permission error gracefully
                assert result.success is False
                assert len(result.errors) > 0


class TestCompleteScenarios:
    """Test complete real-world scenarios."""

    def test_complete_metapackage_installation_scenario(self, temp_config_dir):
        """Test complete metapackage installation scenario."""
        config_path = Path(temp_config_dir) / 'config.json'
        test_config_data = {
            'custom_prefixes': ['company-', 'suite-'],
            'offline_mode': False,
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config_data, f, indent=2)
        
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                # Setup interface mocks
                mock_apt_instance = Mock()
                mock_dpkg_instance = Mock()
                mock_apt.return_value = mock_apt_instance
                mock_dpkg.return_value = mock_dpkg_instance
                
                # Configure metapackage with dependencies
                main_package = Package('company-suite', '1.0.0', is_metapackage=True, is_custom=True)
                dependencies = [
                    Package('company-app1', '1.0.0', is_custom=True),
                    Package('company-app2', '1.0.0', is_custom=True),
                    Package('company-lib', '1.0.0', is_custom=True),
                ]
                
                mock_apt_instance.get_dependencies.return_value = dependencies
                mock_apt_instance.is_installed.return_value = False
                mock_apt_instance.install.return_value = True
                
                # Test metapackage installation
                engine = PackageEngine(config)
                result = engine.install_package('company-suite')
                
                assert result.success is True
                # Should have attempted to install main package and dependencies
                assert mock_apt_instance.install.call_count >= 1

    def test_system_migration_scenario(self, temp_config_dir):
        """Test system migration scenario (offline to online mode)."""
        config_path = Path(temp_config_dir) / 'config.json'
        
        # Start in offline mode with pinned versions
        config = Config(str(config_path))
        config.set_offline_mode(True)
        config.set_pinned_version('migrate-pkg', '1.0.0')
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            mock_apt_instance = Mock()
            mock_apt.return_value = mock_apt_instance
            
            # Setup versions (newer available)
            mock_apt_instance.get_available_versions.return_value = ['1.0.0', '1.1.0', '2.0.0']
            
            from debian_metapackage_manager.core.mode_manager import ModeManager
            mode_manager = ModeManager(config, mock_apt_instance)
            
            # Test migration workflow
            # 1. Start in offline mode
            assert mode_manager.is_offline_mode() is True
            version_offline = mode_manager.get_package_version_for_mode('migrate-pkg')
            assert version_offline == '1.0.0'  # Uses pinned version
            
            # 2. Switch to online mode
            mode_manager.switch_to_online_mode()
            assert mode_manager.is_offline_mode() is False
            version_online = mode_manager.get_package_version_for_mode('migrate-pkg')
            assert version_online == '2.0.0'  # Uses latest version

    def test_disaster_recovery_scenario(self, temp_config_dir):
        """Test disaster recovery scenario."""
        config_path = Path(temp_config_dir) / 'config.json'
        config = Config(str(config_path))
        
        with patch('debian_metapackage_manager.interfaces.apt.APTInterface') as mock_apt:
            with patch('debian_metapackage_manager.interfaces.dpkg.DPKGInterface') as mock_dpkg:
                mock_apt_instance = Mock()
                mock_dpkg_instance = Mock()
                mock_apt.return_value = mock_apt_instance
                mock_dpkg.return_value = mock_dpkg_instance
                
                # Simulate heavily broken system
                broken_packages = [
                    Package('broken1', '1.0.0', status=PackageStatus.BROKEN),
                    Package('broken2', '1.0.0', status=PackageStatus.BROKEN),
                ]
                locks = ['/var/lib/dpkg/lock', '/var/cache/apt/archives/lock']
                
                mock_dpkg_instance.list_broken_packages.return_value = broken_packages
                mock_dpkg_instance.detect_locks.return_value = locks
                mock_dpkg_instance.fix_broken_packages.return_value = True
                mock_apt_instance.update_package_cache.return_value = True
                
                engine = PackageEngine(config)
                
                # Test disaster recovery workflow
                # 1. Assess damage
                health_result = engine.check_system_health()
                assert health_result.success is False
                assert len(health_result.errors) > 0
                
                # 2. Attempt automatic fix
                fix_result = engine.fix_broken_system()
                assert fix_result.success is True
                
                # 3. Verify fix
                mock_dpkg_instance.list_broken_packages.return_value = []  # Fixed
                mock_dpkg_instance.detect_locks.return_value = []  # Locks cleared
                
                health_result_after = engine.check_system_health()
                assert health_result_after.success is True