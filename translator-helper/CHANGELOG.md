# Changelog

All notable changes to the NMS MXML Translator Helper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2025-11-02

### Fixed
- **True Parallel Workflow**: Implemented rolling parallel execution for full_parallel workflow
  - Now runs maximum 3 patches concurrently (instead of just 1)
  - When a worker completes a patch, it immediately picks up the next patch from queue
  - Uses ThreadPoolExecutor with as_completed() for optimal throughput
  - Thread-safe signal emission with threading.Lock for concurrent operations
  - Verbose logging for parallel workflow progress tracking
- **Thread Hanging Issue**: Fixed terminal hanging when closing translation dialog
  - App now force exits with `os._exit()` after QApplication closes
  - Ctrl+C signal handler for immediate termination
  - Background threads don't block app termination
  - Clear warnings when closing with active threads
- **Dialog Close Handling**: Fixed missing confirmation dialog
  - Override `reject()` method to intercept Close button
  - Both closeEvent and reject now check for running translation
  - Confirmation prompt appears consistently when translation active
  - Worker threads check cancel flag immediately after API response
  - Enhanced logging to track dialog close and cancellation flow

### Added
- **Enhanced API Call Logging**: Detailed logging for each Gemini API call
  - Request details: patch size, sample keys, estimated tokens
  - Response details: timing, response size, preview
  - Model and temperature parameters logged for each call
- **Translation Cancellation**: Ability to cancel ongoing translation
  - Cancel via dialog close event with confirmation prompt
  - Graceful shutdown of parallel workers
  - Cancel flag propagated to all worker threads
  - **Enhanced cancellation logging** with clear visual indicators (🛑)
  - Shows completed vs remaining patches when cancelled
- **Configurable Translation Settings**:
  - **Token Limit** setting (default: 50000, range: 1000-100000)
  - **Max Retries** setting (default: 3, range: 0-10)
  - Settings persisted and loaded from config file
  - Validation for token limit and max retries values

### Technical Details
- Added `concurrent.futures.ThreadPoolExecutor` for parallel patch processing
- Created `translate_data_direct()` function to avoid nested QThread issues
- Implemented direct workflow methods: `_run_sequential_direct()`, `_run_parallel_direct()`
- Refactored `core/translation_engine.py` to use `translate_data_direct()` instead of QThread nesting
- Added helper function `_translate_patch_with_retry_direct()` for worker threads
- Enhanced logging to show concurrent patch completion in real-time
- Test script: `test_parallel_workflow.py` to demonstrate concurrent processing
- Added `cancel_flag` parameter throughout translation pipeline
- `TranslationThread.cancel()` method to interrupt translation
- `MissingEntriesDialog.closeEvent()` with cancellation confirmation

### Architecture Changes
- **translation/engine.py**:
  - `TranslationEngine` (QThread) - For standalone use with signals
  - `translate_data_direct()` - For use within existing threads (no QThread)
  - Parallel execution with ThreadPoolExecutor and as_completed pattern
  - Cancel flag support in all workflow functions
- **core/translation_engine.py**:
  - `TranslationThread` now calls `translate_data_direct()` to avoid nested threads
  - Callbacks for progress and patch completion instead of signal connections
  - `cancel()` method sets flag to interrupt workers
- **ui/missing_entries_dialog.py**:
  - `closeEvent()` handler to cancel translation on dialog close
- **ui/settings_dialog.py**:
  - Added Token Limit input field with validation (1000-100000)
  - Added Max Retries input field with validation (0-10)
  - Load and save settings from/to TranslationConfig
  - `closeEvent()` handler to cancel translation on dialog close

## [0.5.0] - 2025-11-02

### Added
- **AI Translation Integration** with Google Gemini API (gemini-2.5-flash)
- **Translate with AI** feature (Ctrl+T) to translate missing entries using Gemini AI
- **Settings Dialog** (Ctrl+,) for configuring Gemini API key and workflow type
- Missing Entries Dialog with real-time translation progress and status updates
- Support for sequence and full_parallel translation workflows
- Token-based patch splitting (50,000 tokens per patch) for handling large datasets
- Smart quota handling with automatic retry and countdown for rate limits
- Translation validation to ensure all keys are translated
- Auto-detect missing translations after merging translation files
- Persistent settings storage using TranslationConfig
- Comprehensive error handling with retry logic (3 attempts per patch)
- Professional Vietnamese translation prompt with game-specific terminology

### Improvements
- Modular translation architecture with dedicated `translation/` module
  - `translation/engine.py`: Core translation engine with PyQt6 signals
  - `translation/config.py`: Configuration management with WorkflowType enum
  - `translation/prompts.py`: Translation prompts and instructions
  - `translation/utils.py`: Utility functions for patching and validation
- Enhanced Tools menu with "Translate with AI" action
- Updated "Merge Translation Files" shortcut to Ctrl+Shift+T (to avoid conflict)
- Missing entries dialog now triggered automatically after merge if untranslated entries found
- Color-coded translation status (light green) in table for translated entries
- Progress tracking with patch-by-patch updates
- Thread-safe translation execution without nested QThread issues
- Better separation of UI and translation logic

### Technical Details
- New `TranslationEngine` module with Gemini API integration
- `SettingsDialog` class for API configuration management
- `MissingEntriesDialog` with 3-column table and progress tracking
- `TranslationThread` for background AI translation with Qt signals
- JSON-based settings persistence in user home directory
- Patch completion signal for real-time table updates
- Support for both sequence and parallel translation strategies
- Markdown cleanup in translation responses
- Dependencies: Added `google-generativeai>=0.3.0`

## [0.4.0] - 2025-11-02

### Added
- **Merge Translation Files** feature (Ctrl+T) to load and apply translations
- Support for loading translations from folder or individual files
- Multi-format translation support (MXML, MBIN, JSON)
- Third column "Translated Content" in table view
- Visual highlighting (light green) for translated entries
- Background threading for translation merge with progress feedback
- Batch processing of multiple translation files
- Smart content replacement based on entry keys
- Export functions now use translated content when available
- Translation count display in export success messages

### Improvements
- Table now shows original and translated content side-by-side
- Export operations include translation statistics
- Better status messages during merge operations
- File count progress indicator during batch loading

### Technical Details
- New `MergeThread` class for background translation loading
- Support for JSON flat dictionary format
- Automatic MBIN to MXML conversion for translation files
- Dictionary-based translation storage (key -> translated_content)
- Export entries dynamically generated with translations applied
- Color-coded UI feedback for translated entries

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
- Background threading for comparison operations with progress feedback
- Real-time status updates during MBIN conversion and file parsing
- Application icon (translator.ico) with multi-resolution support
- Version display in status bar (bottom-left corner)
- PNG to ICO conversion utility for icon creation

### Technical Details
- New `MBINCompiler` wrapper class in utils module
- Automatic MBIN to MXML conversion for loading
- Automatic MXML to MBIN conversion for export
- Temporary file management with automatic cleanup
- New `EntryComparator` class for comparing entry sets
- New `CompareDialog` for displaying comparison results
- New `ComparisonThread` for background comparison processing
- Support for comparing MXML and MBIN files
- Comprehensive diff indicators (ADDED, REMOVED, MODIFIED, UNCHANGED)
- Background thread support for MBIN conversion
- Non-blocking UI during comparison operations with progress bar
- Multi-resolution ICO file generation with Pillow library
- Icon integration in window title bar and executable
- Resources directory bundled with PyInstaller build

### Fixed
- Compare export now only exports modified and added entries (not removed)
- setup.py license classifier deprecation warning resolved

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
