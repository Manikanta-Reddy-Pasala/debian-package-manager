"""Advanced dependency resolution for complex package scenarios."""

from typing import List, Optional, Set, Tuple
from ...models import Package, Conflict, DependencyPlan, PackageStatus
from ...config import Config
from ...interfaces.apt import APTInterface
from ...core.classifier import PackageClassifier


class DependencyResolver:
    """Advanced dependency resolver with conflict handling."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize resolver with configuration."""
        self.config = config or Config()
        self.apt = APTInterface()
        self.classifier = PackageClassifier(self.config)
    
    def is_package_upgradable(self, package: Package) -> bool:
        """Check if a package can be upgraded."""
        # Check if package is installed
        if not self.apt.is_installed(package.name):
            return False
        
        # Check if package is upgradable
        current_info = self.apt.get_package_info(package.name)
        if current_info and current_info.status == PackageStatus.UPGRADABLE:
            return True
        
        return False
    
    def _detect_conflicts(self, packages: List[Package]) -> List[Conflict]:
        """Detect conflicts for a list of packages."""
        all_conflicts = []
        
        for package in packages:
            package_conflicts = self.apt.check_conflicts(package.name)
            all_conflicts.extend(package_conflicts)
        
        return all_conflicts
    
    def _plan_conflict_resolution(self, conflicts: List[Conflict]) -> List[Package]:
        """Plan package removals to resolve conflicts."""
        to_remove = []
        
        for conflict in conflicts:
            # Determine which package should be removed
            removal_candidate = self._choose_removal_candidate(
                conflict.package, 
                conflict.conflicting_package
            )
            
            if removal_candidate and removal_candidate not in to_remove:
                to_remove.append(removal_candidate)
        
        # Sort by removal priority (custom packages first, system packages last)
        to_remove.sort(key=self._get_removal_priority)
        
        return to_remove
    
    def _choose_removal_candidate(self, package1: Package, package2: Package) -> Optional[Package]:
        """Choose which package should be removed in a conflict."""
        # Prioritize preserving system packages
        pkg1_preserve = self.classifier.should_prioritize_preservation(package1.name)
        pkg2_preserve = self.classifier.should_prioritize_preservation(package2.name)
        
        if pkg1_preserve and not pkg2_preserve:
            return package2
        elif pkg2_preserve and not pkg1_preserve:
            return package1
        
        # If both or neither are system packages, prefer removing custom packages
        pkg1_custom = self.classifier.is_custom_package(package1.name)
        pkg2_custom = self.classifier.is_custom_package(package2.name)
        
        if pkg1_custom and not pkg2_custom:
            return package1
        elif pkg2_custom and not pkg1_custom:
            return package2
        
        # If same type, prefer removing the one that's not installed
        if not self.apt.is_installed(package1.name):
            return package1
        elif not self.apt.is_installed(package2.name):
            return package2
        
        # Default to removing the first package
        return package1
    
    def _get_removal_priority(self, package: Package) -> int:
        """Get removal priority (lower number = higher priority for removal)."""
        if self.classifier.should_prioritize_preservation(package.name):
            return 100  # System packages - lowest priority for removal
        elif self.classifier.is_custom_package(package.name):
            return 10   # Custom packages - high priority for removal
        else:
            return 50   # Other packages - medium priority
    
    def create_installation_order(self, packages: List[Package]) -> List[Package]:
        """Create optimal installation order considering dependencies."""
        ordered = []
        remaining = packages.copy()
        
        while remaining:
            # Find packages with no unmet dependencies in remaining list
            installable = []
            
            for pkg in remaining:
                deps = self._get_all_dependencies(pkg.name)
                dep_names = {dep.name for dep in deps}
                remaining_names = {p.name for p in remaining}
                
                # Check if all dependencies are either already ordered or not in remaining
                unmet_deps = dep_names.intersection(remaining_names)
                unmet_deps.discard(pkg.name)  # Remove self-reference
                
                if not unmet_deps:
                    installable.append(pkg)
            
            if not installable:
                # Circular dependency or complex case - just add remaining packages
                ordered.extend(remaining)
                break
            
            # Sort installable packages by priority (system packages first)
            installable.sort(key=lambda p: (
                not self.classifier.should_prioritize_preservation(p.name),
                p.name
            ))
            
            # Add first installable package and remove from remaining
            next_pkg = installable[0]
            ordered.append(next_pkg)
            remaining.remove(next_pkg)
        
        return ordered
    
    def validate_resolution_plan(self, plan: DependencyPlan) -> Tuple[bool, List[str]]:
        """Validate that a resolution plan is feasible."""
        issues = []
        
        # Check for circular dependencies
        all_packages = plan.to_install + plan.to_upgrade
        for pkg in all_packages:
            if self._has_circular_dependency(pkg.name, all_packages):
                issues.append(f"Circular dependency detected involving {pkg.name}")
        
        # Check for essential package removals
        for pkg in plan.to_remove:
            if self.classifier.should_prioritize_preservation(pkg.name):
                risk_level = self.classifier.get_removal_risk_level(pkg.name)
                if risk_level == "HIGH":
                    issues.append(f"High-risk removal: {pkg.name} is a critical system package")
        
        # Check for metapackage consistency
        for pkg in plan.to_install:
            if self.classifier.is_metapackage(pkg.name):
                # Ensure all metapackage dependencies are included
                meta_deps = self._get_all_dependencies(pkg.name)
                missing_deps = []
                for dep in meta_deps:
                    if not self.apt.is_installed(dep.name) and dep not in plan.to_install:
                        missing_deps.append(dep.name)
                
                if missing_deps:
                    issues.append(f"Metapackage {pkg.name} missing dependencies: {', '.join(missing_deps)}")
        
        return len(issues) == 0, issues
    
    def _has_circular_dependency(self, package_name: str, package_list: List[Package]) -> bool:
        """Check if a package has circular dependencies within the given list."""
        package_names = {pkg.name for pkg in package_list}
        
        def check_circular(pkg_name: str, visited: Set[str]) -> bool:
            if pkg_name in visited:
                return True
            
            visited.add(pkg_name)
            deps = self._get_all_dependencies(pkg_name)
            
            for dep in deps:
                if dep.name in package_names and check_circular(dep.name, visited.copy()):
                    return True
            
            return False
        
        return check_circular(package_name, set())
    
    def get_resolution_summary(self, plan: DependencyPlan) -> str:
        """Get a human-readable summary of the resolution plan."""
        summary_parts = []
        
        if plan.to_install:
            install_summary = self.classifier.get_package_category_summary(
                [pkg.name for pkg in plan.to_install]
            )
            summary_parts.append(f"Install: {install_summary}")
        
        if plan.to_upgrade:
            upgrade_summary = self.classifier.get_package_category_summary(
                [pkg.name for pkg in plan.to_upgrade]
            )
            summary_parts.append(f"Upgrade: {upgrade_summary}")
        
        if plan.to_remove:
            remove_summary = self.classifier.get_package_category_summary(
                [pkg.name for pkg in plan.to_remove]
            )
            summary_parts.append(f"Remove: {remove_summary}")
        
        if plan.conflicts:
            summary_parts.append(f"Conflicts: {len(plan.conflicts)} detected")
        
        return "; ".join(summary_parts) if summary_parts else "No changes required"