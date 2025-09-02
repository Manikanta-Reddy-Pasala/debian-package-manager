"""Info command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler

if TYPE_CHECKING:
    from ...core.managers import PackageEngine, RemotePackageManager


class InfoCommandHandler(CommandHandler):
    """Handler for package info command."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager'):
        """Initialize info command handler."""
        self.engine = engine
        self.remote_manager = remote_manager
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add info command parser."""
        parser = subparsers.add_parser('info', help='Show information about a package')
        parser.add_argument('package_name', help='Name of the package to show info for')
        parser.add_argument('--dependencies', action='store_true', 
                           help='Show dependency information')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle info command."""
        target = self.remote_manager.get_current_target()
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            # Execute on remote system
            result = self.remote_manager.execute_command('info', args.package_name)
            self._display_operation_result(result)
            return 0 if result.success else 1
        else:
            # Execute locally
            package_info = self.engine.get_package_info(args.package_name)
            
            if not package_info:
                print(f"Package '{args.package_name}' not found on {target}.")
                return 1
            
            dependencies = []
            if args.dependencies:
                dependencies = self.engine.apt.get_dependencies(args.package_name)
            
            self.engine.conflict_handler.display_package_info(package_info, dependencies)
            return 0
    
    def _display_operation_result(self, result) -> None:
        """Display operation result."""
        if result.success:
            print("✅ Operation completed successfully")
            if result.details and 'stdout' in result.details:
                stdout = result.details['stdout'].strip()
                if stdout:
                    print(f"\n📄 Remote output:\n{stdout}")
        else:
            print("❌ Operation failed")
            for error in result.errors:
                print(f"  - {error}")