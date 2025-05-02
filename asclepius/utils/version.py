"""
Version Parser - Utilities for parsing and comparing software version strings

This module provides functions for extracting version numbers from text,
normalizing version strings, and comparing versions
"""

import re
from typing import List, Tuple


def extract_version_numbers(text: str) -> List[str]:
    """
    Extract version numbers from text
    
    This function looks for common version number patterns in the given text
    
    Args:
        text: The text to search for version numbers
        
    Returns:
        A list of version strings found in the text
    """
    # Common version patterns
    patterns = [
        # Match "version X.Y.Z" format
        r'version\s+(\d+(?:\.\d+)+)',
        # Match "vX.Y.Z" format
        r'\bv(\d+(?:\.\d+)+)\b',
        # Match standalone version numbers like X.Y.Z
        r'(?<!\w)(\d+\.\d+(?:\.\d+)*)',
        # Match "Version: X.Y.Z" format
        r'version:\s+(\d+(?:\.\d+)+)',
        # Match "X.Y.Z (build N)" format
        r'(\d+\.\d+(?:\.\d+)*)\s*\(build\s+\d+\)',
        # Match standalone Major.Minor format
        r'(?<!\w)(\d+\.\d+)(?!\.\d+)(?!\d)'
    ]
    
    versions = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        versions.extend(matches)
    
    # Deduplicate versions while preserving order
    unique_versions = []
    for version in versions:
        if version not in unique_versions:
            unique_versions.append(version)
    
    return unique_versions


def normalize_version(version: str) -> str:
    """
    Normalize a version string to a standard format
    
    Args:
        version: The version string to normalize
        
    Returns:
        A normalized version string
    """
    # Remove any 'v' prefix
    if version.lower().startswith('v'):
        version = version[1:]
    
    # Remove any trailing zeros after the last non-zero digit
    parts = version.split('.')
    while len(parts) > 1 and parts[-1] == '0':
        parts = parts[:-1]
    
    return '.'.join(parts)


def parse_version(version: str) -> Tuple[int, ...]:
    """
    Parse a version string into a tuple of integers
    
    Args:
        version: The version string to parse
        
    Returns:
        A tuple of integers representing the version components
    """
    # Normalize the version first
    version = normalize_version(version)
    
    # Split by dots and convert to integers
    # Non-numeric parts are treated as 0
    components = []
    for part in version.split('.'):
        try:
            components.append(int(part))
        except ValueError:
            # If there's a non-numeric suffix, extract any leading digits
            match = re.match(r'(\d+)', part)
            if match:
                components.append(int(match.group(1)))
            else:
                components.append(0)
    
    return tuple(components)


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings
    
    Args:
        version1: The first version string
        version2: The second version string
        
    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
    """
    v1_components = parse_version(version1)
    v2_components = parse_version(version2)
    
    # Pad shorter tuple with zeros to match length
    length = max(len(v1_components), len(v2_components))
    v1_components = v1_components + (0,) * (length - len(v1_components))
    v2_components = v2_components + (0,) * (length - len(v2_components))
    
    # Compare component by component
    for c1, c2 in zip(v1_components, v2_components):
        if c1 < c2:
            return -1
        if c1 > c2:
            return 1
    
    # All components are equal
    return 0


def is_newer_version(current: str, latest: str) -> bool:
    """
    Check if the latest version is newer than the current version
    
    Args:
        current: The current version string
        latest: The latest version string
        
    Returns:
        True if the latest version is newer than the current version
    """
    return compare_versions(latest, current) > 0