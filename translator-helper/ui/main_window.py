"""
Main Window Module

This module provides the main GUI window for the NMS MXML Translator Helper application.
"""

from typing import Optional, List, Dict
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QProgressBar,
    QStatusBar, QMenuBar, QMenu, QHeaderView, QLabel
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QColor
from pathlib import Path

from core.mxml_parser import MXMLParser, MXMLEntry
from core.exporter import MXMLExporter
from core.comparator import EntryComparator
from utils.mbin_compiler import MBINCompiler, MBINCompilerError, cleanup_temp_dir
from ui.compare_dialog import CompareDialog


class LoaderThread(QThread):
    """
    Background thread for loading MXML files without blocking the UI.

    Signals:
        progress: Emits (current, total) for progress updates
        finished: Emits list of MXMLEntry when loading is complete
        error: Emits error message string if loading fails
    """

    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, is_mbin: bool = False):
        """
        Initialize the loader thread.

        Args:
            file_path: Path to the MXML or MBIN file to load
            is_mbin: True if file is MBIN format (requires conversion)
        """
        super().__init__()
        self.file_path = file_path
        self.is_mbin = is_mbin
        self.temp_mxml_path = None

    def run(self):
        """Execute the file loading in background."""
        try:
            file_to_parse = self.file_path

            # If MBIN, convert to MXML first
            if self.is_mbin:
                compiler = MBINCompiler()
                self.temp_mxml_path = compiler.mbin_to_mxml(self.file_path)
                file_to_parse = self.temp_mxml_path

            # Parse the MXML file
            parser = MXMLParser()
            entries = parser.parse_file(file_to_parse)
            self.finished.emit(entries)

        except MBINCompilerError as e:
            self.error.emit(f"MBIN conversion error: {e}")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Cleanup temp files
            if self.temp_mxml_path:
                temp_dir = Path(self.temp_mxml_path).parent
                cleanup_temp_dir(str(temp_dir))


class ComparisonThread(QThread):
    """
    Background thread for loading and comparing files without blocking the UI.

    Signals:
        status: Emits status message for UI updates
        finished: Emits (compare_entries, compare_filename) when loading is complete
        error: Emits error message string if loading fails
    """

    status = pyqtSignal(str)
    finished = pyqtSignal(list, str)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        """
        Initialize the comparison thread.

        Args:
            file_path: Path to the MXML or MBIN file to compare
        """
        super().__init__()
        self.file_path = file_path
        self.temp_mxml_path = None

    def run(self):
        """Execute the file loading and comparison in background."""
        try:
            compare_path = Path(self.file_path)

            # Determine if MBIN or MXML
            is_mbin = compare_path.suffix.upper() in ['.MBIN', '.PC']

            # Load the comparison file
            if is_mbin:
                self.status.emit(f"Converting MBIN file: {compare_path.name}...")
                # Convert MBIN to MXML
                compiler = MBINCompiler()
                self.temp_mxml_path = compiler.mbin_to_mxml(self.file_path)
                file_to_parse = self.temp_mxml_path
            else:
                file_to_parse = self.file_path

            self.status.emit(f"Parsing file: {compare_path.name}...")
            # Parse the file
            parser = MXMLParser()
            compare_entries = parser.parse_file(file_to_parse)

            self.status.emit("Comparing entries...")
            self.finished.emit(compare_entries, compare_path.name)

        except MBINCompilerError as e:
            self.error.emit(f"MBIN conversion error: {e}")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Cleanup temp files
            if self.temp_mxml_path:
                temp_dir = Path(self.temp_mxml_path).parent
                cleanup_temp_dir(str(temp_dir))


