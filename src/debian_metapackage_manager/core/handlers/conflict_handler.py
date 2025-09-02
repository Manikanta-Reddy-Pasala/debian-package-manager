"""Conflict handling and user interaction system."""

import sys
from typing import List, Dict, Optional, Tuple
from ...models import Package, Conflict, DependencyPlan
from ..classifier import PackageClassifier
from ...config import Config


class ConflictHandler:
    """Handles package conflicts and user interactions."""
    
    def __init__(self, classifier: Optional[PackageClassifier] = None,
                 config: Optional[Config] = None):
        """Initialize conflict handler."""
        self.classifier = classifier or PackageClassifier(config)
        self.config = config or Config()
    
    def handle_conflicts(self, plan: DependencyPlan) -> Tuple[bool, DependencyPlan]:
        """Handle conflicts in a dependency plan with user interaction."""
        if not plan.conflicts and not plan.to_remove:
            return True, plan
        
        print("\n" + "="*60)
        print("PACKAGE CONFLICT RESOLUTION REQUIRED")
        print("="*60)
        
        # Show conflict details
        if plan.conflicts:
            self._display_conflicts(plan.conflicts)
        
        # Show packages that need to be removed
        if plan.to_remove:
            user_approved = self._prompt_for_removals(plan.to_remove)
            if not user_approved:
                print("Operation cancelled by user.")
                return False, plan
        
        # Show installation/upgrade summary
        if plan.to_install or plan.to_upgrade:
            self._display_operation_summary(plan)
        
        # Final confirmation
        if plan.requires_user_confirmation:
            final_approval = self._prompt_final_confirmation()
            if not final_approval:
                print("Operation cancelled by user.")
                return False, plan
        
        return True, plan
    
    def _display_conflicts(self, conflicts: List[Conflict]) -> None:
        """Display conflict information to the user."""
        print(f"\nDetected {len(conflicts)} package conflict(s):")
        print("-" * 40)
        
        for i, conflict in enumerate(conflicts, 1):
            print(f"{i}. {conflict.package.name} conflicts with {conflict.conflicting_package.name}")
            print(f"   Reason: {conflict.reason}")
            
            # Show package types
            pkg_type = self.classifier.get_package_type(conflict.package.name)
            conflict_type = self.classifier.get_package_type(conflict.conflicting_package.name)
            print(f"   Types: {conflict.package.name} ({pkg_type.value}) vs {conflict.conflicting_package.name} ({conflict_type.value})")
            print()
    
    def _prompt_for_removals(self, packages_to_remove: List[Package]) -> bool:
        """Prompt user for approval of package removals."""
        if not packages_to_remove:
            return True
        
        # Filter out protected packages and check policy
        filtered_packages, blocked_packages = self._filter_packages_for_removal(packages_to_remove)
        
        if blocked_packages:
            print(f"\n🚫 BLOCKED REMOVALS - The following packages CANNOT be removed:")
            print("-" * 70)
            for pkg in blocked_packages:
                print(f"   - {pkg.name} (v{pkg.version}) - System package (no custom prefix)")
            print()
            print("ℹ️  System packages are never removed for safety.")
            print("   Only packages with configured custom prefixes can be removed.")
            print("   Add custom prefixes with: dpm config --add-prefix 'yourprefix-'")
            print()
            
            if not filtered_packages:
                print("❌ Cannot proceed: All required removals are system packages.")
                print("   Configure custom prefixes to enable conflict resolution.")
                return False
        
        if not filtered_packages:
            return True
        
        print(f"\nThe following {len(filtered_packages)} package(s) need to be REMOVED:")
        print("-" * 50)
        
        # Categorize packages by risk level
        risk_categories = self._categorize_by_risk(filtered_packages)
        
        # Display high-risk packages first
        if risk_categories.get("HIGH"):
            print("⚠️  HIGH RISK REMOVALS (Critical System Packages):")
            for pkg in risk_categories["HIGH"]:
                print(f"   - {pkg.name} (v{pkg.version}) - CRITICAL SYSTEM PACKAGE")
            print()
        
        # Display medium-risk packages
        if risk_categories.get("MEDIUM"):
            print("⚡ MEDIUM RISK REMOVALS:")
            for pkg in risk_categories["MEDIUM"]:
                pkg_type = self.classifier.get_package_type(pkg.name)
                print(f"   - {pkg.name} (v{pkg.version}) - {pkg_type.value}")
            print()
        
        # Display low-risk packages
        if risk_categories.get("LOW"):
            print("✓ LOW RISK REMOVALS (Custom Packages):")
            for pkg in risk_categories["LOW"]:
                print(f"   - {pkg.name} (v{pkg.version}) - custom package")
            print()
        
        # Show removal summary
        summary = self.classifier.get_package_category_summary([pkg.name for pkg in filtered_packages])
        print(f"Summary: {summary}")
        print()
        
        # Prompt for confirmation
        if risk_categories.get("HIGH"):
            print("⚠️  WARNING: This operation will remove CRITICAL SYSTEM PACKAGES!")
            print("   This could make your system unstable or unusable.")
            response = self._get_user_input("Do you want to proceed with HIGH RISK removals? (type 'YES' to confirm): ")
            return response.upper() == "YES"
        else:
            response = self._get_user_input("Do you want to proceed with these removals? [y/N]: ")
            return response.lower() in ['y', 'yes']
    
    def _categorize_by_risk(self, packages: List[Package]) -> Dict[str, List[Package]]:
        """Categorize packages by removal risk level."""
        categories = {"HIGH": [], "MEDIUM": [], "LOW": []}
        
        for pkg in packages:
            risk_level = self.classifier.get_removal_risk_level(pkg.name)
            categories[risk_level].append(pkg)
        
        return categories
    
    def _display_operation_summary(self, plan: DependencyPlan) -> None:
        """Display summary of planned operations."""
        print("\nPLANNED OPERATIONS:")
        print("-" * 30)
        
        if plan.to_install:
            install_summary = self.classifier.get_package_category_summary([pkg.name for pkg in plan.to_install])
            print(f"📦 INSTALL: {install_summary}")
            for pkg in plan.to_install[:5]:  # Show first 5
                pkg_type = self.classifier.get_package_type(pkg.name)
                print(f"   + {pkg.name} (v{pkg.version}) - {pkg_type.value}")
            if len(plan.to_install) > 5:
                print(f"   ... and {len(plan.to_install) - 5} more packages")
            print()
        
        if plan.to_upgrade:
            upgrade_summary = self.classifier.get_package_category_summary([pkg.name for pkg in plan.to_upgrade])
            print(f"⬆️  UPGRADE: {upgrade_summary}")
            for pkg in plan.to_upgrade[:5]:  # Show first 5
                print(f"   ↑ {pkg.name} (v{pkg.version})")
            if len(plan.to_upgrade) > 5:
                print(f"   ... and {len(plan.to_upgrade) - 5} more packages")
            print()
    
    def _prompt_final_confirmation(self) -> bool:
        """Prompt for final confirmation of the entire operation."""
        print("\n" + "="*60)
        print("FINAL CONFIRMATION")
        print("="*60)
        print("This operation will modify your package system as described above.")
        print("All changes will be applied with appropriate force options if needed.")
        print()
        
        response = self._get_user_input("Do you want to proceed with this operation? [y/N]: ")
        return response.lower() in ['y', 'yes']
    
    def _get_user_input(self, prompt: str) -> str:
        """Get user input with proper handling."""
        try:
            return input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            return ""
    
    def _filter_packages_for_removal(self, packages: List[Package]) -> Tuple[List[Package], List[Package]]:
        """Filter packages for removal based on custom prefixes.
        
        Only packages with configured custom prefixes can be removed.
        All system packages are blocked from removal.
        """
        allowed_packages = []
        blocked_packages = []
        
        for pkg in packages:
            # Only allow removal of packages with custom prefixes
            if self.config.can_remove_package(pkg.name):
                allowed_packages.append(pkg)
            else:
                blocked_packages.append(pkg)
        
        return allowed_packages, blocked_packages
    
    def create_safe_resolution_plan(self, conflicts: List[Conflict]) -> DependencyPlan:
        """Create a safe conflict resolution plan that respects configuration policies."""
        plan = DependencyPlan(
            to_install=[],
            to_remove=[],
            to_upgrade=[],
            conflicts=conflicts,
            requires_user_confirmation=True
        )
        
        # For each conflict, determine safe resolution
        for conflict in conflicts:
            target_pkg = conflict.package
            conflicting_pkg = conflict.conflicting_package
            
            # Determine which package to remove based on policy
            pkg_to_remove = self._choose_package_for_removal(target_pkg, conflicting_pkg)
            
            if pkg_to_remove and pkg_to_remove not in plan.to_remove:
                plan.to_remove.append(pkg_to_remove)
        
        return plan
    
    def _choose_package_for_removal(self, target_pkg: Package, conflicting_pkg: Package) -> Optional[Package]:
        """Choose which package to remove in a conflict based on custom prefixes.
        
        Only packages with custom prefixes can be removed.
        Prefer removing the conflicting package (already installed) over the target.
        """
        target_can_remove = self.config.can_remove_package(target_pkg.name)
        conflicting_can_remove = self.config.can_remove_package(conflicting_pkg.name)
        
        # If neither can be removed, conflict cannot be resolved
        if not target_can_remove and not conflicting_can_remove:
            return None
        
        # If only one can be removed, remove that one
        if conflicting_can_remove and not target_can_remove:
            return conflicting_pkg
        elif target_can_remove and not conflicting_can_remove:
            return target_pkg
        
        # If both can be removed, prefer removing the conflicting package
        # (the one that's already installed and blocking the new installation)
        return conflicting_pkg
    
    def create_forced_resolution_plan(self, conflicts: List[Conflict]) -> DependencyPlan:
        """Create a plan that resolves conflicts with forced operations."""
        # Use safe resolution first
        plan = self.create_safe_resolution_plan(conflicts)
        
        # If safe resolution couldn't resolve all conflicts, mark as requiring force
        unresolved_conflicts = []
        for conflict in conflicts:
            if conflict.conflicting_package not in plan.to_remove and conflict.package not in plan.to_remove:
                unresolved_conflicts.append(conflict)
        
        if unresolved_conflicts:
            plan.conflicts = unresolved_conflicts
            plan.requires_force_mode = True
        
        return plan
    
    def display_operation_result(self, success: bool, packages_affected: List[Package], 
                               warnings: List[str], errors: List[str]) -> None:
        """Display the result of an operation."""
        print("\n" + "="*60)
        if success:
            print("✅ OPERATION COMPLETED SUCCESSFULLY")
        else:
            print("❌ OPERATION FAILED")
        print("="*60)
        
        if packages_affected:
            print(f"\nPackages affected ({len(packages_affected)}):")
            for pkg in packages_affected:
                status_icon = "✓" if success else "✗"
                print(f"  {status_icon} {pkg.name} (v{pkg.version})")
        
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  - {warning}")
        
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")
        
        print()
    
    def prompt_for_force_mode(self, operation: str, package_name: str) -> bool:
        """Prompt user whether to use force mode for an operation."""
        print(f"\n⚠️  {operation.upper()} FAILED for package: {package_name}")
        print("This might be due to dependency conflicts or package locks.")
        print()
        print("Force mode options:")
        print("  - Ignore dependency conflicts")
        print("  - Override package locks")
        print("  - Remove essential packages if needed")
        print()
        
        response = self._get_user_input(f"Do you want to retry with FORCE mode? [y/N]: ")
        return response.lower() in ['y', 'yes']
    
    def display_package_info(self, package: Package, dependencies: List[Package]) -> None:
        """Display detailed package information."""
        print(f"\nPackage Information: {package.name}")
        print("-" * 40)
        print(f"Version: {package.version}")
        print(f"Status: {package.status.value}")
        print(f"Type: {self.classifier.get_package_type(package.name).value}")
        print(f"Custom Package: {'Yes' if self.classifier.is_custom_package(package.name) else 'No'}")
        print(f"Metapackage: {'Yes' if self.classifier.is_metapackage(package.name) else 'No'}")
        print(f"Removal Risk: {self.classifier.get_removal_risk_level(package.name)}")
        
        if dependencies:
            print(f"\nDependencies ({len(dependencies)}):")
            for dep in dependencies[:10]:  # Show first 10
                dep_type = self.classifier.get_package_type(dep.name)
                print(f"  - {dep.name} (v{dep.version}) - {dep_type.value}")
            if len(dependencies) > 10:
                print(f"  ... and {len(dependencies) - 10} more dependencies")
        
        print()


class UserPrompt:
    """Helper class for user prompts and confirmations."""
    
    @staticmethod
    def confirm_operation(message: str, default: bool = False) -> bool:
        """Get user confirmation for an operation."""
        suffix = "[Y/n]" if default else "[y/N]"
        try:
            response = input(f"{message} {suffix}: ").strip().lower()
            if not response:
                return default
            return response in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            return False
    
    @staticmethod
    def select_from_options(prompt: str, options: List[str]) -> Optional[str]:
        """Let user select from a list of options."""
        print(f"\n{prompt}")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        
        try:
            while True:
                response = input(f"Select option (1-{len(options)}): ").strip()
                try:
                    index = int(response) - 1
                    if 0 <= index < len(options):
                        return options[index]
                    else:
                        print(f"Please enter a number between 1 and {len(options)}")
                except ValueError:
                    print("Please enter a valid number")
        except (KeyboardInterrupt, EOFError):
            return None
    
    @staticmethod
    def get_text_input(prompt: str, required: bool = True) -> Optional[str]:
        """Get text input from user."""
        try:
            while True:
                response = input(f"{prompt}: ").strip()
                if response or not required:
                    return response if response else None
                print("This field is required. Please enter a value.")
        except (KeyboardInterrupt, EOFError):
            return None