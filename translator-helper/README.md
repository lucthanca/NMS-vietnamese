# NMS MXML Translator Helper

A GUI application for managing No Man's Sky MXML localization files. This tool helps translators load and view MXML files containing game text for translation purposes.

## Features

- **Simple GUI Interface**: User-friendly PyQt6-based interface
- **MXML File Loading**: Load and parse No Man's Sky MXML localization files
- **Data Table View**: Display key-content pairs in an easy-to-read table format
- **Export Functionality**: Export to JSON and MXML formats with HTML entity preservation
- **Progress Tracking**: Real-time loading progress with status bar
- **Responsive Design**: Table automatically adapts to window resizing
- **Extensible Design**: Structured codebase ready for future translation tools

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
cd translator-helper
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

From the `translator-helper` directory:

```bash
python -m src.main
```

Or using the provided script:

```bash
python run.py
```

### Loading Files

1. Launch the application
2. Go to **File > Load** and choose one of the loading options:
   - **Load MXML** (`Ctrl+O`): Load an MXML localization file directly
   - **Load MBIN** (`Ctrl+B`): Load an MBIN file (automatically converts to MXML)
3. Select a file (e.g., `examples/NMS_LOC1_ENGLISH_EXAMPLE.MXML`)
4. View the loaded entries in the table

**Note:** MBIN files are automatically converted to MXML using MBINCompiler before loading.

### Exporting Data

After loading a file, you can export the data in multiple formats:

1. **Export to JSON** (`Ctrl+J`):
   - Go to `File > Export > Export to JSON`
   - Choose a save location
   - Creates a JSON file with key-value pairs

2. **Export to MXML** (`Ctrl+M`):
   - Go to `File > Export > Export to MXML`
   - Choose a save location
   - Creates a valid MXML file with proper structure
   - HTML entities are automatically preserved (&lt;, &gt;, &amp;, etc.)

3. **Export to MBIN** (`Ctrl+Shift+B`):
   - Go to `File > Export > Export to MBIN`
   - Choose a save location
   - Creates an MBIN file (automatically converts from MXML)

### Comparing Files

After loading a file, you can compare it with another file:

1. Go to `Tools > Compare Files` (`Ctrl+D`)
2. Select a file to compare (MXML or MBIN)
3. View the comparison results:
   - **Green (+)**: Entries added in comparison file
   - **Red (-)**: Entries removed in comparison file
   - **Orange (~)**: Entries with modified content
4. Export only the changes (modified/added entries):
   - **Export to JSON**: Key-value pairs of modified/added entries only
   - **Export to MXML**: Modified/added entries in MXML format

**Note:** Exports only include modified and added entries (not removed ones).

**Note:** If files are identical, you'll see a confirmation message.

### Menu Options

- **File > Load > Load MXML** (`Ctrl+O`): Open and load an MXML file
- **File > Load > Load MBIN** (`Ctrl+B`): Open and load an MBIN file (with conversion)
- **File > Export > Export to JSON** (`Ctrl+J`): Export loaded data to JSON format
- **File > Export > Export to MXML** (`Ctrl+M`): Export loaded data to MXML format
- **File > Export > Export to MBIN** (`Ctrl+Shift+B`): Export loaded data to MBIN format
- **Tools > Compare Files** (`Ctrl+D`): Compare current file with another file
- **File > Exit** (`Ctrl+Q`): Close the application

## Project Structure

```
translator-helper/
├── src/                    # Application entry point
│   └── main.py            # Main application launcher
├── ui/                     # User interface modules
│   ├── main_window.py     # Main window implementation
│   └── compare_dialog.py  # File comparison dialog
├── core/                   # Core functionality
│   ├── mxml_parser.py     # MXML file parser
│   ├── exporter.py        # Export functionality (JSON, MXML)
│   └── comparator.py      # File comparison logic
├── utils/                  # Utility modules
│   └── mbin_compiler.py   # MBIN compiler wrapper
├── tools/                  # External tools
│   └── MBINCompiler.6.13.0.1.exe  # MBIN<->MXML converter
├── tests/                  # Test suite
│   ├── test_export.py     # Export tests
│   ├── test_mbin.py       # MBIN conversion tests
│   └── test_comparison.py # Comparison tests
├── examples/               # Example MXML files
│   └── NMS_LOC1_ENGLISH_EXAMPLE.MXML
├── requirements.txt        # Python dependencies
├── setup.py               # Package configuration
├── run.py                 # Launcher script
└── README.md              # This file
```

## Development

### Code Style

This project follows Python best practices:
- Type hints for all function signatures
- Comprehensive docstrings
- PEP 8 style guidelines

### Testing

Run tests using pytest:
```bash
pytest
```

### Building Executable

To build a standalone executable:

```bash
python build.py
```

The executable will be created in the `dist/` directory.

## Future Features

- Translation editing capabilities
- Export to various formats
- Translation memory integration
- Batch file processing
- Search and filter functionality

## Contributing

When contributing to this project:
1. Follow the existing code structure
2. Add docstrings to all functions and classes
3. Update relevant documentation
4. Test your changes thoroughly

## License

This project is part of the NMS Vietnamese Translation effort.

## Support

For issues or questions, please refer to the DEV_DOCS.md file for technical details.
