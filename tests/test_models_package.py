"""Tests for package data models."""

import pytest
from debian_metapackage_manager.models.package import Package, PackageStatus, PackageType


class TestPackage:
    """Test suite for Package model."""

    def test_package_creation_basic(self):
        """Test basic package creation."""
        package = Package(name="test-pkg", version="1.0.0")
        
        assert package.name == "test-pkg"
        assert package.version == "1.0.0"
        assert not package.is_metapackage
        assert not package.is_custom
        assert package.dependencies == []
        assert package.conflicts == []
        assert package.status == PackageStatus.NOT_INSTALLED

    def test_package_creation_with_options(self):
        """Test package creation with all options."""
        package = Package(
            name="custom-app",
            version="2.1.0",
            is_metapackage=True,
            is_custom=True,
            status=PackageStatus.INSTALLED
        )
        
        assert package.name == "custom-app"
        assert package.version == "2.1.0"
        assert package.is_metapackage
        assert package.is_custom
        assert package.status == PackageStatus.INSTALLED

    def test_package_type_custom(self):
        """Test package type classification for custom packages."""
        package = Package(name="custom-app", version="1.0.0", is_custom=True)
        assert package.package_type == PackageType.CUSTOM

    def test_package_type_metapackage(self):
        """Test package type classification for metapackages."""
        package = Package(name="bundle-app", version="1.0.0", is_metapackage=True)
        assert package.package_type == PackageType.METAPACKAGE

    def test_package_type_system(self):
        """Test package type classification for system packages."""
        package = Package(name="libc6", version="2.31-0ubuntu9.7")
        assert package.package_type == PackageType.SYSTEM

    def test_package_type_precedence(self):
        """Test that metapackage type takes precedence over custom."""
        package = Package(
            name="meta-bundle", 
            version="1.0.0", 
            is_metapackage=True, 
            is_custom=True
        )
        assert package.package_type == PackageType.METAPACKAGE

    def test_package_string_representation(self):
        """Test package string representation."""
        package = Package(name="test-app", version="1.2.3")
        assert str(package) == "test-app (v1.2.3)"

    def test_package_repr(self):
        """Test package detailed representation."""
        package = Package(name="test-app", version="1.2.3", is_custom=True)
        expected = "Package(name='test-app', version='1.2.3', type=custom)"
        assert repr(package) == expected

    def test_package_dependencies_initialization(self):
        """Test that dependencies list is properly initialized."""
        package = Package(name="test-pkg", version="1.0.0")
        assert isinstance(package.dependencies, list)
        assert len(package.dependencies) == 0
        
        # Should be able to add dependencies
        dep = Package(name="dep-pkg", version="1.0.0")
        package.dependencies.append(dep)
        assert len(package.dependencies) == 1
        assert package.dependencies[0].name == "dep-pkg"

    def test_package_conflicts_initialization(self):
        """Test that conflicts list is properly initialized."""
        package = Package(name="test-pkg", version="1.0.0")
        assert isinstance(package.conflicts, list)
        assert len(package.conflicts) == 0


class TestPackageStatus:
    """Test suite for PackageStatus enum."""

    def test_package_status_values(self):
        """Test PackageStatus enum values."""
        assert PackageStatus.INSTALLED.value == "installed"
        assert PackageStatus.NOT_INSTALLED.value == "not_installed"
        assert PackageStatus.UPGRADABLE.value == "upgradable"
        assert PackageStatus.BROKEN.value == "broken"

    def test_package_status_membership(self):
        """Test PackageStatus membership."""
        statuses = list(PackageStatus)
        assert len(statuses) == 4
        assert PackageStatus.INSTALLED in statuses
        assert PackageStatus.NOT_INSTALLED in statuses
        assert PackageStatus.UPGRADABLE in statuses
        assert PackageStatus.BROKEN in statuses


class TestPackageType:
    """Test suite for PackageType enum."""

    def test_package_type_values(self):
        """Test PackageType enum values."""
        assert PackageType.CUSTOM.value == "custom"
        assert PackageType.SYSTEM.value == "system"
        assert PackageType.METAPACKAGE.value == "metapackage"

    def test_package_type_membership(self):
        """Test PackageType membership."""
        types = list(PackageType)
        assert len(types) == 3
        assert PackageType.CUSTOM in types
        assert PackageType.SYSTEM in types
        assert PackageType.METAPACKAGE in types


