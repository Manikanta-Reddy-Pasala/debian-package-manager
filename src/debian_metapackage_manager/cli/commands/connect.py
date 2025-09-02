"""Connect command handler."""

import argparse
from typing import TYPE_CHECKING

from ..base import CommandHandler

if TYPE_CHECKING:
    from ...core.managers import PackageEngine, RemotePackageManager


class ConnectCommandHandler(CommandHandler):
    """Handler for remote connection management command."""
    
    def __init__(self, engine: 'PackageEngine', remote_manager: 'RemotePackageManager'):
        """Initialize connect command handler."""
        self.engine = engine
        self.remote_manager = remote_manager
    
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add connect command parser."""
        parser = subparsers.add_parser('connect', help='Connect to remote system or show connection status')
        parser.add_argument('user', nargs='?', help='SSH username')
        parser.add_argument('host', nargs='?', help='Remote host IP/hostname')
        parser.add_argument('--key', help='SSH private key path')
        parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
        parser.add_argument('--disconnect', action='store_true', help='Disconnect from remote system')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle connect command."""
        if args.disconnect:
            return self._handle_disconnect()
        
        if not args.user or not args.host:
            return self._show_connection_status()
        
        return self._handle_connect(args)
    
    def _handle_disconnect(self) -> int:
        """Handle disconnect from remote system."""
        if self.remote_manager.is_remote_connected():
            target = self.remote_manager.get_current_target()
            self.remote_manager.disconnect()
            print(f"✅ Disconnected from {target}")
            print("🏠 Now executing commands locally")
        else:
            print("ℹ️  Not connected to any remote system")
        return 0
    
    def _show_connection_status(self) -> int:
        """Show current connection status."""
        if self.remote_manager.is_remote_connected():
            target = self.remote_manager.get_current_target()
            print(f"🌐 Connected to: {target}")
            print("   All DPM commands will execute on the remote system")
            print("   Use 'dpm connect --disconnect' to return to local execution")
        else:
            print("🏠 Executing locally")
            print("   Use 'dpm connect <user> <host>' to connect to remote system")
        return 0
    
    def _handle_connect(self, args: argparse.Namespace) -> int:
        """Handle connection to remote system."""
        print(f"🔌 Connecting to {args.user}@{args.host}:{args.port}...")
        
        success = self.remote_manager.connect(args.host, args.user, args.key, args.port)
        
        if success:
            print(f"✅ Successfully connected to {args.user}@{args.host}:{args.port}")
            print("🌐 All DPM commands will now execute on the remote system")
            print("   Use 'dpm connect --disconnect' to return to local execution")
            return 0
        else:
            print(f"❌ Failed to connect to {args.user}@{args.host}:{args.port}")
            print("   Please check:")
            print("   - Network connectivity")
            print("   - SSH credentials")
            print("   - Remote host accessibility")
            if args.key:
                print(f"   - SSH key file: {args.key}")
            return 1