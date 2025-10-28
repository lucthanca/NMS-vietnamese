"""
Compare Dialog Module

This module provides a dialog window to display comparison results
between two MXML files.
"""

from typing import List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFileDialog, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from pathlib import Path

from core.comparator import ComparisonEntry, DiffType
from core.exporter import MXMLExporter
from core.mxml_parser import MXMLEntry


class CompareDialog(QDialog):
    """
    Dialog window for displaying file comparison results.
    """

    def __init__(self, main_filename: str, compare_filename: str,
                 comparison_results: List[ComparisonEntry], parent=None):
        """
        Initialize the compare dialog.

        Args:
            main_filename: Name of the main file
            compare_filename: Name of the comparison file
            comparison_results: List of comparison results
            parent: Parent widget
        """
        super().__init__(parent)
        self.main_filename = main_filename
        self.compare_filename = compare_filename
        self.comparison_results = comparison_results

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("File Comparison Results")
        self.setGeometry(150, 150, 1200, 700)

        layout = QVBoxLayout(self)

        # Header with file names and summary
        header_layout = QVBoxLayout()

        # File names
        files_label = QLabel(
            f"<b>Main File:</b> {self.main_filename}<br>"
            f"<b>Compare File:</b> {self.compare_filename}"
        )
        header_layout.addWidget(files_label)

        # Summary
        summary = self._calculate_summary()
        if summary['total_differences'] == 0:
            summary_text = "<b style='color: green;'>✓ Files are identical</b>"
        else:
            summary_text = (
                f"<b>Differences Found:</b> {summary['total_differences']} "
                f"(<span style='color: green;'>+{summary['added']}</span>, "
                f"<span style='color: red;'>-{summary['removed']}</span>, "
                f"<span style='color: orange;'>~{summary['modified']}</span>)"
            )
        summary_label = QLabel(summary_text)
        header_layout.addWidget(summary_label)

        layout.addLayout(header_layout)

        # Table for comparison results
        self._create_table()
        layout.addWidget(self.table)

        # Button bar
        button_layout = QHBoxLayout()

        # Export buttons
        export_json_btn = QPushButton("Export to JSON")
        export_json_btn.clicked.connect(self._on_export_json)
        button_layout.addWidget(export_json_btn)

        export_mxml_btn = QPushButton("Export to MXML")
        export_mxml_btn.clicked.connect(self._on_export_mxml)
        button_layout.addWidget(export_mxml_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Populate table
        self._populate_table()

    def _create_table(self):
        """Create the comparison table."""
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Status", "Key", "Main File Content", "Compare File Content"])

        # Configure columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Key
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Main content
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Compare content

        # Table properties
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setWordWrap(True)

    def _populate_table(self):
        """Populate the table with comparison results."""
        self.table.setSortingEnabled(False)

        # Only show differences
        differences = [r for r in self.comparison_results if r.diff_type != DiffType.UNCHANGED]
        self.table.setRowCount(len(differences))

        for row, entry in enumerate(differences):
            # Status column
            status_item = QTableWidgetItem(entry.diff_type.value)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Color coding
            if entry.diff_type == DiffType.ADDED:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif entry.diff_type == DiffType.REMOVED:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif entry.diff_type == DiffType.MODIFIED:
                status_item.setBackground(QColor(255, 230, 200))  # Light orange

            self.table.setItem(row, 0, status_item)

            # Key column
            key_item = QTableWidgetItem(entry.key)
            self.table.setItem(row, 1, key_item)

            # Main content column
            main_content_item = QTableWidgetItem(entry.main_content)
            if entry.diff_type == DiffType.REMOVED:
                main_content_item.setForeground(QColor(150, 150, 150))  # Gray out
            self.table.setItem(row, 2, main_content_item)

            # Compare content column
            compare_content_item = QTableWidgetItem(entry.compare_content)
            if entry.diff_type == DiffType.ADDED:
                compare_content_item.setForeground(QColor(0, 128, 0))  # Green
            elif entry.diff_type == DiffType.MODIFIED:
                compare_content_item.setForeground(QColor(255, 140, 0))  # Orange
            self.table.setItem(row, 3, compare_content_item)

        self.table.setSortingEnabled(True)
        self.table.resizeRowsToContents()

    def _calculate_summary(self):
        """Calculate summary statistics."""
        summary = {
            'added': sum(1 for r in self.comparison_results if r.diff_type == DiffType.ADDED),
            'removed': sum(1 for r in self.comparison_results if r.diff_type == DiffType.REMOVED),
            'modified': sum(1 for r in self.comparison_results if r.diff_type == DiffType.MODIFIED),
        }
        summary['total_differences'] = summary['added'] + summary['removed'] + summary['modified']
        return summary

    def _on_export_json(self):
        """Export changes and additions (modified/added) to JSON."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Changes to JSON",
            "comparison_changes.json",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if file_path:
            try:
                import json

                # Build export data with only modified and added entries
                data = {}

                for entry in self.comparison_results:
                    # Only export MODIFIED and ADDED (not REMOVED)
                    if entry.diff_type in [DiffType.MODIFIED, DiffType.ADDED]:
                        # Use compare_content (the new/changed content)
                        data[entry.key] = entry.compare_content

                if not data:
                    QMessageBox.information(
                        self,
                        "No Changes",
                        "No modified or added entries to export."
                    )
                    return

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Exported {len(data)} changed/added entries to:\n{file_path}"
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export comparison:\n\n{str(e)}"
                )

    def _on_export_mxml(self):
        """Export changes and additions (modified/added) to MXML."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Changes to MXML",
            "comparison_changes.MXML",
            "MXML Files (*.MXML);;All Files (*.*)"
        )

        if file_path:
            try:
                # Create MXMLEntry objects from modified and added entries only
                entries = []
                for entry in self.comparison_results:
                    # Only export MODIFIED and ADDED (not REMOVED)
                    if entry.diff_type in [DiffType.MODIFIED, DiffType.ADDED]:
                        # Use compare_content (the new/changed content)
                        entries.append(MXMLEntry(key=entry.key, content=entry.compare_content))

                if not entries:
                    QMessageBox.information(
                        self,
                        "No Changes",
                        "No modified or added entries to export."
                    )
                    return

                # Export
                exporter = MXMLExporter(entries)
                exporter.export_to_mxml(file_path)

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Exported {len(entries)} changed/added entries to:\n{file_path}"
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export to MXML:\n\n{str(e)}"
                )
