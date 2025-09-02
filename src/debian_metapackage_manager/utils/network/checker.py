"""Network connectivity checker."""

import subprocess
from typing import Optional
from ...utils.logging import get_logger

logger = get_logger('network.checker')


class NetworkChecker:
    """Handles network connectivity checks with caching."""
    
    def __init__(self, cache_timeout: int = 30):
        """Initialize network checker with cache timeout in seconds."""
        self.cache_timeout = cache_timeout
        self._network_available: Optional[bool] = None
        self._repository_accessible: Optional[bool] = None
        self._last_check_time: float = 0
    
    def is_network_available(self, force_check: bool = False) -> bool:
        """
        Check if network connectivity is available.
        
        Args:
            force_check: Force a new check ignoring cache
            
        Returns:
            True if network is available, False otherwise
        """
        if not force_check and self._network_available is not None:
            return self._network_available
        
        try:
            logger.debug("Checking network connectivity...")
            # Try to ping a reliable DNS server
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '3', '8.8.8.8'],
                capture_output=True,
                timeout=5
            )
            self._network_available = result.returncode == 0
            logger.debug(f"Network check result: {self._network_available}")
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Network check failed: {e}")
            self._network_available = False
        
        return self._network_available
    
    def are_repositories_accessible(self, force_check: bool = False) -> bool:
        """
        Check if package repositories are accessible.
        
        Args:
            force_check: Force a new check ignoring cache
            
        Returns:
            True if repositories are accessible, False otherwise
        """
        if not force_check and self._repository_accessible is not None:
            return self._repository_accessible
        
        try:
            logger.debug("Checking repository accessibility...")
            # Try to update package cache (dry run)
            result = subprocess.run(
                ['apt-get', 'update', '--dry-run'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._repository_accessible = result.returncode == 0
            logger.debug(f"Repository check result: {self._repository_accessible}")
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Repository check failed: {e}")
            self._repository_accessible = False
        
        return self._repository_accessible
    
    def clear_cache(self) -> None:
        """Clear cached network status to force re-detection."""
        logger.debug("Clearing network cache")
        self._network_available = None
        self._repository_accessible = None
        self._last_check_time = 0
    
    def get_status(self) -> dict:
        """Get comprehensive network status."""
        return {
            'network_available': self.is_network_available(),
            'repositories_accessible': self.are_repositories_accessible(),
            'cache_valid': self._network_available is not None
        }