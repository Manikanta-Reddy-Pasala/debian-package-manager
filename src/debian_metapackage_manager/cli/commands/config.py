"""Config command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler

if TYPE_CHECKING:
    from ...core.managers import PackageEngine, RemotePackageManager


class ConfigCommandHandler(CommandHandler):
    """Handler for configuration management command."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager'):
        """Initialize config command handler."""
        self.engine = engine
        self.remote_manager = remote_manager
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add config command parser."""
        parser = subparsers.add_parser('config', help='Manage configuration')
        parser.add_argument('--show', action='store_true', 
                           help='Show current configuration')
        parser.add_argument('--add-prefix', help='Add a custom package prefix')
        parser.add_argument('--remove-prefix', help='Remove a custom package prefix')
        parser.add_argument('--add-removable', help='Add a package to removable packages list')
        parser.add_argument('--remove-removable', help='Remove a package from removable packages list')
        parser.add_argument('--list-removable', action='store_true', 
                           help='List all removable packages')
        parser.add_argument('--set-offline', action='store_true', 
                           help='Enable offline mode')
        parser.add_argument('--set-online', action='store_true', 
                           help='Enable online mode')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle config command."""
        target = self.remote_manager.get_current_target()
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            # Execute on remote system
            kwargs = {
                'show': args.show,
                'add_prefix': args.add_prefix,
                'remove_prefix': args.remove_prefix,
                'add_removable': args.add_removable,
                'remove_removable': args.remove_removable,
                'list_removable': args.list_removable,
                'set_offline': args.set_offline,
                'set_online': args.set_online
            }
            result = self.remote_manager.execute_command('config', '', **kwargs)
            self._display_operation_result(result)
            return 0 if result.success else 1
        else:
            # Execute locally
            if args.show:
                self._show_config()
            elif args.add_prefix:
                self.engine.config.add_custom_prefix(args.add_prefix)
                self.engine.config.save_config()
                print(f"✅ Added custom prefix on {target}: {args.add_prefix}")
                print(f"   Packages starting with '{args.add_prefix}' will now be treated as custom packages.")
            elif args.remove_prefix:
                self.engine.config.remove_custom_prefix(args.remove_prefix)
                print(f"✅ Removed custom prefix from {target}: {args.remove_prefix}")
            elif args.add_removable:
                try:
                    self.engine.config.add_removable_package(args.add_removable)
                    print(f"✅ Added removable package on {target}: {args.add_removable}")
                    print(f"   This package can now be removed during conflict resolution.")
                except ValueError as e:
                    print(f"❌ Error: {e}")
                    return 1
            elif args.remove_removable:
                self.engine.config.remove_removable_package(args.remove_removable)
                print(f"✅ Removed removable package from {target}: {args.remove_removable}")
            elif args.list_removable:
                removable = self.engine.config.get_removable_packages()
                print(f"📦 Removable Packages on {target} ({len(removable)}):")
                if removable:
                    for package in removable:
                        print(f"  - {package}")
                else:
                    print("  (none configured)")
            elif args.set_offline:
                self.engine.config.set_offline_mode(True)
                print(f"✅ Enabled offline mode on {target}")
            elif args.set_online:
                self.engine.config.set_offline_mode(False)
                print(f"✅ Enabled online mode on {target}")
            else:
                self._show_config()
            
            return 0
    
    def _show_config(self) -> None:
        """Show current configuration."""
        config = self.engine.config
        target = self.remote_manager.get_current_target()
        
        print(f"Configuration - {target}")
        print("=" * 40)
        print(f"Offline Mode: {config.is_offline_mode()}")
        print(f"Custom Prefixes: {', '.join(config.get_custom_prefixes()) or 'None'}")
        print(f"Removable Packages: {len(config.get_removable_packages())}")
        
        # Show additional config details
        if hasattr(config, 'get_config_path'):
            print(f"Config File: {config.get_config_path()}")
    
    def _display_operation_result(self, result) -> None:
        """Display operation result."""
        if result.success:
            if result.details and 'stdout' in result.details:
                stdout = result.details['stdout'].strip()
                if stdout:
                    print(stdout)
        else:
            print("❌ Configuration operation failed")
            for error in result.errors:
                print(f"  - {error}")