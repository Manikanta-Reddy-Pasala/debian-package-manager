"""Tests for CLI command handlers."""

import pytest
import argparse
from unittest.mock import Mock, patch

from debian_metapackage_manager.cli.commands import (
    InstallCommandHandler, RemoveCommandHandler, ModeCommandHandler,
    InfoCommandHandler, HealthCommandHandler, ConfigCommandHandler
)
from debian_metapackage_manager.cli.base import CommandHandler, CLIBase
from debian_metapackage_manager.models import OperationResult, Package, PackageStatus


class TestInstallCommandHandler:
    """Test suite for InstallCommandHandler."""

    def test_install_handler_initialization(self):
        """Test InstallCommandHandler initialization."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        
        handler = InstallCommandHandler(mock_engine, mock_remote_manager)
        
        assert handler.engine == mock_engine
        assert handler.remote_manager == mock_remote_manager

    def test_install_handler_add_parser(self):
        """Test adding install command parser."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = InstallCommandHandler(mock_engine, mock_remote_manager)
        
        subparsers = Mock()
        mock_parser = Mock()
        subparsers.add_parser.return_value = mock_parser
        
        result = handler.add_parser(subparsers)
        
        subparsers.add_parser.assert_called_with('install', help='Install a package or metapackage')
        assert result == mock_parser

    def test_install_handler_handle_success(self):
        """Test successful package installation."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = InstallCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        
        success_result = OperationResult(
            success=True, packages_affected=[Package('test-pkg', '1.0.0')],
            warnings=[], errors=[], user_confirmations_required=[]
        )
        mock_engine.install_package.return_value = success_result
        
        # Create mock args
        args = Mock()
        args.package_name = 'test-pkg'
        args.force = False
        args.offline = False
        args.online = False
        args.version = None
        
        with patch('builtins.print'):
            result = handler.handle(args)
            
            assert result == 0
            mock_engine.install_package.assert_called_once()

    def test_install_handler_validation_error(self):
        """Test install handler with validation error."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = InstallCommandHandler(mock_engine, mock_remote_manager)
        
        # Create args with conflicting options
        args = Mock()
        args.package_name = 'test-pkg'
        args.offline = True
        args.online = True
        args.force = False
        args.version = None
        
        from debian_metapackage_manager.cli.base import ValidationError
        
        with pytest.raises(ValidationError):
            handler.handle(args)


class TestRemoveCommandHandler:
    """Test suite for RemoveCommandHandler."""

    def test_remove_handler_initialization(self):
        """Test RemoveCommandHandler initialization."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        
        handler = RemoveCommandHandler(mock_engine, mock_remote_manager)
        
        assert handler.engine == mock_engine
        assert handler.remote_manager == mock_remote_manager

    def test_remove_handler_handle_success(self):
        """Test successful package removal."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = RemoveCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        
        success_result = OperationResult(
            success=True, packages_affected=[Package('test-pkg', '1.0.0')],
            warnings=[], errors=[], user_confirmations_required=[]
        )
        mock_engine.remove_package.return_value = success_result
        
        # Create mock args
        args = Mock()
        args.package_name = 'test-pkg'
        args.force = False
        args.purge = False
        
        with patch('builtins.print'):
            result = handler.handle(args)
            
            assert result == 0


