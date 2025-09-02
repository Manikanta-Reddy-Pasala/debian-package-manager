"""Command-line interface for Debian Metapackage Manager."""

import argparse
import sys
import os
from typing import Optional

from .engine import PackageEngine
from .config import Config
from .conflict_handler import UserPrompt


class PackageManagerCLI:
    """Main CLI interface for the package manager."""
    
    def __init__(self):
        """Initialize CLI with package engine."""
        self.engine = PackageEngine()
        self.config = self.engine.config
    
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
  dpm install mycompany-dev-tools          # Install a custom package
  dpm install vim --force                  # Force install with conflicts
  dpm remove old-package --force           # Force remove package
  dpm info mycompany-meta-suite           # Show package information
  dpm list --custom                       # List custom packages only
  dpm health                              # Check system health
  dpm fix                                 # Fix broken packages
  dpm mode --offline                      # Switch to offline mode
  dpm config --add-prefix "newcompany-"   # Add custom prefix (IMPORTANT!)
  dpm config --show                       # View safety settings
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
        
        return parser
    
    def _handle_install(self, args) -> int:
        """Handle package installation."""
        print(f"Installing package: {args.package_name}")
        
        if args.offline:
            self.engine.mode_manager.switch_to_offline_mode()
        
        result = self.engine.install_package(args.package_name, force=args.force)
        
        self.engine.conflict_handler.display_operation_result(
            result.success, result.packages_affected, result.warnings, result.errors
        )
        
        return 0 if result.success else 1
    
    def _handle_remove(self, args) -> int:
        """Handle package removal."""
        print(f"Removing package: {args.package_name}")
        
        result = self.engine.remove_package(args.package_name, force=args.force)
        
        self.engine.conflict_handler.display_operation_result(
            result.success, result.packages_affected, result.warnings, result.errors
        )
        
        return 0 if result.success else 1
    
    def _handle_info(self, args) -> int:
        """Handle package info display."""
        package_info = self.engine.get_package_info(args.package_name)
        
        if not package_info:
            print(f"Package '{args.package_name}' not found.")
            return 1
        
        dependencies = []
        if args.dependencies:
            dependencies = self.engine.apt.get_dependencies(args.package_name)
        
        self.engine.conflict_handler.display_package_info(package_info, dependencies)
        return 0
    
    def _handle_list(self, args) -> int:
        """Handle package listing."""
        if args.broken:
            packages = self.engine.dpkg.list_broken_packages()
            print(f"Broken packages ({len(packages)}):")
        else:
            packages = self.engine.list_installed_packages(custom_only=args.custom)
            
            if args.metapackages:
                packages = [pkg for pkg in packages if pkg.is_metapackage]
            
            print(f"Installed packages ({len(packages)}):")
        
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
        result = self.engine.check_system_health()
        
        print("System Health Check")
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
        result = self.engine.fix_broken_system()
        
        self.engine.conflict_handler.display_operation_result(
            result.success, result.packages_affected, result.warnings, result.errors
        )
        
        return 0 if result.success else 1
    
    def _handle_config(self, args) -> int:
        """Handle configuration management."""
        if args.show:
            self._show_config()
        elif args.add_prefix:
            self.config.add_custom_prefix(args.add_prefix)
            self.config.save_config()
            print(f"✅ Added custom prefix: {args.add_prefix}")
            print(f"   Packages starting with '{args.add_prefix}' will now be treated as custom packages.")
        elif args.remove_prefix:
            self.config.remove_custom_prefix(args.remove_prefix)
            print(f"✅ Removed custom prefix: {args.remove_prefix}")
        elif args.set_offline:
            self.config.set_offline_mode(True)
            print("✅ Enabled offline mode")
        elif args.set_online:
            self.config.set_offline_mode(False)
            print("✅ Enabled online mode")

        else:
            self._show_config()
        
        return 0
    
    def _handle_mode(self, args) -> int:
        """Handle mode management."""
        if args.offline:
            self.engine.mode_manager.switch_to_offline_mode()
        elif args.online:
            self.engine.mode_manager.switch_to_online_mode()
        elif args.auto:
            mode = self.engine.mode_manager.auto_detect_mode()
            print(f"Auto-detected mode: {mode}")
        else:
            # Show status by default
            mode_status = self.engine.mode_manager.get_mode_status()
            print("Mode Status:")
            print(f"  Current Mode: {'Offline' if mode_status['offline_mode'] else 'Online'}")
            print(f"  Network Available: {mode_status['network_available']}")
            print(f"  Repositories Accessible: {mode_status['repositories_accessible']}")
            print(f"  Pinned Packages: {mode_status['pinned_packages_count']}")
            print(f"  Config Setting: {'Offline' if mode_status['config_offline_setting'] else 'Online'}")
        
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
            print("    (none configured)")
        print()
        
        # Conflict resolution policy
        policy = self.config.get_conflict_resolution_policy()
        print("⚔️  Conflict Resolution Policy:")
        system_removal = "✅ Allowed" if policy.get('allow_system_package_removal', False) else "🚫 Blocked (SAFE)"
        print(f"    System Package Removal: {system_removal}")
        prefer_custom = "✅ Yes" if policy.get('prefer_custom_package_removal', True) else "❌ No"
        print(f"    Prefer Custom Package Removal: {prefer_custom}")
        print()
        
        # Protected packages
        protected = self.config.get_protected_packages()
        print(f"🛡️  Protected Packages ({len(protected)}):")
        if protected:
            for pkg in protected[:10]:  # Show first 10
                print(f"    - {pkg}")
            if len(protected) > 10:
                print(f"    ... and {len(protected) - 10} more")
        else:
            print("    (using default system protection)")
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
        print("    - Add your custom package prefixes to enable safe conflict resolution")
        print("    - Keep system package removal blocked for safety")
        print("    - Use protected packages list for critical custom packages")
        print("    - Example: dpm config --add-prefix 'mycompany-'")


def main():
    """Main entry point for the CLI."""
    cli = PackageManagerCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())