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
        parser.add_argument('--version', help='Specific version to install')
        parser.add_argument('--force', action='store_true', 
                           help='Force installation even with conflicts - shows impact analysis and requires confirmation')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle install command."""
        target = self.remote_manager.get_current_target()
        print(f"Installing package '{args.package_name}' on {target}")
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            return self._handle_remote_install(args)
        else:
            return self._handle_local_install(args)
    
    def _handle_local_install(self, args: argparse.Namespace) -> int:
        """Handle local installation."""
        result = self.engine.install_package(
            args.package_name, 
            force=args.force,
            version=args.version
        )
        return 0 if result.success else 1
    
    def _handle_remote_install(self, args: argparse.Namespace) -> int:
        """Handle remote installation."""
        kwargs = {
            'force': args.force,
            'version': args.version
        }
        result = self.remote_manager.execute_command('install', args.package_name, **kwargs)
        return 0 if result.success else 1