# Changelog

All notable changes to the NMS MXML Translator Helper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-10-29

### Added
- MBIN file support with automatic conversion using MBINCompiler
- Load MBIN functionality with keyboard shortcut (Ctrl+B)
- Export to MBIN functionality with keyboard shortcut (Ctrl+Shift+B)
- Load submenu for organized file loading (Load MXML, Load MBIN)
- Tools menu with Compare Files functionality (Ctrl+D)
- File comparison feature to identify differences between two files
- Comparison dialog showing additions (+), deletions (-), and modifications (~)
- Color-coded comparison results for easy identification
- Export comparison changes (modified/added only) to JSON and MXML formats
- Identical files detection with informational message

### Technical Details
- New `MBINCompiler` wrapper class in utils module
- Automatic MBIN to MXML conversion for loading
- Automatic MXML to MBIN conversion for export
- Temporary file management with automatic cleanup
- New `EntryComparator` class for comparing entry sets
- New `CompareDialog` for displaying comparison results
- Support for comparing MXML and MBIN files
- Comprehensive diff indicators (ADDED, REMOVED, MODIFIED, UNCHANGED)
- Background thread support for MBIN conversion

## [0.2.0] - 2025-10-29

### Added
- Export to JSON functionality with keyboard shortcut (Ctrl+J)
- Export to MXML functionality with keyboard shortcut (Ctrl+M)
- Export submenu under File menu
- Save file dialogs for both export formats
- Automatic HTML entity preservation in MXML exports (&lt;, &gt;, &amp;, etc.)
- Export menu enabled/disabled based on loaded file state
- Success/error dialogs for export operations
- Test script for verifying export functionality

### Technical Details
- New `MXMLExporter` class in core module
- JSON export with UTF-8 encoding and proper formatting
- MXML export maintains original file structure
- HTML entities automatically encoded by lxml during XML writing
- MBINCompiler comment added to exported MXML files

## [0.1.1] - 2025-10-29

### Improved
- Enhanced table UI responsiveness when resizing window
- Key column now uses ResizeToContents mode for optimal width
- Content column stretches to fill remaining space
- Added word wrap support for better text display in content column
- Improved overall user experience with dynamic column sizing

## [0.1.0] - 2025-10-29

### Added
- Initial release of NMS MXML Translator Helper
- PyQt6-based GUI application
- MXML file parser for No Man's Sky localization files
- Main window with menu bar (File menu)
- Load MXML functionality with file dialog
- Two-column table view (Key, Content) for displaying entries
- Background threading for file loading
- Status bar with progress indicator
- Keyboard shortcuts (Ctrl+O for Open, Ctrl+Q for Exit)
- Alternating row colors in table for better readability
- Row selection support
- Sorting capability in table columns
- Error handling for invalid files
- Complete project documentation (README, DEV_DOCS, CHANGELOG)
- Build script for creating standalone executable
- Example MXML file for testing

### Technical Details
- Python 3.10+ support
- lxml for XML parsing
- PyQt6 for GUI framework
- Type hints throughout codebase
- Comprehensive docstrings
- Modular code structure (core, ui, src modules)
