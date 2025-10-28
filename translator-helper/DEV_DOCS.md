# Developer Documentation

## Architecture Overview

The NMS MXML Translator Helper is built with a modular architecture separating concerns into distinct layers:

```
Application Layer (src/)
    ↓
UI Layer (ui/)
    ↓
Core Logic Layer (core/)
    ↓
Data Layer (MXML files)
```

## Module Breakdown

### 1. Core Module (`core/`)

#### `mxml_parser.py`
Handles all MXML file parsing operations.

**Classes:**
- `MXMLEntry`: Data class representing a single localization entry
  - Properties: `key` (str), `content` (str)
  
- `MXMLParser`: Main parser class
  - `parse_file(file_path: str) -> List[MXMLEntry]`: Parse MXML and extract entries
  - `get_entries() -> List[MXMLEntry]`: Get all parsed entries
  - `get_entry_count() -> int`: Get number of entries
  - `to_dict() -> List[Dict[str, str]]`: Convert entries to dictionary format

**XML Structure:**
```xml
<Data template="cTkLocalisationTable">
  <Property name="Table">
    <Property name="Table" value="TkLocalisationEntry" _id="KEY">
      <Property name="Id" value="KEY" />
      <Property name="English" value="Content text" />
      ...
    </Property>
  </Property>
</Data>
```

### 2. UI Module (`ui/`)

#### `main_window.py`
Implements the main application window using PyQt6.

**Classes:**
- `LoaderThread`: QThread subclass for background file loading
  - Signals:
    - `progress(int, int)`: Loading progress updates
    - `finished(list)`: Loading complete with entries
    - `error(str)`: Loading failed with error message

- `MainWindow`: Main application window (QMainWindow)
  - Components:
    - Menu bar with File menu
    - QTableWidget for displaying entries
    - Status bar with progress indicator
  - Key Methods:
    - `_on_load_mxml()`: Handle file selection
    - `_load_file(file_path)`: Load file in background thread
    - `_populate_table()`: Display entries in table

### 3. Application Layer (`src/`)

#### `main.py`
Application entry point.

**Functions:**
- `main()`: Initialize QApplication and show main window

## Threading Model

The application uses a background thread for file loading to prevent UI freezing:

```
Main Thread (GUI)
    ↓ User clicks "Load MXML"
    ↓ Create LoaderThread
    ↓
Background Thread
    ↓ Parse MXML file
    ↓ Emit finished signal
    ↓
Main Thread
    ↓ Receive entries
    ↓ Update table
```

## Data Flow

```
MXML File
    ↓
MXMLParser.parse_file()
    ↓
List[MXMLEntry]
    ↓
LoaderThread.finished signal
    ↓
MainWindow._on_load_finished()
    ↓
QTableWidget display
```

## Error Handling

### Parser Errors
- `FileNotFoundError`: File doesn't exist
- `etree.XMLSyntaxError`: Invalid XML
- `ValueError`: Invalid MXML structure

### UI Error Handling
- Errors are caught in LoaderThread
- Emitted via `error` signal
- Displayed to user via QMessageBox

## PyQt6 Components Used

### Widgets
- `QMainWindow`: Main window container
- `QTableWidget`: Data table display
- `QMenuBar`, `QMenu`: Menu system
- `QStatusBar`: Status display
- `QProgressBar`: Loading indicator
- `QFileDialog`: File selection

### Threading
- `QThread`: Background processing
- `pyqtSignal`: Thread communication

## Extension Points

### Adding New Features

1. **Export Functionality**
   - Add export methods to `MXMLParser`
   - Add export action to File menu
   - Implement export dialog

2. **Translation Editing**
   - Make table cells editable
   - Add save functionality
   - Implement MXML writing in parser

3. **Search/Filter**
   - Add search bar widget
   - Implement filter logic in table
   - Add filter state management

## Code Style Guidelines

### Type Hints
Always use type hints:
```python
def parse_file(self, file_path: str) -> List[MXMLEntry]:
    pass
```

### Docstrings
Use Google-style docstrings:
```python
def method(self, param: str) -> bool:
    """
    Brief description.
    
    Args:
        param: Parameter description
        
    Returns:
        Return value description
        
    Raises:
        ValueError: When validation fails
    """
    pass
```

### Error Handling
```python
try:
    # Operation
    pass
except SpecificError as e:
    # Handle specific error
    logger.error(f"Error: {e}")
    raise
```

## Testing Strategy

### Unit Tests
- Test MXML parser with various file structures
- Test entry extraction accuracy
- Test error handling

### Integration Tests
- Test full load workflow
- Test UI updates
- Test threading

### Manual Testing
- Load various MXML files
- Test menu functionality
- Test error conditions (invalid files, corrupted XML)

## Building

### Development Build
```bash
python -m src.main
```

### Production Build
```bash
python build.py
```

Creates standalone executable using PyInstaller.

## Dependencies

### Core Dependencies
- **PyQt6**: GUI framework
- **lxml**: Fast XML parsing with XPath support

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting

## Performance Considerations

### File Loading
- Large files (>1MB) loaded in background thread
- Progress indication for user feedback
- Memory-efficient parsing with lxml

### Table Display
- Sorting enabled on columns
- Row height auto-adjusted to content
- Efficient item creation

## Future Architecture Plans

### Plugin System
- Plugin interface for translation tools
- Dynamic tool loading
- Tool registration system

### Translation Memory
- Database integration
- Fuzzy matching
- Translation suggestions

### Batch Processing
- Multiple file support
- Parallel processing
- Progress tracking per file
