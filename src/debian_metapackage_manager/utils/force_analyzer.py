"""Enhanced dependency analysis for force operations."""

from typing import List, Set, Dict, Tuple, Optional
from ..models import Package, PackageStatus
from ..config import Config
from ..interfaces.apt import APTInterface
from ..interfaces.dpkg import DPKGInterface
from ..core.classifier import PackageClassifier
import subprocess


class ForceOperationAnalyzer:
    """Analyzes dependencies and conflicts for force operations."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize analyzer."""
        self.config = config or Config()
        self.apt = APTInterface()
        self.dpkg = DPKGInterface()
        self.classifier = PackageClassifier(self.config)
    
    def analyze_force_install_impact(self, package_name: str, version: Optional[str] = None) -> Dict:
        """Analyze the impact of force installing a package."""
        print(f"Analyzing force install impact for {package_name}...")
        
        # Get packages that would be removed due to conflicts
        conflicts_to_remove = self._get_conflicting_packages(package_name, version)
        
        # Get dependencies that would be installed
        new_dependencies = self._get_new_dependencies(package_name, version)
        
        # Calculate custom packages that might be affected
        custom_packages_at_risk = self._get_custom_packages_at_risk(conflicts_to_remove)
        
        # Determine packages we can safely mark as manual to preserve them
        preservable_packages = self._get_preservable_packages(conflicts_to_remove)
        
        return {
            'target_package': package_name,
            'target_version': version,
            'conflicts_to_remove': conflicts_to_remove,
            'new_dependencies': new_dependencies,
            'custom_packages_at_risk': custom_packages_at_risk,
            'preservable_packages': preservable_packages,
            'requires_confirmation': len(conflicts_to_remove) > 0,
            'protection_strategy': self._create_protection_strategy(preservable_packages)
        }
    
    def analyze_force_remove_impact(self, package_name: str) -> Dict:
        """Analyze the impact of force removing a package."""
        print(f"Analyzing force remove impact for {package_name}...")
        
        # Get dependencies that would be removed
        dependencies_to_remove = self._get_dependencies_to_remove(package_name)
        
        # Get packages that depend on this package (reverse dependencies)
        dependents_affected = self._get_reverse_dependencies(package_name)
        
        # Calculate custom packages that might be affected
        custom_packages_at_risk = self._get_custom_packages_in_list(dependencies_to_remove + dependents_affected)
        
        # Determine packages we can mark as manual to preserve them
        preservable_packages = self._get_preservable_packages(dependents_affected)
        
        return {
            'target_package': package_name,
            'dependencies_to_remove': dependencies_to_remove,
            'dependents_affected': dependents_affected,
            'custom_packages_at_risk': custom_packages_at_risk,
            'preservable_packages': preservable_packages,
            'requires_confirmation': len(dependencies_to_remove) > 0 or len(dependents_affected) > 0,
            'protection_strategy': self._create_protection_strategy(preservable_packages)
        }
    
    def _get_conflicting_packages(self, package_name: str, version: Optional[str] = None) -> List[Package]:
        """Get packages that conflict with the target package."""
        conflicts = []
        
        try:
            # Use apt to simulate installation and get conflicts
            package_info = self.apt.get_package_info(package_name)
            if package_info and hasattr(package_info, 'conflicts'):
                for conflict in package_info.conflicts:
                    if self.apt.is_installed(conflict):
                        conflict_info = self.apt.get_package_info(conflict)
                        if conflict_info:
                            conflicts.append(conflict_info)
            
            # Also check for packages that would be replaced
            # This requires more complex APT analysis
            conflicts.extend(self._get_packages_to_be_replaced(package_name, version))
            
        except Exception as e:
            print(f"Warning: Could not analyze conflicts for {package_name}: {e}")
        
        return conflicts
    
    def _get_packages_to_be_replaced(self, package_name: str, version: Optional[str] = None) -> List[Package]:
        """Get packages that would be replaced during installation."""
        replacements = []
        
        try:
            import subprocess
            import re
            
            # Prepare command to simulate installation
            if version:
                package_spec = f"{package_name}={version}"
            else:
                package_spec = package_name
            
            cmd = ['apt-get', 'install', '-s', package_spec]  # -s for simulation
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse output for packages that would be removed
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'The following packages will be REMOVED:' in line:
                        # Extract package names from the removal line and subsequent lines
                        idx = lines.index(line)
                        removal_text = ' '.join(lines[idx:idx+10])  # Get following lines
                        # Extract package names (basic regex)
                        removed_packages = re.findall(r'\b([a-zA-Z0-9][a-zA-Z0-9+\-\.]+)\b', removal_text)
                        for pkg_name in removed_packages:
                            if pkg_name != package_name and self.apt.is_installed(pkg_name):
                                pkg_info = self.apt.get_package_info(pkg_name)
                                if pkg_info:
                                    replacements.append(pkg_info)
        
        except Exception as e:
            print(f"Warning: Could not simulate installation for {package_name}: {e}")
        
        return replacements
    
    def _get_new_dependencies(self, package_name: str, version: Optional[str] = None) -> List[Package]:
        """Get new dependencies that would be installed."""
        new_deps = []
        
        try:
            import subprocess
            import re
            
            # Prepare command to simulate installation
            if version:
                package_spec = f"{package_name}={version}"
            else:
                package_spec = package_name
            
            cmd = ['apt-get', 'install', '-s', package_spec]  # -s for simulation
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse output for new packages to be installed
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'The following NEW packages will be installed:' in line:
                        # Extract package names
                        idx = lines.index(line)
                        install_text = ' '.join(lines[idx:idx+10])
                        new_packages = re.findall(r'\b([a-zA-Z0-9][a-zA-Z0-9+\-\.]+)\b', install_text)
                        for pkg_name in new_packages:
                            if pkg_name != package_name and not self.apt.is_installed(pkg_name):
                                # Create package object for new dependency
                                new_deps.append(Package(
                                    name=pkg_name,
                                    version="",  # Version will be determined during install
                                    is_metapackage=self.classifier.is_metapackage(pkg_name),
                                    is_custom=self.classifier.is_custom_package(pkg_name),
                                    status=PackageStatus.AVAILABLE
                                ))
        
        except Exception as e:
            print(f"Warning: Could not analyze new dependencies for {package_name}: {e}")
        
        return new_deps
    
    def _get_dependencies_to_remove(self, package_name: str) -> List[Package]:
        """Get dependencies that would be removed with the package."""
        deps_to_remove = []
        
        try:
            import subprocess
            import re
            
            cmd = ['apt-get', 'remove', '-s', package_name]  # -s for simulation
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse output for packages that would be removed
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'The following packages will be REMOVED:' in line:
                        idx = lines.index(line)
                        removal_text = ' '.join(lines[idx:idx+10])
                        removed_packages = re.findall(r'\b([a-zA-Z0-9][a-zA-Z0-9+\-\.]+)\b', removal_text)
                        for pkg_name in removed_packages:
                            if pkg_name != package_name and self.apt.is_installed(pkg_name):
                                pkg_info = self.apt.get_package_info(pkg_name)
                                if pkg_info:
                                    deps_to_remove.append(pkg_info)
        
        except Exception as e:
            print(f"Warning: Could not analyze dependencies to remove for {package_name}: {e}")
        
        return deps_to_remove
    
    def _get_reverse_dependencies(self, package_name: str) -> List[Package]:
        """Get packages that depend on the target package."""
        reverse_deps = []
        
        try:
            import subprocess
            
            # Use apt-cache to find reverse dependencies
            cmd = ['apt-cache', 'rdepends', '--installed', package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('Reverse Depends:'):
                        pkg_name = line.strip()
                        if pkg_name != package_name and self.apt.is_installed(pkg_name):
                            pkg_info = self.apt.get_package_info(pkg_name)
                            if pkg_info:
                                reverse_deps.append(pkg_info)
        
        except Exception as e:
            print(f"Warning: Could not find reverse dependencies for {package_name}: {e}")
        
        return reverse_deps
    
    def _get_custom_packages_at_risk(self, packages: List[Package]) -> List[Package]:
        """Filter packages to find custom packages at risk."""
        return [pkg for pkg in packages if self.classifier.is_custom_package(pkg.name)]
    
    def _get_custom_packages_in_list(self, packages: List[Package]) -> List[Package]:
        """Filter packages to find custom packages in the list."""
        return [pkg for pkg in packages if self.classifier.is_custom_package(pkg.name)]
    
    def _get_preservable_packages(self, packages: List[Package]) -> List[Package]:
        """Get packages that can be marked as manually installed to preserve them."""
        preservable = []
        
        for pkg in packages:
            if self.classifier.is_custom_package(pkg.name):
                # Custom packages can usually be preserved by marking as manual
                preservable.append(pkg)
        
        return preservable
    
    def _create_protection_strategy(self, preservable_packages: List[Package]) -> Dict:
        """Create a strategy to protect custom packages during force operations."""
        return {
            'mark_as_manual': [pkg.name for pkg in preservable_packages],
            'backup_before_operation': True,
            'preserve_custom_configs': True
        }
    
    def apply_protection_strategy(self, strategy: Dict) -> bool:
        """Apply protection strategy before force operation."""
        try:
            # Mark packages as manually installed to prevent auto-removal
            if strategy.get('mark_as_manual'):
                for pkg_name in strategy['mark_as_manual']:
                    cmd = ['sudo', 'apt-mark', 'manual', pkg_name]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"✅ Marked {pkg_name} as manually installed to prevent auto-removal")
                    else:
                        print(f"⚠️  Warning: Could not mark {pkg_name} as manual: {result.stderr}")
            
            return True
        
        except Exception as e:
            print(f"⚠️  Warning: Could not apply protection strategy: {e}")
            return False
    
    def mark_package_as_manual(self, package_name: str) -> bool:
        """Mark a single package as manually installed."""
        try:
            cmd = ['sudo', 'apt-mark', 'manual', package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Marked {package_name} as manually installed")
                return True
            else:
                print(f"⚠️  Warning: Could not mark {package_name} as manual: {result.stderr}")
                return False
        except Exception as e:
            print(f"⚠️  Error marking {package_name} as manual: {e}")
            return False