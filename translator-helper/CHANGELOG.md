# Changelog

All notable changes to the NMS MXML Translator Helper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
