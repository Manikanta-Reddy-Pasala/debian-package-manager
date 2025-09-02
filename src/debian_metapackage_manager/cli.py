"""Command-line interface for Debian Metapackage Manager."""

import argparse
import sys
import os
from typing import Optional

from .engine import PackageEngine
from .config import Config
from .conflict_handler import UserPrompt
from .cleanup import SystemCleanup
from .remote import RemotePackageManager
from .interfaces import OperationResult


class PackageManagerCLI:
    """Main CLI interface for the package manager."""
    
    def __init__(self):
        """Initialize CLI with package engine."""
        self.engine = PackageEngine()
        self.config = self.engine.config
        self.cleanup = SystemCleanup()
        self.remote_manager = RemotePackageManager()
    
    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI with given arguments."""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        # Check for root privileges if needed
        if parsed_args.command in ['install', 'remove'] and os.geteuid() != 0:
            print("Warning: This operation typically requires root privileges.")
            print("You may need to run with 'sudo' for actual package operations.")
        
        try:
            if parsed_args.command == 'install':
                return self._handle_install(parsed_args)
            elif parsed_args.command == 'remove':
                return self._handle_remove(parsed_args)
            elif parsed_args.command == 'info':
                return self._handle_info(parsed_args)
            elif parsed_args.command == 'list':
                return self._handle_list(parsed_args)
            elif parsed_args.command == 'health':
                return self._handle_health(parsed_args)
            elif parsed_args.command == 'fix':
                return self._handle_fix(parsed_args)
            elif parsed_args.command == 'config':
                return self._handle_config(parsed_args)
            elif parsed_args.command == 'mode':
                return self._handle_mode(parsed_args)
            elif parsed_args.command == 'cleanup':
                return self._handle_cleanup(parsed_args)
            elif parsed_args.command == 'connect':
                return self._handle_connect(parsed_args)
            
            return 0
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="Debian Package Manager - Intelligent package management for custom package systems",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Local operations
  dpm install mycompany-dev-tools          # Install a custom package locally
  dpm remove old-package --force           # Force remove package locally
  dpm list --custom                       # List custom packages locally
  dpm health                              # Check local system health
  dpm config --add-prefix "newcompany-"   # Add custom prefix locally
  dpm cleanup --all                       # Comprehensive local cleanup
  
  # Remote operations
  dpm connect user 10.0.1.5               # Connect to remote system
  dpm connect user host.com --key ~/.ssh/id_rsa --port 2222
  dpm install mycompany-dev-tools          # Install on connected remote system
  dpm list --custom                       # List packages on remote system
  dpm health                              # Check remote system health
  dpm connect --disconnect                # Disconnect and return to local
  dpm connect                             # Show current connection status
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Install command
        install_parser = subparsers.add_parser('install', help='Install a package or metapackage')
        install_parser.add_argument('package_name', help='Name of the package to install')
        install_parser.add_argument('--force', action='store_true', 
                                   help='Force installation even with conflicts')
        install_parser.add_argument('--offline', action='store_true', 
                                   help='Use offline mode with pinned versions')
        install_parser.add_argument('--online', action='store_true', 
                                   help='Use online mode with latest versions')
        install_parser.add_argument('--version', help='Specific version to install')
        
        # Remove command
        remove_parser = subparsers.add_parser('remove', help='Remove a package or metapackage')
        remove_parser.add_argument('package_name', help='Name of the package to remove')
        remove_parser.add_argument('--force', action='store_true', 
                                  help='Force removal even with dependencies')
        remove_parser.add_argument('--purge', action='store_true', 
                                  help='Purge configuration files as well')
        
        # Info command
        info_parser = subparsers.add_parser('info', help='Show information about a package')
        info_parser.add_argument('package_name', help='Name of the package to show info for')
        info_parser.add_argument('--dependencies', action='store_true', 
                                help='Show dependency information')
        
        # List command
        list_parser = subparsers.add_parser('list', help='List installed packages')
        list_parser.add_argument('--custom', action='store_true', 
                                help='Show only custom packages')
        list_parser.add_argument('--metapackages', action='store_true', 
                                help='Show only metapackages')
        list_parser.add_argument('--broken', action='store_true', 
                                help='Show only broken packages')
        
        # Health command
        health_parser = subparsers.add_parser('health', help='Check system package health')
        health_parser.add_argument('--verbose', action='store_true', 
                                  help='Show detailed health information')
        
        # Fix command
        fix_parser = subparsers.add_parser('fix', help='Fix broken package system')
        fix_parser.add_argument('--force', action='store_true', 
                               help='Use aggressive fixing methods')
        
        # Config command
        config_parser = subparsers.add_parser('config', help='Manage configuration')
        config_parser.add_argument('--show', action='store_true', 
                                  help='Show current configuration')
        config_parser.add_argument('--add-prefix', help='Add a custom package prefix')
        config_parser.add_argument('--remove-prefix', help='Remove a custom package prefix')
        config_parser.add_argument('--add-removable', help='Add a package to removable packages list')
        config_parser.add_argument('--remove-removable', help='Remove a package from removable packages list')
        config_parser.add_argument('--list-removable', action='store_true', 
                                  help='List all removable packages')
        config_parser.add_argument('--set-offline', action='store_true', 
                                  help='Enable offline mode')
        config_parser.add_argument('--set-online', action='store_true', 
                                  help='Enable online mode')
        
        # Mode command
        mode_parser = subparsers.add_parser('mode', help='Manage offline/online mode')
        mode_parser.add_argument('--status', action='store_true', 
                                help='Show current mode status')
        mode_parser.add_argument('--offline', action='store_true', 
                                help='Switch to offline mode')
        mode_parser.add_argument('--online', action='store_true', 
                                help='Switch to online mode')
        mode_parser.add_argument('--auto', action='store_true', 
                                help='Auto-detect appropriate mode')
        
        # Cleanup command
        cleanup_parser = subparsers.add_parser('cleanup', help='System cleanup and maintenance')
        cleanup_parser.add_argument('--apt-cache', action='store_true', 
                                   help='Clean APT package cache')
        cleanup_parser.add_argument('--offline-repos', action='store_true', 
                                   help='Clean offline repository caches')
        cleanup_parser.add_argument('--artifactory', action='store_true', 
                                   help='Clean artifactory cache')
        cleanup_parser.add_argument('--all', action='store_true', 
                                   help='Perform comprehensive cleanup')
        cleanup_parser.add_argument('--aggressive', action='store_true', 
                                   help='Use aggressive cleanup methods')
        
        # Connect command
        connect_parser = subparsers.add_parser('connect', help='Connect to remote system or show connection status')
        connect_parser.add_argument('user', nargs='?', help='SSH username')
        connect_parser.add_argument('host', nargs='?', help='Remote host IP/hostname')
        connect_parser.add_argument('--key', help='SSH private key path')
        connect_parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
        connect_parser.add_argument('--disconnect', action='store_true', help='Disconnect from remote system')
        
        return parser
    
    def _handle_install(self, args) -> int:
        """Handle package installation."""
        target = self.remote_manager.get_current_target()
        print(f"Installing package '{args.package_name}' on {target}")
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            # Execute on remote system
            kwargs = {
                'force': args.force,
                'offline': args.offline,
                'online': args.online,
                'version': args.version
            }
            result = self.remote_manager.execute_command('install', args.package_name, **kwargs)
        else:
            # Execute locally
            if args.offline and args.online:
                print("Error: Cannot specify both --offline and --online modes")
                return 1
            elif args.offline:
                print("Switching to offline mode for this operation")
                self.engine.mode_manager.switch_to_offline_mode()
            elif args.online:
                print("Switching to online mode for this operation")
                self.engine.mode_manager.switch_to_online_mode()
            
            result = self.engine.install_package(args.package_name, force=args.force)
        
        self._display_operation_result(result)
        return 0 if result.success else 1
    
    def _handle_remove(self, args) -> int:
        """Handle package removal."""
        target = self.remote_manager.get_current_target()
        print(f"Removing package '{args.package_name}' from {target}")
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            # Execute on remote system
            kwargs = {
                'force': args.force,
                'purge': args.purge
            }
            result = self.remote_manager.execute_command('remove', args.package_name, **kwargs)
        else:
            # Execute locally
            result = self.engine.remove_package(args.package_name, force=args.force)
        
        self._display_operation_result(result)
        return 0 if result.success else 1
    
    def _handle_info(self, args) -> int:
        """Handle package info display."""
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
    
    def _handle_list(self, args) -> int:
        """Handle package listing."""
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
    
    def _handle_health(self, args) -> int:
        """Handle system health check."""
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
                print(f"  Offline Mode: {mode_status['offline_mode']}")
                print(f"  Network Available: {mode_status['network_available']}")
                print(f"  Repositories Accessible: {mode_status['repositories_accessible']}")
                print(f"  Pinned Packages: {mode_status['pinned_packages_count']}")
            
            return 0 if result.success else 1
    
    def _handle_fix(self, args) -> int:
        """Handle system fixing."""
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
    
    def _handle_config(self, args) -> int:
        """Handle configuration management."""
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
                self.config.add_custom_prefix(args.add_prefix)
                self.config.save_config()
                print(f"✅ Added custom prefix on {target}: {args.add_prefix}")
                print(f"   Packages starting with '{args.add_prefix}' will now be treated as custom packages.")
            elif args.remove_prefix:
                self.config.remove_custom_prefix(args.remove_prefix)
                print(f"✅ Removed custom prefix from {target}: {args.remove_prefix}")
            elif args.add_removable:
                try:
                    self.config.add_removable_package(args.add_removable)
                    print(f"✅ Added removable package on {target}: {args.add_removable}")
                    print(f"   This package can now be removed during conflict resolution.")
                except ValueError as e:
                    print(f"❌ Error: {e}")
                    return 1
            elif args.remove_removable:
                self.config.remove_removable_package(args.remove_removable)
                print(f"✅ Removed removable package from {target}: {args.remove_removable}")
            elif args.list_removable:
                removable = self.config.get_removable_packages()
                print(f"📦 Removable Packages on {target} ({len(removable)}):")
                if removable:
                    for package in removable:
                        print(f"  - {package}")
                else:
                    print("  (none configured)")
            elif args.set_offline:
                self.config.set_offline_mode(True)
                print(f"✅ Enabled offline mode on {target}")
            elif args.set_online:
                self.config.set_offline_mode(False)
                print(f"✅ Enabled online mode on {target}")
            else:
                self._show_config()
            
            return 0
    
    def _handle_mode(self, args) -> int:
        """Handle mode management."""
        target = self.remote_manager.get_current_target()
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            # Execute on remote system
            kwargs = {
                'status': not (args.offline or args.online or args.auto),
                'offline': args.offline,
                'online': args.online,
                'auto': args.auto
            }
            result = self.remote_manager.execute_command('mode', '', **kwargs)
            self._display_operation_result(result)
            return 0 if result.success else 1
        else:
            # Execute locally
            if args.offline:
                self.engine.mode_manager.switch_to_offline_mode()
                print(f"✅ Switched to offline mode on {target}")
            elif args.online:
                self.engine.mode_manager.switch_to_online_mode()
                print(f"✅ Switched to online mode on {target}")
            elif args.auto:
                mode = self.engine.mode_manager.auto_detect_mode()
                print(f"Auto-detected mode on {target}: {mode}")
            else:
                # Show status by default
                mode_status = self.engine.mode_manager.get_mode_status()
                print(f"Mode Status - {target}:")
                print(f"  Current Mode: {'Offline' if mode_status['offline_mode'] else 'Online'}")
                print(f"  Network Available: {mode_status['network_available']}")
                print(f"  Repositories Accessible: {mode_status['repositories_accessible']}")
                print(f"  Pinned Packages: {mode_status['pinned_packages_count']}")
                print(f"  Config Setting: {'Offline' if mode_status['config_offline_setting'] else 'Online'}")
            
            return 0
    
    def _handle_cleanup(self, args) -> int:
        """Handle system cleanup operations."""
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
                # Perform comprehensive cleanup
                mode = 'offline' if self.config.is_offline_mode() else 'online'
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
            
            elif args.apt_cache:
                result = self.cleanup.clean_apt_cache(aggressive=args.aggressive)
                print(f"🧹 APT Cache Cleanup - {target}")
                if result.success:
                    space_freed = result.details.get('space_freed_mb', 0) if result.details else 0
                    print(f"✅ APT cache cleaned - {space_freed} MB freed")
                else:
                    print("❌ Failed to clean APT cache")
                    for error in result.errors:
                        print(f"  - {error}")
                return 0 if result.success else 1
            
            elif args.offline_repos:
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
            
            elif args.artifactory:
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
            
            else:
                print(f"🧹 Available cleanup options for {target}:")
                print("  --apt-cache      Clean APT package cache")
                print("  --offline-repos  Clean offline repository caches")
                print("  --artifactory    Clean artifactory cache")
                print("  --all           Perform comprehensive cleanup")
                print("  --aggressive    Use aggressive cleanup methods")
                return 0
    
    def _display_operation_result(self, result: OperationResult) -> None:
        """Display operation result in a consistent format."""
        if hasattr(self.engine, 'conflict_handler'):
            self.engine.conflict_handler.display_operation_result(
                result.success, result.packages_affected, result.warnings, result.errors
            )
        else:
            # Fallback display for remote operations
            if result.success:
                print("✅ Operation completed successfully")
                if result.packages_affected:
                    print(f"📦 Packages affected: {len(result.packages_affected)}")
                    for pkg in result.packages_affected[:5]:
                        print(f"  - {pkg.name}")
            else:
                print("❌ Operation failed")
            
            if result.warnings:
                print(f"⚠️  Warnings: {len(result.warnings)}")
                for warning in result.warnings:
                    print(f"  - {warning}")
            
            if result.errors:
                print(f"❌ Errors: {len(result.errors)}")
                for error in result.errors:
                    print(f"  - {error}")
            
            # Show remote output if available
            if result.details and 'stdout' in result.details:
                stdout = result.details['stdout'].strip()
                if stdout:
                    print(f"\n📄 Remote output:\n{stdout}")
    
    def _handle_connect(self, args) -> int:
        """Handle connection management."""
        if args.disconnect:
            # Disconnect from remote system
            if self.remote_manager.is_remote_connected():
                target = self.remote_manager.get_current_target()
                self.remote_manager.disconnect()
                print(f"✅ Disconnected from {target}")
                print("🏠 Now executing commands locally")
            else:
                print("ℹ️  Not connected to any remote system")
            return 0
        
        if not args.user or not args.host:
            # Show connection status
            if self.remote_manager.is_remote_connected():
                target = self.remote_manager.get_current_target()
                print(f"🌐 Connected to: {target}")
                print("   All DPM commands will execute on the remote system")
                print("   Use 'dpm connect --disconnect' to return to local execution")
            else:
                print("🏠 Executing locally")
                print("   Use 'dpm connect <user> <host>' to connect to remote system")
            return 0
        
        # Connect to remote system
        print(f"🔌 Connecting to {args.user}@{args.host}:{args.port}...")
        
        success = self.remote_manager.connect(args.host, args.user, args.key, args.port)
        
        if success:
            print(f"✅ Successfully connected to {args.user}@{args.host}:{args.port}")
            print("🌐 All DPM commands will now execute on the remote system")
            print("   Use 'dpm connect --disconnect' to return to local execution")
        else:
            print(f"❌ Failed to connect to {args.user}@{args.host}:{args.port}")
            print("   Check SSH key, credentials, and network connectivity")
            return 1
        
        return 0
    
    def _show_config(self) -> None:
        """Show current configuration."""
        print("📋 DEBIAN PACKAGE MANAGER CONFIGURATION")
        print("=" * 50)
        print(f"Config File: {self.config.config_path}")
        print(f"Offline Mode: {'✅ Enabled' if self.config.is_offline_mode() else '❌ Disabled'}")
        print()
        
        # Custom prefixes
        prefixes = self.config.get_custom_prefixes()
        print(f"🏷️  Custom Package Prefixes ({len(prefixes)}):")
        if prefixes:
            for prefix in prefixes:
                print(f"    - {prefix}")
        else:
            print("    ⚠️  (none configured - no packages can be removed!)")
        print()
        
        # Safety policy
        print("🛡️  Safety Policy:")
        print("    System Package Removal: 🚫 NEVER ALLOWED (SAFE)")
        print("    Custom Package Removal: ✅ Only packages with configured prefixes")
        print()
        
        # Removable packages
        removable = self.config.get_removable_packages()
        print(f"📦 Removable Packages ({len(removable)}):")
        if removable:
            for package in removable[:5]:  # Show first 5
                print(f"    - {package}")
            if len(removable) > 5:
                print(f"    ... and {len(removable) - 5} more")
        else:
            print("    (none configured)")
        print()
        
        # Pinned versions
        pinned = self.config.version_pinning.get_all_pinned()
        print(f"📌 Pinned Versions ({len(pinned)}):")
        if pinned:
            for package, version in list(pinned.items())[:5]:  # Show first 5
                print(f"    - {package}: {version}")
            if len(pinned) > 5:
                print(f"    ... and {len(pinned) - 5} more")
        else:
            print("    (none configured)")
        print()
        
        print("💡 Configuration Tips:")
        print("    - Add your custom package prefixes to enable conflict resolution")
        print("    - Only packages with these prefixes can be removed during conflicts")
        print("    - System packages are NEVER removed for safety")
        print("    - Example: dpm config --add-prefix 'mycompany-'")
        print("    - Example: dpm config --add-prefix 'internal-'")


def main():
    """Main entry point for the CLI."""
    cli = PackageManagerCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())