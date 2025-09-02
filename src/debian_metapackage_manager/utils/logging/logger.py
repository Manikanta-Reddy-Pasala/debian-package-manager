"""Enhanced logging utilities for Debian Package Manager."""

import logging
import os
from pathlib import Path
from typing import Optional
from .formatters import DPMFormatter, ColoredFormatter


def setup_logging(log_level: str = "INFO", 
                 log_file: Optional[str] = None,
                 use_colors: bool = True) -> logging.Logger:
    """Set up enhanced logging configuration."""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Default log location
        log_dir = Path.home() / '.local' / 'share' / 'debian-package-manager' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = str(log_dir / 'dpm.log')
    
    # Clear any existing handlers
    root_logger = logging.getLogger('debian_metapackage_manager')
    root_logger.handlers.clear()
    
    # Set log level
    log_level_obj = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level_obj)
    
    # File handler with detailed formatting
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level_obj)
    file_handler.setFormatter(DPMFormatter())
    root_logger.addHandler(file_handler)
    
    # Console handler with colored formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only show warnings and errors on console
    
    if use_colors and os.getenv('TERM') and 'color' in os.getenv('TERM', ''):
        console_handler.setFormatter(ColoredFormatter())
    else:
        console_handler.setFormatter(DPMFormatter(include_timestamp=False))
    
    root_logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate messages
    root_logger.propagate = False
    
    root_logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f'debian_metapackage_manager.{name}')


def set_log_level(level: str) -> None:
    """Dynamically change log level."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger('debian_metapackage_manager')
    logger.setLevel(log_level)
    
    # Update all handlers
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setLevel(log_level)


def get_log_file_path() -> str:
    """Get the current log file path."""
    logger = logging.getLogger('debian_metapackage_manager')
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return handler.baseFilename
    return ""