"""Package validation utilities."""

import re
from typing import List
from ...exceptions import ValidationError


def validate_package_name(name: str) -> bool:
    """
    Validate a Debian package name.
    
    Package names must:
    - Be at least 2 characters long
    - Start with alphanumeric character
    - Contain only lowercase letters, digits, hyphens, and dots
    - Not end with hyphen or dot
    
    Args:
        name: Package name to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If package name is invalid
    """
    if not name:
        raise ValidationError("Package name cannot be empty")
    
    if len(name) < 2:
        raise ValidationError("Package name must be at least 2 characters long")
    
    if len(name) > 214:
        raise ValidationError("Package name cannot exceed 214 characters")
    
    # Check valid characters
    if not re.match(r'^[a-z0-9][a-z0-9+.-]*$', name):
        raise ValidationError(
            "Package name must start with alphanumeric character and contain only "
            "lowercase letters, digits, hyphens, dots, and plus signs"
        )
    
    # Cannot end with hyphen or dot
    if name.endswith(('-', '.')):
        raise ValidationError("Package name cannot end with hyphen or dot")
    
    # Cannot contain consecutive dots or hyphens
    if '..' in name or '--' in name:
        raise ValidationError("Package name cannot contain consecutive dots or hyphens")
    
    return True


def validate_version(version: str) -> bool:
    """
    Validate a Debian package version.
    
    Args:
        version: Version string to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If version is invalid
    """
    if not version:
        raise ValidationError("Version cannot be empty")
    
    if len(version) > 255:
        raise ValidationError("Version cannot exceed 255 characters")
    
    # Basic version format check
    # Debian versions can be complex, so we do basic validation
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9+.~:-]*$', version):
        raise ValidationError(
            "Version must start with alphanumeric character and contain only "
            "letters, digits, dots, hyphens, colons, tildes, and plus signs"
        )
    
    return True


def validate_package_list(packages: List[str]) -> List[str]:
    """
    Validate a list of package names.
    
    Args:
        packages: List of package names to validate
        
    Returns:
        List of valid package names
        
    Raises:
        ValidationError: If any package name is invalid
    """
    if not packages:
        raise ValidationError("Package list cannot be empty")
    
    valid_packages = []
    invalid_packages = []
    
    for package in packages:
        try:
            validate_package_name(package)
            valid_packages.append(package)
        except ValidationError as e:
            invalid_packages.append(f"{package}: {e.message}")
    
    if invalid_packages:
        raise ValidationError(
            f"Invalid package names found:\n" + "\n".join(invalid_packages)
        )
    
    return valid_packages