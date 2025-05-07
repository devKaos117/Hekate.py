"""
Wikipedia Method - Search for software versions using Wikipedia pages

This module provides a method for finding software version information
by searching for Wikipedia pages on the software
"""
from typing import Dict, Any

from bs4 import BeautifulSoup

from .archmethod import ArchMethod
from ..utils.version import VersionCheck


class WikipediaMethod(ArchMethod):
    """
    Method for finding software versions using Wikipedia pages
    
    This method performs a Wikipedia search for a page dedicated
    to the software and tries to extract the latest version from there
    """
    
    def can_handle(self, software_name: str) -> bool:
        """
        This method can handle any software
        
        Args:
            software_name: The common name of the software
            
        Returns:
            True for all software names
        """
        return True
    
    def get_version(self, software_name: str) -> Dict[str, Any]:
        """
        Get the latest version by lookin on Wikipedia
        
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

        # Search for the page
        langs = ["en", "pt"]
        page_id = None
        wiki_page = None

        for lang in langs:
            search_url = f"https://{lang}.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "format": "json",
                "generator": "prefixsearch",
                "redirects": None,
                "gpssearch": software_name,
                "gpslimit": "1",
                "gpsnamespace": 0
            }

            try:
                response = self._client.get(url=search_url, params=search_params)
                if not response:
                    continue
                
                data = response.json()
                if len(data['query']['pages']) == 0:
                    continue
                
                page_id = list(data['query']['pages'].keys())[0]
                
                # Grab the page
                url = f"https://{lang}.wikipedia.org/w/index.php"
                params = { "curid": page_id }

                wiki_page = self._client.get(url=url, params=params)
                if not wiki_page:
                    continue

                soup = BeautifulSoup(wiki_page.text, "html.parser")
                result["source_url"] = wiki_page.url
                break
            except Exception as e:
                self._logger.warning(f"Error searching Wikipedia page for {software_name} ({lang}): {str(e)}")

        if not wiki_page:
            self._logger.warning(f"No results searching Wikipedia page for {software_name}")
            return result
        
        # Look for the version
        infobox = soup.find("table", class_="infobox")
        table = infobox.find("tbody")

        for row in rows:
            if isinstance(row.text, str):
                attempt = VersionCheck.extract(row.text)
            if attempt:
                break

        
        result["latest_version"] = attempt

        return result