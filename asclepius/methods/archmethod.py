"""
Arch Method - Abstract base class for version checking strategies

This module defines the ArchMethod abstract class that all concrete
version checking strategies should inherit from
"""
import kronos
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ArchMethod(ABC):
    """
    Abstract base class for version checking strategies
    
    All concrete version checking strategies should inherit from this class and
    implement its abstract methods
    """
    
    def __init__(self, config: Dict[str, Any] = None, rate_limiter: Optional[kronos.RateLimiter] = None):
        """
        Initialize the strategy with the configurations dictionary and a RateLimiter
        
        Args:
            rate_limiter: The RateLimiter instance
        """
        if rate_limiter:
            self._rate_limiter = rate_limiter
    
    @abstractmethod
    def can_handle(self, software_name: str) -> bool:
        """
        Determine if this strategy can handle the given software
        
        Args:
            software_name: The common name of the software
            
        Returns:
            True if this strategy can handle the software, False otherwise
        """
        pass
    
    @abstractmethod
    def get_version(self, software_name: str) -> Dict:
        """
        Get the latest version information for the software
        
        Args:
            software_name: The common name of the software
            
        Returns:
            A dictionary containing version information:
            {
                'latest_version': Latest version found,
                'download_url': URL to download the latest version (if available),
                'release_date': Release date of the latest version (if available),
                'source': Name of the strategy that provided the result
            }
        """
        pass