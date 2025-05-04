"""
HTML Utilities - Helper functions for processing HTML

This module provides functions for parsing and extracting information from HTML 
content during web scraping operations
"""

import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def extract_text_around_version(soup: BeautifulSoup, search_term: str, context_chars: int = 100) -> List[str]:
    """
    Extract text fragments containing the search term
    
    Args:
        soup: BeautifulSoup object representing an HTML document
        search_term: The term to search for (e.g., "version")
        context_chars: Number of characters to include before and after matches
        
    Returns:
        List of text fragments containing the search term
    """
    # Convert the BeautifulSoup object to plain text
    text = soup.get_text(" ", strip=True)
    
    # Find all occurrences of the search term
    fragments = []
    pattern = re.compile(search_term, re.IGNORECASE)
    
    for match in pattern.finditer(text):
        start = max(0, match.start() - context_chars)
        end = min(len(text), match.end() + context_chars)
        
        # Extract the fragment
        fragment = text[start:end]
        fragments.append(fragment)
    
    return fragments


def find_version_in_meta_tags(soup: BeautifulSoup) -> Optional[str]:
    """
    Search for version information in meta tags
    
    Args:
        soup: BeautifulSoup object representing an HTML document
        
    Returns:
        Version string if found, None otherwise
    """
    version_meta_attrs = [
        "version",
        "application-version",
        "app-version",
        "software-version",
        "product-version"
    ]
    
    for attr in version_meta_attrs:
        meta_tag = soup.find("meta", attrs={"name": attr})
        if meta_tag and "content" in meta_tag.attrs:
            return meta_tag["content"]
    
    return None


def extract_version_from_header(soup: BeautifulSoup) -> Optional[str]:
    """
    Look for version information in page headers (h1-h3 tags)
    
    Args:
        soup: BeautifulSoup object representing an HTML document
        
    Returns:
        Version string if found, None otherwise
    """
    from ..utils.version_parser import extract_version_numbers
    
    for header_tag in ["h1", "h2", "h3"]:
        for header in soup.find_all(header_tag):
            header_text = header.get_text(strip=True)
            versions = extract_version_numbers(header_text)
            if versions:
                return versions[0]
    
    return None


def find_download_links(soup: BeautifulSoup, base_url: str) -> List[Tuple[str, str]]:
    """
    Find download links in the HTML
    
    Args:
        soup: BeautifulSoup object representing an HTML document
        base_url: Base URL for resolving relative links
        
    Returns:
        List of tuples containing (link text, URL)
    """
    download_links = []
    
    # Keywords that suggest a download link
    download_keywords = [
        "download", "get", "install", "setup",
        "binary", "executable", "latest", "stable"
    ]
    
    # File extensions that suggest software downloads
    download_extensions = [
        ".exe", ".msi", ".dmg", ".pkg", ".rpm", ".deb",
        ".zip", ".tar.gz", ".tar.xz", ".appimage"
    ]
    
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        link_text = a_tag.get_text(strip=True).lower()
        
        # Skip empty links or JavaScript actions
        if not href or href.startswith("javascript:") or href == "#":
            continue
        
        # Make absolute URL if it's relative
        if not urlparse(href).netloc:
            href = urljoin(base_url, href)
        
        # Check if the link text contains download keywords
        is_download_text = any(keyword in link_text for keyword in download_keywords)
        
        # Check if the URL ends with a download extension
        is_download_extension = any(href.lower().endswith(ext) for ext in download_extensions)
        
        # Check if the URL path contains download keywords
        url_path = urlparse(href).path.lower()
        is_download_path = any(keyword in url_path for keyword in download_keywords)
        
        if is_download_text or is_download_extension or is_download_path:
            download_links.append((link_text, href))
    
    return download_links


def extract_release_date(soup: BeautifulSoup) -> Optional[str]:
    """
    Try to extract a release date from the HTML
    
    Args:
        soup: BeautifulSoup object representing an HTML document
        
    Returns:
        Release date string if found, None otherwise
    """
    # Look for time tags
    time_tags = soup.find_all("time")
    if time_tags:
        for time_tag in time_tags:
            if "datetime" in time_tag.attrs:
                return time_tag["datetime"]
            return time_tag.get_text(strip=True)
    
    # Look for text patterns that might indicate a release date
    release_date_patterns = [
        r"released on (\w+ \d+,? \d{4})",
        r"release date:?\s*(\w+ \d+,? \d{4})",
        r"released:?\s*(\w+ \d+,? \d{4})",
        r"available since (\w+ \d+,? \d{4})",
        r"released (\d{1,2}/\d{1,2}/\d{2,4})",
        r"released (\d{4}-\d{2}-\d{2})"
    ]
    
    text = soup.get_text(" ", strip=True)
    for pattern in release_date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None