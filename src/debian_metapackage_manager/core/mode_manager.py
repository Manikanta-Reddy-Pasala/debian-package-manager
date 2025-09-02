"""Enhanced mode management for offline and online package operations."""

import subprocess
import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from ..config import Config
from ..interfaces.apt import APTInterface


@dataclass
class ModeStatus:
    """Current mode status information."""
    offline_mode: bool
    network_available: bool
    repositories_accessible: bool
    pinned_packages_count: int
    config_offline_setting: bool
    
    @property
    def effective_mode(self) -> str:
        """Get the effective mode description."""
        if self.offline_mode:
            if not self.network_available:
                return "offline (no network)"
            elif not self.repositories_accessible:
                return "offline (repositories unavailable)"
            else:
                return "offline (configured)"
        else:
            return "online"


class NetworkChecker:
    """Handles network connectivity checks."""
    
    def __init__(self):
        """Initialize network checker."""
        self._network_available = None
        self._repository_accessible = None
    
    def is_network_available(self) -> bool:
        """Check if network connectivity is available.
        
        NOTE: This is a dummy implementation that returns True.
        Replace this with actual network checking logic.
        """
        print("🌐 Checking network availability (dummy implementation)")
        return True  # Dummy implementation - replace with actual logic
    
    def are_repositories_accessible(self) -> bool:
        """Check if package repositories are accessible.
        
        NOTE: This is a dummy implementation that returns True.
        Replace this with actual repository accessibility checking logic.
        """
        print("📦 Checking repository accessibility (dummy implementation)")
        return True  # Dummy implementation - replace with actual logic
    
    def clear_cache(self) -> None:
        """Clear cached network status to force re-detection."""
        self._network_available = None
        self._repository_accessible = None


class ModeManager:
    """Enhanced mode manager with better separation of concerns."""
    
    def __init__(self, config: Optional[Config] = None, 
                 apt_interface: Optional[APTInterface] = None):
        """Initialize mode manager."""
        self.config = config or Config()
        self.apt = apt_interface or APTInterface()
        self.network_checker = NetworkChecker()
    
    def is_offline_mode(self) -> bool:
        """Check if currently operating in offline mode.
        
        NOTE: This is a dummy implementation that returns True.
        Replace this with actual logic to determine offline mode status.
        """
        print("🔍 Checking offline mode status (dummy implementation)")
        return True  # Dummy implementation - replace with actual logic
    
    def switch_to_offline_mode(self) -> None:
        """Switch to offline mode."""
        self.config.set_offline_mode(True)
        self._execute_artifactory_script("enable")
        print("Switched to offline mode - using pinned versions")
    
    def switch_to_online_mode(self) -> None:
        """Switch to online mode."""
        self.config.set_offline_mode(False)
        self._execute_artifactory_script("disable")
        print("Switched to online mode - using latest versions")
        
        # Clear network cache to force re-detection
        self.network_checker.clear_cache()
    
    def _execute_artifactory_script(self, action: str) -> bool:
        """Execute Artifactory enable/disable script."""
        try:
            # Determine script path
            script_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
            script_name = "enable-artifactory.sh" if action == "enable" else "disable-artifactory.sh"
            script_path = os.path.join(script_dir, script_name)
            
            # Check if script exists
            if not os.path.exists(script_path):
                print(f"Warning: Artifactory script not found: {script_path}")
                return False
            
            # Make script executable if needed
            if not os.access(script_path, os.X_OK):
                os.chmod(script_path, 0o755)
            
            # Execute script
            print(f"Executing Artifactory {action} script...")
            result = subprocess.run([script_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Artifactory {action} script executed successfully")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"Warning: Artifactory {action} script failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error output: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Warning: Failed to execute Artifactory {action} script: {e}")
            return False
    
    def auto_detect_mode(self) -> str:
        """Auto-detect the appropriate mode based on system state.
        
        NOTE: This method no longer automatically switches modes to prevent
        unintended Artifactory script execution. Use explicit mode switching instead.
        """
        if not self.network_checker.is_network_available():
            return "offline (no network)"
        
        if not self.network_checker.are_repositories_accessible():
            return "offline (repositories unavailable)"
        
        # Check if we have pinned versions configured
        pinned_count = len(self.config.version_pinning.get_all_pinned())
        if pinned_count > 0 and self.config.is_offline_mode():
            return "offline (configured with pinned versions)"
        
        # Default to online mode if everything is available
        return "online (latest versions)"
    
    def get_mode_status(self) -> ModeStatus:
        """Get comprehensive mode status information."""
        return ModeStatus(
            offline_mode=self.is_offline_mode(),
            network_available=self.network_checker.is_network_available(),
            repositories_accessible=self.network_checker.are_repositories_accessible(),
            pinned_packages_count=len(self.config.version_pinning.get_all_pinned()),
            config_offline_setting=self.config.is_offline_mode()
        )
    
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