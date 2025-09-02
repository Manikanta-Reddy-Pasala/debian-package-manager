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
        self.dependency_resolver = DependencyResolver(self.config)
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
            
            # If force is enabled, try to execute the plan even with issues
            if force and not is_valid:
                print("⚠️  Continuing with force despite validation issues...")
                for issue in validation_issues:
                    print(f"   - {issue}")
            
            # Execute the installation plan
            return self._execute_installation_plan(dependency_plan, force)
            
        except Exception as e:
            # If dependency resolution fails, fall back to force installation
            if force:
                print(f"Dependency resolution failed: {e}")
                print("Falling back to direct force installation...")
                return self.package_manager.install_package(name, force=True, version=version)
            else:
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=[],
                    errors=[f"Dependency resolution failed: {str(e)}"],
                    user_confirmations_required=[]
                )
    
    def remove_package(self, name: str, force: bool = False) -> OperationResult:
        """Remove a package with intelligent dependency handling."""
        # Try simple removal first
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
                    # Apply protection strategy before force removal
                    self.dpkg.mark_as_manual(package.name)
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
                            errors.append(f"Failed to force install {package.name}")
                    else:
                        errors.append(f"Failed to install {package.name}")
            
            # Attempt to fix broken packages if any errors occurred
            if errors:
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
        """Force install a package using intelligent methods with protection strategies."""
        print(f"🔧 Force installing package: {package.name}")
        
        # Delegate to package manager's improved force install method
        return self.package_manager._force_install_package(package)
    
    def _force_remove_package(self, package: Package) -> OperationResult:
        """Force remove a package using intelligent methods with protection strategies."""
        print(f"🔧 Force removing package: {package.name}")
        
        # Delegate to package manager's improved force remove method
        return self.package_manager._force_remove_package(package)
    
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
            
            # Method 4: Try force installation with flags
            if version:
                package_spec = f"{package_name}={version}"
            else:
                package_spec = package_name
            
            # Try with --force-yes
            import subprocess
            cmd = ['sudo', 'apt-get', 'install', '-y', '--force-yes', package_spec]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            
            # Try with --allow-downgrades
            cmd = ['sudo', 'apt-get', 'install', '-y', '--allow-downgrades', package_spec]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return result.returncode == 0
            
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