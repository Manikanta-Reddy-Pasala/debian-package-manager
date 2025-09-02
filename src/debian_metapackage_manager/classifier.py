"""Package classification and recognition system."""

from typing import List, Optional
from .models import PackageType
from .config import Config


class PackageClassifier:
    """Classifies packages as custom, system, or metapackage."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize with configuration."""
        self.config = config or Config()
        self._metapackage_indicators = [
            'meta-', 'bundle-', 'suite-', 'collection-'
        ]
    
    def is_custom_package(self, package_name: str) -> bool:
        """Check if package is a custom package using prefixes."""
        custom_prefixes = self.config.get_custom_prefixes()
        return any(package_name.startswith(prefix) for prefix in custom_prefixes)
    
    def is_metapackage(self, package_name: str) -> bool:
        """Check if package is likely a metapackage."""
        # Check for metapackage indicators in name
        for indicator in self._metapackage_indicators:
            if indicator in package_name.lower():
                return True
        
        # Custom packages with certain patterns are likely metapackages
        if self.is_custom_package(package_name):
            metapackage_patterns = ['meta', 'bundle', 'suite', 'all', 'full']
            package_lower = package_name.lower()
            return any(pattern in package_lower for pattern in metapackage_patterns)
        
        return False
    
    def get_package_type(self, package_name: str) -> PackageType:
        """Determine the type of package."""
        if self.is_metapackage(package_name):
            return PackageType.METAPACKAGE
        elif self.is_custom_package(package_name):
            return PackageType.CUSTOM
        else:
            return PackageType.SYSTEM
    
    def classify_packages(self, package_names: List[str]) -> dict:
        """Classify multiple packages and return categorized results."""
        result = {
            'custom': [],
            'system': [],
            'metapackage': []
        }
        
        for package_name in package_names:
            package_type = self.get_package_type(package_name)
            if package_type == PackageType.CUSTOM:
                result['custom'].append(package_name)
            elif package_type == PackageType.SYSTEM:
                result['system'].append(package_name)
            elif package_type == PackageType.METAPACKAGE:
                result['metapackage'].append(package_name)
        
        return result
    
    def should_prioritize_preservation(self, package_name: str) -> bool:
        """Determine if package should be prioritized for preservation during conflicts."""
        package_type = self.get_package_type(package_name)
        
        # System packages have highest priority for preservation
        if package_type == PackageType.SYSTEM:
            return True
        
        # Critical system packages (additional check)
        critical_patterns = [
            'libc', 'systemd', 'kernel', 'init', 'base-', 'essential',
            'apt', 'dpkg', 'ubuntu-', 'debian-'
        ]
        
        package_lower = package_name.lower()
        return any(pattern in package_lower for pattern in critical_patterns)
    
    def get_removal_risk_level(self, package_name: str) -> str:
        """Get risk level for removing a package."""
        if self.should_prioritize_preservation(package_name):
            return "HIGH"
        elif self.get_package_type(package_name) == PackageType.METAPACKAGE:
            return "MEDIUM"
        elif self.get_package_type(package_name) == PackageType.CUSTOM:
            return "LOW"
        else:
            return "MEDIUM"
    
    def add_metapackage_indicator(self, indicator: str) -> None:
        """Add a new metapackage indicator pattern."""
        if indicator not in self._metapackage_indicators:
            self._metapackage_indicators.append(indicator)
    
    def get_package_category_summary(self, package_names: List[str]) -> str:
        """Get a human-readable summary of package categories."""
        classified = self.classify_packages(package_names)
        
        summary_parts = []
        if classified['metapackage']:
            summary_parts.append(f"{len(classified['metapackage'])} metapackage(s)")
        if classified['custom']:
            summary_parts.append(f"{len(classified['custom'])} custom package(s)")
        if classified['system']:
            summary_parts.append(f"{len(classified['system'])} system package(s)")
        
        return ", ".join(summary_parts) if summary_parts else "No packages"