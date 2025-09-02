"""Tests for validation utility functions."""

import pytest

from debian_metapackage_manager.utils.validation.package import (
    validate_package_name, validate_version, validate_package_list
)
from debian_metapackage_manager.utils.validation.config import validate_config
from debian_metapackage_manager.exceptions import ValidationError, ConfigValidationError


class TestPackageValidation:
    """Test suite for package validation functions."""

    def test_validate_package_name_valid(self):
        """Test validation of valid package names."""
        valid_names = [
            'test-package',
            'my.package',
            'lib++12',
            'package123',
            'a0',  # Minimum length
            'package-name-with-many-parts',
            'lib64',
            'python3.9-dev',
            'gcc-9-base',
            'libssl1.1'
        ]
        
        for name in valid_names:
            assert validate_package_name(name) is True

    def test_validate_package_name_invalid_empty(self):
        """Test validation fails for empty package name."""
        with pytest.raises(ValidationError, match="Package name cannot be empty"):
            validate_package_name("")

    def test_validate_package_name_invalid_too_short(self):
        """Test validation fails for too short package name."""
        with pytest.raises(ValidationError, match="must be at least 2 characters long"):
            validate_package_name("a")

    def test_validate_package_name_invalid_too_long(self):
        """Test validation fails for too long package name."""
        long_name = "a" * 215  # 215 characters
        with pytest.raises(ValidationError, match="cannot exceed 214 characters"):
            validate_package_name(long_name)

    def test_validate_package_name_invalid_characters(self):
        """Test validation fails for invalid characters."""
        invalid_names = [
            "UPPERCASE",      # Uppercase not allowed
            "package with spaces",  # Spaces not allowed
            "package_underscore",   # Underscores not allowed
            "package@symbol",       # @ not allowed
            "package#hash",         # # not allowed
            "-starts-with-hyphen",  # Cannot start with hyphen
            ".starts-with-dot",     # Cannot start with dot
        ]
        
        for name in invalid_names:
            with pytest.raises(ValidationError):
                validate_package_name(name)

    def test_validate_package_name_invalid_endings(self):
        """Test validation fails for invalid endings."""
        invalid_endings = [
            "package-",
            "package.",
            "multiple-hyphens-",
            "multiple.dots."
        ]
        
        for name in invalid_endings:
            with pytest.raises(ValidationError, match="cannot end with hyphen or dot"):
                validate_package_name(name)

    def test_validate_package_name_edge_cases(self):
        """Test edge cases for package name validation."""
        # Minimum valid length
        assert validate_package_name("ab") is True
        
        # Maximum valid length
        max_name = "a" * 214
        assert validate_package_name(max_name) is True
        
        # Valid with numbers and special chars
        assert validate_package_name("lib123+extra") is True

    def test_validate_version_valid(self):
        """Test validation of valid version strings."""
        valid_versions = [
            "1.0.0",
            "2.3.4-1",
            "1:2.3.4-5ubuntu1",
            "1.0.0~beta1",
            "2.0+dfsg",
            "1.2.3-4+deb9u1",
            "0.1.2~git20200101.1234567",
            "1:7.4.052-1ubuntu3.1",
            "a",  # Single character
            "1a2b3c"  # Mixed alphanumeric
        ]
        
        for version in valid_versions:
            assert validate_version(version) is True

    def test_validate_version_invalid_empty(self):
        """Test validation fails for empty version."""
        with pytest.raises(ValidationError, match="Version cannot be empty"):
            validate_version("")

    def test_validate_version_invalid_too_long(self):
        """Test validation fails for too long version."""
        long_version = "a" * 256  # 256 characters
        with pytest.raises(ValidationError, match="cannot exceed 255 characters"):
            validate_version(long_version)

    def test_validate_version_invalid_characters(self):
        """Test validation fails for invalid characters."""
        invalid_versions = [
            " 1.0.0",      # Leading space
            "1.0.0 ",      # Trailing space
            "1.0.0@test",  # @ not allowed
            "1.0.0#hash",  # # not allowed
            "1.0.0$var",   # $ not allowed
            "1.0.0&test",  # & not allowed
        ]
        
        for version in invalid_versions:
            with pytest.raises(ValidationError):
                validate_version(version)

    def test_validate_version_invalid_start(self):
        """Test validation fails for invalid starting character."""
        invalid_starts = [
            "-1.0.0",
            ".1.0.0",
            ":1.0.0",
            "~1.0.0",
            "+1.0.0"
        ]
        
        for version in invalid_starts:
            with pytest.raises(ValidationError):
                validate_version(version)

    def test_validate_package_list_valid(self):
        """Test validation of valid package lists."""
        valid_packages = ["pkg1", "pkg2", "lib-dev"]
        result = validate_package_list(valid_packages)
        
        assert result == valid_packages

    def test_validate_package_list_empty(self):
        """Test validation fails for empty package list."""
        with pytest.raises(ValidationError, match="Package list cannot be empty"):
            validate_package_list([])

    def test_validate_package_list_with_invalid_packages(self):
        """Test validation fails when list contains invalid packages."""
        mixed_packages = ["valid-pkg", "INVALID", "another-valid"]
        
        with pytest.raises(ValidationError, match="Invalid package names found"):
            validate_package_list(mixed_packages)

    def test_validate_package_list_all_invalid(self):
        """Test validation fails when all packages are invalid."""
        invalid_packages = ["INVALID1", "INVALID2", ""]
        
        with pytest.raises(ValidationError, match="Invalid package names found"):
            validate_package_list(invalid_packages)

    def test_validate_package_list_single_valid(self):
        """Test validation of single valid package in list."""
        result = validate_package_list(["valid-package"])
        assert result == ["valid-package"]

    def test_validate_package_list_single_invalid(self):
        """Test validation fails for single invalid package in list."""
        with pytest.raises(ValidationError):
            validate_package_list(["INVALID"])


