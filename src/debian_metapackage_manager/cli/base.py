"""Base CLI components and utilities."""

import argparse
import sys
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from ..models import OperationResult


class CommandHandler(ABC):
    """Base class for command handlers."""
    
    @abstractmethod
    def add_parser(self, subparsers) -> argparse.ArgumentParser:
        """Add command parser to subparsers."""
        pass
    
    @abstractmethod
    def handle(self, args: argparse.Namespace) -> int:
        """Handle the command execution."""
        pass


class CLIBase:
    """Base CLI functionality."""
    
    def __init__(self):
        """Initialize base CLI."""
        self.handlers: Dict[str, CommandHandler] = {}
    
    def register_handler(self, command: str, handler: CommandHandler):
        """Register a command handler."""
        self.handlers[command] = handler
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            description="Debian Package Manager - Intelligent package management for custom package systems",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_examples()
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Register all command parsers
        for command, handler in self.handlers.items():
            handler.add_parser(subparsers)
        
        return parser
    
    def _get_examples(self) -> str:
        """Get CLI usage examples."""
        return """
Examples:
  # Local operations
  dpm install mycompany-dev-tools          # Install a custom package locally
  dpm remove old-package --force           # Force remove package locally
  dpm list --custom                       # List custom packages locally
  dpm health                              # Check local system health
  dpm cleanup --all                       # Comprehensive local cleanup
  
  # Remote operations
  dpm connect user 10.0.1.5               # Connect to remote system
  dpm connect user host.com --key ~/.ssh/id_rsa --port 2222
  dpm install mycompany-dev-tools          # Install on connected remote system
  dpm list --custom                       # List packages on remote system
  dpm health                              # Check remote system health
  dpm connect --disconnect                # Disconnect and return to local
  dpm connect                             # Show current connection status
  
  # Mode management
  dpm install --online package-name       # Force online mode
  dpm install --offline package-name      # Force offline mode
  dpm mode --status                       # Check current mode
  dpm mode --auto                         # Auto-detect mode
        """
    
    def display_operation_result(self, result: OperationResult) -> None:
        """Display operation result in a consistent format."""
        if result.success:
            print("✅ Operation completed successfully")
            if result.packages_affected:
                print(f"📦 Packages affected: {len(result.packages_affected)}")
                for pkg in result.packages_affected[:5]:
                    print(f"  - {pkg.name}")
                if len(result.packages_affected) > 5:
                    print(f"  ... and {len(result.packages_affected) - 5} more")
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
        if hasattr(result, 'details') and result.details and 'stdout' in result.details:
            stdout = result.details['stdout'].strip()
            if stdout:
                print(f"\n📄 Remote output:\n{stdout}")


class CLIError(Exception):
    """CLI-specific error."""
    pass


class ValidationError(CLIError):
    """Validation error in CLI arguments."""
    pass