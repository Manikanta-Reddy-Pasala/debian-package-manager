"""Custom logging formatters for Debian Package Manager."""

import logging
from typing import Optional


class DPMFormatter(logging.Formatter):
    """Custom formatter for DPM logs."""
    
    def __init__(self, include_timestamp: bool = True):
        """Initialize DPM formatter."""
        if include_timestamp:
            fmt = '%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s'
        else:
            fmt = '%(name)-30s | %(levelname)-8s | %(message)s'
        
        super().__init__(fmt, datefmt='%Y-%m-%d %H:%M:%S')
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with enhanced information."""
        # Shorten logger name for readability
        if record.name.startswith('debian_metapackage_manager.'):
            record.name = record.name.replace('debian_metapackage_manager.', 'dpm.')
        
        return super().format(record)


class ColoredFormatter(DPMFormatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        # Store original levelname
        original_levelname = record.levelname
        
        # Add colors
        record.levelname = f"{level_color}{record.levelname}{reset_color}"
        
        # Format the message
        formatted = super().format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        
        return formatted