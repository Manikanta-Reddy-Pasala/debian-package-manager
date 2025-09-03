"""Fix command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler

if TYPE_CHECKING:
    from ...core.managers import PackageEngine, RemotePackageManager


class FixCommandHandler(CommandHandler):
    """Handler for system fix command."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager'):
        """Initialize fix command handler."""
        self.engine = engine
        self.remote_manager = remote_manager
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add fix command parser."""
        parser = subparsers.add_parser('fix', help='Fix broken package system')
        parser.add_argument('--force', action='store_true', 
                           help='Use aggressive fixing methods')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle fix command."""
        target = self.remote_manager.get_current_target()
        print(f"Fixing broken packages on {target}")
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            # Execute on remote system
            kwargs = {'force': args.force}
            result = self.remote_manager.execute_command('fix', '', **kwargs)
        else:
            # Execute locally
            result = self.engine.fix_broken_system()
        
        self._display_operation_result(result)
        return 0 if result.success else 1
    
    def _display_operation_result(self, result) -> None:
        """Display operation result."""
        if result.success:
            print("System fixed successfully")
            if result.packages_affected:
                print(f"Packages affected: {len(result.packages_affected)}")
                for pkg in result.packages_affected[:5]:
                    print(f"  - {pkg.name}")
        else:
            print("Failed to fix system")
        
        if result.warnings:
            print(f"Warnings: {len(result.warnings)}")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        if result.errors:
            print(f"Errors: {len(result.errors)}")
            for error in result.errors:
                print(f"  - {error}")
        
        # Show remote output if available
        if result.details and 'stdout' in result.details:
            stdout = result.details['stdout'].strip()
            if stdout:
                print(f"\nRemote output:\n{stdout}")