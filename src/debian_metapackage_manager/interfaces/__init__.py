"""System interfaces for Debian Package Manager."""

from .base import PackageInterface, DependencyResolverInterface, ConfigInterface
from .apt import APTInterface
from .dpkg import DPKGInterface

__all__ = [
    'PackageInterface', 'DependencyResolverInterface', 'ConfigInterface',
    'APTInterface', 'DPKGInterface'
]