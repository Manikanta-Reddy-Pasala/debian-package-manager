"""Remove command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler

if TYPE_CHECKING:
    from ...engine import PackageEngine
    from ...remote import RemotePackageManager


class RemoveCommandHandler(CommandHandler):
    """Handler for remove command."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager'):
        """Initialize remove handler."""
        self.engine = engine
        self.remote_manager = remote_manager
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add remove command parser."""
        parser = subparsers.add_parser('remove', help='Remove a package or metapackage')
        parser.add_argument('package_name', help='Name of the package to remove')
        parser.add_argument('--force', action='store_true', 
                          help='Force removal even with dependencies - shows impact analysis and requires confirmation')
        parser.add_argument('--purge', action='store_true', 
                          help='Purge configuration files as well')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle remove command."""
        target = self.remote_manager.get_current_target()
        print(f"Removing package '{args.package_name}' from {target}")
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            return self._handle_remote_remove(args)
        else:
            return self._handle_local_remove(args)
    
    def _handle_local_remove(self, args: argparse.Namespace) -> int:
        """Handle local removal."""
        result = self.engine.remove_package(args.package_name, force=args.force)
        return 0 if result.success else 1
    
    def _handle_remote_remove(self, args: argparse.Namespace) -> int:
        """Handle remote removal."""
        kwargs = {
            'force': args.force,
            'purge': args.purge
        }
        result = self.remote_manager.execute_command('remove', args.package_name, **kwargs)
        return 0 if result.success else 1