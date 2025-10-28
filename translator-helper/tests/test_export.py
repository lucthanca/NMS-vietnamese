"""
Test script for export functionality and HTML entity preservation.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mxml_parser import MXMLParser
from core.exporter import MXMLExporter

def test_exports():
    """Test JSON and MXML exports with HTML entity preservation."""
    
    # Parse example file
    example_file = Path(__file__).parent.parent / "examples" / "NMS_LOC1_ENGLISH_EXAMPLE.MXML"
    
    print("=" * 60)
    print("Testing Export Functionality")
    print("=" * 60)
    print(f"\nParsing: {example_file.name}")
    
    parser = MXMLParser()
    entries = parser.parse_file(str(example_file))
    
    print(f"Loaded {len(entries)} entries\n")
    
    # Show sample entry with HTML entities
    for entry in entries[:2]:
        print(f"Key: {entry.key}")
        print(f"Content: {entry.content}")
        print()
    
    # Test JSON export
    print("\n" + "=" * 60)
    print("Testing JSON Export")
    print("=" * 60)
    
    json_output = Path(__file__).parent / "test_export.json"
    exporter = MXMLExporter(entries)
    exporter.export_to_json(str(json_output))
    
    print(f"✓ Exported to: {json_output}")
    
    # Read and verify JSON content
    with open(json_output, 'r', encoding='utf-8') as f:
        content = f.read()
        # Check if HTML entities are preserved
        if '&lt;' in content and '&gt;' in content:
            print("✓ HTML entities preserved in JSON")
        else:
            print("✗ HTML entities NOT preserved in JSON!")
    
    # Show sample from JSON
    import json
    with open(json_output, 'r', encoding='utf-8') as f:
        data = json.load(f)
        first_key = list(data.keys())[0]
        print(f"\nSample JSON entry:")
        print(f'  "{first_key}": "{data[first_key]}"')
    
    # Test MXML export
    print("\n" + "=" * 60)
    print("Testing MXML Export")
    print("=" * 60)
    
    mxml_output = Path(__file__).parent / "test_export.MXML"
    exporter.export_to_mxml(str(mxml_output))
    
    print(f"✓ Exported to: {mxml_output}")
    
    # Read and verify MXML content
    with open(mxml_output, 'r', encoding='utf-8') as f:
        content = f.read()
        # Check if HTML entities are preserved
        if '&lt;' in content and '&gt;' in content:
            print("✓ HTML entities preserved in MXML")
        else:
            print("✗ HTML entities NOT preserved in MXML!")
        
        # Check structure
        if 'cTkLocalisationTable' in content:
            print("✓ MXML structure correct")
        if 'MBINCompiler' in content:
            print("✓ MBINCompiler comment added")
    
    # Show sample from MXML
    print(f"\nSample MXML lines:")
    lines = content.split('\n')
    for line in lines[5:10]:
        print(f"  {line}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_exports()
