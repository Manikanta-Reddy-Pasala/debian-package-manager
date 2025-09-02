"""DPKG interface for forced package operations."""

import subprocess
import time
import os
from typing import List, Optional, Tuple
from .models import Package, PackageStatus


class DPKGInterface:
    """Interface for direct DPKG operations and forced actions."""
    
    def __init__(self):
        """Initialize DPKG interface."""
        self.lock_files = [
            '/var/lib/dpkg/lock',
            '/var/lib/dpkg/lock-frontend',
            '/var/cache/apt/archives/lock'
        ]
    
    def force_remove(self, package: str, ignore_dependencies: bool = True) -> bool:
        """Force remove a package, ignoring dependencies if specified."""
        try:
            # Check and handle locks first
            if not self._handle_locks():
                print("Warning: Could not resolve package locks")
            
            cmd = ['sudo', 'dpkg', '--remove']
            
            if ignore_dependencies:
                cmd.append('--force-depends')
                cmd.append('--force-remove-essential')
            
            cmd.append(package)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                # Try with more aggressive force options
                return self._force_remove_aggressive(package)
                
        except Exception as e:
            print(f"Error force removing package {package}: {e}")
            return False
    
    def _force_remove_aggressive(self, package: str) -> bool:
        """Use most aggressive force removal options."""
        try:
            cmd = [
                'sudo', 'dpkg', '--remove',
                '--force-depends',
                '--force-remove-essential',
                '--force-remove-reinstreq',
                '--force-confmiss',
                '--force-confold',
                package
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error in aggressive force removal: {e}")
            return False
    
    def purge_package(self, package: str, force: bool = False) -> bool:
        """Purge a package completely, removing configuration files."""
        try:
            cmd = ['sudo', 'dpkg', '--purge']
            
            if force:
                cmd.extend([
                    '--force-depends',
                    '--force-remove-essential',
                    '--force-confmiss'
                ])
            
            cmd.append(package)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
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