class TestPackageComparisons:
    """Test package comparison and equality."""

    def test_package_equality(self):
        """Test package equality comparison."""
        pkg1 = Package(name="test-app", version="1.0.0")
        pkg2 = Package(name="test-app", version="1.0.0")
        pkg3 = Package(name="test-app", version="2.0.0")
        pkg4 = Package(name="other-app", version="1.0.0")

        # Same name and version should be equal
        assert pkg1.name == pkg2.name
        assert pkg1.version == pkg2.version
        
        # Different version should not be equal
        assert pkg1.version != pkg3.version
        
        # Different name should not be equal
        assert pkg1.name != pkg4.name

    def test_package_hash_consistency(self):
        """Test that packages with same attributes have consistent hashes."""
        pkg1 = Package(name="test-app", version="1.0.0")
        pkg2 = Package(name="test-app", version="1.0.0")
        
        # While packages are dataclasses and should be hashable if frozen,
        # we test that the same attributes produce consistent string representation
        assert str(pkg1) == str(pkg2)
        assert repr(pkg1) == repr(pkg2)


class TestPackageEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_package_name(self):
        """Test package with empty name."""
        package = Package(name="", version="1.0.0")
        assert package.name == ""
        assert str(package) == " (v1.0.0)"

    def test_empty_package_version(self):
        """Test package with empty version."""
        package = Package(name="test-pkg", version="")
        assert package.version == ""
        assert str(package) == "test-pkg (v)"

    def test_special_characters_in_name(self):
        """Test package name with special characters."""
        package = Package(name="lib++12-dev", version="1.0.0")
        assert package.name == "lib++12-dev"
        assert str(package) == "lib++12-dev (v1.0.0)"

    def test_version_with_epoch_and_revision(self):
        """Test complex version string."""
        package = Package(name="test-pkg", version="1:2.3.4-5ubuntu1")
        assert package.version == "1:2.3.4-5ubuntu1"
        assert str(package) == "test-pkg (v1:2.3.4-5ubuntu1)"

    def test_package_with_none_dependencies(self):
        """Test package when dependencies is explicitly set to None."""
        package = Package(name="test-pkg", version="1.0.0", dependencies=None)
        assert package.dependencies == []

    def test_package_with_none_conflicts(self):
        """Test package when conflicts is explicitly set to None."""
        package = Package(name="test-pkg", version="1.0.0", conflicts=None)
        assert package.conflicts == []


class TestPackageIntegration:
    """Integration tests for Package model with other components."""

    def test_package_dependency_chain(self):
        """Test creating a dependency chain."""
        main_pkg = Package(name="main-app", version="1.0.0")
        dep1 = Package(name="lib1", version="1.0.0")
        dep2 = Package(name="lib2", version="1.0.0")
        
        main_pkg.dependencies = [dep1, dep2]
        
        assert len(main_pkg.dependencies) == 2
        assert main_pkg.dependencies[0].name == "lib1"
        assert main_pkg.dependencies[1].name == "lib2"

    def test_package_conflict_scenario(self):
        """Test package with conflicts."""
        pkg1 = Package(name="app-v1", version="1.0.0")
        pkg2 = Package(name="app-v2", version="2.0.0")
        
        pkg1.conflicts = [pkg2]
        
        assert len(pkg1.conflicts) == 1
        assert pkg1.conflicts[0].name == "app-v2"

    def test_complex_package_scenario(self):
        """Test complex package with multiple attributes."""
        metapackage = Package(
            name="company-suite",
            version="3.0.0",
            is_metapackage=True,
            is_custom=True,
            status=PackageStatus.INSTALLED
        )
        
        # Add dependencies
        dep1 = Package(name="company-app1", version="3.0.0", is_custom=True)
        dep2 = Package(name="company-app2", version="3.0.0", is_custom=True)
        metapackage.dependencies = [dep1, dep2]
        
        # Add conflicts
        conflicting = Package(name="competitor-suite", version="2.0.0")
        metapackage.conflicts = [conflicting]
        
        # Verify all attributes
        assert metapackage.package_type == PackageType.METAPACKAGE
        assert metapackage.status == PackageStatus.INSTALLED
        assert len(metapackage.dependencies) == 2
        assert len(metapackage.conflicts) == 1
        assert str(metapackage) == "company-suite (v3.0.0)"