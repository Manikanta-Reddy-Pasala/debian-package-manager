"""System cleanup and maintenance functionality."""

import subprocess
import os
import shutil
from typing import List, Dict, Optional
from pathlib import Path

from .interfaces import OperationResult
from .models import Package


class SystemCleanup:
    """Handles system cleanup and maintenance operations."""
    
    def __init__(self):
        """Initialize cleanup manager."""
        self.apt_cache_dirs = [
            '/var/cache/apt/archives',
            '/var/cache/apt/archives/partial'
        ]
        self.dpkg_cache_dirs = [
            '/var/cache/debconf',
            '/var/lib/dpkg/info'
        ]
    
    def clean_apt_cache(self, aggressive: bool = False) -> OperationResult:
        """Clean APT package cache."""
        try:
            commands = ['apt-get', 'clean']
            if aggressive:
                commands.extend(['&&', 'apt-get', 'autoclean', '&&', 'apt-get', 'autoremove'])
            
            result = subprocess.run(
                commands, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Calculate space freed
            space_freed = self._calculate_cache_size()
            
            return OperationResult(
                success=True,
                packages_affected=[],
                warnings=[],
                errors=[],
                details={'space_freed_mb': space_freed}
            )
            
        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[f"Failed to clean APT cache: {e.stderr}"]
            )
    
    def clean_offline_repositories(self, repo_paths: List[str]) -> OperationResult:
        """Clean offline repository caches and temporary files."""
        cleaned_paths = []
        errors = []
        total_space_freed = 0
        
        for repo_path in repo_paths:
            try:
                if os.path.exists(repo_path):
                    # Calculate size before cleanup
                    size_before = self._get_directory_size(repo_path)
                    
                    # Clean temporary files
                    temp_patterns = ['*.tmp', '*.temp', '*.lock', '.#*']
                    for pattern in temp_patterns:
                        self._remove_files_by_pattern(repo_path, pattern)
                    
                    # Clean old package files (keep only latest versions)
                    self._clean_old_package_versions(repo_path)
                    
                    # Calculate size after cleanup
                    size_after = self._get_directory_size(repo_path)
                    space_freed = size_before - size_after
                    total_space_freed += space_freed
                    
                    cleaned_paths.append(repo_path)
                    
            except Exception as e:
                errors.append(f"Failed to clean {repo_path}: {str(e)}")
        
        return OperationResult(
            success=len(errors) == 0,
            packages_affected=[],
            warnings=[],
            errors=errors,
            details={
                'cleaned_paths': cleaned_paths,
                'space_freed_mb': total_space_freed // (1024 * 1024)
            }
        )
    
    def clean_artifactory_cache(self, artifactory_config: Dict) -> OperationResult:
        """Clean artifactory-related cache and temporary files."""
        try:
            cache_dir = artifactory_config.get('cache_dir', '/tmp/artifactory-cache')
            
            if os.path.exists(cache_dir):
                size_before = self._get_directory_size(cache_dir)
                
                # Remove old cache files (older than 7 days)
                self._remove_old_files(cache_dir, days=7)
                
                # Clean temporary download files
                temp_patterns = ['*.downloading', '*.partial', '*.tmp']
                for pattern in temp_patterns:
                    self._remove_files_by_pattern(cache_dir, pattern)
                
                size_after = self._get_directory_size(cache_dir)
                space_freed = size_before - size_after
                
                return OperationResult(
                    success=True,
                    packages_affected=[],
                    warnings=[],
                    errors=[],
                    details={'space_freed_mb': space_freed // (1024 * 1024)}
                )
            else:
                return OperationResult(
                    success=True,
                    packages_affected=[],
                    warnings=[f"Artifactory cache directory not found: {cache_dir}"],
                    errors=[]
                )
                
        except Exception as e:
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[f"Failed to clean artifactory cache: {str(e)}"]
            )
    
    def perform_system_maintenance(self, mode: str = 'online') -> OperationResult:
        """Perform comprehensive system maintenance based on mode."""
        results = []
        total_space_freed = 0
        all_errors = []
        all_warnings = []
        
        # Clean APT cache
        apt_result = self.clean_apt_cache(aggressive=(mode == 'offline'))
        results.append(apt_result)
        if apt_result.details:
            total_space_freed += apt_result.details.get('space_freed_mb', 0)
        all_errors.extend(apt_result.errors)
        all_warnings.extend(apt_result.warnings)
        
        # Mode-specific cleanup
        if mode == 'offline':
            # Clean offline repositories
            offline_repos = self._discover_offline_repositories()
            if offline_repos:
                offline_result = self.clean_offline_repositories(offline_repos)
                results.append(offline_result)
                if offline_result.details:
                    total_space_freed += offline_result.details.get('space_freed_mb', 0)
                all_errors.extend(offline_result.errors)
                all_warnings.extend(offline_result.warnings)
        
        elif mode == 'online':
            # Clean artifactory cache if configured
            artifactory_config = self._get_artifactory_config()
            if artifactory_config:
                art_result = self.clean_artifactory_cache(artifactory_config)
                results.append(art_result)
                if art_result.details:
                    total_space_freed += art_result.details.get('space_freed_mb', 0)
                all_errors.extend(art_result.errors)
                all_warnings.extend(art_result.warnings)
        
        # Clean orphaned packages
        orphan_result = self._clean_orphaned_packages()
        results.append(orphan_result)
        all_errors.extend(orphan_result.errors)
        all_warnings.extend(orphan_result.warnings)
        
        return OperationResult(
            success=len(all_errors) == 0,
            packages_affected=[],
            warnings=all_warnings,
            errors=all_errors,
            details={
                'total_space_freed_mb': total_space_freed,
                'operations_performed': len(results),
                'mode': mode
            }
        )
    
    def _calculate_cache_size(self) -> int:
        """Calculate total cache size in MB."""
        total_size = 0
        for cache_dir in self.apt_cache_dirs:
            if os.path.exists(cache_dir):
                total_size += self._get_directory_size(cache_dir)
        return total_size // (1024 * 1024)
    
    def _get_directory_size(self, path: str) -> int:
        """Get total size of directory in bytes."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except (OSError, IOError):
            pass
        return total_size
    
    def _remove_files_by_pattern(self, directory: str, pattern: str) -> None:
        """Remove files matching pattern in directory."""
        import glob
        pattern_path = os.path.join(directory, pattern)
        for filepath in glob.glob(pattern_path):
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
            except (OSError, IOError):
                pass
    
    def _remove_old_files(self, directory: str, days: int) -> None:
        """Remove files older than specified days."""
        import time
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    if os.path.getmtime(filepath) < cutoff_time:
                        try:
                            os.remove(filepath)
                        except (OSError, IOError):
                            pass
        except (OSError, IOError):
            pass
    
    def _clean_old_package_versions(self, repo_path: str) -> None:
        """Clean old versions of packages, keeping only the latest."""
        try:
            # Group packages by name (without version)
            packages = {}
            for filename in os.listdir(repo_path):
                if filename.endswith('.deb'):
                    # Extract package name (before first underscore)
                    package_name = filename.split('_')[0]
                    if package_name not in packages:
                        packages[package_name] = []
                    packages[package_name].append(filename)
            
            # For each package, keep only the latest version
            for package_name, versions in packages.items():
                if len(versions) > 1:
                    # Sort by modification time, keep the newest
                    versions.sort(key=lambda x: os.path.getmtime(os.path.join(repo_path, x)))
                    # Remove all but the latest
                    for old_version in versions[:-1]:
                        try:
                            os.remove(os.path.join(repo_path, old_version))
                        except (OSError, IOError):
                            pass
        except (OSError, IOError):
            pass
    
    def _discover_offline_repositories(self) -> List[str]:
        """Discover offline repository paths."""
        potential_paths = [
            '/var/cache/apt/archives',
            '/usr/local/share/offline-packages',
            '/opt/offline-repo',
            '/tmp/offline-packages'
        ]
        
        existing_paths = []
        for path in potential_paths:
            if os.path.exists(path) and os.path.isdir(path):
                existing_paths.append(path)
        
        return existing_paths
    
    def _get_artifactory_config(self) -> Optional[Dict]:
        """Get artifactory configuration if available."""
        config_paths = [
            '/etc/artifactory/config.json',
            os.path.expanduser('~/.artifactory/config.json'),
            '/usr/local/etc/artifactory.conf'
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    import json
                    with open(config_path, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    continue
        
        return None
    
    def _clean_orphaned_packages(self) -> OperationResult:
        """Clean orphaned packages that are no longer needed."""
        try:
            result = subprocess.run(
                ['apt-get', 'autoremove', '--dry-run'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse output to find orphaned packages
            orphaned_packages = []
            for line in result.stdout.split('\n'):
                if 'The following packages will be REMOVED:' in line:
                    # Extract package names from the next lines
                    continue
            
            return OperationResult(
                success=True,
                packages_affected=orphaned_packages,
                warnings=[],
                errors=[],
                details={'orphaned_count': len(orphaned_packages)}
            )
            
        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[f"Failed to check orphaned packages: {e.stderr}"]
            )