class MergeThread(QThread):
    """
    Background thread for loading and merging translation files without blocking the UI.

    Signals:
        status: Emits status message for UI updates
        progress: Emits (current, total) for progress updates
        finished: Emits Dict[str, str] with merged translations (key -> translated_content)
        error: Emits error message string if loading fails
    """

    status = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, paths: List[str]):
        """
        Initialize the merge thread.

        Args:
            paths: List of file or folder paths to load translations from
        """
        super().__init__()
        self.paths = paths
        self.temp_files = []

    def run(self):
        """Execute the file loading and merging in background."""
        try:
            merged_translations: Dict[str, str] = {}
            all_files = []

            self.status.emit("Scanning for translation files...")
            
            # Collect all files to process
            for path_str in self.paths:
                path = Path(path_str)
                if path.is_dir():
                    self.status.emit(f"Scanning directory: {path.name}...")
                    # Find all translation files in directory (non-recursive for speed)
                    for pattern in ["*.MXML", "*.mxml", "*.MBIN", "*.mbin", "*.json", "*.JSON"]:
                        all_files.extend(list(path.glob(pattern)))
                    # Also check for .MBIN.PC files
                    all_files.extend(list(path.glob("*.MBIN.PC")))
                    all_files.extend(list(path.glob("*.mbin.pc")))
                else:
                    all_files.append(path)

            # Remove duplicates
            all_files = list(set(all_files))

            if not all_files:
                self.error.emit("No valid translation files found")
                return

            total_files = len(all_files)
            self.status.emit(f"Found {total_files} translation file(s)...")

            # Process each file
            for idx, file_path in enumerate(all_files, 1):
                self.progress.emit(idx, total_files)
                self.status.emit(f"Loading {file_path.name}... ({idx}/{total_files})")

                try:
                    translations = self._load_file(file_path)
                    # Merge translations (later files override earlier ones)
                    merged_translations.update(translations)
                except Exception as e:
                    self.status.emit(f"Warning: Failed to load {file_path.name}: {e}")
                    continue

            self.status.emit(f"Loaded {len(merged_translations)} translation(s)")
            self.finished.emit(merged_translations)

        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Cleanup temp files
            for temp_file in self.temp_files:
                try:
                    temp_dir = Path(temp_file).parent
                    cleanup_temp_dir(str(temp_dir))
                except:
                    pass

    def _load_file(self, file_path: Path) -> Dict[str, str]:
        """
        Load translations from a single file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary mapping keys to translated content
        """
        suffix = file_path.suffix.upper()

        # Handle JSON files
        if suffix == '.JSON':
            self.status.emit(f"Parsing JSON: {file_path.name}...")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Support both flat dict and nested structures
                if isinstance(data, dict):
                    return {k: str(v) for k, v in data.items()}
                return {}

        # Handle MBIN files (check full name for .MBIN.PC pattern)
        is_mbin = suffix == '.MBIN' or file_path.name.upper().endswith('.MBIN.PC')
        
        if is_mbin:
            self.status.emit(f"Converting MBIN: {file_path.name}...")
            compiler = MBINCompiler()
            temp_mxml = compiler.mbin_to_mxml(str(file_path))
            self.temp_files.append(temp_mxml)
            file_to_parse = temp_mxml
        else:
            file_to_parse = str(file_path)

        # Parse MXML
        self.status.emit(f"Parsing MXML: {file_path.name}...")
        parser = MXMLParser()
        entries = parser.parse_file(file_to_parse)

        # Convert to dictionary
        self.status.emit(f"Extracted {len(entries)} entries from {file_path.name}")
        return {entry.key: entry.content for entry in entries}


