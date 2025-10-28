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
    tools_dir = project_root / "tools"
    icon_path = project_root / "resources" / "translator.ico"

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
        # Add tools directory (includes MBINCompiler.exe)
        f"--add-data={tools_dir};tools",
        # Add resources directory (includes icon)
        f"--add-data={project_root / 'resources'};resources",
    ]

    # Add icon if exists
    if icon_path.exists():
        args.append(f"--icon={icon_path}")

    print("Building standalone executable...")
    print(f"Main script: {main_script}")
    print(f"Output directory: {project_root / 'dist'}")
    print(f"Including tools: {tools_dir}")
    if icon_path.exists():
        print(f"Including icon: {icon_path}")
    print()

    try:
        PyInstaller.__main__.run(args)
        print("\n" + "="*60)
        print("Build completed successfully!")
        print(f"Executable location: {project_root / 'dist' / 'NMS-MXML-Translator-Helper.exe'}")
        print("="*60)
        print("\nNote: The executable includes MBINCompiler for MBIN support.")
    except Exception as e:
        print(f"\nBuild failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    build()
