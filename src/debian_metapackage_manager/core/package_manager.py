"""Core package management functionality."""

from typing import List, Optional
from ..models import Package, OperationResult, PackageStatus
from ..config import Config
from ..interfaces.apt import APTInterface
from ..interfaces.dpkg import DPKGInterface
from .classifier import PackageClassifier
from .mode_manager import ModeManager


class PackageManager:
    """Core package management operations."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize package manager."""
        self.config = config or Config()
        self.apt = APTInterface()
        self.dpkg = DPKGInterface()
        self.classifier = PackageClassifier(self.config)
        self.mode_manager = ModeManager(self.config, self.apt)
    
    def install_package(self, name: str, force: bool = False, 
                       version: Optional[str] = None) -> OperationResult:
        """Install a package with intelligent upgrade handling and dependency resolution."""
        print(f"Installing package: {name}")
        
        # Get appropriate version for current mode
        if not version:
            version = self.mode_manager.get_package_version_for_mode(name)
        
        # Create package object
        package = Package(
            name=name,
            version=version or "",
            is_metapackage=self.classifier.is_metapackage(name),
            is_custom=self.classifier.is_custom_package(name)
        )
        
        # Check if already installed and handle upgrades intelligently
        if self.apt.is_installed(name):
            return self._handle_already_installed_package(package, version, force)
        
        # Package not installed - proceed with installation
        return self._perform_new_installation(package, version, force)
    
    def _handle_already_installed_package(self, package: Package, target_version: Optional[str], 
                                         force: bool) -> OperationResult:
        """Handle installation when package is already installed - check for upgrades."""
        current_info = self.apt.get_package_info(package.name)
        
        if not current_info:
            # Package shows as installed but we can't get info - treat as corrupted
            print(f"Warning: {package.name} appears installed but package info unavailable")
            return self._perform_new_installation(package, target_version, force)
        
        current_version = current_info.version
        print(f"Package {package.name} is already installed (v{current_version})")
        
        # If no specific version requested, check if upgrade is available
        if not target_version:
            # Auto-upgrade check - upgrade if newer version available
            if self._is_package_upgradable(package.name):
                return self._perform_upgrade(package, current_version, force)
            else:
                print(f"Package {package.name} is up to date")
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=[f"Package {package.name} is already installed and up to date"],
                    errors=[],
                    user_confirmations_required=[]
                )
        
        # Specific version requested - check if we need to upgrade/downgrade
        if current_version == target_version:
            print(f"Package {package.name} v{target_version} is already installed")
            return OperationResult(
                success=True,
                packages_affected=[package],
                warnings=[f"Package {package.name} v{target_version} is already installed"],
                errors=[],
                user_confirmations_required=[]
            )
        
        # Different version requested - perform upgrade/downgrade
        print(f"Upgrading {package.name} from v{current_version} to v{target_version}")
        return self._perform_version_change(package, current_version, target_version, force)
    
    def _perform_new_installation(self, package: Package, version: Optional[str], force: bool) -> OperationResult:
        """Perform installation of a new package."""
        try:
            # Use --no-remove flag to prevent removing other packages
            success = self._safe_install_with_no_remove(package.name, version)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=[],
                    errors=[],
                    user_confirmations_required=[]
                )
            else:
                if force:
                    return self._force_install_package(package)
                else:
                    return OperationResult(
                        success=False,
                        packages_affected=[],
                        warnings=[],
                        errors=[f"Failed to install {package.name}"],
                        user_confirmations_required=[]
                    )
                    
        except Exception as e:
            error_msg = f"Error during installation: {str(e)}"
            print(error_msg)
            
            if force:
                return self._force_install_package(package)
            
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[error_msg],
                user_confirmations_required=[]
            )
    
    def _perform_upgrade(self, package: Package, current_version: str, force: bool) -> OperationResult:
        """Perform package upgrade to latest available version."""
        print(f"Upgrading {package.name} from v{current_version}")
        
        try:
            # Use --only-upgrade to ensure we only upgrade, don't install new packages
            success = self._safe_upgrade_package(package.name)
            
            if success:
                # Get new version info
                new_info = self.apt.get_package_info(package.name)
                new_version = new_info.version if new_info else "unknown"
                
                return OperationResult(
                    success=True,
                    packages_affected=[Package(package.name, new_version, package.is_metapackage, package.is_custom)],
                    warnings=[f"Upgraded {package.name} from v{current_version} to v{new_version}"],
                    errors=[],
                    user_confirmations_required=[]
                )
            else:
                if force:
                    return self._force_install_package(package)
                else:
                    return OperationResult(
                        success=False,
                        packages_affected=[],
                        warnings=[],
                        errors=[f"Failed to upgrade {package.name}"],
                        user_confirmations_required=[]
                    )
                    
        except Exception as e:
            error_msg = f"Error during upgrade: {str(e)}"
            print(error_msg)
            
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[error_msg],
                user_confirmations_required=[]
            )
    
    def _perform_version_change(self, package: Package, current_version: str, target_version: str, force: bool) -> OperationResult:
        """Perform upgrade or downgrade to specific version."""
        operation = "upgrade" if target_version > current_version else "downgrade"
        print(f"{operation.capitalize()}ing {package.name} from v{current_version} to v{target_version}")
        
        try:
            success = self._safe_install_with_no_remove(package.name, target_version)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[Package(package.name, target_version, package.is_metapackage, package.is_custom)],
                    warnings=[f"{operation.capitalize()}d {package.name} from v{current_version} to v{target_version}"],
                    errors=[],
                    user_confirmations_required=[]
                )
            else:
                if force:
                    return self._force_install_package(package)
                else:
                    return OperationResult(
                        success=False,
                        packages_affected=[],
                        warnings=[],
                        errors=[f"Failed to {operation} {package.name} to v{target_version}"],
                        user_confirmations_required=[]
                    )
                    
        except Exception as e:
            error_msg = f"Error during {operation}: {str(e)}"
            print(error_msg)
            
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[error_msg],
                user_confirmations_required=[]
            )
    
    def _safe_install_with_no_remove(self, package_name: str, version: Optional[str]) -> bool:
        """Install package with --no-remove flag to prevent removing other packages."""
        try:
            import subprocess
            
            if version:
                package_spec = f"{package_name}={version}"
            else:
                package_spec = package_name
            
            # Use apt-get with --no-remove to prevent removing other packages
            cmd = ['sudo', 'apt-get', 'install', '-y', '--no-remove', package_spec]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Successfully installed: {package_spec}")
                return True
            else:
                print(f"Failed to install {package_spec}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error installing {package_name}: {e}")
            return False
    
    def _safe_upgrade_package(self, package_name: str) -> bool:
        """Upgrade package using --only-upgrade flag."""
        try:
            import subprocess
            
            # Use apt-get with --only-upgrade to only upgrade existing packages
            cmd = ['sudo', 'apt-get', 'install', '-y', '--only-upgrade', package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Successfully upgraded: {package_name}")
                return True
            else:
                print(f"Failed to upgrade {package_name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error upgrading {package_name}: {e}")
            return False
    
    def _is_package_upgradable(self, package_name: str) -> bool:
        """Check if package has available upgrades."""
        try:
            import subprocess
            
            cmd = ['apt', 'list', '--upgradable', package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return package_name in result.stdout and 'upgradable' in result.stdout
            
        except Exception:
            return False
    
    def remove_package(self, name: str, force: bool = False) -> OperationResult:
        """Remove a package."""
        print(f"Removing package: {name}")
        
        # Check if package is installed
        if not self.apt.is_installed(name):
            return OperationResult(
                success=True,
                packages_affected=[],
                warnings=[f"Package {name} is not installed"],
                errors=[],
                user_confirmations_required=[]
            )
        
        package_info = self.apt.get_package_info(name)
        package = Package(
            name=name,
            version=package_info.version if package_info else "",
            is_metapackage=self.classifier.is_metapackage(name),
            is_custom=self.classifier.is_custom_package(name),
            status=PackageStatus.INSTALLED
        )
        
        try:
            # Try normal removal first
            success = self.apt.remove(name, force=False)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=[],
                    errors=[],
                    user_confirmations_required=[]
                )
            
            # If normal removal fails, try with force
            if force:
                return self._force_remove_package(package)
            else:
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=["Normal removal failed, use --force to override"],
                    errors=[],
                    user_confirmations_required=[]
                )
                    
        except Exception as e:
            error_msg = f"Error during removal: {str(e)}"
            print(error_msg)
            
            if force:
                return self._force_remove_package(package)
            
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[error_msg],
                user_confirmations_required=[]
            )
    
    def get_package_info(self, name: str) -> Optional[Package]:
        """Get comprehensive package information."""
        package_info = self.apt.get_package_info(name)
        if not package_info:
            return None
        
        # Enhance with classification info
        package_info.is_custom = self.classifier.is_custom_package(name)
        package_info.is_metapackage = self.classifier.is_metapackage(name)
        
        return package_info
    
    def list_installed_packages(self, custom_only: bool = False) -> List[Package]:
        """List installed packages with classification."""
        packages = self.dpkg.get_installed_packages()
        
        if custom_only:
            packages = [pkg for pkg in packages if self.classifier.is_custom_package(pkg.name)]
        
        # Enhance with classification info
        for package in packages:
            package.is_custom = self.classifier.is_custom_package(package.name)
            package.is_metapackage = self.classifier.is_metapackage(package.name)
        
        return packages
    
    def check_system_health(self) -> OperationResult:
        """Check overall system package health."""
        print("Checking system package health...")
        
        warnings = []
        errors = []
        
        try:
            # Check for broken packages
            broken_packages = self.dpkg.list_broken_packages()
            if broken_packages:
                errors.extend([f"Broken package: {pkg.name}" for pkg in broken_packages])
            
            # Check pinned version validity in offline mode
            if self.mode_manager.is_offline_mode():
                is_valid, issues = self.mode_manager.validate_pinned_versions()
                if not is_valid:
                    warnings.extend(issues)
            
            # Check for package locks
            active_locks = self.dpkg.detect_locks()
            if active_locks:
                warnings.extend([f"Active lock: {lock}" for lock in active_locks])
            
            success = len(errors) == 0
            
            return OperationResult(
                success=success,
                packages_affected=[],
                warnings=warnings,
                errors=errors,
                user_confirmations_required=[]
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=warnings,
                errors=[f"Health check error: {str(e)}"],
                user_confirmations_required=[]
            )
    
    def fix_broken_system(self) -> OperationResult:
        """Attempt to fix broken package system."""
        print("Attempting to fix broken package system...")
        
        packages_affected = []
        warnings = []
        errors = []
        
        try:
            # Fix broken packages
            if self.dpkg.fix_broken_packages():
                warnings.append("Fixed broken package configurations")
            
            # Handle locks
            active_locks = self.dpkg.detect_locks()
            if active_locks:
                if self.dpkg._handle_locks():
                    warnings.append("Resolved package locks")
                else:
                    errors.append("Could not resolve package locks")
            
            # Reconfigure broken packages
            broken_packages = self.dpkg.list_broken_packages()
            for package in broken_packages:
                if self.dpkg.reconfigure_package(package.name):
                    packages_affected.append(package)
                    warnings.append(f"Reconfigured {package.name}")
                else:
                    errors.append(f"Could not reconfigure {package.name}")
            
            success = len(errors) == 0
            
            return OperationResult(
                success=success,
                packages_affected=packages_affected,
                warnings=warnings,
                errors=errors,
                user_confirmations_required=[]
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                packages_affected=packages_affected,
                warnings=warnings,
                errors=[f"System fix error: {str(e)}"],
                user_confirmations_required=[]
            )
    
    def _force_install_package(self, package: Package) -> OperationResult:
        """Force install a package using aggressive methods."""
        print(f"Force installing: {package.name}")
        
        try:
            # Try to fix broken packages first
            self.dpkg.fix_broken_packages()
            
            # Try again
            success = self.apt.install(package.name, package.version)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=["Package installed with force methods"],
                    errors=[],
                    user_confirmations_required=[]
                )
            else:
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=[],
                    errors=[f"Force installation failed for {package.name}"],
                    user_confirmations_required=[]
                )
                
        except Exception as e:
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[f"Force installation error: {str(e)}"],
                user_confirmations_required=[]
            )
    
    def _force_remove_package(self, package: Package) -> OperationResult:
        """Force remove a package using DPKG."""
        print(f"Force removing: {package.name}")
        
        try:
            # Try DPKG safe removal first
            success = self.dpkg.safe_remove(package.name)
            
            if not success:
                # Try safe purge as last resort
                success = self.dpkg.safe_purge(package.name)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=["Package removed with force methods"],
                    errors=[],
                    user_confirmations_required=[]
                )
            else:
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=[],
                    errors=[f"Force removal failed for {package.name}"],
                    user_confirmations_required=[]
                )
                
        except Exception as e:
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[f"Force removal error: {str(e)}"],
                user_confirmations_required=[]
            )