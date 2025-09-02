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
        print("Switched to offline mode")
    
    def switch_to_online_mode(self) -> None:
        """Switch to online mode."""
        self.config.set_offline_mode(False)
        self._execute_artifactory_script("disable")
        print("Switched to online mode")
        
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
        
        # Default to online mode if everything is available
        return "online (latest versions)"
    
    def get_mode_status(self) -> ModeStatus:
        """Get comprehensive mode status information."""
        return ModeStatus(
            offline_mode=self.is_offline_mode(),
            network_available=self.network_checker.is_network_available(),
            repositories_accessible=self.network_checker.are_repositories_accessible(),
            config_offline_setting=self.config.is_offline_mode()
        )
    
    def get_package_version_for_mode(self, package_name: str) -> Optional[str]:
        """Get the appropriate package version based on current mode."""
        # In online mode, we don't pin versions, so return None to get latest
        # In offline mode, we also don't pin versions, so return None
        return None