class TestConfigValidation:
    """Test suite for configuration validation functions."""

    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        valid_config = {
            'custom_prefixes': ['test-', 'dev-'],
            'offline_mode': False,
            'removable_packages': ['pkg1', 'pkg2']
        }
        
        assert validate_config(valid_config) is True

    def test_validate_config_empty(self):
        """Test validation of empty configuration."""
        assert validate_config({}) is True

    def test_validate_config_invalid_type(self):
        """Test validation fails for non-dict config."""
        with pytest.raises(ConfigValidationError, match="must be a dictionary"):
            validate_config("not a dict")

        with pytest.raises(ConfigValidationError, match="must be a dictionary"):
            validate_config(["list", "instead"])

    def test_validate_config_invalid_custom_prefixes_type(self):
        """Test validation fails for invalid custom_prefixes type."""
        invalid_config = {
            'custom_prefixes': 'not a list'
        }
        
        with pytest.raises(ConfigValidationError, match="custom_prefixes.*must be a list"):
            validate_config(invalid_config)

    def test_validate_config_invalid_custom_prefixes_content(self):
        """Test validation fails for invalid custom_prefixes content."""
        # Non-string prefix
        invalid_config = {
            'custom_prefixes': ['valid-', 123, 'another-valid']
        }
        
        with pytest.raises(ConfigValidationError, match="custom_prefixes\\[1\\].*must be a string"):
            validate_config(invalid_config)

    def test_validate_config_empty_custom_prefix(self):
        """Test validation fails for empty custom prefix."""
        invalid_config = {
            'custom_prefixes': ['valid-', '', 'another-valid']
        }
        
        with pytest.raises(ConfigValidationError, match="custom_prefixes\\[1\\].*cannot be empty"):
            validate_config(invalid_config)

    def test_validate_config_invalid_custom_prefix_characters(self):
        """Test validation fails for invalid characters in custom prefix."""
        invalid_config = {
            'custom_prefixes': ['valid-', 'invalid@prefix', 'another-valid']
        }
        
        with pytest.raises(ConfigValidationError, match="must contain only alphanumeric characters"):
            validate_config(invalid_config)

    def test_validate_config_invalid_offline_mode_type(self):
        """Test validation fails for invalid offline_mode type."""
        invalid_config = {
            'offline_mode': 'not a boolean'
        }
        
        with pytest.raises(ConfigValidationError, match="offline_mode.*must be a boolean"):
            validate_config(invalid_config)

    def test_validate_config_invalid_removable_packages_type(self):
        """Test validation fails for invalid removable_packages type."""
        invalid_config = {
            'removable_packages': 'not a list'
        }
        
        with pytest.raises(ConfigValidationError, match="removable_packages.*must be a list"):
            validate_config(invalid_config)

    def test_validate_config_invalid_removable_packages_content(self):
        """Test validation fails for invalid removable_packages content."""
        # Non-string package
        invalid_config = {
            'removable_packages': ['valid-pkg', 123, 'another-pkg']
        }
        
        with pytest.raises(ConfigValidationError, match="removable_packages\\[1\\].*must be a string"):
            validate_config(invalid_config)

    def test_validate_config_empty_removable_package(self):
        """Test validation fails for empty removable package."""
        invalid_config = {
            'removable_packages': ['valid-pkg', '', 'another-pkg']
        }
        
        with pytest.raises(ConfigValidationError, match="removable_packages\\[1\\].*cannot be empty"):
            validate_config(invalid_config)

    def test_validate_config_partial_validation(self):
        """Test that only present fields are validated."""
        # Config with only some fields should still validate
        partial_config = {
            'custom_prefixes': ['test-']
            # Missing offline_mode and removable_packages
        }
        
        assert validate_config(partial_config) is True

    def test_validate_config_extra_fields_allowed(self):
        """Test that extra fields don't cause validation to fail."""
        config_with_extra = {
            'custom_prefixes': ['test-'],
            'offline_mode': True,
            'removable_packages': ['pkg1'],
            'extra_field': 'this should be ignored'
        }
        
        assert validate_config(config_with_extra) is True


