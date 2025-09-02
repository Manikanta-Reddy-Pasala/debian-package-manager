"""Cleanup command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler

if TYPE_CHECKING:
    from ...core.managers import PackageEngine, RemotePackageManager, SystemCleanup


class CleanupCommandHandler(CommandHandler):
    """Handler for system cleanup command."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager', cleanup: 'SystemCleanup'):
        """Initialize cleanup command handler."""
        self.engine = engine
        self.remote_manager = remote_manager
        self.cleanup = cleanup
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add cleanup command parser."""
        parser = subparsers.add_parser('cleanup', help='System cleanup and maintenance')
        parser.add_argument('--apt-cache', action='store_true', 
                           help='Clean APT package cache')
        parser.add_argument('--offline-repos', action='store_true', 
                           help='Clean offline repository caches')
        parser.add_argument('--artifactory', action='store_true', 
                           help='Clean artifactory cache')
        parser.add_argument('--all', action='store_true', 
                           help='Perform comprehensive cleanup')
        parser.add_argument('--aggressive', action='store_true', 
                           help='Use aggressive cleanup methods')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle cleanup command."""
        target = self.remote_manager.get_current_target()
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            # Execute on remote system
            kwargs = {
                'all': args.all,
                'apt_cache': args.apt_cache,
                'offline_repos': args.offline_repos,
                'artifactory': args.artifactory,
                'aggressive': args.aggressive
            }
            result = self.remote_manager.execute_command('cleanup', '', **kwargs)
            self._display_operation_result(result)
            return 0 if result.success else 1
        else:
            # Execute locally
            if args.all:
                return self._handle_comprehensive_cleanup(target)
            elif args.apt_cache:
                return self._handle_apt_cache_cleanup(target, args.aggressive)
            elif args.offline_repos:
                return self._handle_offline_repos_cleanup(target)
            elif args.artifactory:
                return self._handle_artifactory_cleanup(target)
            else:
                self._show_cleanup_options(target)
                return 0
    
    def _handle_comprehensive_cleanup(self, target: str) -> int:
        """Handle comprehensive cleanup."""
        mode = 'offline' if self.engine.config.is_offline_mode() else 'online'
        result = self.cleanup.perform_system_maintenance(mode)
        
        print(f"🧹 System Maintenance Complete - {target}")
        print("=" * 40)
        
        if result.success:
            print("✅ Cleanup completed successfully")
            if result.details:
                space_freed = result.details.get('total_space_freed_mb', 0)
                operations = result.details.get('operations_performed', 0)
                print(f"💾 Space freed: {space_freed} MB")
                print(f"🔧 Operations performed: {operations}")
        else:
            print("❌ Some cleanup operations failed")
        
        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        if result.errors:
            print(f"\n❌ Errors ({len(result.errors)}):")
            for error in result.errors:
                print(f"  - {error}")
        
        return 0 if result.success else 1
    
    def _handle_apt_cache_cleanup(self, target: str, aggressive: bool) -> int:
        """Handle APT cache cleanup."""
        result = self.cleanup.clean_apt_cache(aggressive=aggressive)
        print(f"🧹 APT Cache Cleanup - {target}")
        if result.success:
            space_freed = result.details.get('space_freed_mb', 0) if result.details else 0
            print(f"✅ APT cache cleaned - {space_freed} MB freed")
        else:
            print("❌ Failed to clean APT cache")
            for error in result.errors:
                print(f"  - {error}")
        return 0 if result.success else 1
    
    def _handle_offline_repos_cleanup(self, target: str) -> int:
        """Handle offline repositories cleanup."""
        offline_repos = self.cleanup._discover_offline_repositories()
        result = self.cleanup.clean_offline_repositories(offline_repos)
        print(f"🧹 Offline Repository Cleanup - {target}")
        if result.success:
            cleaned = result.details.get('cleaned_paths', []) if result.details else []
            space_freed = result.details.get('space_freed_mb', 0) if result.details else 0
            print(f"✅ Cleaned {len(cleaned)} repositories - {space_freed} MB freed")
        else:
            print("❌ Failed to clean offline repositories")
            for error in result.errors:
                print(f"  - {error}")
        return 0 if result.success else 1
    
    def _handle_artifactory_cleanup(self, target: str) -> int:
        """Handle artifactory cleanup."""
        artifactory_config = self.cleanup._get_artifactory_config()
        if not artifactory_config:
            print(f"⚠️  No artifactory configuration found on {target}")
            return 1
        
        result = self.cleanup.clean_artifactory_cache(artifactory_config)
        print(f"🧹 Artifactory Cache Cleanup - {target}")
        if result.success:
            space_freed = result.details.get('space_freed_mb', 0) if result.details else 0
            print(f"✅ Artifactory cache cleaned - {space_freed} MB freed")
        else:
            print("❌ Failed to clean artifactory cache")
            for error in result.errors:
                print(f"  - {error}")
        return 0 if result.success else 1
    
    def _show_cleanup_options(self, target: str) -> None:
        """Show available cleanup options."""
        print(f"🧹 Available cleanup options for {target}:")
        print("  --apt-cache      Clean APT package cache")
        print("  --offline-repos  Clean offline repository caches")
        print("  --artifactory    Clean artifactory cache")
        print("  --all           Perform comprehensive cleanup")
        print("  --aggressive    Use aggressive cleanup methods")
    
    def _display_operation_result(self, result) -> None:
        """Display operation result."""
        if result.success:
            print("✅ Cleanup completed successfully")
            if result.details and 'stdout' in result.details:
                stdout = result.details['stdout'].strip()
                if stdout:
                    print(f"\n📄 Remote output:\n{stdout}")
        else:
            print("❌ Cleanup failed")
            for error in result.errors:
                print(f"  - {error}")