"""Table formatting utilities for user confirmations and package displays."""

from typing import List, Dict, Any, Optional, Union
from ..models import Package


class TableFormatter:
    """Utility class for formatting tables in CLI output."""
    
    @staticmethod
    def format_packages_table(packages: List[Package], 
                            columns: Optional[List[str]] = None,
                            title: str = "Packages") -> str:
        """Format a list of packages into a table."""
        if not packages:
            return f"No {title.lower()} to display."
        
        # Default columns if not specified
        if columns is None:
            columns = ["S.No", "Package Name", "Version", "Type", "Status"]
        
        # Calculate column widths
        widths = {}
        
        # Header widths
        for col in columns:
            widths[col] = len(col)
        
        # Data widths
        for i, pkg in enumerate(packages, 1):
            data = TableFormatter._get_package_data(pkg, i)
            for col in columns:
                if col in data:
                    widths[col] = max(widths[col], len(str(data[col])))
        
        # Minimum column widths
        for col in columns:
            widths[col] = max(widths[col], 8)
        
        # Build table
        lines = []
        
        # Title
        total_width = sum(widths.values()) + len(columns) * 3 + 1
        lines.append("┌" + "─" * (total_width - 2) + "┐")
        title_line = f"│ {title.center(total_width - 4)} │"
        lines.append(title_line)
        lines.append("├" + "─" * (total_width - 2) + "┤")
        
        # Header
        header_parts = []
        for col in columns:
            header_parts.append(f" {col:<{widths[col]}} ")
        header_line = "│" + "│".join(header_parts) + "│"
        lines.append(header_line)
        
        # Separator
        sep_parts = []
        for col in columns:
            sep_parts.append("─" * (widths[col] + 2))
        sep_line = "├" + "┼".join(sep_parts) + "┤"
        lines.append(sep_line)
        
        # Data rows
        for i, pkg in enumerate(packages, 1):
            data = TableFormatter._get_package_data(pkg, i)
            row_parts = []
            for col in columns:
                value = str(data.get(col, "N/A"))
                row_parts.append(f" {value:<{widths[col]}} ")
            row_line = "│" + "│".join(row_parts) + "│"
            lines.append(row_line)
        
        # Bottom border
        lines.append("└" + "─" * (total_width - 2) + "┘")
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_package_data(pkg: Package, index: int) -> Dict[str, str]:
        """Extract data from package for table display."""
        from .classifier import PackageClassifier
        from ..config import Config
        
        config = Config()
        classifier = PackageClassifier(config)
        
        pkg_type = "Custom" if pkg.is_custom else "System"
        if pkg.is_metapackage:
            pkg_type = "Metapackage"
        
        status = pkg.status.value if hasattr(pkg, 'status') and pkg.status else "Unknown"
        
        return {
            "S.No": str(index),
            "Package Name": pkg.name,
            "Version": pkg.version or "N/A",
            "Type": pkg_type,
            "Status": status,
            "Risk Level": classifier.get_removal_risk_level(pkg.name) if hasattr(classifier, 'get_removal_risk_level') else "Unknown"
        }
    
    @staticmethod
    def format_dependency_impact_table(package_name: str, 
                                     dependencies_to_remove: List[Package],
                                     dependents_affected: List[Package]) -> str:
        """Format dependency impact analysis into a table."""
        lines = []
        
        if dependencies_to_remove:
            lines.append(f"\n📦 Dependencies that will be REMOVED when removing '{package_name}':")
            lines.append(TableFormatter.format_packages_table(
                dependencies_to_remove, 
                columns=["S.No", "Package Name", "Version", "Type", "Risk Level"],
                title="Dependencies to Remove"
            ))
        
        if dependents_affected:
            lines.append(f"\n⚠️  Packages that DEPEND on '{package_name}' (may break):")
            lines.append(TableFormatter.format_packages_table(
                dependents_affected,
                columns=["S.No", "Package Name", "Version", "Type"],
                title="Affected Dependents"
            ))
        
        return "\n".join(lines)
    
    @staticmethod
    def format_installation_conflicts_table(package_name: str,
                                          conflicts_to_remove: List[Package]) -> str:
        """Format installation conflicts into a table."""
        if not conflicts_to_remove:
            return ""
        
        lines = []
        lines.append(f"\n⚠️  Packages that conflict with '{package_name}' and need to be REMOVED:")
        lines.append(TableFormatter.format_packages_table(
            conflicts_to_remove,
            columns=["S.No", "Package Name", "Version", "Type", "Risk Level"],
            title="Conflicting Packages to Remove"
        ))
        
        return "\n".join(lines)