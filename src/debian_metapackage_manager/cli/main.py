"""Main CLI interface for Debian Package Manager."""

import os
import sys
from typing import Optional

from .base import CLIBase, ValidationError
from .commands import (
    InstallCommandHandler, RemoveCommandHandler, ModeCommandHandler,
    InfoCommandHandler, ListCommandHandler, HealthCommandHandler,
    FixCommandHandler, CleanupCommandHandler,
    ConnectCommandHandler
)
from ..core.managers import PackageEngine
from ..config import Config
from ..core.managers import SystemCleanup, RemotePackageManager
from ..utils.logging import get_logger

logger = get_logger('cli.main')


class PackageManagerCLI(CLIBase):
    """Main CLI interface for the package manager."""
    
    def __init__(self):
        """Initialize CLI with all components."""
        super().__init__()
        
        # Initialize core components
        self.engine = PackageEngine()
        self.config = self.engine.config
        self.cleanup = SystemCleanup()
        self.remote_manager = RemotePackageManager()
        
        # Register command handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all command handlers."""
        self.register_handler('install', InstallCommandHandler(self.engine, self.remote_manager))
        self.register_handler('remove', RemoveCommandHandler(self.engine, self.remote_manager))
        self.register_handler('mode', ModeCommandHandler(self.engine, self.remote_manager))
        self.register_handler('info', InfoCommandHandler(self.engine, self.remote_manager))
        self.register_handler('list', ListCommandHandler(self.engine, self.remote_manager))
        self.register_handler('health', HealthCommandHandler(self.engine, self.remote_manager))
        self.register_handler('fix', FixCommandHandler(self.engine, self.remote_manager))
        self.register_handler('cleanup', CleanupCommandHandler(self.engine, self.remote_manager, self.cleanup))
        self.register_handler('connect', ConnectCommandHandler(self.engine, self.remote_manager))
    
    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI with given arguments."""
        try:
            parser = self.create_parser()
            parsed_args = parser.parse_args(args)
            
            if not parsed_args.command:
                parser.print_help()
                return 1
            
            # Check for root privileges if needed
            self._check_privileges(parsed_args)
            
            # Execute command
            if parsed_args.command in self.handlers:
                logger.info(f"Executing command: {parsed_args.command}")
                result = self.handlers[parsed_args.command].handle(parsed_args)
                logger.info(f"Command {parsed_args.command} completed with result: {result}")
                return result
            else:
                print(f"Unknown command: {parsed_args.command}")
                print("Available commands:", ", ".join(self.handlers.keys()))
                return 1
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            logger.info("Operation cancelled by user")
            return 1
        except ValidationError as e:
            print(f"Validation Error: {e}")
            logger.error(f"Validation error: {e}")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return 1
    
    def _check_privileges(self, args) -> None:
        """Check for required privileges."""
        if args.command in ['install', 'remove'] and os.geteuid() != 0:
            print("Warning: This operation typically requires root privileges.")
            print("You may need to run with 'sudo' for actual package operations.")
            logger.warning("Command executed without root privileges")