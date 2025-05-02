"""
Website Strategy - Check official websites for software versions

This module provides a strategy for finding software version information
by checking the official websites of common software
"""

import re
from typing import Dict

from bs4 import BeautifulSoup

from .archmethod import ArchMethod
from ..utils.version import extract_version_numbers


class WebsiteStrategy(ArchMethod):
    """
    Strategy for finding software versions by checking official websites
    
    This strategy contains a mapping of software names to their official websites
    and implements custom parsing logic for each supported website
    """
    
    # Mapping of software names (lowercase) to their official websites and selectors
    WEBSITE_MAP = {
        'firefox': {
            'url': 'https://www.mozilla.org/en-US/firefox/new/',
            'version_selector': '.c-release-version',
            'download_selector': '.download-link'
        },
        'chrome': {
            'url': 'https://www.google.com/chrome/',
            'version_regex': r'Chrome\s+(\d+\.\d+\.\d+\.\d+)',
        },
        'vlc': {
            'url': 'https://www.videolan.org/vlc/',
            'version_selector': '.get-vlc-release'
        },
        'vmware': {
            'url': 'https://www.vmware.com/products/workstation-pro.html',
            'version_regex': r'VMware Workstation (\d+\.?\d*)',
        },
        'visual studio code': {
            'url': 'https://code.visualstudio.com/updates',
            'version_selector': '.release .title'
        },
        'nodejs': {
            'url': 'https://nodejs.org/en/',
            'version_selector': '.home-downloadbutton'
        },
        'python': {
            'url': 'https://www.python.org/downloads/',
            'version_selector': '.download-for-current-os .download-os-windows a',
            'version_regex': r'Python\s+(\d+\.\d+\.\d+)'
        }
        # More software can be added here
    }
    
    # Aliases mapping (e.g., "vs code" -> "visual studio code")
    ALIASES = {
        'vs code': 'visual studio code',
        'vscode': 'visual studio code',
        'chrome browser': 'chrome',
        'google chrome': 'chrome',
        'mozilla firefox': 'firefox',
        'vmware workstation': 'vmware',
        'vmware workstation pro': 'vmware',
        'node.js': 'nodejs',
        'node': 'nodejs'
    }
    
    def can_handle(self, software_name: str) -> bool:
        """
        Check if this strategy can handle the given software
        
        Args:
            software_name: The common name of the software
            
        Returns:
            True if the software is in our website map or aliases
        """
        name_lower = software_name.lower()
        return name_lower in self.WEBSITE_MAP or name_lower in self.ALIASES
    
    def get_version(self, software_name: str) -> Dict:
        """
        Get the latest version by checking the software's official website
        
        Args:
            software_name: The common name of the software
            
        Returns:
            A dictionary containing version information
        """
        result = {
            'software': software_name,
            'latest_version': None,
            'download_url': None,
            'release_date': None,
            'source': 'WebsiteStrategy'
        }
        
        # Normalize the software name
        name_lower = software_name.lower()
        if name_lower in self.ALIASES:
            name_lower = self.ALIASES[name_lower]
        
        if name_lower not in self.WEBSITE_MAP:
            return result
        
        website_info = self.WEBSITE_MAP[name_lower]
        url = website_info['url']
        
        try:
            response = self.checker.make_request(url)
            if not response:
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract version based on configured selector or regex
            version = None
            if 'version_selector' in website_info:
                element = soup.select_one(website_info['version_selector'])
                if element:
                    text = element.get_text().strip()
                    if 'version_regex' in website_info:
                        match = re.search(website_info['version_regex'], text)
                        if match:
                            version = match.group(1)
                    else:
                        versions = extract_version_numbers(text)
                        if versions:
                            version = versions[0]
            
            elif 'version_regex' in website_info:
                matches = re.findall(website_info['version_regex'], response.text)
                if matches:
                    version = matches[0]
            
            # Extract download URL if configured
            download_url = None
            if 'download_selector' in website_info:
                download_elem = soup.select_one(website_info['download_selector'])
                if download_elem and 'href' in download_elem.attrs:
                    download_url = download_elem['href']
                    # Make absolute URL if it's relative
                    if download_url.startswith('/'):
                        from urllib.parse import urljoin
                        download_url = urljoin(url, download_url)
            
            # Update the result
            if version:
                result['latest_version'] = version
            if download_url:
                result['download_url'] = download_url
                
        except Exception as e:
            self.checker.logger.warning(
                f"Error checking website for {software_name}: {str(e)}")
        
        return result