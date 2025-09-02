"""Dependency resolution engine for complex package operations."""

from typing import List, Set, Dict, Optional, Tuple
from ...interfaces import DependencyResolverInterface
from ...models import Package, DependencyPlan, Conflict, PackageStatus
from ...interfaces.apt import APTInterface
from ..classifier import PackageClassifier
from ...config import Config


class DependencyResolver(DependencyResolverInterface):
    """Handles complex dependency resolution with conflict detection."""
    
    def __init__(self, apt_interface: Optional[APTInterface] = None, 
                 classifier: Optional[PackageClassifier] = None,
                 config: Optional[Config] = None):
        """Initialize dependency resolver."""
        self.apt = apt_interface or APTInterface()
        self.classifier = classifier or PackageClassifier(config)
        self.config = config or Config()
        self._resolution_cache = {}
    
    def resolve_dependencies(self, package: Package) -> DependencyPlan:
        """Resolve dependencies for a package installation."""
        plan = DependencyPlan(
            to_install=[],
            to_remove=[],
            to_upgrade=[],
            conflicts=[]
        )
        
        # Get all dependencies recursively
        all_deps = self._get_all_dependencies(package.name)
        
        # Categorize dependencies
        for dep in all_deps:
            if not self.apt.is_installed(dep.name):
                plan.to_install.append(dep)
            elif self._should_upgrade(dep):
                plan.to_upgrade.append(dep)
        
        # Add the main package if not installed
        if not self.apt.is_installed(package.name):
            plan.to_install.insert(0, package)
        
        # Check for conflicts
        conflicts = self._detect_conflicts(plan.to_install + plan.to_upgrade)
        plan.conflicts = conflicts
        
        # Resolve conflicts by determining what needs to be removed
        if conflicts:
            removal_plan = self._plan_conflict_resolution(conflicts)
            plan.to_remove.extend(removal_plan)
            plan.requires_user_confirmation = True
        
        return plan
    
    def resolve_conflicts(self, conflicts: List[Conflict]) -> DependencyPlan:
        """Resolve package conflicts by planning removals."""
        plan = DependencyPlan(
            to_install=[],
            to_remove=[],
            to_upgrade=[],
            conflicts=conflicts,
            requires_user_confirmation=True
        )
        
        # Plan removals to resolve conflicts
        removal_plan = self._plan_conflict_resolution(conflicts)
        plan.to_remove = removal_plan
        
        return plan
    
    def _get_all_dependencies(self, package_name: str, 
                            visited: Optional[Set[str]] = None) -> List[Package]:
        """Get all dependencies recursively."""
        if visited is None:
            visited = set()
        
        if package_name in visited:
            return []  # Avoid circular dependencies
        
        visited.add(package_name)
        
        # Check cache first
        if package_name in self._resolution_cache:
            return self._resolution_cache[package_name]
        
        dependencies = []
        direct_deps = self.apt.get_dependencies(package_name)
        
        for dep in direct_deps:
            dependencies.append(dep)
            # Get recursive dependencies
            recursive_deps = self._get_all_dependencies(dep.name, visited.copy())
            dependencies.extend(recursive_deps)
        
        # Remove duplicates while preserving order
        unique_deps = []
        seen_names = set()
        for dep in dependencies:
            if dep.name not in seen_names:
                unique_deps.append(dep)
                seen_names.add(dep.name)
        
        # Cache the result
        self._resolution_cache[package_name] = unique_deps
        
        return unique_deps
    
    def _should_upgrade(self, package: Package) -> bool:
        """Determine if a package should be upgraded."""
        if not self.apt.is_installed(package.name):
            return False
        
        # Check if package is upgradable
        current_info = self.apt.get_package_info(package.name)
        if current_info and current_info.status == PackageStatus.UPGRADABLE:
            return True
        
        # In offline mode, check against pinned versions
        if self.config.is_offline_mode():
            pinned_version = self.config.get_pinned_version(package.name)
            if pinned_version and current_info:
                return current_info.version != pinned_version
        
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