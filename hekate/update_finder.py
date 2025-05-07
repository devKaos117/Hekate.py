"""
"""
import os, importlib, inspect
from typing import Dict, List, Any, Optional

import kronos

from . import methods as methods_pkg
from .methods.archmethod import ArchMethod
from .utils import version
from .utils import configuration
from .utils.http import HTTPy


class UpdateFinder:
    
    _DEFAULT_CONFIG = {
        "methods": ["google", "wikipedia", "cve_details", "provider"],
        "httpy": {
            "randomize-agent": True,
            "max-retries": 3,
            "retry_status_codes": [429, 500, 502, 503, 504],
            "success_status_codes": [200, 201, 202, 203, 204, 205, 206, 207, 208],
            "timeout": 10,
            "headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml,application/json",
                "Accept-Language": "en-US,en,pt-BR,pt",
                "Cache-Control": "no-cache",
                "Referer": "https://www.google.com/",
                "DNT": "1"
            }
        }
    }

    def __init__(self, logger: kronos.Logger, rate_limiter: Optional[kronos.RateLimiter] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize UpdateFinder

        Args:
            logger: kronos.Logger instance
            rate_limiter: kronos.RateLimiter instance
            config: Configurations dictionary following https://github.com/devKaos117/Hekate.py/blob/main/documentation/schema/config.schema.json
        """
        self._logger = logger
        self._rate_limiter = rate_limiter
        self._config = configuration.import_config(config, self._DEFAULT_CONFIG)
        self._client = self._create_client()

        self._load_methods(self._config['methods'])
        self._logger.debug("UpdateFinder config", self._config)
        self._logger.info("UpdateFinder initialized")
    
    def _create_client(self) -> HTTPy:
        """
        Create and configure a HTTPy client with API key.
        
        Returns:
            Configured HTTPy instance
        """
        return HTTPy(self._logger, self._config["httpy"], self._rate_limiter)

    def _load_methods(self, methods_names: Optional[List[str]] = None):
        """
        Load all available methods
        
        Args:
            methods_names: Optional list of methods names to load
        """
        self._methods = []
        
        # Get the directory of the methods package
        methods_dir = os.path.dirname(methods_pkg.__file__)
        
        # Import all Python files in the methods directory
        for filename in os.listdir(methods_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # Remove .py extension
                
                # Skip if specific methods were requested and this isn't one of them
                if methods_names and module_name not in methods_names:
                    continue
                
                # Import the module
                try:
                    module = importlib.import_module(f".methods.{module_name}", package=__package__)
                    
                    # Find all classes in the module that inherit from ArchMethod
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, ArchMethod) and obj.__module__ == module.__name__ and name != "ArchMethod"):
                            self._methods.append(obj(self._logger, self._client))
                            self._logger.debug(f"Loaded method: {name}")
                
                except (ImportError, AttributeError) as e:
                    self._logger.error(f"Failed to load method module {module_name}: {e}")
    
    def find_latest(self, software_name: str, current_version: Optional[str] = None) -> Dict[str, str]:
        """
        Find the latest version of the specified software
        
        Args:
            software_name: The common name of the software
            current_version: Optional string with the currently installed version
        
        Returns:
            A dictionary containing version information or None, following https://github.com/devKaos117/Hekate.py/blob/main/documentation/schema/version.schema.json
        """
        results = []
        self._logger.info(f"Searching for update to {software_name}")
        # Execute each method and collect results
        for method in self._methods:
            try:
                if not method.can_handle(software_name):
                    continue
                
                result = method.get_version(software_name)

                if result and result.get('latest_version'):
                    results.append(result)
                    self._logger.debug(f"Found version {result['latest_version']} via {method.__class__.__name__}")
            except Exception as e:
                self._logger.exception(f"Error in method {method.__class__.__name__}: {e}")
        
        if not results:
            self._logger.warning(f"No version information found")
            return None
        
        best_result = version.VersionCheck.find_higher(results)
        
        # Determine if an update is available
        best_result['current_version'] = current_version
        best_result['update_found'] = version.VersionCheck.compare(best_result['latest_version'], ">", current_version)
        
        return best_result