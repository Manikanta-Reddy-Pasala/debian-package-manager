"""Health command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler

if TYPE_CHECKING:
    from ...core.managers import PackageEngine, RemotePackageManager


class HealthCommandHandler(CommandHandler):
    """Handler for system health check command."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager'):
        """Initialize health command handler."""
        self.engine = engine
        self.remote_manager = remote_manager
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add health command parser."""
        parser = subparsers.add_parser('health', help='Check system package health')
        parser.add_argument('--verbose', action='store_true', 
                           help='Show detailed health information')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle health command."""
        target = self.remote_manager.get_current_target()
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            # Execute on remote system
            result = self.remote_manager.execute_command('health')
            self._display_operation_result(result)
            return 0 if result.success else 1
        else:
            # Execute locally
            result = self.engine.check_system_health()
            
            print(f"System Health Check - {target}")
            print("=" * 40)
            
            if result.success:
                print("✅ System is healthy")
            else:
                print("❌ System has issues")
            
            if result.warnings:
                print(f"\n⚠️  Warnings ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"  - {warning}")
            
            if result.errors:
                print(f"\n❌ Errors ({len(result.errors)}):")
                for error in result.errors:
                    print(f"  - {error}")
            
            if args.verbose:
                # Show mode status
                mode_status = self.engine.mode_manager.get_mode_status()
                print(f"\nMode Status:")
                print(f"  Offline Mode: {mode_status.offline_mode}")
                print(f"  Network Available: {mode_status.network_available}")
                print(f"  Repositories Accessible: {mode_status.repositories_accessible}")
                print(f"  Pinned Packages: {mode_status.pinned_packages_count}")
            
            return 0 if result.success else 1
    
    def _display_operation_result(self, result) -> None:
        """Display operation result."""
        if result.success:
            print("✅ System is healthy")
            if result.details and 'stdout' in result.details:
                stdout = result.details['stdout'].strip()
                if stdout:
                    print(f"\n📄 Remote output:\n{stdout}")
        else:
            print("❌ System has issues")
            for error in result.errors:
                print(f"  - {error}")