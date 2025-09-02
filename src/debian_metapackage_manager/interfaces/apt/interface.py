"""APT interface wrapper for safe package operations."""

import subprocess
import re
from typing import List, Optional, Dict, Tuple
from ..base import PackageInterface
from ...models import Package, Conflict, PackageStatus
from ...utils.logging import get_logger

logger = get_logger('interfaces.apt')


class APTInterface(PackageInterface):
    """Wrapper around APT for safe package management operations."""
    
    def __init__(self, config=None):
        """Initialize APT interface with safety configuration."""
        self.config = config
        self._cache_info = {}
    
    def install(self, package: str, version: Optional[str] = None) -> bool:
        """Install a package with optional version specification."""
        try:
            if version:
                package_spec = f"{package}={version}"
            else:
                package_spec = package
            
            logger.info(f"Installing package: {package_spec}")
            
            # Use apt-get for installation
            cmd = ['sudo', 'apt-get', 'install', '-y', package_spec]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully installed: {package}")
                return True
            else:
                logger.error(f"Failed to install {package}: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"Error installing package {package}: {e}")
            return False
    
    def remove(self, package: str, force: bool = False) -> bool:
        """Remove a package."""
        try:
            logger.info(f"Removing package: {package} (force={force})")
            
            # Use standard apt-get remove
            cmd = ['sudo', 'apt-get', 'remove', '-y', package]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully removed: {package}")
                return True
            else:
                logger.error(f"Failed to remove {package}: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"Error removing package {package}: {e}")
            return False
    
    def get_dependencies(self, package: str) -> List[Package]:
        """Get dependencies for a package."""
        try:
            logger.debug(f"Getting dependencies for: {package}")
            
            # Use apt-cache to get dependencies
            cmd = ['apt-cache', 'depends', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"Could not get dependencies for {package}")
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
            
            logger.debug(f"Found {len(dependencies)} dependencies for {package}")
            return dependencies
            
        except Exception as e:
            logger.error(f"Error getting dependencies for {package}: {e}")
            return []
    
    def check_conflicts(self, package: str) -> List[Conflict]:
        """Check for conflicts when installing a package."""
        try:
            logger.debug(f"Checking conflicts for: {package}")
            
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
            
            logger.debug(f"Found {len(conflicts)} conflicts for {package}")
            return conflicts
            
        except Exception as e:
            logger.error(f"Error checking conflicts for {package}: {e}")
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
            logger.debug(f"Getting package info for: {package}")
            
            # Get package information
            cmd = ['apt-cache', 'show', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"Package {package} not found")
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
            logger.error(f"Error getting package info for {package}: {e}")
            return None
    
    def get_available_versions(self, package: str) -> List[str]:
        """Get available versions for a package."""
        try:
            logger.debug(f"Getting available versions for: {package}")
            
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
                
                if in_version_table and (line.startswith('***') or line.startswith('   ')):
                    # Extract version number
                    version_match = re.search(r'(\d+[.\d]*[^\s]*)', line)
                    if version_match:
                        version = version_match.group(1)
                        if version not in versions:
                            versions.append(version)
            
            logger.debug(f"Found {len(versions)} versions for {package}")
            return versions
            
        except Exception as e:
            logger.error(f"Error getting available versions for {package}: {e}")
            return []
    
    def update_package_cache(self) -> bool:
        """Update the APT package cache."""
        try:
            logger.info("Updating APT package cache")
            cmd = ['sudo', 'apt-get', 'update']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("APT cache updated successfully")
                return True
            else:
                logger.error(f"Failed to update APT cache: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating package cache: {e}")
            return False
    
    def search_packages(self, query: str) -> List[str]:
        """Search for packages matching a query."""
        try:
            logger.debug(f"Searching packages for: {query}")
            
            cmd = ['apt-cache', 'search', query]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return []
            
            packages = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    package_name = line.split(' - ')[0].strip()
                    packages.append(package_name)
            
            logger.debug(f"Found {len(packages)} packages matching '{query}'")
            return packages
            
        except Exception as e:
            logger.error(f"Error searching packages: {e}")
            return []
    
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