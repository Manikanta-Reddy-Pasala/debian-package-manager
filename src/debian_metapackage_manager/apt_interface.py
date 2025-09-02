"""APT interface wrapper for safe package operations."""

import subprocess
import re
from typing import List, Optional, Dict, Tuple
from .interfaces import PackageInterface
from .models import Package, Conflict, PackageStatus
from .config import Config


class APTInterface(PackageInterface):
    """Wrapper around APT for safe package management operations."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize APT interface with safety configuration."""
        self.config = config or Config()
        self._cache_info = {}
    
    def install(self, package: str, version: Optional[str] = None) -> bool:
        """Install a package with optional version specification."""
        try:
            if version:
                package_spec = f"{package}={version}"
            else:
                package_spec = package
            
            # Use apt-get for installation
            cmd = ['sudo', 'apt-get', 'install', '-y', package_spec]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error installing package {package}: {e}")
            return False
    
    def remove_safe(self, package: str) -> bool:
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
            # Use standard apt-get remove (no dangerous force options)
            cmd = ['sudo', 'apt-get', 'remove', '-y', package]
            
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
    
    def get_dependencies(self, package: str) -> List[Package]:
        """Get dependencies for a package."""
        try:
            # Use apt-cache to get dependencies
            cmd = ['apt-cache', 'depends', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return []
            
            dependencies = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('Depends:'):
                    dep_name = line.split(':', 1)[1].strip()
                    # Remove version constraints and alternatives
                    dep_name = re.sub(r'\s*\([^)]*\)', '', dep_name)
                    dep_name = dep_name.split('|')[0].strip()
                    
                    if dep_name and not dep_name.startswith('<'):
                        dep_package = Package(
                            name=dep_name,
                            version="",  # Version will be resolved later
                            status=self._get_package_status(dep_name)
                        )
                        dependencies.append(dep_package)
            
            return dependencies
            
        except Exception as e:
            print(f"Error getting dependencies for {package}: {e}")
            return []
    
    def check_conflicts(self, package: str) -> List[Conflict]:
        """Check for conflicts when installing a package."""
        try:
            # Simulate installation to check for conflicts
            cmd = ['apt-get', 'install', '-s', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            conflicts = []
            if result.returncode != 0:
                # Parse output for conflict information
                output = result.stdout + result.stderr
                
                # Look for removal patterns
                removal_pattern = r'The following packages will be REMOVED:\s*\n\s*([^\n]+)'
                removal_match = re.search(removal_pattern, output, re.MULTILINE)
                
                if removal_match:
                    removed_packages = removal_match.group(1).split()
                    for removed_pkg in removed_packages:
                        conflict = Conflict(
                            package=Package(name=package, version=""),
                            conflicting_package=Package(name=removed_pkg, version=""),
                            reason="Package removal required for installation"
                        )
                        conflicts.append(conflict)
            
            return conflicts
            
        except Exception as e:
            print(f"Error checking conflicts for {package}: {e}")
            return []
    
    def is_installed(self, package: str) -> bool:
        """Check if a package is installed."""
        try:
            cmd = ['dpkg', '-l', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Check if package is actually installed (not just known)
                for line in result.stdout.split('\n'):
                    if line.startswith('ii'):  # 'ii' means installed
                        return True
            
            return False
            
        except Exception:
            return False
    
    def get_package_info(self, package: str) -> Optional[Package]:
        """Get detailed information about a package."""
        try:
            # Get package information
            cmd = ['apt-cache', 'show', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
            
            # Parse package information
            version = ""
            description = ""
            
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                elif line.startswith('Description:'):
                    description = line.split(':', 1)[1].strip()
            
            return Package(
                name=package,
                version=version,
                status=self._get_package_status(package)
            )
            
        except Exception as e:
            print(f"Error getting package info for {package}: {e}")
            return None
    
    def _get_package_status(self, package: str) -> PackageStatus:
        """Get the installation status of a package."""
        if self.is_installed(package):
            # Check if upgradable
            if self._is_upgradable(package):
                return PackageStatus.UPGRADABLE
            else:
                return PackageStatus.INSTALLED
        else:
            return PackageStatus.NOT_INSTALLED
    
    def _is_upgradable(self, package: str) -> bool:
        """Check if a package is upgradable."""
        try:
            cmd = ['apt', 'list', '--upgradable', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return package in result.stdout and 'upgradable' in result.stdout
            
        except Exception:
            return False
    
    def get_available_versions(self, package: str) -> List[str]:
        """Get available versions for a package."""
        try:
            cmd = ['apt-cache', 'policy', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return []
            
            versions = []
            in_version_table = False
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if 'Version table:' in line:
                    in_version_table = True
                    continue
                
                if in_version_table and line.startswith('***') or line.startswith('   '):
                    # Extract version number
                    version_match = re.search(r'(\d+[.\d]*[^\s]*)', line)
                    if version_match:
                        version = version_match.group(1)
                        if version not in versions:
                            versions.append(version)
            
            return versions
            
        except Exception as e:
            print(f"Error getting available versions for {package}: {e}")
            return []
    
    def update_package_cache(self) -> bool:
        """Update the APT package cache."""
        try:
            cmd = ['sudo', 'apt-get', 'update']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error updating package cache: {e}")
            return False
    
    def search_packages(self, query: str) -> List[str]:
        """Search for packages matching a query."""
        try:
            cmd = ['apt-cache', 'search', query]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return []
            
            packages = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    package_name = line.split(' - ')[0].strip()
                    packages.append(package_name)
            
            return packages
            
        except Exception as e:
            print(f"Error searching packages: {e}")
            return []