"""
MBIN Compiler Utility Module

This module provides a wrapper around MBINCompiler.exe for converting
between MBIN and MXML formats.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple


class MBINCompilerError(Exception):
    """Exception raised when MBINCompiler fails."""
    pass


class MBINCompiler:
    """
    Wrapper for MBINCompiler.exe to convert between MBIN and MXML formats.

    MBINCompiler is a tool for No Man's Sky that converts between:
    - MBIN (binary) format
    - MXML (XML) format
    """

    def __init__(self, compiler_path: Optional[str] = None):
        """
        Initialize the MBIN compiler wrapper.

        Args:
            compiler_path: Path to MBINCompiler.exe. If None, looks in tools directory.
        """
        if compiler_path:
            self.compiler_path = Path(compiler_path)
        else:
            # Default to tools directory
            self.compiler_path = Path(__file__).parent.parent / "tools" / "MBINCompiler.6.13.0.1.exe"

        if not self.compiler_path.exists():
            raise FileNotFoundError(f"MBINCompiler not found at: {self.compiler_path}")

    def mbin_to_mxml(self, mbin_file: str, output_dir: Optional[str] = None) -> str:
        """
        Convert MBIN file to MXML format.

        Args:
            mbin_file: Path to the MBIN file
            output_dir: Directory where MXML will be saved. If None, uses temp directory.

        Returns:
            Path to the generated MXML file

        Raises:
            FileNotFoundError: If MBIN file doesn't exist
            MBINCompilerError: If conversion fails
        """
        mbin_path = Path(mbin_file)
        if not mbin_path.exists():
            raise FileNotFoundError(f"MBIN file not found: {mbin_file}")

        # Determine output directory
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = Path(tempfile.mkdtemp())

        # Run MBINCompiler
        # Command: MBINCompiler.exe convert -y --output-dir=<dir> --output-format=MXML <input>
        cmd = [
            str(self.compiler_path),
            "convert",
            "-y",  # Overwrite if exists
            "-q",  # Quiet mode
            f"--output-dir={out_dir}",
            "--output-format=MXML",
            str(mbin_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise MBINCompilerError(f"MBIN to MXML conversion failed: {result.stderr}")

        # Find the generated MXML file
        # MBINCompiler creates file with same name but .MXML extension
        mxml_file = out_dir / (mbin_path.stem + ".MXML")

        # Handle .MBIN.PC extension case
        if not mxml_file.exists() and mbin_path.suffix.upper() == ".PC":
            # Try without .PC extension
            base_name = mbin_path.stem  # Gets name without .PC
            if base_name.upper().endswith(".MBIN"):
                base_name = base_name[:-5]  # Remove .MBIN part
            mxml_file = out_dir / (base_name + ".MXML")

        if not mxml_file.exists():
            raise MBINCompilerError(f"Expected MXML file not found: {mxml_file}")

        return str(mxml_file)

    def mxml_to_mbin(self, mxml_file: str, output_dir: Optional[str] = None) -> str:
        """
        Convert MXML file to MBIN format.

        Args:
            mxml_file: Path to the MXML file
            output_dir: Directory where MBIN will be saved. If None, uses temp directory.

        Returns:
            Path to the generated MBIN file

        Raises:
            FileNotFoundError: If MXML file doesn't exist
            MBINCompilerError: If conversion fails
        """
        mxml_path = Path(mxml_file)
        if not mxml_path.exists():
            raise FileNotFoundError(f"MXML file not found: {mxml_file}")

        # Determine output directory
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = Path(tempfile.mkdtemp())

        # Run MBINCompiler
        # Command: MBINCompiler.exe convert -y --output-dir=<dir> --output-format=MBIN <input>
        cmd = [
            str(self.compiler_path),
            "convert",
            "-y",  # Overwrite if exists
            "-q",  # Quiet mode
            f"--output-dir={out_dir}",
            "--output-format=MBIN",
            str(mxml_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise MBINCompilerError(f"MXML to MBIN conversion failed: {result.stderr}")

        # Find the generated MBIN file
        # MBINCompiler creates file with same name but .MBIN extension
        mbin_file = out_dir / (mxml_path.stem + ".MBIN")

        if not mbin_file.exists():
            raise MBINCompilerError(f"Expected MBIN file not found: {mbin_file}")

        return str(mbin_file)

    def get_version(self) -> str:
        """
        Get MBINCompiler version.

        Returns:
            Version string
        """
        cmd = [str(self.compiler_path), "version", "-q"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip()


def cleanup_temp_dir(path: str) -> None:
    """
    Clean up temporary directory.

    Args:
        path: Path to temporary directory to remove
    """
    try:
        dir_path = Path(path)
        if dir_path.exists() and dir_path.parent == Path(tempfile.gettempdir()):
            shutil.rmtree(path)
    except Exception:
        pass  # Ignore cleanup errors
