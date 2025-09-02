#!/usr/bin/env python3
"""
Integration tests for Debian Package Manager.
These tests verify that all components work together correctly.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from debian_metapackage_manager.engine import PackageEngine
from debian_metapackage_manager.models import Package, PackageStatus, DependencyPlan, OperationResult
from debian_metapackage_manager.config import Config


class TestPackageEngineIntegration:
    """Integration tests for the complete package engine."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "config.json")
        
        # Create test config
        test_config = {
            "package_prefixes": {
                "custom_prefixes": ["test-", "mycompany-", "integration-"]
            },
            "offline_mode": False,
            "version_pinning": {
                "test-package": "1.0.0",
                "mycompany-tools": "2.1.0"
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Create engine with test config
        self.engine = PackageEngine(config_path=self.config_file)
    
    def test_complete_install_workflow(self):
        """Test complete package installation workflow."""
        # Mock all the underlying interfaces
        with patch.object(self.engine.apt, 'is_package_available') as mock_available, \
             patch.object(self.engine.apt, 'get_dependencies') as mock_deps, \
             patch.object(self.engine.dependency_resolver, 'resolve_dependencies') as mock_resolve, \
             patch.object(self.engine.conflict_handler, 'handle_conflicts') as mock_conflicts, \
             patch.object(self.engine.apt, 'install_package') as mock_install:
            
            # Set up mocks
            mock_available.return_value = True
            mock_deps.return_value = [
                Package("dependency1", "1.0.0", PackageStatus.NOT_INSTALLED),
                Package("dependency2", "2.0.0", PackageStatus.INSTALLED)
            ]
            
            mock_resolve.return_value = DependencyPlan(
                to_install=[Package("test-package", "1.0.0", PackageStatus.NOT_INSTALLED)],
                to_remove=[],
                to_upgrade=[],
                conflicts=[]
            )
            
            mock_conflicts.return_value = True  # User approved
            mock_install.return_value = OperationResult(
                success=True,
                packages_affected=[Package("test-package", "1.0.0", PackageStatus.INSTALLED)],
                warnings=[],
                errors=[]
            )
            
            # Execute installation
            result = self.engine.install_package("test-package")
            
            # Verify workflow
            assert result.success
            assert len(result.packages_affected) == 1
            assert result.packages_affected[0].name == "test-package"
            
            # Verify all components were called
            mock_available.assert_called_once_with("test-package")
            mock_deps.assert_called_once_with("test-package")
            mock_resolve.assert_called_once()
            mock_conflicts.assert_called_once()
            mock_install.assert_called_once()
    
    def test_complete_remove_workflow(self):
        """Test complete package removal workflow."""
        with patch.object(self.engine.apt, 'is_package_installed') as mock_installed, \
             patch.object(self.engine.apt, 'get_reverse_dependencies') as mock_rdeps, \
             patch.object(self.engine.dependency_resolver, 'resolve_dependencies') as mock_resolve, \
             patch.object(self.engine.conflict_handler, 'handle_conflicts') as mock_conflicts, \
             patch.object(self.engine.apt, 'remove_package') as mock_remove:
            
            # Set up mocks
            mock_installed.return_value = True
            mock_rdeps.return_value = [
                Package("dependent1", "1.0.0", PackageStatus.INSTALLED)
            ]
            
            mock_resolve.return_value = DependencyPlan(
                to_install=[],
                to_remove=[Package("test-package", "1.0.0", PackageStatus.INSTALLED)],
                to_upgrade=[],
                conflicts=[]
            )
            
            mock_conflicts.return_value = True  # User approved
            mock_remove.return_value = OperationResult(
                success=True,
                packages_affected=[Package("test-package", "1.0.0", PackageStatus.NOT_INSTALLED)],
                warnings=[],
                errors=[]
            )
            
            # Execute removal
            result = self.engine.remove_package("test-package")
            
            # Verify workflow
            assert result.success
            assert len(result.packages_affected) == 1
            assert result.packages_affected[0].name == "test-package"
            
            # Verify all components were called
            mock_installed.assert_called_once_with("test-package")
            mock_rdeps.assert_called_once_with("test-package")
            mock_resolve.assert_called_once()
            mock_conflicts.assert_called_once()
            mock_remove.assert_called_once()
    
    def test_offline_mode_integration(self):
        """Test offline mode integration across components."""
        # Switch to offline mode
        self.engine.mode_manager.switch_to_offline_mode()
        
        with patch.object(self.engine.apt, 'is_package_available') as mock_available, \
             patch.object(self.engine.mode_manager, 'get_pinned_version') as mock_pinned, \
             patch.object(self.engine.apt, 'install_specific_version') as mock_install_version:
            
            mock_available.return_value = True
            mock_pinned.return_value = "1.0.0"
            mock_install_version.return_value = OperationResult(
                success=True,
                packages_affected=[Package("test-package", "1.0.0", PackageStatus.INSTALLED)],
                warnings=[],
                errors=[]
            )
            
            # Install in offline mode
            result = self.engine.install_package("test-package")
            
            # Verify offline mode was used
            mock_pinned.assert_called_once_with("test-package")
            mock_install_version.assert_called_once_with("test-package", "1.0.0")
    
    def test_custom_package_recognition_integration(self):
        """Test custom package recognition across all components."""
        # Test with custom package
        custom_package = "mycompany-dev-tools"
        
        with patch.object(self.engine.apt, 'is_package_available') as mock_available, \
             patch.object(self.engine.apt, 'get_dependencies') as mock_deps:
            
            mock_available.return_value = True
            mock_deps.return_value = []
            
            # Check if package is recognized as custom
            is_custom = self.engine.classifier.is_custom_package(custom_package)
            assert is_custom
            
            # Verify it's handled as custom throughout the system
            package_info = self.engine.get_package_info(custom_package)
            if package_info:
                assert package_info.is_custom
    
    def test_conflict_resolution_integration(self):
        """Test conflict resolution integration."""
        with patch.object(self.engine.apt, 'is_package_available') as mock_available, \
             patch.object(self.engine.dependency_resolver, 'resolve_dependencies') as mock_resolve, \
             patch.object(self.engine.conflict_handler, 'handle_conflicts') as mock_conflicts:
            
            mock_available.return_value = True
            
            # Create a conflict scenario
            mock_resolve.return_value = DependencyPlan(
                to_install=[Package("new-package", "1.0.0", PackageStatus.NOT_INSTALLED)],
                to_remove=[Package("conflicting-package", "1.0.0", PackageStatus.INSTALLED)],
                to_upgrade=[],
                conflicts=[
                    ("new-package", "conflicting-package", "version conflict")
                ]
            )
            
            # Test user rejection
            mock_conflicts.return_value = False
            result = self.engine.install_package("new-package")
            assert not result.success
            
            # Test user approval
            mock_conflicts.return_value = True
            with patch.object(self.engine.apt, 'install_package') as mock_install:
                mock_install.return_value = OperationResult(success=True, packages_affected=[], warnings=[], errors=[])
                result = self.engine.install_package("new-package")
                assert result.success
    
    def test_error_recovery_integration(self):
        """Test error recovery across components."""
        with patch.object(self.engine.apt, 'is_package_available') as mock_available, \
             patch.object(self.engine.apt, 'install_package') as mock_install, \
             patch.object(self.engine.error_handler, 'handle_installation_error') as mock_error:
            
            mock_available.return_value = True
            
            # Simulate installation failure
            mock_install.return_value = OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=["Installation failed due to network error"]
            )
            
            mock_error.return_value = OperationResult(
                success=True,
                packages_affected=[],
                warnings=["Recovered from error"],
                errors=[]
            )
            
            # Test error recovery
            result = self.engine.install_package("test-package")
            
            # Verify error handler was called
            mock_error.assert_called_once()
    
    def test_system_health_integration(self):
        """Test system health check integration."""
        with patch.object(self.engine.dpkg, 'list_broken_packages') as mock_broken, \
             patch.object(self.engine.apt, 'check_system_integrity') as mock_integrity, \
             patch.object(self.engine.mode_manager, 'get_mode_status') as mock_mode:
            
            mock_broken.return_value = []
            mock_integrity.return_value = True
            mock_mode.return_value = {
                'offline_mode': False,
                'network_available': True,
                'repositories_accessible': True,
                'pinned_packages_count': 2
            }
            
            # Check system health
            result = self.engine.check_system_health()
            
            assert result.success
            assert len(result.errors) == 0
            
            # Verify all components were checked
            mock_broken.assert_called_once()
            mock_integrity.assert_called_once()
            mock_mode.assert_called_once()
    
    def test_configuration_integration(self):
        """Test configuration integration across components."""
        # Test adding custom prefix
        self.engine.config.add_custom_prefix("newcompany-")
        
        # Verify it's recognized by classifier
        assert self.engine.classifier.is_custom_package("newcompany-test")
        
        # Test offline mode setting
        self.engine.config.set_offline_mode(True)
        
        # Verify mode manager respects the setting
        mode_status = self.engine.mode_manager.get_mode_status()
        assert mode_status['config_offline_setting']
    
    def test_concurrent_operations_safety(self):
        """Test that concurrent operations are handled safely."""
        import threading
        import time
        
        results = []
        errors = []
        
        def install_package(package_name):
            try:
                with patch.object(self.engine.apt, 'install_package') as mock_install:
                    mock_install.return_value = OperationResult(
                        success=True,
                        packages_affected=[Package(package_name, "1.0.0", PackageStatus.INSTALLED)],
                        warnings=[],
                        errors=[]
                    )
                    
                    # Simulate some processing time
                    time.sleep(0.1)
                    result = self.engine.install_package(package_name)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=install_package, args=[f"package-{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) == 5
        
        # Verify all operations succeeded
        for result in results:
            assert result.success


def run_integration_tests():
    """Run all integration tests."""
    print("Running integration tests...")
    
    test_class = TestPackageEngineIntegration()
    
    tests = [
        test_class.test_complete_install_workflow,
        test_class.test_complete_remove_workflow,
        test_class.test_offline_mode_integration,
        test_class.test_custom_package_recognition_integration,
        test_class.test_conflict_resolution_integration,
        test_class.test_error_recovery_integration,
        test_class.test_system_health_integration,
        test_class.test_configuration_integration,
        test_class.test_concurrent_operations_safety
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test_class.setup_method()
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    print(f"\nIntegration Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)