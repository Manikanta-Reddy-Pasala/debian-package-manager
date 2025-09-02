"""Data models for Debian Package Manager."""

from .package import Package, PackageStatus, PackageType
from .operations import OperationResult, DependencyPlan, Conflict

__all__ = ['Package', 'PackageStatus', 'PackageType', 'OperationResult', 'DependencyPlan', 'Conflict']