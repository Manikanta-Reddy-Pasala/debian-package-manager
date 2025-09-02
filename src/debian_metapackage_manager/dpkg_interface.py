"""DPKG interface for safe package operations."""

import subprocess
import time
import os
from typing import List, Optional, Tuple
from .models import Package, PackageStatus
from .config import Config


class DPKGInterface:
    """Interface for safe DPKG operations with prefix-based safety."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize DPKG interface with safety configuration."""
        self.config = config or Config()
        self.lock_files = [
            '/var/lib/dpkg/lock',
            '/var/lib/dpkg/lock-frontend',
            '/var/cache/apt/archives/lock'
        ]
    
    def safe_remove(self, package: str) -> bool:
        """Safely remove a package only if it has a custom prefix.
        
        This method enforces the safety-first approach by only removing
        packages that match configured custom prefixes.
        """
        # Safety check: only remove packages with custom prefixes
        if not self.config.can_remove_package(package):
            print(f"🚫 Cannot remove {package}: System package (no custom prefix)")
            print("   Only packages with configured custom prefixes can be removed.")
            print("   Add custom prefixes with: dpm config --add-prefix 'yourprefix-'")
            return False
        
        try:
            # Check and handle locks first
            if not self._handle_locks():
                print("Warning: Could not resolve package locks")
            
            # Use standard dpkg remove (no dangerous force options)
            cmd = ['sudo', 'dpkg', '--remove', package]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully removed custom package: {package}")
                return True
            else:
                print(f"❌ Failed to remove {package}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error removing package {package}: {e}")
            return False
    
    def safe_purge(self, package: str) -> bool:
        """Safely purge a package only if it has a custom prefix.
        
        This removes the package and its configuration files, but only
        for packages with configured custom prefixes.
        """
        # Safety check: only purge packages with custom prefixes
        if not self.config.can_remove_package(package):
            print(f"🚫 Cannot purge {package}: System package (no custom prefix)")
            print("   Only packages with configured custom prefixes can be purged.")
            return False
        
        try:
            # Use standard dpkg purge (no dangerous force options)
            cmd = ['sudo', 'dpkg', '--purge', package]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully purged custom package: {package}")
                return True
            else:
                print(f"❌ Failed to purge {package}: {result.stderr}")
                return False
            
        except Exception as e:
            print(f"Error purging package {package}: {e}")
            return False
    
    def fix_broken_packages(self) -> bool:
        """Attempt to fix broken package states."""
        try:
            # First try dpkg --configure -a
            cmd = ['sudo', 'dpkg', '--configure', '-a']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            
            # If that fails, try apt-get fix-broken
            cmd = ['sudo', 'apt-get', 'install', '-f', '-y']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error fixing broken packages: {e}")
            return False
    
    def detect_locks(self) -> List[str]:
        """Detect active package management locks."""
        active_locks = []
        
        for lock_file in self.lock_files:
            if os.path.exists(lock_file):
                try:
                    # Try to get lock file info
                    stat_info = os.stat(lock_file)
                    if stat_info.st_size > 0:  # Lock file has content
                        active_locks.append(lock_file)
                except OSError:
                    # File might be locked or inaccessible
                    active_locks.append(lock_file)
        
        return active_locks
    
    def _handle_locks(self, max_retries: int = 3, wait_time: int = 5) -> bool:
        """Handle package management locks with retry logic."""
        for attempt in range(max_retries):
            active_locks = self.detect_locks()
            
            if not active_locks:
                return True
            
            if attempt < max_retries - 1:
                print(f"Waiting for locks to be released (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                # Last attempt - try to force remove locks
                return self._force_remove_locks(active_locks)
        
        return False
    
    def _force_remove_locks(self, lock_files: List[str]) -> bool:
        """Force remove lock files (dangerous operation)."""
        try:
            for lock_file in lock_files:
                if os.path.exists(lock_file):
                    cmd = ['sudo', 'rm', '-f', lock_file]
                    subprocess.run(cmd, capture_output=True, text=True)
            
            # Wait a moment for system to stabilize
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"Error removing lock files: {e}")
            return False
    
    def get_package_status_detailed(self, package: str) -> Tuple[PackageStatus, str]:
        """Get detailed package status including error information."""
        try:
            cmd = ['dpkg', '-s', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse status from output
                for line in result.stdout.split('\n'):
                    if line.startswith('Status:'):
                        status_line = line.split(':', 1)[1].strip()
                        if 'installed' in status_line:
                            return PackageStatus.INSTALLED, "Package is properly installed"
                        elif 'config-files' in status_line:
                            return PackageStatus.NOT_INSTALLED, "Only configuration files remain"
                        elif 'half-configured' in status_line:
                            return PackageStatus.BROKEN, "Package is half-configured"
                        elif 'half-installed' in status_line:
                            return PackageStatus.BROKEN, "Package is half-installed"
                
                return PackageStatus.INSTALLED, "Package is installed"
            else:
                return PackageStatus.NOT_INSTALLED, "Package is not installed"
                
        except Exception as e:
            return PackageStatus.BROKEN, f"Error checking status: {e}"
    
    def list_broken_packages(self) -> List[Package]:
        """List packages in broken states."""
        try:
            cmd = ['dpkg', '-l']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            broken_packages = []
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('iU') or line.startswith('iF') or line.startswith('iH'):
                        # iU = unpacked, iF = half-configured, iH = half-installed
                        parts = line.split()
                        if len(parts) >= 3:
                            package_name = parts[1]
                            version = parts[2] if len(parts) > 2 else ""
                            
                            package = Package(
                                name=package_name,
                                version=version,
                                status=PackageStatus.BROKEN
                            )
                            broken_packages.append(package)
            
            return broken_packages
            
        except Exception as e:
            print(f"Error listing broken packages: {e}")
            return []
    
    def reconfigure_package(self, package: str) -> bool:
        """Reconfigure a package that's in a broken state."""
        try:
            cmd = ['sudo', 'dpkg-reconfigure', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error reconfiguring package {package}: {e}")
            return False
    
    def force_install_deb(self, deb_file_path: str) -> bool:
        """Force install a .deb file, ignoring dependencies."""
        try:
            if not os.path.exists(deb_file_path):
                print(f"DEB file not found: {deb_file_path}")
                return False
            
            cmd = [
                'sudo', 'dpkg', '-i',
                '--force-depends',
                '--force-conflicts',
                deb_file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error force installing DEB file: {e}")
            return False
    
    def get_installed_packages(self) -> List[Package]:
        """Get list of all installed packages."""
        try:
            cmd = ['dpkg', '-l']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            packages = []
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('ii'):  # Installed packages
                        parts = line.split()
                        if len(parts) >= 3:
                            package_name = parts[1]
                            version = parts[2]
                            
                            package = Package(
                                name=package_name,
                                version=version,
                                status=PackageStatus.INSTALLED
                            )
                            packages.append(package)
            
            return packages
            
        except Exception as e:
            print(f"Error getting installed packages: {e}")
            return []