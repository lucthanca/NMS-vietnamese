"""
Convert PNG to ICO for Windows application icon.
"""

from PIL import Image
from pathlib import Path

def convert_to_ico():
    """Convert translator.png to .ico format."""

    resources_dir = Path(__file__).parent
    png_path = resources_dir / "translator.png"
    ico_path = resources_dir / "translator.ico"

    if not png_path.exists():
        print(f"Error: {png_path} not found!")
        return

    try:
        # Open PNG and convert to ICO
        img = Image.open(png_path)

        # Create multiple sizes for ICO (Windows standard)
        img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

        print(f"✓ Successfully converted to: {ico_path}")

    except Exception as e:
        print(f"Error converting: {e}")
        print("Note: Install Pillow if needed: pip install Pillow")

if __name__ == "__main__":
    convert_to_ico()
