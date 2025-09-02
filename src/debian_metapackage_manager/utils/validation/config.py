"""Configuration validation utilities."""

from typing import Dict, Any, List
from ...exceptions import ConfigValidationError


def validate_config(config_data: Dict[str, Any]) -> bool:
    """
    Validate configuration data.
    
    Args:
        config_data: Configuration dictionary to validate
        
    Returns:
        True if valid
        
    Raises:
        ConfigValidationError: If configuration is invalid
    """
    if not isinstance(config_data, dict):
        raise ConfigValidationError("config", str(type(config_data)), "must be a dictionary")
    
    # Validate custom prefixes
    if 'custom_prefixes' in config_data:
        _validate_custom_prefixes(config_data['custom_prefixes'])
    
    # Validate offline mode setting
    if 'offline_mode' in config_data:
        _validate_offline_mode(config_data['offline_mode'])
    
    return True


def _validate_custom_prefixes(prefixes: Any) -> None:
    """Validate custom prefixes configuration."""
    if not isinstance(prefixes, list):
        raise ConfigValidationError("custom_prefixes", str(type(prefixes)), "must be a list")
    
    for i, prefix in enumerate(prefixes):
        if not isinstance(prefix, str):
            raise ConfigValidationError(
                f"custom_prefixes[{i}]", str(type(prefix)), "must be a string"
            )
        
        if not prefix:
            raise ConfigValidationError(
                f"custom_prefixes[{i}]", "empty string", "cannot be empty"
            )
        
        if not prefix.replace('-', '').replace('_', '').isalnum():
            raise ConfigValidationError(
                f"custom_prefixes[{i}]", prefix, 
                "must contain only alphanumeric characters, hyphens, and underscores"
            )


def _validate_offline_mode(offline_mode: Any) -> None:
    """Validate offline mode setting."""
    if not isinstance(offline_mode, bool):
        raise ConfigValidationError("offline_mode", str(type(offline_mode)), "must be a boolean")