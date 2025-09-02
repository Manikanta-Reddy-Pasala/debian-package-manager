"""Install command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler, ValidationError

if TYPE_CHECKING:
    from ...engine import PackageEngine
    from ...remote import RemotePackageManager


class InstallCommandHandler(CommandHandler):
    """Handler for install command."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager'):
        """Initialize install handler."""
        self.engine = engine
        self.remote_manager = remote_manager
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add install command parser."""
        parser = subparsers.add_parser('install', help='Install a package or metapackage')
        parser.add_argument('package_name', help='Name of the package to install')
        parser.add_argument('--force', action='store_true', 
                           help='Force installation even with conflicts')
        parser.add_argument('--offline', action='store_true', 
                           help='Use offline mode with pinned versions')
        parser.add_argument('--online', action='store_true', 
                           help='Use online mode with latest versions')
        parser.add_argument('--version', help='Specific version to install')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle install command."""
        # Validate arguments
        if args.offline and args.online:
            raise ValidationError("Cannot specify both --offline and --online modes")
        
        target = self.remote_manager.get_current_target()
        print(f"Installing package '{args.package_name}' on {target}")
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            return self._handle_remote_install(args)
        else:
            return self._handle_local_install(args)
    
    def _handle_local_install(self, args: argparse.Namespace) -> int:
        """Handle local installation."""
        # Set mode if specified
        if args.offline:
            print("Switching to offline mode for this operation")
            self.engine.mode_manager.switch_to_offline_mode()
        elif args.online:
            print("Switching to online mode for this operation")
            self.engine.mode_manager.switch_to_online_mode()
        
        result = self.engine.install_package(args.package_name, force=args.force)
        return 0 if result.success else 1
    
    def _handle_remote_install(self, args: argparse.Namespace) -> int:
        """Handle remote installation."""
        kwargs = {
            'force': args.force,
            'offline': args.offline,
            'online': args.online,
            'version': args.version
        }
        result = self.remote_manager.execute_command('install', args.package_name, **kwargs)
        return 0 if result.success else 1