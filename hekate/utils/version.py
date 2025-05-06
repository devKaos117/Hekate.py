import re
from packaging import version
from typing import List, Tuple, Optional

class VersionCheck:

    # Pattern for matching version strings with possible wildcards
    # Format: major.minor.patch.build + optional suffix
    _PATTERN =  r"(\d+(?:(?:\.\d+){0,2})(?:(?:\.\*)|(?:\.\d+))?)((?:[a-zA-Z]{1}|\*)|(?:(?:-|_|\+)(?:[a-zA-Z0-9_\-\+]+|\*)))?"
    # Components:
    # 1. (\d+(?:(?:\.\d+){0,2})(?:(?:\.\*)|(?:\.\d+))?) - Version numbers group:
    #   - \d+ : Starts with one or more digits (major version)
    #   - (?:(?:\.\d+){0,2}) : Followed by 0-2 occurrences of dot + digits (minor.patch)
    #   - (?:(?:\.\*)|(?:\.\d+))? : Optional final component that can be .* or .digits (build)
    # 
    # 2. ((?:[a-zA-Z]{1}|\*)|(?:(?:-|_|\+)(?:[a-zA-Z0-9_\-\+]+|\*)))? - Optional suffix group:
    #   - (?:[a-zA-Z]{1}|\*) : Single letter suffix or wildcard
    #   - OR
    #   - (?:(?:-|_|\+)(?:[a-zA-Z0-9_\-\+]+|\*)) : Delimiter followed by alphanumeric suffix or wildcard
    
    # Pattern for matching specific version strings without wildcards
    # Format: major.minor.patch.build + optional suffix
    _EXTRACTION_PATTERNS = [
        r"(\d+(?:\.\d+){3})((?:-|_|\+)(?:[a-zA-Z0-9_\-\+]+))",
        r"(\d+(?:\.\d+){2})((?:-|_|\+)(?:[a-zA-Z0-9_\-\+]+))",
        r"(\d+(?:\.\d+){1})((?:-|_|\+)(?:[a-zA-Z0-9_\-\+]+))",
        r"(\d+)((?:-|_|\+)(?:[a-zA-Z0-9_\-\+]+))",
        r"(\d+(?:\.\d+){3})([a-zA-Z]{1})",
        r"(\d+(?:\.\d+){2})([a-zA-Z]{1})",
        r"(\d+(?:\.\d+){1})([a-zA-Z]{1})",
        r"(\d+)([a-zA-Z]{1})",
        r"(\d+(?:\.\d+){3})",
        r"(\d+(?:\.\d+){2})",
        r"(\d+(?:\.\d+){1})",
        r"(\d+)"
    ]
    # Components:
    # 1. (\d+(?:\.\d+){0,3}) - Version numbers group:
    #   - \d+ : Starts with one or more digits (major version)
    #   - (?:\.\d+){0,3} : Followed by 0-3 occurrences of dot + digits (minor.patch.build)
    # 
    # 2. ((?:[a-zA-Z]{1})|(?:(?:-|_|\+)(?:[a-zA-Z0-9_\-\+]+))) - Suffix group:
    #   - (?:[a-zA-Z]{1}) : Single letter suffix
    #   - OR
    #   - (?:(?:-|_|\+)(?:[a-zA-Z0-9_\-\+]+)) : Delimiter followed by alphanumeric suffix

    _SUPPORTED_COMPARISONS = ["<", "<=", "==", ">=", ">"]
    
    @staticmethod
    def is_valid(v: str) -> bool:
        """
        Check if a version string is valid
        
        Args:
            v: Version string to check
        
        Returns:
            True if matched by pattern
        
        """
        return True if re.match(f"^{VersionCheck._PATTERN}$", v) else False
    
    @staticmethod
    def extract(str: str) -> Optional[str]:
        """
        Extract version strings

        Args:
            str: Source string
        
        Returns:
            Best version found
        """
        for pattern in VersionCheck._EXTRACTION_PATTERNS:
            version = VersionCheck.find_higher(re.findall(pattern, str))

            if version:
                return version
        
        return None

    @staticmethod
    def find_higher(versions: List[str]) -> Optional[str]:
        """
        Return highest version found in a list

        Args:
            versions: Versions list
        
        Returns:
            Best version found
        """
        v = "0"

        for ver in versions:
            if not VersionCheck.is_valid(ver):
                continue

            v = ver if VersionCheck.compare(ver, ">", v) else v
        
        return v if v != "0" else None

    @staticmethod
    def _execute_comparison(a, op, b) -> bool:
        """
        Execute the comparison directly through a serie of ifs

        Args:
            v1: First version string
            op: Comparison operation ("<", "<=", "==", ">=", ">")
            v2: Second version string
            
        Returns:
            Result of comparison
        """
        if op not in VersionCheck._SUPPORTED_COMPARISONS:
            raise Exception("Unsupported comparison")

        if op == "<":
            return a < b
        elif op == "<=":
            return a <= b
        elif op == "==":
            return a == b
        elif op == ">=":
            return a >= b
        elif op == ">":
            return a > b
        else:
            raise Exception("Impossible comparison result")

    @staticmethod
    def _normalize_wildcard(v1_in: str, v2_in: str) -> str:
        """
        Normalize version string by replacing "*" with "0" and removing both suffixes if one of them presents "*"
        
        Args:
            v1_in: First version string to normalize
            v2_in: First version string to normalize
            
        Returns:
            Normalized version string
        """
        v1, s1 = VersionCheck._split_suffix(v1_in)
        v2, s2 = VersionCheck._split_suffix(v2_in)
        # Removes wildcards from version
        if "*" in v1:
            v1 = re.sub(r"\*", "0", v1)
        if "*" in v2:
            v2 = re.sub(r"\*", "0", v2)
        
        # Removes suffixes if any contains an wildcard
        if (s1 and "*" in s1) or (s2 and "*" in s2):
            s1, s2 = None, None

        return f"{v1}{s1}", f"{v2}{s2}"
    
    @staticmethod
    def _split_suffix(v: str) -> Tuple[str]:
        """
        Split the version into semantic version and suffix

        Args:
            v: version string to be splitted
        
        Returns:
            version first, suffix last
        """
        match = re.match(VersionCheck._PATTERN, v)
        return match.group(1), match.group(2)

    @staticmethod
    def compare(v1_in: str, op: str, v2_in: str) -> bool:
        """
        Compare two version strings with the specified operation, handling special version formats
        
        Args:
            v1_in: First version string
            op: Comparison operation ("<", "<=", "==", ">=", ">")
            v2_in: Second version string
            
        Returns:
            Result of comparison
        """
        if not VersionCheck.is_valid(v1_in) or not VersionCheck.is_valid(v2_in):
            return False

        # Normalize "*" wildcards in version strings
        if "*" in v1_in or "*" in v2_in:
            v1_in, v2_in = VersionCheck._normalize_wildcard(v1_in, v2_in)
        
        # Standard semantic version
        if re.match(f"^{version.VERSION_PATTERN}$", v1_in, flags=re.IGNORECASE|re.VERBOSE) and re.match(f"^{version.VERSION_PATTERN}$", v2_in, flags=re.IGNORECASE|re.VERBOSE):
            v1 = version.parse(v1_in)
            v2 = version.parse(v2_in)

            return VersionCheck._execute_comparison(v1, op, v2)
        
        # Fall back to custom version comparison for special formats
        return VersionCheck._custom_compare(v1_in, op, v2_in)

    @staticmethod
    def _custom_compare(v1_in: str, op: str, v2_in: str) -> bool:
        """
        Custom version comparison for formats not supported by packaging.version
        
        Args:
            v1_in: First version string
            operation: Comparison operation ("<", "<=", "==", ">=", ">")
            v2_in: Second version string
            
        Returns:
            Result of comparison
        """
        v1, s1 = VersionCheck._split_suffix(v1_in)
        v2, s2 = VersionCheck._split_suffix(v2_in)
        
        # Split numeric parts
        try:
            v1_parts = [int(x) for x in v1.split(".")]
            v2_parts = [int(x) for x in v2.split(".")]
            
            # Compare numeric parts
            for i in range(max(len(v1_parts), len(v2_parts))):
                p1 = v1_parts[i] if i < len(v1_parts) else 0
                p2 = v2_parts[i] if i < len(v2_parts) else 0
                
                if p1 < p2:
                    return op in ["<", "<="]
                elif p1 > p2:
                    return op in [">", ">="]
            
            # If there is a missing suffix
            if not s1 and not s2:
                return op in ["==", "<=", ">="]
            elif not s1:
                return op in ["<", "<="]
            elif not s2:
                return op in [">", ">="]

            # Compare suffixes
            return VersionCheck._execute_comparison(s1, op, s2)
        except Exception:
            # Execute a lexicographical comparison as last resort
            return VersionCheck._execute_comparison(v1_in, op, v2_in)

    @staticmethod
    def is_covered(v_in: str, min: str = None, max: str = None, including: bool = True) -> bool:
        """
        Check if a specific version is covered by a range
        
        Args:
            v_in: Version string to check
            min: Lower limit in the range
            max: Upper limit in the range 
            including: Whether the range is including or not
            
        Returns:
            True if version is covered, False otherwise
        """
        if not min and not max:
            return True
                
        # Range checks with enhanced version comparison
        try:
            if including:
                # If there is a minimum and the input is not above or equal to it, return false
                if min and not VersionCheck.compare(v_in, ">=", min):
                    return False
                # If there is a maximum and the input is not below or equal to it, return false
                elif max and not VersionCheck.compare(v_in, "<=", max):
                    return False
            else:
                # If there is a minimum and the input is not above it, return false
                if min and not VersionCheck.compare(v_in, ">", min):
                    return False
                # If there is a maximum and the input is not below it, return false
                elif max and not VersionCheck.compare(v_in, "<", max):
                    return False
                
            return True
        except Exception as e:
            raise Exception(f"Error while executing checkin version covered by range: {e}")