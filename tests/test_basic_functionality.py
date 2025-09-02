"""Basic functionality tests for the project structure."""

import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.models import Package, PackageStatus
from debian_metapackage_manager.interfaces import PackageInterface


def test_package_model_basic():
    """Test basic Package model functionality."""
    package = Package(name="test-pkg", version="1.0.0")
    assert package.name == "test-pkg"
    assert package.version == "1.0.0"
    assert package.status == PackageStatus.NOT_INSTALLED


def test_package_interface_exists():
    """Test that PackageInterface can be imported and has required methods."""
    # Check that the interface has the required abstract methods
    required_methods = [
        'install', 'remove', 'get_dependencies', 
        'check_conflicts', 'is_installed', 'get_package_info'
    ]
    
    for method in required_methods:
        assert hasattr(PackageInterface, method)


def test_cli_module_imports():
    """Test that CLI module can be imported."""
    from debian_metapackage_manager.cli import main, handle_install, handle_remove
    
    # Check that functions exist
    assert callable(main)
    assert callable(handle_install)
    assert callable(handle_remove)


if __name__ == "__main__":
    test_package_model_basic()
    test_package_interface_exists()
    test_cli_module_imports()
    print("All basic tests passed!")