class TestModeCommandHandler:
    """Test suite for ModeCommandHandler."""

    def test_mode_handler_initialization(self):
        """Test ModeCommandHandler initialization."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        
        handler = ModeCommandHandler(mock_engine, mock_remote_manager)
        
        assert handler.engine == mock_engine
        assert handler.remote_manager == mock_remote_manager

    def test_mode_handler_switch_to_offline(self):
        """Test switching to offline mode."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = ModeCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        mock_engine.mode_manager.switch_to_offline_mode.return_value = None
        
        # Create mock args
        args = Mock()
        args.status = False
        args.offline = True
        args.online = False
        args.auto = False
        
        with patch('builtins.print'):
            result = handler.handle(args)
            
            assert result == 0
            mock_engine.mode_manager.switch_to_offline_mode.assert_called_once()

    def test_mode_handler_status_short_and_long_options(self):
        """Test that both -s and --status options work for mode status."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = ModeCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        
        # Mock ModeStatus object
        from debian_metapackage_manager.core.mode_manager import ModeStatus
        mock_status = ModeStatus(
            offline_mode=True,
            network_available=True,
            repositories_accessible=False,
            pinned_packages_count=0,
            config_offline_setting=True
        )
        mock_engine.mode_manager.get_mode_status.return_value = mock_status
        
        # Test short option (-s)
        args = Mock()
        args.status = True
        args.offline = False
        args.online = False
        args.auto = False
        
        with patch('builtins.print') as mock_print:
            result = handler.handle(args)
            
            assert result == 0
            mock_engine.mode_manager.get_mode_status.assert_called()
            # Check that status information was printed
            assert any('Mode Status - local system:' in str(call) for call in mock_print.call_args_list)

    def test_mode_handler_parser_supports_short_options(self):
        """Test that mode parser supports both short and long options."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = ModeCommandHandler(mock_engine, mock_remote_manager)
        
        # Create a mock subparsers
        import argparse
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers()
        
        # Add the mode parser
        mode_parser = handler.add_parser(subparsers)
        
        # Test that both short and long options parse correctly
        # Short options
        args_short = mode_parser.parse_args(['-s', '-a'])
        assert args_short.status is True
        assert args_short.auto is True
        
        # Long options  
        args_long = mode_parser.parse_args(['--status', '--auto'])
        assert args_long.status is True
        assert args_long.auto is True


class TestInfoCommandHandler:
    """Test suite for InfoCommandHandler."""

    def test_info_handler_package_found(self):
        """Test info handler when package is found."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = InfoCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        
        package_info = Package(
            name='test-pkg', version='1.0.0', is_custom=True,
            status=PackageStatus.INSTALLED
        )
        mock_engine.get_package_info.return_value = package_info
        
        # Create mock args
        args = Mock()
        args.package_name = 'test-pkg'
        args.dependencies = False
        
        with patch('builtins.print'):
            result = handler.handle(args)
            
            assert result == 0

    def test_info_handler_package_not_found(self):
        """Test info handler when package is not found."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = InfoCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        mock_engine.get_package_info.return_value = None
        
        # Create mock args
        args = Mock()
        args.package_name = 'nonexistent-pkg'
        args.dependencies = False
        
        with patch('builtins.print'):
            result = handler.handle(args)
            
            assert result == 1


class TestHealthCommandHandler:
    """Test suite for HealthCommandHandler."""

    def test_health_handler_healthy_system(self):
        """Test health check on healthy system."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = HealthCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        
        health_result = OperationResult(
            success=True, packages_affected=[], warnings=[], errors=[],
            user_confirmations_required=[]
        )
        mock_engine.check_system_health.return_value = health_result
        
        # Create mock args
        args = Mock()
        args.verbose = False
        
        with patch('builtins.print'):
            result = handler.handle(args)
            
            assert result == 0

    def test_health_handler_unhealthy_system(self):
        """Test health check on unhealthy system."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = HealthCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        
        health_result = OperationResult(
            success=False, packages_affected=[], warnings=[],
            errors=['Broken packages found'], user_confirmations_required=[]
        )
        mock_engine.check_system_health.return_value = health_result
        
        # Create mock args
        args = Mock()
        args.verbose = False
        
        with patch('builtins.print'):
            result = handler.handle(args)
            
            assert result == 1


class TestConfigCommandHandler:
    """Test suite for ConfigCommandHandler."""

    def test_config_handler_show_config(self):
        """Test showing configuration."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = ConfigCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        
        # Create mock args
        args = Mock()
        args.show = True
        args.add_prefix = None
        args.remove_prefix = None
        args.add_removable = None
        args.remove_removable = None
        args.list_removable = False
        args.set_offline = False
        args.set_online = False
        
        with patch('builtins.print'):
            with patch.object(handler, '_show_config') as mock_show:
                result = handler.handle(args)
                
                assert result == 0
                mock_show.assert_called_once()

    def test_config_handler_add_prefix(self):
        """Test adding custom prefix."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = ConfigCommandHandler(mock_engine, mock_remote_manager)
        
        # Setup mocks
        mock_remote_manager.get_current_target.return_value = "local system"
        mock_remote_manager.is_remote_connected.return_value = False
        
        # Create mock args
        args = Mock()
        args.show = False
        args.add_prefix = 'new-prefix-'
        args.remove_prefix = None
        args.add_removable = None
        args.remove_removable = None
        args.list_removable = False
        args.set_offline = False
        args.set_online = False
        
        with patch('builtins.print'):
            result = handler.handle(args)
            
            assert result == 0
            mock_engine.config.add_custom_prefix.assert_called_with('new-prefix-')


