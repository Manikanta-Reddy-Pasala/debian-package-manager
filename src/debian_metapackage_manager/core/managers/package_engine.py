"""Core package engine for orchestrating all package operations."""

from typing import Optional, List
from ...models import Package, OperationResult, PackageStatus
from ..package_manager import PackageManager
from ..mode_manager import ModeManager
from ..resolvers import DependencyResolver
from ..handlers import ConflictHandler
from ...config import Config


class PackageEngine:
    """Main orchestration class for package operations - delegates to core components."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize package engine with all components."""
        self.config = config or Config()
        self.package_manager = PackageManager(self.config)
        
        # Expose commonly used components for backward compatibility
        self.apt = self.package_manager.apt
        self.dpkg = self.package_manager.dpkg
        self.classifier = self.package_manager.classifier
        self.mode_manager = self.package_manager.mode_manager
        
        # Keep advanced components for complex operations
        self.dependency_resolver = DependencyResolver(self.apt, self.classifier, self.config)
        self.conflict_handler = ConflictHandler(self.classifier, self.config)
    
    def install_package(self, name: str, force: bool = False, 
                       version: Optional[str] = None) -> OperationResult:
        """
        Install a package with dependency resolution and conflict handling.
        
        For simple installations, delegates to PackageManager.
        For complex installations with conflicts, uses full dependency resolution.
        """
        # Try simple installation first
        simple_result = self.package_manager.install_package(name, force, version)
        
        # If simple installation succeeds or fails without conflicts, return result
        if simple_result.success or not force:
            return simple_result
        
        # For complex cases with conflicts, use full dependency resolution
        print("Attempting advanced dependency resolution...")
        
        target_version = version or self.mode_manager.get_package_version_for_mode(name)
        package = Package(
            name=name,
            version=target_version or "",
            is_metapackage=self.classifier.is_metapackage(name),
            is_custom=self.classifier.is_custom_package(name)
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
            error_msg = f"Error during advanced installation: {str(e)}"
            print(error_msg)
            return simple_result  # Return the original simple result
    
    def remove_package(self, name: str, force: bool = False) -> OperationResult:
        """
        Remove a package with conflict resolution.
        
        For simple removals, delegates to PackageManager.
        For complex removals with high risk, uses conflict handler.
        """
        # Check removal risk first
        risk_level = self.classifier.get_removal_risk_level(name)
        
        if risk_level == "HIGH" and not force:
            # Use conflict handler for high-risk removals
            package_info = self.apt.get_package_info(name)
            package = Package(
                name=name,
                version=package_info.version if package_info else "",
                is_metapackage=self.classifier.is_metapackage(name),
                is_custom=self.classifier.is_custom_package(name),
                status=PackageStatus.INSTALLED
            )
            
            # Prompt for confirmation of high-risk removal
            if not self.conflict_handler._prompt_for_removals([package]):
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=["High-risk removal cancelled by user"],
                    errors=[],
                    user_confirmations_required=[]
                )
        
        # Delegate to simple package manager
        result = self.package_manager.remove_package(name, force)
        
        # If simple removal fails and not forced, ask user about force mode
        if not result.success and not force:
            if self.conflict_handler.prompt_for_force_mode("removal", name):
                return self.package_manager.remove_package(name, force=True)
        
        return result
    
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
        return self.package_manager.get_package_info(name)
    
    def list_installed_packages(self, custom_only: bool = False) -> List[Package]:
        """List installed packages with classification."""
        return self.package_manager.list_installed_packages(custom_only)
    
    def check_system_health(self) -> OperationResult:
        """Check overall system package health."""
        return self.package_manager.check_system_health()
    
    def fix_broken_system(self) -> OperationResult:
        """Attempt to fix broken package system."""
        return self.package_manager.fix_broken_system()