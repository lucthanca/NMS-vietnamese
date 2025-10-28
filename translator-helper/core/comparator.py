"""
Comparison Module

This module provides functionality to compare two sets of MXML entries
and identify differences (additions, deletions, modifications).
"""

from typing import List, Dict, Set
from enum import Enum
from dataclasses import dataclass

from core.mxml_parser import MXMLEntry


class DiffType(Enum):
    """Type of difference between entries."""
    ADDED = "+"      # Entry exists in compare file but not in main
    REMOVED = "-"    # Entry exists in main file but not in compare
    MODIFIED = "~"   # Entry exists in both but content is different
    UNCHANGED = "="  # Entry exists in both with same content


@dataclass
class ComparisonEntry:
    """
    Represents a comparison result for a single entry.
    
    Attributes:
        key: The entry key
        main_content: Content from main file (None if added)
        compare_content: Content from compare file (None if removed)
        diff_type: Type of difference
    """
    key: str
    main_content: str
    compare_content: str
    diff_type: DiffType
    
    def __repr__(self) -> str:
        return f"ComparisonEntry({self.diff_type.value} {self.key})"


class EntryComparator:
    """
    Compares two sets of MXML entries and identifies differences.
    """
    
    def __init__(self, main_entries: List[MXMLEntry], compare_entries: List[MXMLEntry]):
        """
        Initialize the comparator.
        
        Args:
            main_entries: Entries from the main (currently loaded) file
            compare_entries: Entries from the file to compare against
        """
        self.main_entries = main_entries
        self.compare_entries = compare_entries
        
        # Create dictionaries for quick lookup
        self.main_dict = {entry.key: entry.content for entry in main_entries}
        self.compare_dict = {entry.key: entry.content for entry in compare_entries}
    
    def compare(self) -> List[ComparisonEntry]:
        """
        Compare the two sets of entries.
        
        Returns:
            List of ComparisonEntry objects representing all differences
        """
        results = []
        
        # Get all unique keys from both files
        all_keys = set(self.main_dict.keys()) | set(self.compare_dict.keys())
        
        for key in sorted(all_keys):
            main_content = self.main_dict.get(key)
            compare_content = self.compare_dict.get(key)
            
            if main_content is None:
                # Key only exists in compare file (ADDED)
                diff_type = DiffType.ADDED
            elif compare_content is None:
                # Key only exists in main file (REMOVED from compare)
                diff_type = DiffType.REMOVED
            elif main_content == compare_content:
                # Key exists in both with same content (UNCHANGED)
                diff_type = DiffType.UNCHANGED
            else:
                # Key exists in both but content differs (MODIFIED)
                diff_type = DiffType.MODIFIED
            
            results.append(ComparisonEntry(
                key=key,
                main_content=main_content or "",
                compare_content=compare_content or "",
                diff_type=diff_type
            ))
        
        return results
    
    def get_differences_only(self) -> List[ComparisonEntry]:
        """
        Get only entries that have differences (exclude unchanged).
        
        Returns:
            List of ComparisonEntry objects with differences only
        """
        all_results = self.compare()
        return [entry for entry in all_results if entry.diff_type != DiffType.UNCHANGED]
    
    def get_summary(self) -> Dict[str, int]:
        """
        Get a summary of comparison results.
        
        Returns:
            Dictionary with counts for each diff type
        """
        results = self.compare()
        summary = {
            "total": len(results),
            "added": sum(1 for r in results if r.diff_type == DiffType.ADDED),
            "removed": sum(1 for r in results if r.diff_type == DiffType.REMOVED),
            "modified": sum(1 for r in results if r.diff_type == DiffType.MODIFIED),
            "unchanged": sum(1 for r in results if r.diff_type == DiffType.UNCHANGED),
        }
        return summary
    
    def is_identical(self) -> bool:
        """
        Check if both files are identical.
        
        Returns:
            True if files are identical, False otherwise
        """
        summary = self.get_summary()
        return summary["added"] == 0 and summary["removed"] == 0 and summary["modified"] == 0
