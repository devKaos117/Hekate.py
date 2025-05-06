"""
Arch Method - Abstract base class for version checking strategies

This module defines the ArchMethod abstract class that all concrete
version checking strategies should inherit from
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

import kronos

from ..utils.http import HTTPy


class ArchMethod(ABC):
    """
    Abstract base class for version checking strategies
    
    All concrete version checking strategies should inherit from this class and
    implement its abstract methods
    """
    
    def __init__(self, logger: kronos.Logger, client: HTTPy):
        """
        Initialize the strategy with the configurations dictionary and a RateLimiter
        
        Args:
            rate_limiter: The RateLimiter instance
        """
        self._logger = logger
        self._client = client
    
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
    def get_version(self, software_name: str) -> Dict[str, Any]:
        """
        Get the latest version information for the software
        
        Args:
            software_name: The common name of the software
            
        Returns:
            A dictionary containing version information following https://github.com/devKaos117/Hekate.py/blob/main/documentation/schema/version.schema.json
        """
        pass