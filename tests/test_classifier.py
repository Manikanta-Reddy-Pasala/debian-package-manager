"""Tests for package classification system."""

import os
import sys
import tempfile

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debian_metapackage_manager.classifier import PackageClassifier
from debian_metapackage_manager.config import Config
from debian_metapackage_manager.models import PackageType


def test_custom_package_recognition():
    """Test custom package recognition using prefixes."""
    # Create config with test prefixes
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        import json
        test_config = {
            'custom_prefixes': ['mycompany-', 'internal-', 'custom-'],
            'offline_mode': False,
            'pinned_versions': {}
        }
        json.dump(test_config, f)
        temp_path = f.name
    
    try:
        config = Config(temp_path)
        classifier = PackageClassifier(config)
        
        # Test custom package recognition
        assert classifier.is_custom_package('mycompany-tool')
        assert classifier.is_custom_package('internal-service')
        assert classifier.is_custom_package('custom-package')
        
        # Test non-custom packages
        assert not classifier.is_custom_package('vim')
        assert not classifier.is_custom_package('libc6')
        assert not classifier.is_custom_package('systemd')
        
    finally:
        os.unlink(temp_path)


def test_metapackage_recognition():
    """Test metapackage recognition."""
    classifier = PackageClassifier()
    
    # Test metapackage indicators
    assert classifier.is_metapackage('meta-development')
    assert classifier.is_metapackage('bundle-tools')
    assert classifier.is_metapackage('suite-office')
    assert classifier.is_metapackage('collection-games')
    
    # Test custom metapackages
    assert classifier.is_metapackage('mycompany-meta-tools')
    assert classifier.is_metapackage('internal-bundle-dev')
    assert classifier.is_metapackage('custom-suite-all')
    
    # Test non-metapackages
    assert not classifier.is_metapackage('vim')
    assert not classifier.is_metapackage('mycompany-single-tool')


def test_package_type_classification():
    """Test package type classification."""
    classifier = PackageClassifier()
    
    # Test metapackage classification
    assert classifier.get_package_type('meta-development') == PackageType.METAPACKAGE
    assert classifier.get_package_type('mycompany-meta-tools') == PackageType.METAPACKAGE
    
    # Test custom package classification
    assert classifier.get_package_type('mycompany-tool') == PackageType.CUSTOM
    assert classifier.get_package_type('internal-service') == PackageType.CUSTOM
    
    # Test system package classification
    assert classifier.get_package_type('vim') == PackageType.SYSTEM
    assert classifier.get_package_type('libc6') == PackageType.SYSTEM


def test_package_classification_batch():
    """Test batch package classification."""
    classifier = PackageClassifier()
    
    packages = [
        'meta-development',
        'mycompany-tool',
        'vim',
        'internal-service',
        'libc6',
        'bundle-office'
    ]
    
    classified = classifier.classify_packages(packages)
    
    assert 'meta-development' in classified['metapackage']
    assert 'bundle-office' in classified['metapackage']
    assert 'mycompany-tool' in classified['custom']
    assert 'internal-service' in classified['custom']
    assert 'vim' in classified['system']
    assert 'libc6' in classified['system']


def test_preservation_priority():
    """Test package preservation priority."""
    classifier = PackageClassifier()
    
    # System packages should be prioritized for preservation
    assert classifier.should_prioritize_preservation('libc6')
    assert classifier.should_prioritize_preservation('systemd')
    assert classifier.should_prioritize_preservation('base-files')
    assert classifier.should_prioritize_preservation('ubuntu-minimal')
    
    # Custom packages should not be prioritized
    assert not classifier.should_prioritize_preservation('mycompany-tool')
    assert not classifier.should_prioritize_preservation('internal-service')


def test_removal_risk_levels():
    """Test removal risk level assessment."""
    classifier = PackageClassifier()
    
    # High risk: critical system packages
    assert classifier.get_removal_risk_level('libc6') == "HIGH"
    assert classifier.get_removal_risk_level('systemd') == "HIGH"
    
    # Low risk: custom packages
    assert classifier.get_removal_risk_level('mycompany-tool') == "LOW"
    assert classifier.get_removal_risk_level('internal-service') == "LOW"
    
    # Medium risk: metapackages
    assert classifier.get_removal_risk_level('meta-development') == "MEDIUM"


def test_category_summary():
    """Test package category summary generation."""
    classifier = PackageClassifier()
    
    packages = [
        'meta-development',
        'mycompany-tool',
        'vim',
        'internal-service'
    ]
    
    summary = classifier.get_package_category_summary(packages)
    
    assert "1 metapackage(s)" in summary
    assert "2 custom package(s)" in summary
    assert "1 system package(s)" in summary


if __name__ == "__main__":
    test_custom_package_recognition()
    test_metapackage_recognition()
    test_package_type_classification()
    test_package_classification_batch()
    test_preservation_priority()
    test_removal_risk_levels()
    test_category_summary()
    print("All classifier tests passed!")