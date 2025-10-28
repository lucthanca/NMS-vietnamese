"""
Build script for creating standalone executable.

This script uses PyInstaller to create a standalone executable
of the NMS MXML Translator Helper application.
"""

import PyInstaller.__main__
import sys
from pathlib import Path

def build():
    """
    Build the standalone executable using PyInstaller.
    
    Creates a single-file executable in the dist/ directory.
    """
    
    # Get the project root directory
    project_root = Path(__file__).parent
    main_script = project_root / "src" / "main.py"
    
    # PyInstaller arguments
    args = [
        str(main_script),
        "--name=NMS-MXML-Translator-Helper",
        "--windowed",  # No console window
        "--onefile",  # Single executable file
        f"--distpath={project_root / 'dist'}",
        f"--workpath={project_root / 'build'}",
        f"--specpath={project_root}",
        "--clean",
        # Add data files if needed
        # f"--add-data={project_root / 'examples'}:examples",
    ]
    
    print("Building standalone executable...")
    print(f"Main script: {main_script}")
    print(f"Output directory: {project_root / 'dist'}")
    print()
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "="*60)
        print("Build completed successfully!")
        print(f"Executable location: {project_root / 'dist' / 'NMS-MXML-Translator-Helper.exe'}")
        print("="*60)
    except Exception as e:
        print(f"\nBuild failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    build()
