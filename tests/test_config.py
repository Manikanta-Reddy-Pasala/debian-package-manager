"""Tests for configuration management."""

import json
import os
import tempfile
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.config import Config, PackagePrefixes, VersionPinning


def test_package_prefixes():
    """Test PackagePrefixes functionality."""
    prefixes = PackagePrefixes(['test-', 'custom-'])
    
    assert prefixes.is_custom_package('test-package')
    assert prefixes.is_custom_package('custom-tool')
    assert not prefixes.is_custom_package('standard-package')
    
    prefixes.add_prefix('new-')
    assert prefixes.is_custom_package('new-package')
    
    prefixes.remove_prefix('test-')
    assert not prefixes.is_custom_package('test-package')


def test_version_pinning():
    """Test VersionPinning functionality."""
    pinning = VersionPinning({'package1': '1.0.0', 'package2': '2.0.0'})
    
    assert pinning.get_pinned_version('package1') == '1.0.0'
    assert pinning.get_pinned_version('package2') == '2.0.0'
    assert pinning.get_pinned_version('package3') is None
    
    assert pinning.has_pinned_version('package1')
    assert not pinning.has_pinned_version('package3')
    
    pinning.set_pinned_version('package3', '3.0.0')
    assert pinning.get_pinned_version('package3') == '3.0.0'
    
    pinning.remove_pinned_version('package1')
    assert pinning.get_pinned_version('package1') is None


def test_config_with_temp_file():
    """Test Config with temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {
            'custom_prefixes': ['test-', 'demo-'],
            'offline_mode': True,
            'pinned_versions': {'pkg1': '1.0.0'}
        }
        json.dump(test_config, f)
        temp_path = f.name
    
    try:
        config = Config(temp_path)
        
        assert config.get_custom_prefixes() == ['test-', 'demo-']
        assert config.is_offline_mode() is True
        assert config.get_pinned_version('pkg1') == '1.0.0'
        
        # Test modifications
        config.add_custom_prefix('new-')
        assert 'new-' in config.get_custom_prefixes()
        
        config.set_pinned_version('pkg2', '2.0.0')
        assert config.get_pinned_version('pkg2') == '2.0.0'
        
    finally:
        os.unlink(temp_path)


def test_config_default_creation():
    """Test Config creates default configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, 'test_config.json')
        config = Config(config_path)
        
        # Should have default prefixes
        prefixes = config.get_custom_prefixes()
        assert len(prefixes) > 0
        assert 'mycompany-' in prefixes
        
        # Should be in online mode by default
        assert config.is_offline_mode() is False
        
        # Config file should be created
        assert os.path.exists(config_path)


if __name__ == "__main__":
    test_package_prefixes()
    test_version_pinning()
    test_config_with_temp_file()
    test_config_default_creation()
    print("All configuration tests passed!")