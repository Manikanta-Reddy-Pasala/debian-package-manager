"""Tests for CLI interface."""

import os
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.cli import PackageManagerCLI, main
from debian_metapackage_manager.models import Package, OperationResult, PackageStatus


def create_mock_engine():
    """Create a mock package engine."""
    mock_engine = Mock()
    
    # Mock successful operation result
    mock_result = OperationResult(
        success=True,
        packages_affected=[Package(name="test-pkg", version="1.0.0")],
        warnings=[],
        errors=[],
        user_confirmations_required=[]
    )
    
    mock_engine.install_package.return_value = mock_result
    mock_engine.remove_package.return_value = mock_result
    mock_engine.check_system_health.return_value = mock_result
    mock_engine.fix_broken_system.return_value = mock_result
    
    mock_engine.get_package_info.return_value = Package(
        name="test-pkg", 
        version="1.0.0",
        status=PackageStatus.INSTALLED
    )
    
    mock_engine.list_installed_packages.return_value = [
        Package(name="pkg1", version="1.0.0", is_custom=True),
        Package(name="pkg2", version="2.0.0", is_metapackage=True)
    ]
    
    # Mock sub-components
    mock_engine.config = Mock()
    mock_engine.config.config_path = "/test/config.json"
    mock_engine.config.is_offline_mode.return_value = False
    mock_engine.config.get_custom_prefixes.return_value = ["test-", "custom-"]
    mock_engine.config.version_pinning.get_all_pinned.return_value = {"pkg1": "1.0.0"}
    mock_engine.config.add_custom_prefix = Mock()
    mock_engine.config.set_offline_mode = Mock()
    mock_engine.config.package_prefixes.remove_prefix = Mock()
    
    mock_engine.mode_manager = Mock()
    mock_engine.mode_manager.switch_to_offline_mode = Mock()
    mock_engine.mode_manager.switch_to_online_mode = Mock()
    mock_engine.mode_manager.auto_detect_mode.return_value = "online (latest versions)"
    mock_engine.mode_manager.get_mode_status.return_value = {
        'offline_mode': False,
        'network_available': True,
        'repositories_accessible': True,
        'pinned_packages_count': 1,
        'config_offline_setting': False
    }
    
    mock_engine.conflict_handler = Mock()
    mock_engine.conflict_handler.display_operation_result = Mock()
    mock_engine.conflict_handler.display_package_info = Mock()
    
    mock_engine.apt = Mock()
    mock_engine.apt.get_dependencies.return_value = []
    
    mock_engine.dpkg = Mock()
    mock_engine.dpkg.list_broken_packages.return_value = []
    
    return mock_engine


def test_cli_creation():
    """Test CLI can be created."""
    with patch('debian_metapackage_manager.cli.PackageEngine'):
        cli = PackageManagerCLI()
        assert cli is not None


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('os.geteuid', return_value=0)  # Mock root user
def test_install_command(mock_geteuid, mock_engine_class):
    """Test install command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['install', 'test-package'])
    
    assert result == 0
    mock_engine.install_package.assert_called_once_with('test-package', force=False)


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('os.geteuid', return_value=0)
def test_install_command_with_force(mock_geteuid, mock_engine_class):
    """Test install command with force flag."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['install', 'test-package', '--force'])
    
    assert result == 0
    mock_engine.install_package.assert_called_once_with('test-package', force=True)


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('os.geteuid', return_value=0)
def test_install_command_with_offline(mock_geteuid, mock_engine_class):
    """Test install command with offline flag."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['install', 'test-package', '--offline'])
    
    assert result == 0
    mock_engine.mode_manager.switch_to_offline_mode.assert_called_once()
    mock_engine.install_package.assert_called_once_with('test-package', force=False)


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('os.geteuid', return_value=0)
def test_remove_command(mock_geteuid, mock_engine_class):
    """Test remove command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['remove', 'test-package'])
    
    assert result == 0
    mock_engine.remove_package.assert_called_once_with('test-package', force=False)


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('os.geteuid', return_value=0)
def test_remove_command_with_force(mock_geteuid, mock_engine_class):
    """Test remove command with force flag."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['remove', 'test-package', '--force'])
    
    assert result == 0
    mock_engine.remove_package.assert_called_once_with('test-package', force=True)


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_info_command(mock_stdout, mock_engine_class):
    """Test info command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['info', 'test-package'])
    
    assert result == 0
    mock_engine.get_package_info.assert_called_once_with('test-package')
    mock_engine.conflict_handler.display_package_info.assert_called_once()


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_info_command_not_found(mock_stdout, mock_engine_class):
    """Test info command for non-existent package."""
    mock_engine = create_mock_engine()
    mock_engine.get_package_info.return_value = None
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['info', 'nonexistent-package'])
    
    assert result == 1
    output = mock_stdout.getvalue()
    assert "not found" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_list_command(mock_stdout, mock_engine_class):
    """Test list command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['list'])
    
    assert result == 0
    mock_engine.list_installed_packages.assert_called_once_with(custom_only=False)
    output = mock_stdout.getvalue()
    assert "Installed packages" in output
    assert "pkg1" in output
    assert "pkg2" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_list_command_custom_only(mock_stdout, mock_engine_class):
    """Test list command with custom only flag."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['list', '--custom'])
    
    assert result == 0
    mock_engine.list_installed_packages.assert_called_once_with(custom_only=True)


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_list_command_broken(mock_stdout, mock_engine_class):
    """Test list command for broken packages."""
    mock_engine = create_mock_engine()
    mock_engine.dpkg.list_broken_packages.return_value = [
        Package(name="broken-pkg", version="1.0.0", status=PackageStatus.BROKEN)
    ]
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['list', '--broken'])
    
    assert result == 0
    output = mock_stdout.getvalue()
    assert "Broken packages" in output
    assert "broken-pkg" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_health_command(mock_stdout, mock_engine_class):
    """Test health command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['health'])
    
    assert result == 0
    mock_engine.check_system_health.assert_called_once()
    output = mock_stdout.getvalue()
    assert "System Health Check" in output
    assert "System is healthy" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_health_command_verbose(mock_stdout, mock_engine_class):
    """Test health command with verbose flag."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['health', '--verbose'])
    
    assert result == 0
    output = mock_stdout.getvalue()
    assert "Mode Status" in output
    assert "Network Available" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
