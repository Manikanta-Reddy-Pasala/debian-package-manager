"""Core package engine for orchestrating all package operations."""

from typing import Optional, List
from .models import Package, OperationResult, PackageStatus
from .apt_interface import APTInterface
from .dpkg_interface import DPKGInterface
from .dependency_resolver import DependencyResolver
from .conflict_handler import ConflictHandler
from .mode_manager import ModeManager
from .classifier import PackageClassifier
from .config import Config


class PackageEngine:
    """Main orchestration class for package operations."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize package engine with all components."""
        self.config = config or Config()
        self.apt = APTInterface()
        self.dpkg = DPKGInterface()
        self.classifier = PackageClassifier(self.config)
        self.mode_manager = ModeManager(self.config, self.apt)
        self.dependency_resolver = DependencyResolver(self.apt, self.classifier, self.config)
        self.conflict_handler = ConflictHandler(self.classifier, self.config)
    
    def install_package(self, name: str, force: bool = False) -> OperationResult:
        """Install a package with full dependency resolution and conflict handling."""
        print(f"Installing package: {name}")
        
        # Create package object
        target_version = self.mode_manager.get_package_version_for_mode(name)
        package = Package(
            name=name,
            version=target_version or "",
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
            # Resolve dependencies
            print("Resolving dependencies...")
            dependency_plan = self.dependency_resolver.resolve_dependencies(package)
            
            # Validate the plan
            is_valid, validation_issues = self.dependency_resolver.validate_resolution_plan(dependency_plan)
            if not is_valid and not force:
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=[],
                    errors=validation_issues,
                    user_confirmations_required=[]
                )
            
            # Handle conflicts if any
            if dependency_plan.conflicts or dependency_plan.to_remove:
                approved, final_plan = self.conflict_handler.handle_conflicts(dependency_plan)
                if not approved:
                    return OperationResult(
                        success=False,
                        packages_affected=[],
                        warnings=["Operation cancelled by user"],
                        errors=[],
                        user_confirmations_required=[]
                    )
                dependency_plan = final_plan
            
            # Execute the installation plan
            return self._execute_installation_plan(dependency_plan, force)
            
        except Exception as e:
            error_msg = f"Error during installation: {str(e)}"
            print(error_msg)
            
            if force:
                # Try force installation as last resort
                return self._force_install_package(package)
            
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[error_msg],
                user_confirmations_required=[]
            )
    
    def remove_package(self, name: str, force: bool = False) -> OperationResult:
        """Remove a package with conflict resolution."""
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
            # Check removal risk
            risk_level = self.classifier.get_removal_risk_level(name)
            
            if risk_level == "HIGH" and not force:
                # Prompt for confirmation of high-risk removal
                if not self.conflict_handler._prompt_for_removals([package]):
                    return OperationResult(
                        success=False,
                        packages_affected=[],
                        warnings=["High-risk removal cancelled by user"],
                        errors=[],
                        user_confirmations_required=[]
                    )
            
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
            
            # If normal removal fails, try with force or dpkg
            if force:
                return self._force_remove_package(package)
            else:
                # Ask user if they want to force remove
                if self.conflict_handler.prompt_for_force_mode("removal", name):
                    return self._force_remove_package(package)
                else:
                    return OperationResult(
                        success=False,
                        packages_affected=[],
                        warnings=["Normal removal failed, force removal declined"],
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
    
    def _execute_installation_plan(self, plan, force: bool) -> OperationResult:
        """Execute a dependency installation plan."""
        packages_affected = []
        warnings = []
        errors = []
        
        try:
            # Remove conflicting packages first
            for package in plan.to_remove:
                print(f"Removing conflicting package: {package.name}")
                if force:
                    success = self.dpkg.force_remove(package.name)
                else:
                    success = self.apt.remove(package.name)
                
                if success:
                    packages_affected.append(package)
                else:
                    if force:
                        # Try even more aggressive removal
                        success = self.dpkg.purge_package(package.name, force=True)
                        if success:
                            packages_affected.append(package)
                            warnings.append(f"Had to purge package {package.name}")
                        else:
                            errors.append(f"Failed to remove conflicting package {package.name}")
                    else:
                        errors.append(f"Failed to remove conflicting package {package.name}")
            
            # Install packages in dependency order
            ordered_packages = self.dependency_resolver.create_installation_order(plan.to_install)
            
            for package in ordered_packages:
                print(f"Installing: {package.name} (v{package.version})")
                
                # Get appropriate version for current mode
                target_version = self.mode_manager.get_package_version_for_mode(package.name)
                
                success = self.apt.install(package.name, target_version)
                
                if success:
                    packages_affected.append(package)
                else:
                    if force:
                        # Try force installation
                        success = self._try_force_install(package.name, target_version)
                        if success:
                            packages_affected.append(package)
                            warnings.append(f"Had to force install {package.name}")
                        else:
                            errors.append(f"Failed to install {package.name} even with force")
                    else:
                        errors.append(f"Failed to install {package.name}")
            
            # Upgrade packages if needed
            for package in plan.to_upgrade:
                print(f"Upgrading: {package.name}")
                target_version = self.mode_manager.get_package_version_for_mode(package.name)
                
                success = self.apt.install(package.name, target_version)
                if success:
                    packages_affected.append(package)
                else:
                    warnings.append(f"Failed to upgrade {package.name}")
            
            # Fix any broken packages
            if errors and force:
                print("Attempting to fix broken packages...")
                if self.dpkg.fix_broken_packages():
                    warnings.append("Fixed broken package states")
            
            overall_success = len(errors) == 0 or (force and len(packages_affected) > 0)
            
            return OperationResult(
                success=overall_success,
                packages_affected=packages_affected,
                warnings=warnings,
                errors=errors,
                user_confirmations_required=[]
            )
            
        except Exception as e:
            errors.append(f"Execution error: {str(e)}")
            return OperationResult(
                success=False,
                packages_affected=packages_affected,
                warnings=warnings,
                errors=errors,
                user_confirmations_required=[]
            )
    
    def _force_install_package(self, package: Package) -> OperationResult:
        """Force install a package using aggressive methods."""
        print(f"Force installing: {package.name}")
        
        try:
            # Try APT with force options first
            success = self.apt.install(package.name, package.version)
            
            if not success:
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
            # Try DPKG force removal
            success = self.dpkg.force_remove(package.name)
            
            if not success:
                # Try purge as last resort
                success = self.dpkg.purge_package(package.name, force=True)
            
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
    
    def _try_force_install(self, package_name: str, version: Optional[str]) -> bool:
        """Try various force installation methods."""
        try:
            # Method 1: Fix broken packages first
            self.dpkg.fix_broken_packages()
            if self.apt.install(package_name, version):
                return True
            
            # Method 2: Try to resolve locks
            if self.dpkg._handle_locks():
                if self.apt.install(package_name, version):
                    return True
            
            # Method 3: If it's a .deb file path, try direct installation
            if package_name.endswith('.deb'):
                return self.dpkg.force_install_deb(package_name)
            
            return False
            
        except Exception:
            return False
    
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