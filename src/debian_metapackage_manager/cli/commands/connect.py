"""Connect command handler."""

import argparse
import re
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
        parser.add_argument('user_host', nargs='?', help='SSH username@hostname or just hostname')
        parser.add_argument('host', nargs='?', help='Remote host IP/hostname (if username provided separately)')
        parser.add_argument('--key', help='SSH private key path')
        parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
        parser.add_argument('--disconnect', action='store_true', help='Disconnect from remote system')
        return parser
    
    def handle(self, args: argparse.Namespace) -> int:
        """Handle connect command."""
        if args.disconnect:
            return self._handle_disconnect()
        
        # Handle different argument formats
        if not args.user_host:
            return self._show_connection_status()
        
        # Parse username@host format or separate arguments
        user, host = self._parse_user_host(args.user_host, args.host)
        if not user or not host:
            print("❌ Invalid connection format. Use either:")
            print("   dpm connect username@hostname")
            print("   dpm connect username hostname")
            return 1
        
        # Set port from args
        port = args.port
        
        return self._handle_connect(user, host, args.key, port)
    
    def _parse_user_host(self, user_host: str, host_arg: str = None) -> tuple:
        """Parse username and host from various formats."""
        # If we have username@host format
        if '@' in user_host:
            user, host = user_host.split('@', 1)
            return user, host
        
        # If we have separate user and host arguments
        if host_arg:
            return user_host, host_arg
        
        # Just host provided - use default user
        return 'root', user_host
    
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
            print("   Use 'dpm connect <user>@<host>' to connect to remote system")
            print("   Or: 'dpm connect <user> <host>'")
        return 0
    
    def _handle_connect(self, user: str, host: str, key: str, port: int) -> int:
        """Handle connection to remote system."""
        print(f"🔌 Connecting to {user}@{host}:{port}...")
        
        success = self.remote_manager.connect(host, user, key, port)
        
        if success:
            print(f"✅ Successfully connected to {user}@{host}:{port}")
            print("🌐 All DPM commands will now execute on the remote system")
            print("   Use 'dpm connect --disconnect' to return to local execution")
            return 0
        else:
            print(f"❌ Failed to connect to {user}@{host}:{port}")
            print("   Please check:")
            print("   - Network connectivity")
            print("   - SSH credentials")
            print("   - Remote host accessibility")
            if key:
                print(f"   - SSH key file: {key}")
            return 1