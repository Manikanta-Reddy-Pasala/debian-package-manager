"""Mode management command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler

if TYPE_CHECKING:
    from ...engine import PackageEngine
    from ...remote import RemotePackageManager


class ModeCommandHandler(CommandHandler):
    """Handler for mode management commands."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager'):
        """Initialize mode handler."""
        self.engine = engine
        self.remote_manager = remote_manager
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add mode command parser."""
        parser = subparsers.add_parser('mode', help='Manage offline/online mode')
        parser.add_argument('-s', '--status', action='store_true', 
                           help='Show current mode status')
        parser.add_argument('--offline', action='store_true', 
                           help='Switch to offline mode')
        parser.add_argument('--online', action='store_true', 
                           help='Switch to online mode')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle mode command."""
        target = self.remote_manager.get_current_target()
        
        # Check if we're connected to remote
        if self.remote_manager.is_remote_connected():
            return self._handle_remote_mode(args)
        else:
            return self._handle_local_mode(args, target)
    
    def _handle_local_mode(self, args: argparse.Namespace, target: str) -> int:
        """Handle local mode management."""
        if args.offline:
            self.engine.mode_manager.switch_to_offline_mode()
            print(f"✅ Switched to offline mode on {target}")
            self._show_mode_status(target)
        elif args.online:
            self.engine.mode_manager.switch_to_online_mode()
            print(f"✅ Switched to online mode on {target}")
            self._show_mode_status(target)
        else:
            # Show status by default
            self._show_mode_status(target)
        
        return 0
    
    def _handle_remote_mode(self, args: argparse.Namespace) -> int:
        """Handle remote mode management."""
        kwargs = {
            'status': not (args.offline or args.online),
            'offline': args.offline,
            'online': args.online
        }
        result = self.remote_manager.execute_command('mode', '', **kwargs)
        return 0 if result.success else 1
    
    def _show_mode_status(self, target: str) -> None:
        """Show current mode status."""
        mode_status = self.engine.mode_manager.get_mode_status()
        print(f"Mode Status - {target}:")
        print(f"  Current Mode: {'Offline' if mode_status.offline_mode else 'Online'}")
        print(f"  Network Available: {mode_status.network_available}")
        print(f"  Repositories Accessible: {mode_status.repositories_accessible}")
        print(f"  Pinned Packages: {mode_status.pinned_packages_count}")
        print(f"  Config Setting: {'Offline' if mode_status.config_offline_setting else 'Online'}")