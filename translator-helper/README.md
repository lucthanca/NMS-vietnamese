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

### Loading MXML Files

1. Launch the application
2. Go to `File > Load MXML` (or press `Ctrl+O`)
3. Select an MXML file (e.g., `examples/NMS_LOC1_ENGLISH_EXAMPLE.MXML`)
4. View the loaded entries in the table

### Exporting Data

After loading an MXML file, you can export the data:

1. **Export to JSON** (`Ctrl+J`):
   - Go to `File > Export > Export to JSON`
   - Choose a save location
   - Creates a JSON file with key-value pairs

2. **Export to MXML** (`Ctrl+M`):
   - Go to `File > Export > Export to MXML`
   - Choose a save location
   - Creates a valid MXML file with proper structure
   - HTML entities are automatically preserved (&lt;, &gt;, &amp;, etc.)

### Menu Options

- **File > Load MXML** (`Ctrl+O`): Open and load an MXML file
- **File > Export > Export to JSON** (`Ctrl+J`): Export loaded data to JSON format
- **File > Export > Export to MXML** (`Ctrl+M`): Export loaded data to MXML format
- **File > Exit** (`Ctrl+Q`): Close the application

## Project Structure

```
translator-helper/
├── src/                    # Application entry point
│   └── main.py            # Main application launcher
├── ui/                     # User interface modules
│   └── main_window.py     # Main window implementation
├── core/                   # Core functionality
│   ├── mxml_parser.py     # MXML file parser
│   └── exporter.py        # Export functionality (JSON, MXML)
├── utils/                  # Utility functions (future)
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
