"""
Test script for MBIN conversion functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.mbin_compiler import MBINCompiler, MBINCompilerError
from core.mxml_parser import MXMLParser
from core.exporter import MXMLExporter


def test_mbin_compiler():
    """Test MBIN compiler wrapper."""

    print("=" * 60)
    print("Testing MBIN Compiler Wrapper")
    print("=" * 60)

    try:
        compiler = MBINCompiler()
        print(f"✓ MBINCompiler found at: {compiler.compiler_path}")

        # Get version
        version = compiler.get_version()
        print(f"✓ MBINCompiler version: {version}")

        print("\n" + "=" * 60)
        print("Test Complete!")
        print("=" * 60)
        print("\nNote: To fully test MBIN functionality:")
        print("1. Place an .MBIN file in the tools directory")
        print("2. Use the GUI to test Load MBIN feature")
        print("3. Use the GUI to test Export to MBIN feature")

    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


if __name__ == "__main__":
    test_mbin_compiler()
