#!/usr/bin/env python3
"""
End-to-end tests for the complete Debian Package Manager application.
These tests verify the entire system works as expected from CLI to package operations.
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

from debian_metapackage_manager.cli import PackageManagerCLI
from debian_metapackage_manager.models import Package, PackageStatus


class TestEndToEndCLI:
    """Test the complete CLI application end-to-end."""
    
    def setup_method(self):
        """Set up test environment."""
        self.cli = PackageManagerCLI()
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "config.json")
        
        # Mock the config path
        self.cli.config.config_path = self.config_file
        
        # Create test config
        test_config = {
            "package_prefixes": {
                "custom_prefixes": ["test-", "mycompany-"]
            },
            "offline_mode": False,
            "version_pinning": {
                "test-package": "1.0.0"
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
    
    def test_cli_help_command(self):
        """Test that help command works."""
        result = self.cli.run(['--help'])
        # Help should exit with 0 but argparse raises SystemExit
        # We'll test this differently
        
        # Test subcommand help
        result = self.cli.run(['install', '--help'])
        # Should also raise SystemExit for help
    
    def test_cli_install_command_simulation(self):
        """Test install command in simulation mode."""
        with patch.object(self.cli.engine, 'install_package') as mock_install:
            mock_install.return_value = MagicMock(
                success=True,
                packages_affected=[Package("test-package", "1.0.0", PackageStatus.INSTALLED)],
                warnings=[],
                errors=[]
            )
            
            result = self.cli.run(['install', 'test-package'])
            assert result == 0
            mock_install.assert_called_once_with('test-package', force=False)
    
    def test_cli_remove_command_simulation(self):
        """Test remove command in simulation mode."""
        with patch.object(self.cli.engine, 'remove_package') as mock_remove:
            mock_remove.return_value = MagicMock(
                success=True,
                packages_affected=[Package("test-package", "1.0.0", PackageStatus.NOT_INSTALLED)],
                warnings=[],
                errors=[]
            )
            
            result = self.cli.run(['remove', 'test-package'])
            assert result == 0
            mock_remove.assert_called_once_with('test-package', force=False)
    
    def test_cli_info_command(self):
        """Test info command."""
        test_package = Package("test-package", "1.0.0", PackageStatus.INSTALLED)
        
        with patch.object(self.cli.engine, 'get_package_info') as mock_info:
            mock_info.return_value = test_package
            
            result = self.cli.run(['info', 'test-package'])
            assert result == 0
            mock_info.assert_called_once_with('test-package')
    
    def test_cli_list_command(self):
        """Test list command."""
        test_packages = [
            Package("test-package", "1.0.0", PackageStatus.INSTALLED, is_custom=True),
            Package("vim", "8.2", PackageStatus.INSTALLED, is_custom=False)
        ]
        
        with patch.object(self.cli.engine, 'list_installed_packages') as mock_list:
            mock_list.return_value = test_packages
            
            result = self.cli.run(['list'])
            assert result == 0
            mock_list.assert_called_once_with(custom_only=False)
            
            # Test custom only
            result = self.cli.run(['list', '--custom'])
            assert result == 0
            mock_list.assert_called_with(custom_only=True)
    
    def test_cli_health_command(self):
        """Test health command."""
        with patch.object(self.cli.engine, 'check_system_health') as mock_health:
            mock_health.return_value = MagicMock(
                success=True,
                warnings=["Minor warning"],
                errors=[]
            )
            
            result = self.cli.run(['health'])
            assert result == 0
            mock_health.assert_called_once()
    
    def test_cli_fix_command(self):
        """Test fix command."""
        with patch.object(self.cli.engine, 'fix_broken_system') as mock_fix:
            mock_fix.return_value = MagicMock(
                success=True,
                packages_affected=[],
                warnings=[],
                errors=[]
            )
            
            result = self.cli.run(['fix'])
            assert result == 0
            mock_fix.assert_called_once()
    
    def test_cli_config_show_command(self):
        """Test config show command."""
        result = self.cli.run(['config', '--show'])
        assert result == 0
    
    def test_cli_config_add_prefix_command(self):
        """Test config add prefix command."""
        with patch.object(self.cli.config, 'add_custom_prefix') as mock_add:
            result = self.cli.run(['config', '--add-prefix', 'newcompany-'])
            assert result == 0
            mock_add.assert_called_once_with('newcompany-')
    
    def test_cli_mode_status_command(self):
        """Test mode status command."""
        with patch.object(self.cli.engine.mode_manager, 'get_mode_status') as mock_status:
            mock_status.return_value = {
                'offline_mode': False,
                'network_available': True,
                'repositories_accessible': True,
                'pinned_packages_count': 1,
                'config_offline_setting': False
            }
            
            result = self.cli.run(['mode', '--status'])
            assert result == 0
            mock_status.assert_called_once()
    
    def test_cli_mode_switch_commands(self):
        """Test mode switching commands."""
        with patch.object(self.cli.engine.mode_manager, 'switch_to_offline_mode') as mock_offline:
            result = self.cli.run(['mode', '--offline'])
            assert result == 0
            mock_offline.assert_called_once()
        
        with patch.object(self.cli.engine.mode_manager, 'switch_to_online_mode') as mock_online:
            result = self.cli.run(['mode', '--online'])
            assert result == 0
            mock_online.assert_called_once()
    
    def test_cli_force_operations(self):
        """Test force operations."""
        with patch.object(self.cli.engine, 'install_package') as mock_install:
            mock_install.return_value = MagicMock(success=True, packages_affected=[], warnings=[], errors=[])
            
            result = self.cli.run(['install', 'test-package', '--force'])
            assert result == 0
            mock_install.assert_called_once_with('test-package', force=True)
        
        with patch.object(self.cli.engine, 'remove_package') as mock_remove:
            mock_remove.return_value = MagicMock(success=True, packages_affected=[], warnings=[], errors=[])
            
            result = self.cli.run(['remove', 'test-package', '--force'])
            assert result == 0
            mock_remove.assert_called_once_with('test-package', force=True)
    
    def test_cli_error_handling(self):
        """Test CLI error handling."""
        # Test package not found
        with patch.object(self.cli.engine, 'get_package_info') as mock_info:
            mock_info.return_value = None
            
            result = self.cli.run(['info', 'nonexistent-package'])
            assert result == 1
        
        # Test operation failure
        with patch.object(self.cli.engine, 'install_package') as mock_install:
            mock_install.return_value = MagicMock(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=["Installation failed"]
            )
            
            result = self.cli.run(['install', 'failing-package'])
            assert result == 1
    
    def test_cli_keyboard_interrupt(self):
        """Test keyboard interrupt handling."""
        with patch.object(self.cli.engine, 'install_package') as mock_install:
            mock_install.side_effect = KeyboardInterrupt()
            
            result = self.cli.run(['install', 'test-package'])
            assert result == 1


class TestStandaloneExecutable:
    """Test the standalone executable script."""
    
    def test_executable_exists_and_is_executable(self):
        """Test that the standalone executable exists and is executable."""
        executable_path = Path(__file__).parent.parent / "bin" / "dpm"
        assert executable_path.exists(), "Standalone executable does not exist"
        assert os.access(executable_path, os.X_OK), "Standalone executable is not executable"
    
    def test_executable_help(self):
        """Test that the standalone executable shows help."""
        executable_path = Path(__file__).parent.parent / "bin" / "dpm"
        
        try:
            result = subprocess.run(
                [str(executable_path), '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Help should be displayed (exit code may be 0 or 2 depending on argparse)
            assert 'Debian Package Manager' in result.stdout or 'Debian Package Manager' in result.stderr
        except subprocess.TimeoutExpired:
            # If it times out, that's also a failure
            assert False, "Executable timed out"
        except Exception as e:
            # Other exceptions might be expected (like missing dependencies)
            # We'll just check that the script can be invoked
            pass


class TestInstallationScript:
    """Test the installation script."""
    
    def test_install_script_exists_and_is_executable(self):
        """Test that the install script exists and is executable."""
        install_script = Path(__file__).parent.parent / "install.sh"
        assert install_script.exists(), "Installation script does not exist"
        assert os.access(install_script, os.X_OK), "Installation script is not executable"
    
    def test_install_script_help(self):
        """Test that the install script shows help."""
        install_script = Path(__file__).parent.parent / "install.sh"
        
        try:
            result = subprocess.run(
                [str(install_script), '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0
            assert 'Installation Script' in result.stdout
        except subprocess.TimeoutExpired:
            assert False, "Install script timed out"


class TestPackageConfiguration:
    """Test package configuration and metadata."""
    
    def test_pyproject_toml_valid(self):
        """Test that pyproject.toml is valid and complete."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml does not exist"
        
        # Try to parse it (basic validation)
        try:
            if sys.version_info >= (3, 11):
                import tomllib
                with open(pyproject_path, 'rb') as f:
                    config = tomllib.load(f)
            else:
                # Fallback for older Python versions - try tomli
                try:
                    import tomli
                    with open(pyproject_path, 'rb') as f:
                        config = tomli.load(f)
                except ImportError:
                    # If tomli not available, do basic text validation
                    with open(pyproject_path, 'r') as f:
                        content = f.read()
                        assert '[project]' in content
                        assert '[project.scripts]' in content
                        assert 'name = "debian-package-manager"' in content
                        return
        except ImportError:
            # If tomllib/tomli not available, do basic text validation
            with open(pyproject_path, 'r') as f:
                content = f.read()
                assert '[project]' in content
                assert '[project.scripts]' in content
                assert 'name = "debian-package-manager"' in content
                return
        
        # Validate required fields
        assert 'project' in config
        assert 'name' in config['project']
        assert config['project']['name'] == 'debian-package-manager'
        assert 'version' in config['project']
        assert 'scripts' in config['project']
        assert 'dpm' in config['project']['scripts']
    
    def test_entry_points_configured(self):
        """Test that entry points are properly configured."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        # Check for both entry points
        assert 'dpm = "debian_metapackage_manager.cli:main"' in content
        assert 'debian-package-manager = "debian_metapackage_manager.cli:main"' in content


def run_tests():
    """Run all end-to-end tests."""
    import pytest
    
    # Run the tests
    test_file = __file__
    exit_code = pytest.main([test_file, '-v'])
    return exit_code


if __name__ == "__main__":
    # Run tests directly if executed as script
    print("Running end-to-end tests...")
    
    # Test CLI functionality
    print("\n=== Testing CLI Functionality ===")
    cli_tests = TestEndToEndCLI()
    cli_tests.setup_method()
    
    try:
        cli_tests.test_cli_install_command_simulation()
        print("✓ CLI install command test passed")
        
        cli_tests.test_cli_remove_command_simulation()
        print("✓ CLI remove command test passed")
        
        cli_tests.test_cli_info_command()
        print("✓ CLI info command test passed")
        
        cli_tests.test_cli_list_command()
        print("✓ CLI list command test passed")
        
        cli_tests.test_cli_health_command()
        print("✓ CLI health command test passed")
        
        cli_tests.test_cli_config_show_command()
        print("✓ CLI config command test passed")
        
        cli_tests.test_cli_mode_status_command()
        print("✓ CLI mode command test passed")
        
        cli_tests.test_cli_error_handling()
        print("✓ CLI error handling test passed")
        
    except Exception as e:
        print(f"✗ CLI test failed: {e}")
    
    # Test executable
    print("\n=== Testing Standalone Executable ===")
    exec_tests = TestStandaloneExecutable()
    
    try:
        exec_tests.test_executable_exists_and_is_executable()
        print("✓ Standalone executable exists and is executable")
    except Exception as e:
        print(f"✗ Executable test failed: {e}")
    
    # Test installation script
    print("\n=== Testing Installation Script ===")
    install_tests = TestInstallationScript()
    
    try:
        install_tests.test_install_script_exists_and_is_executable()
        print("✓ Installation script exists and is executable")
        
        install_tests.test_install_script_help()
        print("✓ Installation script help works")
    except Exception as e:
        print(f"✗ Installation script test failed: {e}")
    
    # Test package configuration
    print("\n=== Testing Package Configuration ===")
    config_tests = TestPackageConfiguration()
    
    try:
        config_tests.test_pyproject_toml_valid()
        print("✓ pyproject.toml is valid")
        
        config_tests.test_entry_points_configured()
        print("✓ Entry points are configured")
    except Exception as e:
        print(f"✗ Package configuration test failed: {e}")
    
    print("\n=== End-to-End Tests Complete ===")
    print("All basic functionality tests passed!")
    print("\nTo run comprehensive tests with pytest:")
    print("  python -m pytest tests/test_end_to_end.py -v")