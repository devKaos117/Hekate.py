"""
Google Strategy - Search for software versions using Google search

This module provides a strategy for finding software version information
by parsing Google search results
"""

from typing import Dict

from bs4 import BeautifulSoup

from .archmethod import ArchMethod
from ..utils.version import extract_version_numbers


class GoogleStrategy(ArchMethod):
    """
    Strategy for finding software versions using Google search
    
    This strategy performs a Google search for the software name along with terms
    like "latest version" and parses the search results to find version information
    """
    
    def can_handle(self, software_name: str) -> bool:
        """
        This strategy can handle any software
        
        Args:
            software_name: The common name of the software
            
        Returns:
            True for all software names
        """
        return True
    
    def get_version(self, software_name: str) -> Dict:
        """
        Get the latest version by searching Google
        
        Args:
            software_name: The common name of the software
            
        Returns:
            A dictionary containing version information
        """
        result = {
            'latest_version': None,
            'download_url': None,
            'release_date': None,
            'source': 'GoogleStrategy'
        }
        
        # Craft search query
        search_terms = [
            f"{software_name} latest version",
            f"{software_name} current version",
            f"{software_name} download latest version"
        ]
        
        versions = set()
        download_urls = set()
        
        for search_term in search_terms:
            try:
                url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                response = self.checker.make_request(url)
                
                if not response:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract possible version numbers from search results
                search_results = soup.select('.g')
                
                for item in search_results:
                    # Extract text from title and snippet
                    title_elem = item.select_one('h3')
                    snippet_elem = item.select_one('.VwiC3b')
                    
                    if title_elem:
                        title_text = title_elem.get_text()
                        title_versions = extract_version_numbers(title_text)
                        versions.update(title_versions)
                    
                    if snippet_elem:
                        snippet_text = snippet_elem.get_text()
                        snippet_versions = extract_version_numbers(snippet_text)
                        versions.update(snippet_versions)
                    
                    # Extract download URL if present
                    link_elem = item.select_one('a')
                    if link_elem and 'href' in link_elem.attrs:
                        link = link_elem['href']
                        if 'download' in link.lower() and software_name.lower() in link.lower():
                            download_urls.add(link)
                
                # Look for "featured snippet" which often contains the latest version
                featured_snippet = soup.select_one('.hgKElc')
                if featured_snippet:
                    snippet_text = featured_snippet.get_text()
                    snippet_versions = extract_version_numbers(snippet_text)
                    versions.update(snippet_versions)
                
            except Exception as e:
                self.checker.logger.warning(
                    f"Error searching Google for {software_name}: {str(e)}")
        
        # Find the highest version number from all the versions we collected
        if versions:
            from ..utils.version_parser import compare_versions
            latest_version = sorted(versions, key=lambda v: compare_versions("0", v))[0]
            for version in versions:
                if compare_versions(version, latest_version) > 0:
                    latest_version = version
            
            result['latest_version'] = latest_version
        
        # Add a download URL if we found one
        if download_urls:
            result['download_url'] = list(download_urls)[0]
        
        return result