"""Mode management for offline and online package operations."""

from typing import Optional, List, Dict, Tuple
from .config import Config
from .apt_interface import APTInterface
from .models import Package


class ModeManager:
    """Manages offline and online modes for package operations."""
    
    def __init__(self, config: Optional[Config] = None, 
                 apt_interface: Optional[APTInterface] = None):
        """Initialize mode manager."""
        self.config = config or Config()
        self.apt = apt_interface or APTInterface()
        self._network_available = None
        self._repository_accessible = None
    
    def is_offline_mode(self) -> bool:
        """Check if currently operating in offline mode."""
        # Check configuration setting
        if self.config.is_offline_mode():
            return True
        
        # Auto-detect if network/repositories are unavailable
        if not self.is_network_available() or not self.are_repositories_accessible():
            print("Network or repositories unavailable, switching to offline mode")
            return True
        
        return False
    
    def is_network_available(self) -> bool:
        """Check if network connectivity is available."""
        if self._network_available is not None:
            return self._network_available
        
        try:
            import subprocess
            # Try to ping a reliable DNS server
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '3', '8.8.8.8'],
                capture_output=True,
                timeout=5
            )
            self._network_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self._network_available = False
        
        return self._network_available
    
    def are_repositories_accessible(self) -> bool:
        """Check if package repositories are accessible."""
        if self._repository_accessible is not None:
            return self._repository_accessible
        
        try:
            # Try to update package cache (dry run)
            import subprocess
            result = subprocess.run(
                ['apt-get', 'update', '--dry-run'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._repository_accessible = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self._repository_accessible = False
        
        return self._repository_accessible
    
    def switch_to_offline_mode(self) -> None:
        """Switch to offline mode."""
        self.config.set_offline_mode(True)
        print("Switched to offline mode - using pinned versions")
    
    def switch_to_online_mode(self) -> None:
        """Switch to online mode."""
        if self.is_network_available() and self.are_repositories_accessible():
            self.config.set_offline_mode(False)
            print("Switched to online mode - using latest versions")
        else:
            print("Cannot switch to online mode - network or repositories unavailable")
    
    def get_package_version_for_mode(self, package_name: str) -> Optional[str]:
        """Get the appropriate package version based on current mode."""
        if self.is_offline_mode():
            return self._get_pinned_version(package_name)
        else:
            return self._get_latest_version(package_name)
    
    def _get_pinned_version(self, package_name: str) -> Optional[str]:
        """Get pinned version for offline mode."""
        pinned_version = self.config.get_pinned_version(package_name)
        
        if pinned_version:
            return pinned_version
        
        # If no pinned version, try to get currently installed version
        if self.apt.is_installed(package_name):
            package_info = self.apt.get_package_info(package_name)
            if package_info:
                return package_info.version
        
        # Fallback: try to get any available version from local cache
        available_versions = self.apt.get_available_versions(package_name)
        if available_versions:
            return available_versions[0]  # Return first available version
        
        return None
    
    def _get_latest_version(self, package_name: str) -> Optional[str]:
        """Get latest version for online mode."""
        try:
            # Update package cache first
            self.apt.update_package_cache()
            
            # Get package info which should have latest version
            package_info = self.apt.get_package_info(package_name)
            if package_info:
                return package_info.version
            
            return None
            
        except Exception as e:
            print(f"Error getting latest version for {package_name}: {e}")
            # Fallback to pinned version if available
            return self._get_pinned_version(package_name)
    
    def resolve_metapackage_versions(self, metapackage_name: str) -> Dict[str, str]:
        """Resolve versions for all packages in a metapackage."""
        versions = {}
        
        # Get all dependencies of the metapackage
        dependencies = self.apt.get_dependencies(metapackage_name)
        
        # Add the metapackage itself
        all_packages = [metapackage_name] + [dep.name for dep in dependencies]
        
        for package_name in all_packages:
            version = self.get_package_version_for_mode(package_name)
            if version:
                versions[package_name] = version
        
        return versions
    
    def validate_pinned_versions(self) -> Tuple[bool, List[str]]:
        """Validate that all pinned versions are available."""
        issues = []
        all_pinned = self.config.version_pinning.get_all_pinned()
        
        for package_name, pinned_version in all_pinned.items():
            available_versions = self.apt.get_available_versions(package_name)
            
            if not available_versions:
                issues.append(f"Package {package_name} not found in repositories")
            elif pinned_version not in available_versions:
                issues.append(f"Pinned version {pinned_version} not available for {package_name}")
        
        return len(issues) == 0, issues
    
    def create_offline_snapshot(self, packages: List[str]) -> Dict[str, str]:
        """Create a snapshot of current package versions for offline mode."""
        snapshot = {}
        
        for package_name in packages:
            if self.apt.is_installed(package_name):
                package_info = self.apt.get_package_info(package_name)
                if package_info:
                    snapshot[package_name] = package_info.version
                    # Save as pinned version
                    self.config.set_pinned_version(package_name, package_info.version)
        
        print(f"Created offline snapshot for {len(snapshot)} packages")
        return snapshot
    
    def restore_from_snapshot(self, snapshot: Dict[str, str]) -> bool:
        """Restore package versions from a snapshot."""
        try:
            for package_name, version in snapshot.items():
                self.config.set_pinned_version(package_name, version)
            
            print(f"Restored pinned versions for {len(snapshot)} packages")
            return True
            
        except Exception as e:
            print(f"Error restoring from snapshot: {e}")
            return False
    
    def get_mode_status(self) -> Dict[str, any]:
        """Get current mode status information."""
        return {
            'offline_mode': self.is_offline_mode(),
            'network_available': self.is_network_available(),
            'repositories_accessible': self.are_repositories_accessible(),
            'pinned_packages_count': len(self.config.version_pinning.get_all_pinned()),
            'config_offline_setting': self.config.is_offline_mode()
        }
    
    def auto_detect_mode(self) -> str:
        """Auto-detect the appropriate mode based on system state."""
        if not self.is_network_available():
            self.switch_to_offline_mode()
            return "offline (no network)"
        
        if not self.are_repositories_accessible():
            self.switch_to_offline_mode()
            return "offline (repositories unavailable)"
        
        # Check if we have pinned versions configured
        pinned_count = len(self.config.version_pinning.get_all_pinned())
        if pinned_count > 0 and self.config.is_offline_mode():
            return "offline (configured with pinned versions)"
        
        # Default to online mode if everything is available
        self.switch_to_online_mode()
        return "online (latest versions)"
    
    def prepare_for_offline_operation(self, packages: List[str]) -> bool:
        """Prepare system for offline operation by ensuring pinned versions."""
        missing_pins = []
        
        for package_name in packages:
            if not self.config.version_pinning.has_pinned_version(package_name):
                # Try to get current installed version
                if self.apt.is_installed(package_name):
                    package_info = self.apt.get_package_info(package_name)
                    if package_info:
                        self.config.set_pinned_version(package_name, package_info.version)
                    else:
                        missing_pins.append(package_name)
                else:
                    missing_pins.append(package_name)
        
        if missing_pins:
            print(f"Warning: No pinned versions available for: {', '.join(missing_pins)}")
            return False
        
        return True
    
    def clear_network_cache(self) -> None:
        """Clear cached network status to force re-detection."""
        self._network_available = None
        self._repository_accessible = None