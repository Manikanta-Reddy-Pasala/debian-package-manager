"""List command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler

if TYPE_CHECKING:
    from ...core.managers import PackageEngine, RemotePackageManager


class ListCommandHandler(CommandHandler):
    """Handler for package list command."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager'):
        """Initialize list command handler."""
        self.engine = engine
        self.remote_manager = remote_manager
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add list command parser."""
        parser = subparsers.add_parser('list', help='List installed packages')
        parser.add_argument('--custom', action='store_true', 
                           help='Show only custom packages')
        parser.add_argument('--metapackages', action='store_true', 
                           help='Show only metapackages')
        parser.add_argument('--broken', action='store_true', 
                           help='Show only broken packages')
        parser.add_argument('--table', action='store_true', default=True,
                           help='Display output in table format (default)')
        parser.add_argument('--simple', action='store_true',
                           help='Display output in simple list format')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle list command."""
        target = self.remote_manager.get_current_target()
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            # Execute on remote system
            kwargs = {
                'custom': args.custom,
                'broken': args.broken,
                'metapackages': args.metapackages
            }
            result = self.remote_manager.execute_command('list', '', **kwargs)
            self._display_operation_result(result)
            return 0 if result.success else 1
        else:
            # Execute locally
            if args.broken:
                packages = self.engine.dpkg.list_broken_packages()
                print(f"Broken packages on {target} ({len(packages)}):")
            else:
                packages = self.engine.list_installed_packages(custom_only=args.custom)
                
                if args.metapackages:
                    packages = [pkg for pkg in packages if pkg.is_metapackage]
                
                print(f"Installed packages on {target} ({len(packages)}):")
            
            if not packages:
                print("  No packages found.")
                return 0
            
            for package in packages:
                status_icon = "✓" if package.status.value == "installed" else "✗"
                pkg_type = ""
                
                if package.is_metapackage:
                    pkg_type = " [META]"
                elif package.is_custom:
                    pkg_type = " [CUSTOM]"
                
                print(f"  {status_icon} {package.name} (v{package.version}){pkg_type}")
            
            return 0
    
    def _display_operation_result(self, result) -> None:
        """Display operation result."""
        if result.success:
            if result.details and 'stdout' in result.details:
                stdout = result.details['stdout'].strip()
                if stdout:
                    print(stdout)
        else:
            print("❌ Operation failed")
            for error in result.errors:
                print(f"  - {error}")