"""CLI module for Debian Package Manager."""

from .main import PackageManagerCLI
from .base import CommandHandler, CLIBase, CLIError, ValidationError


def main(args=None):
    """Main entry point for the CLI."""
    cli = PackageManagerCLI()
    return cli.run(args)


def handle_install(package_names, **kwargs):
    """Handle install command - compatibility function."""
    cli = PackageManagerCLI()
    # Create mock args for install command
    class MockArgs:
        def __init__(self):
            self.command = 'install'
            self.packages = package_names
            self.force = kwargs.get('force', False)
            self.dry_run = kwargs.get('dry_run', False)
            self.verbose = kwargs.get('verbose', False)
    
    return cli.handlers['install'].handle(MockArgs())


def handle_remove(package_names, **kwargs):
    """Handle remove command - compatibility function."""
    cli = PackageManagerCLI()
    # Create mock args for remove command
    class MockArgs:
        def __init__(self):
            self.command = 'remove'
            self.packages = package_names
            self.force = kwargs.get('force', False)
            self.dry_run = kwargs.get('dry_run', False)
            self.verbose = kwargs.get('verbose', False)
    
    return cli.handlers['remove'].handle(MockArgs())


__all__ = ['PackageManagerCLI', 'CommandHandler', 'CLIBase', 'CLIError', 'ValidationError', 'main', 'handle_install', 'handle_remove']