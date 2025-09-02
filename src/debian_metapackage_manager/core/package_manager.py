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
        """Install a package with dependency resolution."""
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
        
        # Check if already installed
        if self.apt.is_installed(name) and not force:
            return OperationResult(
                success=True,
                packages_affected=[package],
                warnings=[f"Package {name} is already installed"],
                errors=[],
                user_confirmations_required=[]
            )
        
        try:
            # Try installation
            success = self.apt.install(name, version)
            
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
                        errors=[f"Failed to install {name}"],
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