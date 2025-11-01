"""
Settings Dialog Module

Dialog for configuring application settings including Gemini API key and translation workflow.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QGroupBox
)
from PyQt6.QtCore import Qt
from pathlib import Path
import json


class SettingsDialog(QDialog):
    """Dialog for application settings."""

    def __init__(self, parent=None):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.settings_file = Path.home() / ".nms_translator_settings.json"
        self.settings = self._load_settings()

        self._init_ui()
        self._load_values()

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Gemini API Settings
        api_group = QGroupBox("Google Gemini API")
        api_layout = QFormLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your Gemini API key")
        api_layout.addRow("API Key:", self.api_key_input)

        api_help = QLabel(
            '<a href="https://aistudio.google.com/app/apikey">Get your API key</a>'
        )
        api_help.setOpenExternalLinks(True)
        api_layout.addRow("", api_help)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # Translation Workflow Settings
        workflow_group = QGroupBox("Translation Workflow")
        workflow_layout = QFormLayout()

        self.workflow_combo = QComboBox()
        self.workflow_combo.addItems(["sequence", "full_parallel"])
        self.workflow_combo.setToolTip(
            "sequence: Translate one by one (safer, slower)\n"
            "full_parallel: Translate all at once (faster, uses more quota)"
        )
        workflow_layout.addRow("Workflow Type:", self.workflow_combo)

        workflow_group.setLayout(workflow_layout)
        layout.addWidget(workflow_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_settings(self) -> dict:
        """Load settings from file using TranslationConfig."""
        from translation import TranslationConfig
        config = TranslationConfig.load_from_settings(self.settings_file)
        return {
            "gemini_api_key": config.api_key,
            "workflow_type": config.workflow_type.value
        }

    def _load_values(self):
        """Load saved values into UI."""
        self.api_key_input.setText(self.settings.get("gemini_api_key", ""))

        workflow = self.settings.get("workflow_type", "sequence")
        index = self.workflow_combo.findText(workflow)
        if index >= 0:
            self.workflow_combo.setCurrentIndex(index)

    def _save_and_close(self):
        """Save settings and close dialog using TranslationConfig."""
        from translation import TranslationConfig, WorkflowType

        # Update local settings dict for backward compatibility
        self.settings = {
            "gemini_api_key": self.api_key_input.text().strip(),
            "workflow_type": self.workflow_combo.currentText()
        }

        try:
            # Create and save config
            wf_type = WorkflowType.SEQUENCE if self.workflow_combo.currentText() == "sequence" else WorkflowType.FULL_PARALLEL
            config = TranslationConfig(
                api_key=self.api_key_input.text().strip(),
                workflow_type=wf_type,
                token_limit=50000,
                max_retries=3
            )
            config.save_to_settings(self.settings_file)

            self.accept()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings:\n{e}"
            )

    def get_settings(self) -> dict:
        """Get current settings."""
        return self.settings