class TestCLIBase:
    """Test suite for CLIBase class."""

    def test_cli_base_initialization(self):
        """Test CLIBase initialization."""
        cli = CLIBase()
        
        assert cli.handlers == {}

    def test_cli_base_register_handler(self):
        """Test registering command handler."""
        cli = CLIBase()
        mock_handler = Mock(spec=CommandHandler)
        
        cli.register_handler('test', mock_handler)
        
        assert 'test' in cli.handlers
        assert cli.handlers['test'] == mock_handler

    def test_cli_base_create_parser(self):
        """Test creating argument parser."""
        cli = CLIBase()
        mock_handler = Mock(spec=CommandHandler)
        cli.register_handler('test', mock_handler)
        
        parser = cli.create_parser()
        
        assert parser is not None
        mock_handler.add_parser.assert_called()


class TestCLIIntegration:
    """Integration tests for CLI components."""

    def test_complete_cli_workflow(self):
        """Test complete CLI workflow."""
        from debian_metapackage_manager.cli.main import PackageManagerCLI
        
        with patch('debian_metapackage_manager.core.managers.PackageEngine') as mock_engine_class:
            with patch('debian_metapackage_manager.core.managers.RemotePackageManager') as mock_remote_class:
                with patch('debian_metapackage_manager.core.managers.SystemCleanup') as mock_cleanup_class:
                    # Setup mocks
                    mock_engine = Mock()
                    mock_remote = Mock()
                    mock_cleanup = Mock()
                    
                    mock_engine_class.return_value = mock_engine
                    mock_remote_class.return_value = mock_remote
                    mock_cleanup_class.return_value = mock_cleanup
                    
                    # Create CLI
                    cli = PackageManagerCLI()
                    
                    # Test that handlers are registered
                    expected_commands = ['install', 'remove', 'mode', 'info', 'health', 'config']
                    
                    for command in expected_commands:
                        assert command in cli.handlers

    def test_cli_argument_parsing(self):
        """Test CLI argument parsing."""
        from debian_metapackage_manager.cli.main import PackageManagerCLI
        
        with patch('debian_metapackage_manager.core.managers.PackageEngine'):
            with patch('debian_metapackage_manager.core.managers.RemotePackageManager'):
                with patch('debian_metapackage_manager.core.managers.SystemCleanup'):
                    cli = PackageManagerCLI()
                    parser = cli.create_parser()
                    
                    # Test parsing install command
                    args = parser.parse_args(['install', 'test-package'])
                    assert args.command == 'install'
                    assert hasattr(args, 'package_name')


class TestCLIEdgeCases:
    """Test edge cases and error conditions."""

    def test_handler_with_none_args(self):
        """Test handlers with None arguments."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = InstallCommandHandler(mock_engine, mock_remote_manager)
        
        # Should handle gracefully
        with pytest.raises(AttributeError):
            handler.handle(None)

    def test_handler_with_missing_attributes(self):
        """Test handlers with args missing required attributes."""
        mock_engine = Mock()
        mock_remote_manager = Mock()
        handler = InstallCommandHandler(mock_engine, mock_remote_manager)
        
        args = Mock()
        args.package_name = 'test-pkg'
        args.force = False
        args.offline = False
        args.online = False
        args.version = None
        # Remove the package_name to test missing attribute
        delattr(args, 'package_name')
        
        with pytest.raises(AttributeError):
            handler.handle(args)

    def test_cli_base_with_invalid_handler(self):
        """Test CLIBase with invalid handler."""
        cli = CLIBase()
        
        # Register non-CommandHandler object
        invalid_handler = "not a handler"
        cli.register_handler('invalid', invalid_handler)
        
        # Should handle gracefully when creating parser
        with pytest.raises(AttributeError):
            cli.create_parser()