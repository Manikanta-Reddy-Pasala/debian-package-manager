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
        parser = subparsers.add_parser('list', help='List installed packages with custom prefixes')
        parser.add_argument('--all', action='store_true', 
                           help='Show all installed packages (not just custom prefixes)')
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
                'all': args.all,
                'broken': args.broken,
                'metapackages': args.metapackages,
                'simple': args.simple
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
                # By default, show only custom packages (with configured prefixes)
                # Use --all flag to show all installed packages
                custom_only = not args.all  # Show custom by default, unless --all is specified
                packages = self.engine.list_installed_packages(custom_only=custom_only)
                
                if args.metapackages:
                    packages = [pkg for pkg in packages if pkg.is_metapackage]
                
                package_type = "all" if args.all else "custom prefix"
                print(f"Installed {package_type} packages on {target} ({len(packages)}):")
            
            if not packages:
                print("  No packages found.")
                return 0
            
            # Display packages in table format by default (unless --simple is used)
            if args.simple:
                self._display_simple_list(packages)
            else:
                self._display_table_format(packages)
            
            return 0
    
    def _display_table_format(self, packages) -> None:
        """Display packages in a structured table format with neat lines."""
        if not packages:
            return
        
        # Table configuration
        col_widths = {
            'sno': 6,
            'name': 35,
            'current': 20,
            'available': 20,
            'type': 12
        }
        total_width = sum(col_widths.values()) + 4  # +4 for separators
        
        # Top border
        print("\n" + "┌" + "─" * (total_width - 2) + "┐")
        
        # Header
        header = f"│{'S.No':<{col_widths['sno']}}│{'Package Name':<{col_widths['name']}}│{'Current Version':<{col_widths['current']}}│{'Available Versions':<{col_widths['available']}}│{'Type':<{col_widths['type']}}│"
        print(header)
        
        # Header separator
        sep_line = "├" + "─" * col_widths['sno'] + "┼" + "─" * col_widths['name'] + "┼" + "─" * col_widths['current'] + "┼" + "─" * col_widths['available'] + "┼" + "─" * col_widths['type'] + "┤"
        print(sep_line)
        
        # Data rows
        for i, package in enumerate(packages, 1):
            # Get available versions
            available_versions = self._get_available_versions(package.name)
            available_str = ", ".join(available_versions[:2])  # Show max 2 versions
            if len(available_versions) > 2:
                available_str += "..."
            if not available_str:
                available_str = "N/A"
            
            # Truncate if too long
            if len(available_str) > col_widths['available'] - 1:
                available_str = available_str[:col_widths['available'] - 4] + "..."
            
            # Determine package type
            pkg_type = "SYSTEM"
            if package.is_metapackage:
                pkg_type = "META"
            elif package.is_custom:
                pkg_type = "CUSTOM"
            
            # Truncate package name if too long
            display_name = package.name
            if len(display_name) > col_widths['name'] - 1:
                display_name = display_name[:col_widths['name'] - 4] + "..."
            
            # Truncate version if too long
            display_version = package.version
            if len(display_version) > col_widths['current'] - 1:
                display_version = display_version[:col_widths['current'] - 4] + "..."
            
            # Format row
            row = f"│{i:<{col_widths['sno']}}│{display_name:<{col_widths['name']}}│{display_version:<{col_widths['current']}}│{available_str:<{col_widths['available']}}│{pkg_type:<{col_widths['type']}}│"
            print(row)
        
        # Bottom border
        print("└" + "─" * (total_width - 2) + "┘")
        
        # Summary
        print(f"\nTotal: {len(packages)} packages")
        
        # Legend
        print("\nType Legend: CUSTOM (custom prefixes), META (metapackages), SYSTEM (system packages)")
    
    def _display_simple_list(self, packages) -> None:
        """Display packages in simple list format (original format)."""
        for package in packages:
            status_icon = "✓" if package.status.value == "installed" else "✗"
            pkg_type = ""
            
            if package.is_metapackage:
                pkg_type = " [META]"
            elif package.is_custom:
                pkg_type = " [CUSTOM]"
            
            print(f"  {status_icon} {package.name} (v{package.version}){pkg_type}")
    
    def _get_available_versions(self, package_name: str) -> list:
        """Get list of available versions for a package."""
        try:
            # Use APT interface to get available versions
            return self.engine.apt.get_available_versions(package_name)
        except Exception:
            # If we can't get available versions, return empty list
            return []
    
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