class MainWindow(QMainWindow):
    """
    Main application window for NMS MXML Translator Helper.

    Provides a GUI interface to:
    - Load MXML files
    - Display key-content pairs in a table
    - Show loading progress and status
    """

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        self.entries: List[MXMLEntry] = []
        self.current_file: Optional[Path] = None
        self.loader_thread: Optional[LoaderThread] = None
        self.comparison_thread: Optional[ComparisonThread] = None
        self.merge_thread: Optional[MergeThread] = None
        self.translations: Dict[str, str] = {}  # key -> translated content

        self._init_ui()
        self._set_window_icon()

    def closeEvent(self, event):
        """Handle window close event - cleanup threads."""
        # Wait for any running threads to finish
        for thread in [self.loader_thread, self.comparison_thread, self.merge_thread]:
            if thread and thread.isRunning():
                thread.quit()
                thread.wait(1000)  # Wait max 1 second
        event.accept()

    def _set_window_icon(self):
        """Set the application window icon."""
        icon_path = Path(__file__).parent.parent / "resources" / "translator.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _init_ui(self):
        """Initialize the user interface components."""
        self.setWindowTitle("NMS MXML Translator Helper")
        self.setGeometry(100, 100, 1000, 600)

        # Create menu bar
        self._create_menu_bar()

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create table widget
        self._create_table()
        layout.addWidget(self.table)

        # Create status bar with progress bar
        self._create_status_bar()

    def _create_menu_bar(self):
        """Create the menu bar with File menu."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Load submenu
        load_menu = file_menu.addMenu("&Load")

        # Load MXML action
        load_mxml_action = QAction("Load &MXML", self)
        load_mxml_action.setShortcut("Ctrl+O")
        load_mxml_action.setStatusTip("Load an MXML localization file")
        load_mxml_action.triggered.connect(self._on_load_mxml)
        load_menu.addAction(load_mxml_action)

        # Load MBIN action
        load_mbin_action = QAction("Load M&BIN", self)
        load_mbin_action.setShortcut("Ctrl+B")
        load_mbin_action.setStatusTip("Load an MBIN file (will be converted to MXML)")
        load_mbin_action.triggered.connect(self._on_load_mbin)
        load_menu.addAction(load_mbin_action)

        file_menu.addSeparator()

        # Export submenu
        export_menu = file_menu.addMenu("&Export")        # Export to JSON action
        export_json_action = QAction("Export to &JSON", self)
        export_json_action.setShortcut("Ctrl+J")
        export_json_action.setStatusTip("Export entries to JSON format")
        export_json_action.triggered.connect(self._on_export_json)
        export_menu.addAction(export_json_action)

        # Export to MXML action
        export_mxml_action = QAction("Export to &MXML", self)
        export_mxml_action.setShortcut("Ctrl+M")
        export_mxml_action.setStatusTip("Export entries to MXML format")
        export_mxml_action.triggered.connect(self._on_export_mxml)
        export_menu.addAction(export_mxml_action)

        # Export to MBIN action
        export_mbin_action = QAction("Export to M&BIN", self)
        export_mbin_action.setShortcut("Ctrl+Shift+B")
        export_mbin_action.setStatusTip("Export entries to MBIN format")
        export_mbin_action.triggered.connect(self._on_export_mbin)
        export_menu.addAction(export_mbin_action)

        # Initially disable export until file is loaded
        export_menu.setEnabled(False)
        self.export_menu = export_menu

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Merge Translation action
        merge_action = QAction("&Merge Translation Files", self)
        merge_action.setShortcut("Ctrl+T")
        merge_action.setStatusTip("Load and merge translation files into current entries")
        merge_action.triggered.connect(self._on_merge_translations)
        tools_menu.addAction(merge_action)

        tools_menu.addSeparator()

        # Compare action
        compare_action = QAction("&Compare Files", self)
        compare_action.setShortcut("Ctrl+D")
        compare_action.setStatusTip("Compare current file with another file")
        compare_action.triggered.connect(self._on_compare_files)
        tools_menu.addAction(compare_action)

        # Initially disable tools until file is loaded
        tools_menu.setEnabled(False)
        self.tools_menu = tools_menu

    def _create_table(self):
        """Create the table widget for displaying entries."""
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Key", "Original Content", "Translated Content"])

        # Configure horizontal header for responsive resizing
        header = self.table.horizontalHeader()

        # Key column: Fixed width, resize to contents
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        # Original Content column: Stretch to fill space
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Translated Content column: Stretch to fill space
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Set minimum column widths
        self.table.setColumnWidth(0, 200)

        # Table properties
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)

        # Enable word wrap for content column
        self.table.setWordWrap(True)

    def _create_status_bar(self):
        """Create the status bar with progress indicator."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Version label
        version_label = QLabel("v0.4.0")
        version_label.setStyleSheet("color: gray;")
        self.status_bar.addWidget(version_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Initial status
        self.status_bar.showMessage("Ready")

    def _on_load_mxml(self):
        """Handle Load MXML menu action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open MXML File",
            "",
            "MXML Files (*.MXML);;All Files (*.*)"
        )

        if file_path:
            self._load_file(file_path, is_mbin=False)

    def _on_load_mbin(self):
        """Handle Load MBIN menu action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open MBIN File",
            "",
            "MBIN Files (*.MBIN *.MBIN.PC);;All Files (*.*)"
        )

        if file_path:
            self._load_file(file_path, is_mbin=True)

    def _load_file(self, file_path: str, is_mbin: bool = False):
        """
        Load an MXML or MBIN file in a background thread.

        Args:
            file_path: Path to the MXML or MBIN file
            is_mbin: True if loading MBIN file (requires conversion)
        """
        self.current_file = Path(file_path)

        # Show loading state
        if is_mbin:
            self.status_bar.showMessage(f"Converting and loading {self.current_file.name}...")
        else:
            self.status_bar.showMessage(f"Loading {self.current_file.name}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Disable menu actions during loading
        self.menuBar().setEnabled(False)

        # Start loader thread
        self.loader_thread = LoaderThread(file_path, is_mbin=is_mbin)
        self.loader_thread.finished.connect(self._on_load_finished)
        self.loader_thread.error.connect(self._on_load_error)
        self.loader_thread.start()

    def _on_load_finished(self, entries: List[MXMLEntry]):
        """
        Handle successful file loading.

        Args:
            entries: List of loaded MXML entries
        """
        self.entries = entries
        self._populate_table()

        # Update UI state
        self.progress_bar.setVisible(False)
        self.menuBar().setEnabled(True)

        # Enable export and tools menu after successful load
        self.export_menu.setEnabled(True)
        self.tools_menu.setEnabled(True)

        entry_count = len(entries)
        self.status_bar.showMessage(
            f"Loaded {entry_count} entries from {self.current_file.name}"
        )

    def _on_load_error(self, error_message: str):
        """
        Handle file loading error.

        Args:
            error_message: Error description
        """
        self.progress_bar.setVisible(False)
        self.menuBar().setEnabled(True)

        QMessageBox.critical(
            self,
            "Error Loading File",
            f"Failed to load MXML file:\n\n{error_message}"
        )

        self.status_bar.showMessage("Error loading file")

    def _populate_table(self):
        """Populate the table with loaded entries."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.entries))

        for row, entry in enumerate(self.entries):
            # Key column
            key_item = QTableWidgetItem(entry.key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, key_item)

            # Original Content column
            content_item = QTableWidgetItem(entry.content)
            content_item.setFlags(content_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, content_item)

            # Translated Content column
            translated = self.translations.get(entry.key, "")
            translated_item = QTableWidgetItem(translated)
            translated_item.setFlags(translated_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Highlight if translated
            if translated:
                translated_item.setBackground(QColor(200, 255, 200))  # Light green
            
            self.table.setItem(row, 2, translated_item)

        self.table.setSortingEnabled(True)
        self.table.resizeRowsToContents()

    def _on_export_json(self):
        """Handle Export to JSON action."""
        if not self.entries:
            QMessageBox.warning(
                self,
                "No Data",
                "Please load an MXML file before exporting."
            )
            return

        # Get save file path
        default_name = self.current_file.stem + ".json" if self.current_file else "export.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to JSON",
            default_name,
            "JSON Files (*.json);;All Files (*.*)"
        )

        if file_path:
            try:
                # Create entries with translated content if available
                export_entries = self._get_export_entries()
                exporter = MXMLExporter(export_entries)
                exporter.export_to_json(file_path)

                translated_count = len([e for e in self.entries if e.key in self.translations])
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Successfully exported {len(export_entries)} entries to:\n{file_path}\n\n"
                    f"Translated: {translated_count}"
                )
                self.status_bar.showMessage(f"Exported to {Path(file_path).name}")

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export to JSON:\n\n{str(e)}"
                )
                self.status_bar.showMessage("Export failed")

    def _on_export_mxml(self):
        """Handle Export to MXML action."""
        if not self.entries:
            QMessageBox.warning(
                self,
                "No Data",
                "Please load an MXML file before exporting."
            )
            return

        # Get save file path
        default_name = self.current_file.stem + "_exported.MXML" if self.current_file else "export.MXML"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to MXML",
            default_name,
            "MXML Files (*.MXML);;All Files (*.*)"
        )

        if file_path:
            try:
                # Create entries with translated content if available
                export_entries = self._get_export_entries()
                exporter = MXMLExporter(export_entries)
                exporter.export_to_mxml(file_path)

                translated_count = len([e for e in self.entries if e.key in self.translations])
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Successfully exported {len(export_entries)} entries to:\n{file_path}\n\n"
                    f"Translated: {translated_count}"
                )
                self.status_bar.showMessage(f"Exported to {Path(file_path).name}")

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export to MXML:\n\n{str(e)}"
                )
                self.status_bar.showMessage("Export failed")

    def _on_export_mbin(self):
        """Handle Export to MBIN action."""
        if not self.entries:
            QMessageBox.warning(
                self,
                "No Data",
                "Please load a file before exporting."
            )
            return

        # Get save file path
        default_name = self.current_file.stem + "_exported.MBIN" if self.current_file else "export.MBIN"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to MBIN",
            default_name,
            "MBIN Files (*.MBIN);;All Files (*.*)"
        )

        if file_path:
            try:
                # Show progress
                self.status_bar.showMessage("Exporting to MBIN...")
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)

                # First export to temp MXML
                import tempfile
                temp_mxml = tempfile.NamedTemporaryFile(mode='w', suffix='.MXML', delete=False, encoding='utf-8')
                temp_mxml_path = temp_mxml.name
                temp_mxml.close()

                # Create entries with translated content if available
                export_entries = self._get_export_entries()
                exporter = MXMLExporter(export_entries)
                exporter.export_to_mxml(temp_mxml_path)

                # Convert MXML to MBIN
                compiler = MBINCompiler()
                output_dir = Path(file_path).parent
                mbin_path = compiler.mxml_to_mbin(temp_mxml_path, str(output_dir))

                # Rename to desired filename
                final_path = Path(file_path)
                Path(mbin_path).replace(final_path)

                # Cleanup temp files
                Path(temp_mxml_path).unlink(missing_ok=True)

                self.progress_bar.setVisible(False)

                translated_count = len([e for e in self.entries if e.key in self.translations])
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Successfully exported {len(export_entries)} entries to:\n{file_path}\n\n"
                    f"Translated: {translated_count}"
                )
                self.status_bar.showMessage(f"Exported to {final_path.name}")

            except MBINCompilerError as e:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"MBIN conversion error:\n\n{str(e)}"
                )
                self.status_bar.showMessage("Export failed")
            except Exception as e:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export to MBIN:\n\n{str(e)}"
                )
                self.status_bar.showMessage("Export failed")
            finally:
                # Ensure temp file is cleaned up
                try:
                    if 'temp_mxml_path' in locals():
                        Path(temp_mxml_path).unlink(missing_ok=True)
                except:
                    pass

    def _on_compare_files(self):
        """Handle Compare Files action."""
        if not self.entries:
            QMessageBox.warning(
                self,
                "No Data",
                "Please load a file before comparing."
            )
            return

        # Ask user to select file to compare
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Compare",
            "",
            "Localization Files (*.MXML *.MBIN *.MBIN.PC);;MXML Files (*.MXML);;MBIN Files (*.MBIN *.MBIN.PC);;All Files (*.*)"
        )

        if not file_path:
            return

        # Show progress
        self.status_bar.showMessage("Loading comparison file...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # Disable menus during comparison
        self.menuBar().setEnabled(False)

        # Create and start comparison thread
        self.comparison_thread = ComparisonThread(file_path)
        self.comparison_thread.status.connect(self._on_comparison_status)
        self.comparison_thread.finished.connect(self._on_comparison_finished)
        self.comparison_thread.error.connect(self._on_comparison_error)
        self.comparison_thread.start()

    def _on_comparison_status(self, message: str):
        """
        Handle status updates from comparison thread.

        Args:
            message: Status message to display
        """
        self.status_bar.showMessage(message)

    def _on_comparison_finished(self, compare_entries: List[MXMLEntry], compare_filename: str):
        """
        Handle successful comparison.

        Args:
            compare_entries: Entries from the comparison file
            compare_filename: Name of the comparison file
        """
        self.progress_bar.setVisible(False)
        self.menuBar().setEnabled(True)

        # Perform comparison
        comparator = EntryComparator(self.entries, compare_entries)

        # Check if identical
        if comparator.is_identical():
            QMessageBox.information(
                self,
                "Comparison Result",
                "✓ Files are identical!\n\nBoth files contain the same entries with the same content."
            )
            self.status_bar.showMessage("Files are identical")
            return

        # Get comparison results
        results = comparator.compare()

        # Show comparison dialog
        dialog = CompareDialog(
            self.current_file.name,
            compare_filename,
            results,
            self
        )
        dialog.exec()

        self.status_bar.showMessage("Comparison complete")

    def _on_comparison_error(self, error_message: str):
        """
        Handle comparison errors.

        Args:
            error_message: Error message to display
        """
        self.progress_bar.setVisible(False)
        self.menuBar().setEnabled(True)

        QMessageBox.critical(
            self,
            "Comparison Error",
            f"Failed to compare files:\n\n{error_message}"
        )
        self.status_bar.showMessage("Comparison failed")

    def _on_merge_translations(self):
        """Handle Merge Translation Files action."""
        if not self.entries:
            QMessageBox.warning(
                self,
                "No Data",
                "Please load a main file before merging translations."
            )
            return

        # Ask user: folder or files?
        choice = QMessageBox.question(
            self,
            "Select Translation Source",
            "Do you want to load translations from a folder?\n\n"
            "Click 'Yes' to select a folder\n"
            "Click 'No' to select individual files",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes
        )

        if choice == QMessageBox.StandardButton.Cancel:
            return

        paths = []
        
        if choice == QMessageBox.StandardButton.Yes:
            # Select folder
            folder_path = QFileDialog.getExistingDirectory(
                self,
                "Select Translation Folder",
                "",
                QFileDialog.Option.ShowDirsOnly
            )
            if folder_path:
                paths = [folder_path]
        else:
            # Select files
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Translation Files",
                "",
                "Translation Files (*.MXML *.MBIN *.MBIN.PC *.json *.JSON);;All Files (*.*)"
            )
            paths = file_paths

        if not paths:
            return

        # Show progress
        self.status_bar.showMessage("Loading translation files...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # Disable menus during merge
        self.menuBar().setEnabled(False)

        # Create and start merge thread
        self.merge_thread = MergeThread(paths)
        self.merge_thread.status.connect(self._on_merge_status)
        self.merge_thread.progress.connect(self._on_merge_progress)
        self.merge_thread.finished.connect(self._on_merge_finished)
        self.merge_thread.error.connect(self._on_merge_error)
        self.merge_thread.start()

    def _on_merge_status(self, message: str):
        """
        Handle status updates from merge thread.

        Args:
            message: Status message to display
        """
        self.status_bar.showMessage(message)

    def _on_merge_progress(self, current: int, total: int):
        """
        Handle progress updates from merge thread.

        Args:
            current: Current file number
            total: Total number of files
        """
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)

    def _on_merge_finished(self, translations: Dict[str, str]):
        """
        Handle successful merge.

        Args:
            translations: Dictionary mapping keys to translated content
        """
        self.progress_bar.setVisible(False)
        self.menuBar().setEnabled(True)

        # Update translations
        self.translations = translations

        # Update only the translated column instead of repopulating entire table
        self._update_translation_column()

        # Show summary
        translated_count = len([e for e in self.entries if e.key in translations])
        QMessageBox.information(
            self,
            "Merge Complete",
            f"Successfully merged translations!\n\n"
            f"Total translations loaded: {len(translations)}\n"
            f"Matching entries: {translated_count}/{len(self.entries)}"
        )
        self.status_bar.showMessage(
            f"Merged {translated_count} translations"
        )

    def _update_translation_column(self):
        """Update only the translation column (column 2) without repopulating entire table."""
        self.table.setSortingEnabled(False)
        
        highlight_color = QColor(200, 255, 200)
        
        for row in range(self.table.rowCount()):
            # Get key from first column
            key_item = self.table.item(row, 0)
            if not key_item:
                continue
                
            key = key_item.text()
            translated = self.translations.get(key, "")
            
            # Update translated column
            translated_item = QTableWidgetItem(translated)
            translated_item.setFlags(translated_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            if translated:
                translated_item.setBackground(highlight_color)
            
            self.table.setItem(row, 2, translated_item)
        
        self.table.setSortingEnabled(True)

    def _on_merge_error(self, error_message: str):
        """
        Handle merge errors.

        Args:
            error_message: Error message to display
        """
        self.progress_bar.setVisible(False)
        self.menuBar().setEnabled(True)

        QMessageBox.critical(
            self,
            "Merge Error",
            f"Failed to merge translation files:\n\n{error_message}"
        )
        self.status_bar.showMessage("Merge failed")

    def _get_export_entries(self) -> List[MXMLEntry]:
        """
        Get entries for export, using translated content if available.

        Returns:
            List of MXMLEntry with translated content where available
        """
        export_entries = []
        for entry in self.entries:
            # Use translated content if available, otherwise use original
            content = self.translations.get(entry.key, entry.content)
            export_entries.append(MXMLEntry(key=entry.key, content=content))
        return export_entries