class TestValidationIntegration:
    """Integration tests for validation functions."""

    def test_package_name_and_version_together(self):
        """Test validating package name and version together."""
        # Valid combination
        package_name = "test-package"
        version = "1.0.0-1ubuntu1"
        
        assert validate_package_name(package_name) is True
        assert validate_version(version) is True

    def test_package_list_with_versions(self):
        """Test that package list validation works with complex names."""
        packages = [
            "lib++12-dev",
            "python3.9-pip", 
            "gcc-9-base",
            "my-custom-pkg"
        ]
        
        result = validate_package_list(packages)
        assert result == packages

    def test_config_validation_realistic_scenario(self):
        """Test config validation with realistic configuration."""
        realistic_config = {
            'custom_prefixes': [
                'mycompany-',
                'dev-tools-',
                'internal_',  # Underscore should be rejected
                'test-'
            ],
            'offline_mode': False,
            'removable_packages': [
                'temporary-pkg',
                'dev-only-tool',
                'test-package'
            ],
            'force_confirmation_required': True,
            'auto_resolve_conflicts': True
        }
        
        # Should fail due to underscore in prefix
        with pytest.raises(ConfigValidationError):
            validate_config(realistic_config)

    def test_validation_error_messages_clarity(self):
        """Test that validation error messages are clear and helpful."""
        # Test package name error message
        try:
            validate_package_name("INVALID_NAME")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "alphanumeric character" in str(e)
            assert "lowercase letters" in str(e)

        # Test config error message
        try:
            validate_config({'custom_prefixes': 'not a list'})
            assert False, "Should have raised ConfigValidationError"
        except ConfigValidationError as e:
            assert "custom_prefixes" in str(e)
            assert "must be a list" in str(e)


class TestValidationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_package_name_boundary_lengths(self):
        """Test package names at boundary lengths."""
        # Exactly 2 characters (minimum)
        assert validate_package_name("ab") is True
        
        # Exactly 214 characters (maximum)
        max_name = "a" * 214
        assert validate_package_name(max_name) is True
        
        # 1 character (too short)
        with pytest.raises(ValidationError):
            validate_package_name("a")
        
        # 215 characters (too long)
        too_long = "a" * 215
        with pytest.raises(ValidationError):
            validate_package_name(too_long)

    def test_version_boundary_lengths(self):
        """Test versions at boundary lengths."""
        # Single character (minimum)
        assert validate_version("1") is True
        
        # Exactly 255 characters (maximum)
        max_version = "a" * 255
        assert validate_version(max_version) is True
        
        # 256 characters (too long)
        too_long = "a" * 256
        with pytest.raises(ValidationError):
            validate_version(too_long)

    def test_special_package_name_patterns(self):
        """Test special patterns that might be edge cases."""
        # Package names that might confuse regex
        special_patterns = [
            "lib64-something",
            "package+plus",
            "name.with.dots",
            "complex-name.version+extra",
            "a0a0a0",  # Alternating letters and numbers
            "name-123.456+extra.more"
        ]
        
        for name in special_patterns:
            assert validate_package_name(name) is True

    def test_special_version_patterns(self):
        """Test special version patterns that might be edge cases."""
        # Complex but valid version patterns
        special_versions = [
            "1:2.3.4-5ubuntu1",
            "0.1.2~git20200101.abcdef",
            "1.0+really2.0-1",
            "1.2.3-4+deb10u1",
            "2020.01.01+dfsg-1",
            "1.0.0~alpha1+git123"
        ]
        
        for version in special_versions:
            assert validate_version(version) is True

    def test_none_and_null_inputs(self):
        """Test handling of None and null-like inputs."""
        with pytest.raises(ValidationError):
            validate_package_name(None)

        with pytest.raises(ValidationError):
            validate_version(None)

        with pytest.raises(ValidationError):
            validate_package_list(None)

        with pytest.raises(ConfigValidationError):
            validate_config(None)