def test_fix_command(mock_engine_class):
    """Test fix command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['fix'])
    
    assert result == 0
    mock_engine.fix_broken_system.assert_called_once()


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_config_show(mock_stdout, mock_engine_class):
    """Test config show command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['config', '--show'])
    
    assert result == 0
    output = mock_stdout.getvalue()
    assert "Configuration:" in output
    assert "Custom Prefixes" in output
    assert "test-" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_config_add_prefix(mock_stdout, mock_engine_class):
    """Test config add prefix command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['config', '--add-prefix', 'newcompany-'])
    
    assert result == 0
    mock_engine.config.add_custom_prefix.assert_called_once_with('newcompany-')
    output = mock_stdout.getvalue()
    assert "Added custom prefix" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_config_set_offline(mock_stdout, mock_engine_class):
    """Test config set offline command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['config', '--set-offline'])
    
    assert result == 0
    mock_engine.config.set_offline_mode.assert_called_once_with(True)
    output = mock_stdout.getvalue()
    assert "Enabled offline mode" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_mode_status(mock_stdout, mock_engine_class):
    """Test mode status command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['mode', '--status'])
    
    assert result == 0
    output = mock_stdout.getvalue()
    assert "Mode Status:" in output
    assert "Current Mode:" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
def test_mode_offline(mock_engine_class):
    """Test mode offline command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['mode', '--offline'])
    
    assert result == 0
    mock_engine.mode_manager.switch_to_offline_mode.assert_called_once()


@patch('debian_metapackage_manager.cli.PackageEngine')
def test_mode_online(mock_engine_class):
    """Test mode online command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['mode', '--online'])
    
    assert result == 0
    mock_engine.mode_manager.switch_to_online_mode.assert_called_once()


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_mode_auto(mock_stdout, mock_engine_class):
    """Test mode auto command."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['mode', '--auto'])
    
    assert result == 0
    mock_engine.mode_manager.auto_detect_mode.assert_called_once()
    output = mock_stdout.getvalue()
    assert "Auto-detected mode" in output


@patch('debian_metapackage_manager.cli.PackageEngine')
@patch('sys.stdout', new_callable=StringIO)
def test_no_command_shows_help(mock_stdout, mock_engine_class):
    """Test that no command shows help."""
    mock_engine = create_mock_engine()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run([])
    
    assert result == 1


@patch('debian_metapackage_manager.cli.PackageEngine')
def test_keyboard_interrupt_handling(mock_engine_class):
    """Test keyboard interrupt handling."""
    mock_engine = create_mock_engine()
    mock_engine.install_package.side_effect = KeyboardInterrupt()
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['install', 'test-package'])
    
    assert result == 1


@patch('debian_metapackage_manager.cli.PackageEngine')
def test_exception_handling(mock_engine_class):
    """Test general exception handling."""
    mock_engine = create_mock_engine()
    mock_engine.install_package.side_effect = Exception("Test error")
    mock_engine_class.return_value = mock_engine
    
    cli = PackageManagerCLI()
    result = cli.run(['install', 'test-package'])
    
    assert result == 1


@patch('debian_metapackage_manager.cli.PackageManagerCLI')
def test_main_function(mock_cli_class):
    """Test main function."""
    mock_cli = Mock()
    mock_cli.run.return_value = 0
    mock_cli_class.return_value = mock_cli
    
    result = main()
    
    assert result == 0
    mock_cli.run.assert_called_once()


if __name__ == "__main__":
    test_cli_creation()
    test_install_command()
    test_install_command_with_force()
    test_install_command_with_offline()
    test_remove_command()
    test_remove_command_with_force()
    test_info_command()
    test_info_command_not_found()
    test_list_command()
    test_list_command_custom_only()
    test_list_command_broken()
    test_health_command()
    test_health_command_verbose()
    test_fix_command()
    test_config_show()
    test_config_add_prefix()
    test_config_set_offline()
    test_mode_status()
    test_mode_offline()
    test_mode_online()
    test_mode_auto()
    test_no_command_shows_help()
    test_keyboard_interrupt_handling()
    test_exception_handling()
    test_main_function()
    print("All CLI tests passed!")