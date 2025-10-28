"""
Test script for comparison functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mxml_parser import MXMLParser, MXMLEntry
from core.comparator import EntryComparator, DiffType


def test_comparison():
    """Test comparison functionality with different scenarios."""
    
    print("=" * 60)
    print("Testing Comparison Functionality")
    print("=" * 60)
    
    # Create test data
    main_entries = [
        MXMLEntry("KEY1", "Content 1"),
        MXMLEntry("KEY2", "Content 2"),
        MXMLEntry("KEY3", "Content 3"),
        MXMLEntry("KEY4", "Content 4"),
    ]
    
    # Scenario 1: Identical files
    print("\n1. Testing IDENTICAL files:")
    compare_entries = [
        MXMLEntry("KEY1", "Content 1"),
        MXMLEntry("KEY2", "Content 2"),
        MXMLEntry("KEY3", "Content 3"),
        MXMLEntry("KEY4", "Content 4"),
    ]
    
    comparator = EntryComparator(main_entries, compare_entries)
    summary = comparator.get_summary()
    print(f"   Is identical: {comparator.is_identical()}")
    print(f"   Summary: {summary}")
    
    # Scenario 2: Modified content
    print("\n2. Testing MODIFIED content:")
    compare_entries = [
        MXMLEntry("KEY1", "Content 1"),
        MXMLEntry("KEY2", "Modified Content 2"),  # Modified
        MXMLEntry("KEY3", "Content 3"),
        MXMLEntry("KEY4", "Content 4"),
    ]
    
    comparator = EntryComparator(main_entries, compare_entries)
    differences = comparator.get_differences_only()
    summary = comparator.get_summary()
    print(f"   Differences found: {len(differences)}")
    print(f"   Summary: {summary}")
    for diff in differences:
        print(f"   - {diff}")
    
    # Scenario 3: Added keys
    print("\n3. Testing ADDED keys:")
    compare_entries = [
        MXMLEntry("KEY1", "Content 1"),
        MXMLEntry("KEY2", "Content 2"),
        MXMLEntry("KEY3", "Content 3"),
        MXMLEntry("KEY4", "Content 4"),
        MXMLEntry("KEY5", "New Content 5"),  # Added
        MXMLEntry("KEY6", "New Content 6"),  # Added
    ]
    
    comparator = EntryComparator(main_entries, compare_entries)
    differences = comparator.get_differences_only()
    summary = comparator.get_summary()
    print(f"   Differences found: {len(differences)}")
    print(f"   Summary: {summary}")
    for diff in differences:
        print(f"   - {diff}")
    
    # Scenario 4: Removed keys
    print("\n4. Testing REMOVED keys:")
    compare_entries = [
        MXMLEntry("KEY1", "Content 1"),
        MXMLEntry("KEY2", "Content 2"),
        # KEY3 and KEY4 removed
    ]
    
    comparator = EntryComparator(main_entries, compare_entries)
    differences = comparator.get_differences_only()
    summary = comparator.get_summary()
    print(f"   Differences found: {len(differences)}")
    print(f"   Summary: {summary}")
    for diff in differences:
        print(f"   - {diff}")
    
    # Scenario 5: Mixed changes
    print("\n5. Testing MIXED changes:")
    compare_entries = [
        MXMLEntry("KEY1", "Modified Content 1"),  # Modified
        MXMLEntry("KEY2", "Content 2"),           # Unchanged
        # KEY3 removed
        MXMLEntry("KEY4", "Content 4"),           # Unchanged
        MXMLEntry("KEY5", "New Content 5"),       # Added
    ]
    
    comparator = EntryComparator(main_entries, compare_entries)
    differences = comparator.get_differences_only()
    summary = comparator.get_summary()
    print(f"   Differences found: {len(differences)}")
    print(f"   Summary: {summary}")
    for diff in differences:
        print(f"   - {diff}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nAll comparison scenarios tested successfully!")


if __name__ == "__main__":
    test_comparison()
