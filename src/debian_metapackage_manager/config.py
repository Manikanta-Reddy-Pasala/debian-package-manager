"""Configuration management for Debian Metapackage Manager."""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path

from .interfaces import ConfigInterface


class Config(ConfigInterface):
    """Main configuration management class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration with optional custom path."""
        self.config_path = config_path or self._get_default_config_path()
        self._config_data = self._load_config()
        self.package_prefixes = PackagePrefixes(self._config_data.get('custom_prefixes', []))
        self.version_pinning = VersionPinning(self._config_data.get('pinned_versions', {}))
        self.removable_packages = RemovablePackages(self._config_data.get('removable_packages', []))
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        home_dir = Path.home()
        config_dir = home_dir / '.config' / 'debian-package-manager'
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / 'config.json')
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load config from {self.config_path}: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default configuration."""
        default_config = {
            'custom_prefixes': [
                'mycompany-',
                'internal-',
                'custom-',
                'dev-',
                'local-',
                'meta-',
                'bundle-'
            ],
            'offline_mode': False,
            'pinned_versions': {},
            'removable_packages': [],
            'force_confirmation_required': True,
            'auto_resolve_conflicts': True
        }
        
        # Save default config
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save default config: {e}")
        
        return default_config
    
    def get_custom_prefixes(self) -> List[str]:
        """Get list of custom package prefixes."""
        return self.package_prefixes.get_prefixes()
    
    def is_offline_mode(self) -> bool:
        """Check if operating in offline mode."""
        return self._config_data.get('offline_mode', False)
    
    def get_pinned_version(self, package: str) -> Optional[str]:
        """Get pinned version for a package in offline mode."""
        return self.version_pinning.get_pinned_version(package)
    
    def set_offline_mode(self, offline: bool) -> None:
        """Set offline mode."""
        self._config_data['offline_mode'] = offline
        self._save_config()
    
    def add_custom_prefix(self, prefix: str) -> None:
        """Add a custom package prefix."""
        self.package_prefixes.add_prefix(prefix)
        self._config_data['custom_prefixes'] = self.package_prefixes.get_prefixes()
        self._save_config()
    
    def remove_custom_prefix(self, prefix: str) -> None:
        """Remove a custom package prefix."""
        self.package_prefixes.remove_prefix(prefix)
        self._config_data['custom_prefixes'] = self.package_prefixes.get_prefixes()
        self._save_config()
    
    def set_pinned_version(self, package: str, version: str) -> None:
        """Set pinned version for a package."""
        self.version_pinning.set_pinned_version(package, version)
        self._config_data['pinned_versions'] = self.version_pinning.get_all_pinned()
        self._save_config()
    
    def add_removable_package(self, package_name: str) -> None:
        """Add a package to the removable packages list."""
        # Prevent adding system-critical packages
        if self._is_system_critical_package(package_name):
            raise ValueError(f"Cannot add system-critical package '{package_name}' to removable list")
        
        self.removable_packages.add_package(package_name)
        self._config_data['removable_packages'] = self.removable_packages.get_packages()
        self._save_config()
    
    def remove_removable_package(self, package_name: str) -> None:
        """Remove a package from the removable packages list."""
        self.removable_packages.remove_package(package_name)
        self._config_data['removable_packages'] = self.removable_packages.get_packages()
        self._save_config()
    
    def get_removable_packages(self) -> List[str]:
        """Get list of packages that can be removed during conflicts."""
        return self.removable_packages.get_packages()
    
    def _is_system_critical_package(self, package_name: str) -> bool:
        """Check if a package is system-critical and should never be removable."""
        critical_packages = {
            'libc6', 'bash', 'coreutils', 'util-linux', 'systemd', 'init',
            'kernel', 'linux-image', 'grub', 'apt', 'dpkg', 'base-files',
            'base-passwd', 'login', 'passwd', 'sudo', 'openssh-server'
        }
        
        # Check exact match or if it starts with critical package names
        for critical in critical_packages:
            if package_name == critical or package_name.startswith(f"{critical}-"):
                return True
        
        return False
    
    def can_remove_package(self, package_name: str) -> bool:
        """Check if a package can be removed based on custom prefixes or removable packages list.
        
        Only packages with configured custom prefixes or explicitly listed as removable can be removed.
        System packages (without custom prefixes and not in removable list) are never removed.
        """
        # Check if package is explicitly listed as removable
        if self.removable_packages.is_removable(package_name):
            return True
            
        # Check if package starts with any custom prefix
        custom_prefixes = self.get_custom_prefixes()
        for prefix in custom_prefixes:
            if package_name.startswith(prefix):
                return True
        
        # If no custom prefix matches and not in removable list, it's a system package - cannot remove
        return False
    
    def save_config(self) -> None:
        """Public method to save configuration."""
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._config_data, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save config: {e}")


class PackagePrefixes:
    """Manages custom package prefixes for recognition."""
    
    def __init__(self, prefixes: List[str]):
        """Initialize with list of prefixes."""
        self._prefixes = list(prefixes) if prefixes else []
    
    def get_prefixes(self) -> List[str]:
        """Get all custom prefixes."""
        return self._prefixes.copy()
    
    def add_prefix(self, prefix: str) -> None:
        """Add a new prefix."""
        if prefix not in self._prefixes:
            self._prefixes.append(prefix)
    
    def remove_prefix(self, prefix: str) -> None:
        """Remove a prefix."""
        if prefix in self._prefixes:
            self._prefixes.remove(prefix)
    
    def is_custom_package(self, package_name: str) -> bool:
        """Check if package name matches any custom prefix."""
        return any(package_name.startswith(prefix) for prefix in self._prefixes)


class VersionPinning:
    """Manages pinned versions for offline mode."""
    
    def __init__(self, pinned_versions: Dict[str, str]):
        """Initialize with pinned versions dictionary."""
        self._pinned_versions = dict(pinned_versions) if pinned_versions else {}
    
    def get_pinned_version(self, package: str) -> Optional[str]:
        """Get pinned version for a package."""
        return self._pinned_versions.get(package)
    
    def set_pinned_version(self, package: str, version: str) -> None:
        """Set pinned version for a package."""
        self._pinned_versions[package] = version
    
    def remove_pinned_version(self, package: str) -> None:
        """Remove pinned version for a package."""
        self._pinned_versions.pop(package, None)
    
    def get_all_pinned(self) -> Dict[str, str]:
        """Get all pinned versions."""
        return self._pinned_versions.copy()
    
    def has_pinned_version(self, package: str) -> bool:
        """Check if package has a pinned version."""
        return package in self._pinned_versions


class RemovablePackages:
    """Manages packages that can be safely removed during conflicts."""
    
    def __init__(self, packages: List[str]):
        """Initialize with list of removable packages."""
        self._packages = list(packages) if packages else []
    
    def get_packages(self) -> List[str]:
        """Get all removable packages."""
        return self._packages.copy()
    
    def add_package(self, package_name: str) -> None:
        """Add a package to the removable list."""
        if package_name not in self._packages:
            self._packages.append(package_name)
    
    def remove_package(self, package_name: str) -> None:
        """Remove a package from the removable list."""
        if package_name in self._packages:
            self._packages.remove(package_name)
    
    def is_removable(self, package_name: str) -> bool:
        """Check if package is in the removable list."""
        return package_name in self._packages
    
    def clear_all(self) -> None:
        """Clear all removable packages."""
        self._packages.clear()