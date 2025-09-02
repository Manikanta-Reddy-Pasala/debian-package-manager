"""Core package management operations."""

from typing import List, Optional
from ..interfaces.apt import APTInterface
from ..interfaces.dpkg import DPKGInterface
from .classifier import PackageClassifier
from .mode_manager import ModeManager
from ..models import Package, OperationResult, PackageStatus
from ..config import Config
from ..utils.force_analyzer import ForceOperationAnalyzer
from ..utils.table_formatter import TableFormatter
import subprocess


class PackageManager:
    """Core package management operations."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize package manager."""
        self.config = config or Config()
        self.apt = APTInterface()
        self.dpkg = DPKGInterface()
        self.classifier = PackageClassifier(self.config)
        self.mode_manager = ModeManager(self.config, self.apt)
        self.force_analyzer = ForceOperationAnalyzer(self.config)
    
    def install_package(self, name: str, force: bool = False, 
                       version: Optional[str] = None) -> OperationResult:
        """Install a package with intelligent upgrade handling and dependency resolution."""
        print(f"Installing package: {name}")
        
        # Get appropriate version for current mode (None means latest)
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
    
    def _perform_new_installation(self, package: Package, version: Optional[str], 
                                 force: bool) -> OperationResult:
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
    
    def _show_force_install_confirmation(self, impact_analysis: dict) -> bool:
        """Show force installation impact and get user confirmation."""
        print("\n" + "="*80)
        print("FORCE INSTALLATION CONFIRMATION")
        print("="*80)
        print(f"Package: {impact_analysis['target_package']}")
        if impact_analysis['target_version']:
            print(f"Version: {impact_analysis['target_version']}")
        print()
        
        # Show conflicts table
        if impact_analysis['conflicts_to_remove']:
            conflicts_table = TableFormatter.format_packages_table(
                impact_analysis['conflicts_to_remove'],
                columns=["S.No", "Package Name", "Version", "Type", "Risk Level"],
                title="Packages to be REMOVED due to conflicts"
            )
            print(conflicts_table)
            print()
        
        # Show custom packages at risk
        if impact_analysis['custom_packages_at_risk']:
            print("⚠️  CUSTOM PACKAGES AT RISK:")
            for pkg in impact_analysis['custom_packages_at_risk']:
                print(f"   - {pkg.name} (v{pkg.version})")
            print()
        
        # Show protection strategy
        if impact_analysis['preservable_packages']:
            print("🛡️  PROTECTION STRATEGY:")
            print("   - Marking custom packages as manually installed")
            print("   - Preserving custom package configurations")
            print()
        
        # Get user confirmation
        print("This operation will force install the package with the above impacts.")
        response = input("Do you want to proceed? (type 'YES' to confirm): ")
        return response.upper() == "YES"
    
    def _show_force_remove_confirmation(self, impact_analysis: dict) -> bool:
        """Show force removal impact and get user confirmation."""
        print("\n" + "="*80)
        print("FORCE REMOVAL CONFIRMATION")
        print("="*80)
        print(f"Package: {impact_analysis['target_package']}")
        print()
        
        # Show dependencies that will be removed
        if impact_analysis['dependencies_to_remove']:
            deps_table = TableFormatter.format_packages_table(
                impact_analysis['dependencies_to_remove'],
                columns=["S.No", "Package Name", "Version", "Type", "Risk Level"],
                title="Dependencies to be REMOVED"
            )
            print(deps_table)
            print()
        
        # Show affected dependents
        if impact_analysis['dependents_affected']:
            dependents_table = TableFormatter.format_packages_table(
                impact_analysis['dependents_affected'],
                columns=["S.No", "Package Name", "Version", "Type"],
                title="Packages that DEPEND on this package (may break)"
            )
            print(dependents_table)
            print()
        
        # Show custom packages at risk
        if impact_analysis['custom_packages_at_risk']:
            print("⚠️  CUSTOM PACKAGES AT RISK:")
            for pkg in impact_analysis['custom_packages_at_risk']:
                print(f"   - {pkg.name} (v{pkg.version})")
            print()
        
        # Show protection strategy
        if impact_analysis['preservable_packages']:
            print("🛡️  PROTECTION STRATEGY:")
            print("   - Marking custom packages as manually installed")
            print("   - Preserving custom package configurations")
            print()
        
        # Get user confirmation
        print("This operation will force remove the package with the above impacts.")
        response = input("Do you want to proceed? (type 'YES' to confirm): ")
        return response.upper() == "YES"
    
    def _safe_install_with_force_flags(self, package_name: str, version: Optional[str]) -> bool:
        """Install package with force flags to override conflicts."""
        try:
            if version:
                package_spec = f"{package_name}={version}"
            else:
                package_spec = package_name
            
            # Try with --force-yes to override conflicts
            cmd = ['sudo', 'apt-get', 'install', '-y', '--force-yes', package_spec]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Successfully force installed: {package_spec}")
                return True
            else:
                # Try with --allow-downgrades if needed
                cmd = ['sudo', 'apt-get', 'install', '-y', '--allow-downgrades', package_spec]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"Successfully force installed with downgrades: {package_spec}")
                    return True
                else:
                    print(f"Failed to force install {package_spec}: {result.stderr}")
                    return False
                    
        except Exception as e:
            print(f"Error force installing {package_name}: {e}")
            return False
    
    def _safe_install_with_no_remove(self, package_name: str, version: Optional[str]) -> bool:
        """Install package with --no-remove flag to prevent removing other packages."""
        try:
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
            cmd = ['apt', 'list', '--upgradable', package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return package_name in result.stdout and 'upgradable' in result.stdout
            
        except Exception:
            return False
    
    def _force_install_package(self, package: Package) -> OperationResult:
        """Force install a package using intelligent methods with protection strategies."""
        print(f"🔧 Force installing package: {package.name}")
        
        try:
            # First, analyze the impact of force installation
            impact_analysis = self.force_analyzer.analyze_force_install_impact(
                package.name, package.version
            )
            
            # Apply protection strategy before proceeding
            if impact_analysis['protection_strategy']:
                print("🛡️  Applying protection strategy...")
                self.force_analyzer.apply_protection_strategy(impact_analysis['protection_strategy'])
            
            # Try safe installation methods first
            success = self._safe_install_with_no_remove(package.name, package.version)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=["Package installed with protection strategies applied"],
                    errors=[],
                    user_confirmations_required=[]
                )
            
            # If that fails, try force installation with various methods
            success = self._safe_install_with_force_flags(package.name, package.version)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=["Package force installed with flags"],
                    errors=[],
                    user_confirmations_required=[]
                )
            
            # Show confirmation if there are significant impacts
            if impact_analysis['requires_confirmation']:
                print("⚠️  Significant impact detected during force installation.")
                if not self._show_force_install_confirmation(impact_analysis):
                    return OperationResult(
                        success=False,
                        packages_affected=[],
                        warnings=[],
                        errors=["User cancelled force installation"],
                        user_confirmations_required=[]
                    )
            
            # Try various force installation methods as last resort
            success = self._try_force_install_methods(package.name, package.version)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=["Package installed with force methods as last resort"],
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
    
    def _try_force_install_methods(self, package_name: str, version: Optional[str]) -> bool:
        """Try various force installation methods."""
        try:
            # Method 1: Fix broken packages first
            print("🔧 Fixing broken packages...")
            self.dpkg.fix_broken_packages()
            
            # Method 2: Try with --force-yes
            print("🔄 Trying force installation with --force-yes...")
            if version:
                package_spec = f"{package_name}={version}"
            else:
                package_spec = package_name
            
            cmd = ['sudo', 'apt-get', 'install', '-y', '--force-yes', package_spec]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully force installed: {package_spec}")
                return True
            
            # Method 3: Try with --allow-downgrades
            print("🔄 Trying force installation with --allow-downgrades...")
            cmd = ['sudo', 'apt-get', 'install', '-y', '--allow-downgrades', package_spec]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully force installed with downgrades: {package_spec}")
                return True
            
            # Method 4: Try dpkg direct installation if it's a .deb file
            if package_name.endswith('.deb'):
                print("🔄 Trying direct .deb installation...")
                return self.dpkg.force_install_deb(package_name)
            
            return False
            
        except Exception as e:
            print(f"Error in force installation methods: {e}")
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
    
    def _force_remove_package(self, package: Package) -> OperationResult:
        """Force remove a package using intelligent methods with protection strategies."""
        print(f"🔧 Force removing package: {package.name}")
        
        try:
            # First, analyze the impact of force removal
            impact_analysis = self.force_analyzer.analyze_force_remove_impact(package.name)
            
            # Apply protection strategy before proceeding
            if impact_analysis['protection_strategy']:
                print("🛡️  Applying protection strategy...")
                self.force_analyzer.apply_protection_strategy(impact_analysis['protection_strategy'])
            
            # Try safe removal first
            success = self.dpkg.safe_remove(package.name)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=["Package removed with protection strategies applied"],
                    errors=[],
                    user_confirmations_required=[]
                )
            
            # Show confirmation if there are significant impacts
            if impact_analysis['requires_confirmation']:
                print("⚠️  Significant impact detected during force removal.")
                if not self._show_force_remove_confirmation(impact_analysis):
                    return OperationResult(
                        success=False,
                        packages_affected=[],
                        warnings=[],
                        errors=["User cancelled force removal"],
                        user_confirmations_required=[]
                    )
            
            # Try various force removal methods as last resort
            success = self._try_force_remove_methods(package.name)
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[package],
                    warnings=["Package removed with force methods as last resort"],
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
    
    def _try_force_remove_methods(self, package_name: str) -> bool:
        """Try various force removal methods."""
        try:
            # Method 1: Fix broken packages first
            print("🔧 Fixing broken packages...")
            self.dpkg.fix_broken_packages()
            
            # Method 2: Try standard dpkg removal
            print("🔄 Trying standard dpkg removal...")
            cmd = ['sudo', 'dpkg', '--remove', package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully removed package: {package_name}")
                return True
            
            # Method 3: Try with --force-depends
            print("🔄 Trying force removal with --force-depends...")
            cmd = ['sudo', 'dpkg', '--remove', '--force-depends', package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully force removed package: {package_name}")
                return True
            
            # Method 4: Try with apt-get force remove
            print("🔄 Trying apt-get force removal...")
            cmd = ['sudo', 'apt-get', 'remove', '--force-yes', '-y', package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully force removed package with apt-get: {package_name}")
                return True
            
            # Method 5: Try purge as last resort
            print("🔄 Trying purge as last resort...")
            return self.dpkg.purge_package(package_name, force=True)
            
        except Exception as e:
            print(f"Error in force removal methods: {e}")
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
        
        try:
            success = self.dpkg.fix_broken_packages()
            
            if success:
                return OperationResult(
                    success=True,
                    packages_affected=[],
                    warnings=["Fixed broken package states"],
                    errors=[],
                    user_confirmations_required=[]
                )
            else:
                return OperationResult(
                    success=False,
                    packages_affected=[],
                    warnings=[],
                    errors=["Failed to fix broken packages"],
                    user_confirmations_required=[]
                )
                
        except Exception as e:
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[f"Error fixing broken system: {str(e)}"],
                user_confirmations_required=[]
            )