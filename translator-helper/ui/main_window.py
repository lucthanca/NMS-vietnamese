"""
Main Window Module

This module provides the main GUI window for the NMS MXML Translator Helper application.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableWidget, 
    QTableWidgetItem, QFileDialog, QMessageBox, QProgressBar,
    QStatusBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction
from pathlib import Path

from core.mxml_parser import MXMLParser, MXMLEntry


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
    
    def __init__(self, file_path: str):
        """
        Initialize the loader thread.
        
        Args:
            file_path: Path to the MXML file to load
        """
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        """Execute the file loading in background."""
        try:
            parser = MXMLParser()
            entries = parser.parse_file(self.file_path)
            self.finished.emit(entries)
        except Exception as e:
            self.error.emit(str(e))


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
        
        self._init_ui()
    
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
        
        # Load MXML action
        load_action = QAction("&Load MXML", self)
        load_action.setShortcut("Ctrl+O")
        load_action.setStatusTip("Load an MXML localization file")
        load_action.triggered.connect(self._on_load_mxml)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def _create_table(self):
        """Create the table widget for displaying entries."""
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Key", "Content"])
        
        # Set column widths
        self.table.setColumnWidth(0, 300)
        self.table.setColumnWidth(1, 650)
        
        # Table properties
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
    
    def _create_status_bar(self):
        """Create the status bar with progress indicator."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
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
            self._load_file(file_path)
    
    def _load_file(self, file_path: str):
        """
        Load an MXML file in a background thread.
        
        Args:
            file_path: Path to the MXML file
        """
        self.current_file = Path(file_path)
        
        # Show loading state
        self.status_bar.showMessage(f"Loading {self.current_file.name}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Disable menu actions during loading
        self.menuBar().setEnabled(False)
        
        # Start loader thread
        self.loader_thread = LoaderThread(file_path)
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
            
            # Content column
            content_item = QTableWidgetItem(entry.content)
            content_item.setFlags(content_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, content_item)
        
        self.table.setSortingEnabled(True)
        self.table.resizeRowsToContents()
