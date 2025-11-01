# NMS MXML Translator Helper v0.3.0

## 🎉 Major Release: MBIN Support, File Comparison & UI Enhancements

This release brings significant new features including MBIN file support, file comparison tools, and visual improvements with application icon and version display.

---

## ✨ New Features

### MBIN File Support
- **Load MBIN files** directly with automatic conversion to MXML (`Ctrl+B`)
- **Export to MBIN** format from loaded MXML data (`Ctrl+Shift+B`)
- Seamless integration with MBINCompiler for bidirectional conversion
- Automatic temporary file management and cleanup

### File Comparison Tool
- **Compare two files** side-by-side to identify differences (`Ctrl+D`)
- **Full MBIN support** - Load and compare MBIN files with automatic conversion
- **Background processing** - Non-blocking UI with progress bar and status updates
- **Real-time status messages** - Shows conversion and parsing progress
- Visual diff indicators:
  - 🟢 **Green** - Added entries
  - 🔴 **Red** - Removed entries  
  - 🟠 **Orange** - Modified entries
- **Export comparison results** - Only exports modified and added entries
- Smart detection of identical files
- Supports comparing MXML and MBIN files in any combination

### UI Enhancements
- **Application icon** with multi-resolution support (16-256px)
- **Version display** in status bar for easy identification
- Reorganized menu structure with Load and Export submenus
- New Tools menu for comparison functionality

---

## 🔧 Technical Improvements

### New Components
- `MBINCompiler` wrapper class for MBIN conversion
- `EntryComparator` class for intelligent file comparison
- `CompareDialog` window with color-coded results
- `ComparisonThread` for background comparison processing
- PNG to ICO conversion utility with Pillow

### Build System
- Resources directory bundled with executable
- Application icon embedded in .exe file
- Improved PyInstaller configuration

### Performance Improvements
- Comparison operations run in background thread
- Non-blocking UI during file comparison
- Real-time progress updates for MBIN conversion
- Responsive interface during intensive operations

---

## 🐛 Bug Fixes

- Compare export now correctly exports only modified/added entries (not removed)
- Resolved setup.py license classifier deprecation warning
- Improved error handling for MBIN conversion failures

---

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Windows OS (for MBIN support)

### Install from Source
```bash
git clone https://github.com/lucthanca/NMS-vietnamese.git
cd NMS-vietnamese/translator-helper
pip install -r requirements.txt
python src/main.py
```

### Build Standalone Executable
```bash
python build.py
```
Executable will be created in `dist/NMS-MXML-Translator-Helper.exe`

---

## 📋 Dependencies

- PyQt6 >= 6.6.0 (GUI framework)
- lxml >= 5.1.0 (XML parsing)
- Pillow >= 10.0.0 (Icon conversion)
- PyInstaller >= 6.3.0 (Build tool)

---

## 🎯 Usage

### Loading Files
- **Load MXML**: `File > Load > Load MXML` or `Ctrl+O`
- **Load MBIN**: `File > Load > Load MBIN` or `Ctrl+B`

### Exporting Files
- **Export to JSON**: `File > Export > Export to JSON` or `Ctrl+J`
- **Export to MXML**: `File > Export > Export to MXML` or `Ctrl+M`
- **Export to MBIN**: `File > Export > Export to MBIN` or `Ctrl+Shift+B`

### Comparing Files
- **Compare Files**: `Tools > Compare Files` or `Ctrl+D`
- Select two files to compare
- View color-coded differences
- Export changes to JSON or MXML

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

---

## 🙏 Credits

- **MBINCompiler** by monkeyman192 for MBIN conversion support
- **No Man's Sky** localization community
- NMS Vietnamese Translation Team

---

## 📄 License

MIT License - See LICENSE file for details

---

**Full Changelog**: https://github.com/lucthanca/NMS-vietnamese/compare/v0.2.0...v0.3.0
