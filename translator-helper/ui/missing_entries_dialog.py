"""
Missing Entries Dialog Module

Dialog for displaying entries that don't have translations and providing translation functionality.
"""

from typing import Dict, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QTextEdit, QSplitter, QHeaderView,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from pathlib import Path

from core.mxml_parser import MXMLEntry
from core.translation_engine import TranslationThread


class MissingEntriesDialog(QDialog):
    """Dialog for displaying and translating missing entries."""

    def __init__(self, missing_entries: List[MXMLEntry], parent=None):
        """
        Initialize the missing entries dialog.

        Args:
            missing_entries: List of entries without translations
            parent: Parent widget
        """
        super().__init__(parent)
        self.missing_entries = missing_entries
        self.settings = self._load_settings()
        self.translations: Dict[str, str] = {}  # key -> translated content
        self.translation_thread = None

        self._init_ui()

    def _load_settings(self) -> dict:
        """Load settings from file."""
        from translation import TranslationConfig
        from pathlib import Path
        settings_file = Path.home() / ".nms_translator_settings.json"
        config = TranslationConfig.load_from_settings(settings_file)
        return {
            "gemini_api_key": config.api_key,
            "workflow_type": config.workflow_type.value
        }

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"Missing Translations - {len(self.missing_entries)} Entries")
        self.setGeometry(150, 150, 1200, 800)

        layout = QVBoxLayout(self)

        # Header info
        info_label = QLabel(
            f"<b>{len(self.missing_entries)} entries</b> don't have translations yet"
        )
        layout.addWidget(info_label)

        # Splitter for table and translation progress
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Table for missing entries
        self._create_table()
        splitter.addWidget(self.table)

        # Translation progress area
        progress_widget = self._create_progress_area()
        splitter.addWidget(progress_widget)

        splitter.setSizes([500, 300])
        layout.addWidget(splitter)

        # Buttons
        button_layout = QHBoxLayout()

        self.translate_btn = QPushButton("Translate Missing Entries")
        self.translate_btn.clicked.connect(self._on_translate)
        self.translate_btn.setEnabled(bool(self.settings.get("gemini_api_key")))
        button_layout.addWidget(self.translate_btn)

        button_layout.addStretch()

        self.apply_btn = QPushButton("Apply to Main")
        self.apply_btn.clicked.connect(self._on_apply)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Show warning if no API key
        if not self.settings.get("gemini_api_key"):
            QMessageBox.warning(
                self,
                "No API Key",
                "Please configure your Gemini API key in Settings before translating."
            )

    def _create_table(self):
        """Create the table for missing entries."""
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Key", "Original Content", "Translated Content"])

        # Configure columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Table properties
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setWordWrap(True)

        # Populate table
        self._populate_table()

    def _populate_table(self):
        """Populate the table with missing entries."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.missing_entries))

        for row, entry in enumerate(self.missing_entries):
            # Key column
            key_item = QTableWidgetItem(entry.key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, key_item)

            # Original content column
            content_item = QTableWidgetItem(entry.content)
            content_item.setFlags(content_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, content_item)

            # Translated content column (empty initially)
            translated_item = QTableWidgetItem("")
            translated_item.setFlags(translated_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, translated_item)

        self.table.setSortingEnabled(True)

    def _create_progress_area(self):
        """Create the translation progress area."""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout

        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<b>Translation Progress:</b>"))

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status/log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

        return widget

    def _on_translate(self):
        """Handle translate button click."""
        api_key = self.settings.get("gemini_api_key", "")
        if not api_key:
            QMessageBox.warning(
                self,
                "No API Key",
                "Please configure your Gemini API key in Settings."
            )
            return

        # Prepare entries dict
        entries_dict = {entry.key: entry.content for entry in self.missing_entries}

        # Start translation
        self.translate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_text.append("Starting translation...")

        workflow = self.settings.get("workflow_type", "sequence")
        self.log_text.append(f"Using workflow: {workflow}")

        # Create and start translation thread
        self.translation_thread = TranslationThread(entries_dict, api_key, workflow)
        self.translation_thread.status.connect(self._on_translation_status)
        self.translation_thread.progress.connect(self._on_translation_progress)
        self.translation_thread.patch_completed.connect(self._on_patch_completed)
        self.translation_thread.finished.connect(self._on_translation_finished)
        self.translation_thread.error.connect(self._on_translation_error)
        self.translation_thread.start()

    def _on_translation_status(self, message: str):
        """Handle status updates from translation thread."""
        self.log_text.append(f"• {message}")

    def _on_translation_progress(self, current: int, total: int):
        """Handle progress updates from translation thread."""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)

    def _on_patch_completed(self, translated_patch: Dict[str, str]):
        """Handle completion of a translation patch."""
        # Update translations
        self.translations.update(translated_patch)

        # Update table
        self._update_translation_column()

        self.log_text.append(f"✓ Patch completed: {len(translated_patch)} entries")

    def _update_translation_column(self):
        """Update the translation column with new translations."""
        highlight_color = QColor(200, 255, 200)

        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            if not key_item:
                continue

            key = key_item.text()
            translated = self.translations.get(key, "")

            if translated:
                translated_item = QTableWidgetItem(translated)
                translated_item.setFlags(translated_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                translated_item.setBackground(highlight_color)
                self.table.setItem(row, 2, translated_item)

    def _on_translation_finished(self, all_translations: Dict[str, str]):
        """Handle translation completion."""
        self.progress_bar.setVisible(False)
        self.translate_btn.setEnabled(True)
        self.apply_btn.setEnabled(True)

        self.log_text.append(f"\n✓ Translation complete: {len(all_translations)} entries")

        QMessageBox.information(
            self,
            "Translation Complete",
            f"Successfully translated {len(all_translations)} entries.\n\n"
            f"Click 'Apply to Main' to merge these translations."
        )

    def _on_translation_error(self, error_message: str):
        """Handle translation errors."""
        self.progress_bar.setVisible(False)
        self.translate_btn.setEnabled(True)

        self.log_text.append(f"\n✗ Error: {error_message}")

        QMessageBox.critical(
            self,
            "Translation Error",
            f"Translation failed:\n\n{error_message}"
        )

    def _on_apply(self):
        """Handle apply to main button click."""
        if not self.translations:
            QMessageBox.warning(
                self,
                "No Translations",
                "No translations to apply."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Apply",
            f"Apply {len(self.translations)} translations to main file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_translations(self) -> Dict[str, str]:
        """Get the translations dictionary."""
        return self.translations

    def _check_and_cancel_translation(self):
        """
        Check if translation is running and ask user to cancel.
        Returns True if can close, False if should stay open.
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Checking translation status before close...")
        logger.info(f"  translation_thread exists: {self.translation_thread is not None}")
        if self.translation_thread:
            logger.info(f"  translation_thread.isRunning(): {self.translation_thread.isRunning()}")

        if self.translation_thread and self.translation_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Translation In Progress",
                "Translation is still running. Cancel and close?\n\n"
                "⚠️ Important:\n"
                "• Workers will stop after current API calls complete\n"
                "• Cannot interrupt ongoing API requests (10-30s each)\n"
                "• Partial results will be discarded\n"
                "• You can force quit the app with Ctrl+C if needed",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                logger.warning("=" * 80)
                logger.warning("🛑 USER CONFIRMED CANCEL VIA DIALOG CLOSE")
                logger.warning("=" * 80)

                # Set cancel flag (non-blocking)
                self.translation_thread.cancel()

                # Disconnect signals to prevent errors after dialog closes
                try:
                    self.translation_thread.status.disconnect()
                    self.translation_thread.progress.disconnect()
                    self.translation_thread.finished.disconnect()
                    self.translation_thread.error.disconnect()
                    logger.info("✓ Signals disconnected successfully")
                except Exception as e:
                    logger.warning(f"Error disconnecting signals: {e}")

                # Don't wait for thread - let it finish in background
                logger.warning("⏳ Waiting for current API calls to complete (cannot interrupt blocking API calls)")
                logger.warning("   Workers will stop after current API responses are received")
                logger.warning("   This may take 10-30 seconds depending on API response time")
                return True
            else:
                logger.info("User chose not to cancel - keeping dialog open")
                return False
        else:
            logger.info("No active translation thread - closing dialog normally")
            return True

    def reject(self):
        """Override reject to check for running translation."""
        if self._check_and_cancel_translation():
            super().reject()

    def closeEvent(self, event):
        """Handle dialog close event - cancel translation if running."""
        if self._check_and_cancel_translation():
            event.accept()
        else:
            event.ignore()
