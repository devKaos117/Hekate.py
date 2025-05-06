"""
Google Strategy - Search for software versions using Google search

This module provides a strategy for finding software version information
by parsing Google search results
"""

from typing import Dict

from bs4 import BeautifulSoup

from .archmethod import ArchMethod
from ..utils.version import VersionCheck


class GoogleMethod(ArchMethod):
    """
    Method for finding software versions using Google search
    
    This method performs a Google search for the software name along with terms
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
            A dictionary containing version information following https://github.com/devKaos117/Hekate.py/blob/main/documentation/schema/version.schema.json
        """
        result = {
            "current_version": None,
            "latest_version": None,
            "update_found": False,
            "source_url": None,
            "release_date": None,
            "method": "google"
        }
        
        # Craft search query
        search_terms = [
            f"{software_name} latest version",
            f"{software_name} current version",
            f"{software_name} changelog",
            f"{software_name} download latest version"
        ]
        
        versions = []
        source_urls = []
        
        for search_term in search_terms[:3]:
            try:
                url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                response = self._client.get(url)
                
                if not response:
                    continue
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract possible version numbers from search results
                search_results = soup.find_all(class_="MjjYud")
                
                for item in search_results:
                    # Extract text from title and snippet
                    title_elem = item.select_one("h3")
                    snippet_elem = item.find(class_="VwiC3b")
                    
                    if title_elem:
                        title_text = title_elem.get_text()
                        title_versions = VersionCheck.extract(title_text)
                        versions.append(title_versions)
                    
                    if snippet_elem:
                        snippet_text = snippet_elem.get_text()
                        snippet_versions = VersionCheck.extract(snippet_text)
                        versions.append(snippet_versions)
                    
                    # Extract download URL if present
                    link_elem = item.select_one("a")
                    link_keywords = ["download", "updates", "changelog", "release", software_name.lower()]

                    if link_elem and "href" in link_elem.attrs:
                        link = link_elem["href"]
                        if any(keyword in link.lower() for keyword in link_keywords):
                            source_urls.append(link)
                
                # Look for "featured snippet" which often contains the latest version
                featured_snippet = soup.select_one(".hgKElc")
                if featured_snippet:
                    snippet_text = featured_snippet.get_text()
                    snippet_versions = VersionCheck.extract(snippet_text)
                    versions.append(snippet_versions)
                    
                
            except Exception as e:
                self._logger.warning(f"Error searching Google for {software_name}: {str(e)}")
        
        # Find the highest version number from all the versions we collected
        if versions:
            latest_version = versions[0]
            for ver in versions:
                if VersionCheck.compare(ver, ">", latest_version ):
                    latest_version = ver
            
            result["latest_version"] = latest_version
        
        # Add a download URL if we found one
        if source_urls:
            result["source_url"] = list(source_urls)[0]
        
        return result