"""
"""
import os, importlib, inspect
from typing import Dict, List, Any, Optional

import kronos

from .methods.archmethod import ArchMethod
from . import methods as methods_pkg
from .utils import version
from .utils import configuration


class UpdateFinder:
    def __init__(self, logger: kronos.Logger, rate_limiter: kronos.RateLimiter = None, config: Dict[str, Any] = None):
        """"""
        default_config = {
            "http": {
                "headers": {
                    "Accept": "text/html,application/xhtml+xml,application/xml",
                    "Accept-Language": "en-US, en",
                    "Referer": "https://www.google.com/",
                    "DNT": "1"
                },
                "max-retries": 3,
                "timeout": 10
            }
        }
        self._logger = logger
        self._rate_limiter = rate_limiter
        self._config = configuration.import_config(config, default_config)
    
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
                    module = importlib.import_module(f'.methods.{module_name}', package=__package__)
                    
                    # Find all classes in the module that inherit from ArchMethod
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, ArchMethod) and obj.__module__ == module.__name__ and name != 'ArchMethod'):
                            self._methods.append(self._config, self._rate_limiter)
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
            A dictionary containing version information or None
            {
                'current_version': Current version (if provided),
                'latest_version': Latest version found,
                'update_found': Boolean indicating if update is available,
                'download_url': URL to download the latest version (if available),
                'release_date': Release date of the latest version (if available),
                'source': Name of the strategy that provided the result
            }
        """
        self._logger.info(f"Checking latest version for {software_name}")
        
        results = []
        
        # Execute each strategy and collect results
        for method in self._methods:
            try:
                if not method.can_handle(software_name):
                    continue
                
                result = method.get_version(software_name)
                if result and result.get('latest_version'):
                    results.append(result)
                    self._logger.info(f"Found version {result['latest_version']} via {method.__class__.__name__}")
            except Exception as e:
                self._logger.exception(f"Error in method {method.__class__.__name__}: {e}")
        
        if not results:
            self._logger.warning(f"No version information found")
            return None
        
        best_result = results[0]
        
        for result in results[1:]:
            if version.compare_versions(result['latest_version'], best_result['latest_version']) > 0:
                best_result = result
        
        # Determine if an update is available
        if current_version and best_result['latest_version']:
            best_result['current_version'] = current_version
            best_result['update_found'] = version.compare(best_result['latest_version'], current_version) > 0
        else:
            best_result['current_version'] = current_version
            best_result['update_found'] = False
        
        return best_result