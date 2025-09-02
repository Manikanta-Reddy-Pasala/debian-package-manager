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
    
    def can_remove_package(self, package_name: str) -> bool:
        """Check if a package can be removed based on custom prefixes.
        
        Only packages with configured custom prefixes can be removed.
        System packages (without custom prefixes) are never removed.
        """
        custom_prefixes = self.get_custom_prefixes()
        
        # Check if package starts with any custom prefix
        for prefix in custom_prefixes:
            if package_name.startswith(prefix):
                return True
        
        # If no custom prefix matches, it's a system package - cannot remove
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