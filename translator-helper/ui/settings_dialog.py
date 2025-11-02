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

        # Token limit
        self.token_limit_input = QLineEdit()
        self.token_limit_input.setPlaceholderText("50000")
        self.token_limit_input.setToolTip(
            "Maximum tokens per patch (default: 50000)\n"
            "Smaller values = more patches, more API calls\n"
            "Larger values = fewer patches, faster translation"
        )
        workflow_layout.addRow("Token Limit:", self.token_limit_input)

        # Max retries
        self.max_retries_input = QLineEdit()
        self.max_retries_input.setPlaceholderText("3")
        self.max_retries_input.setToolTip(
            "Maximum retry attempts for failed patches (default: 3)"
        )
        workflow_layout.addRow("Max Retries:", self.max_retries_input)

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
            "workflow_type": config.workflow_type.value,
            "token_limit": config.token_limit,
            "max_retries": config.max_retries
        }

    def _load_values(self):
        """Load saved values into UI."""
        self.api_key_input.setText(self.settings.get("gemini_api_key", ""))

        workflow = self.settings.get("workflow_type", "sequence")
        index = self.workflow_combo.findText(workflow)
        if index >= 0:
            self.workflow_combo.setCurrentIndex(index)

        # Load token limit and max retries
        self.token_limit_input.setText(str(self.settings.get("token_limit", 50000)))
        self.max_retries_input.setText(str(self.settings.get("max_retries", 3)))

    def _save_and_close(self):
        """Save settings and close dialog using TranslationConfig."""
        from translation import TranslationConfig, WorkflowType
        from PyQt6.QtWidgets import QMessageBox

        try:
            # Parse and validate token_limit
            token_limit_text = self.token_limit_input.text().strip()
            token_limit = int(token_limit_text) if token_limit_text else 50000
            if token_limit < 1000:
                QMessageBox.warning(
                    self,
                    "Invalid Token Limit",
                    "Token limit must be at least 1000"
                )
                return
            if token_limit > 100000:
                QMessageBox.warning(
                    self,
                    "Invalid Token Limit",
                    "Token limit should not exceed 100000 (Gemini output limit is ~65k tokens)"
                )
                return

            # Parse and validate max_retries
            max_retries_text = self.max_retries_input.text().strip()
            max_retries = int(max_retries_text) if max_retries_text else 3
            if max_retries < 0:
                QMessageBox.warning(
                    self,
                    "Invalid Max Retries",
                    "Max retries must be at least 0"
                )
                return
            if max_retries > 10:
                QMessageBox.warning(
                    self,
                    "Invalid Max Retries",
                    "Max retries should not exceed 10"
                )
                return

            # Update local settings dict for backward compatibility
            self.settings = {
                "gemini_api_key": self.api_key_input.text().strip(),
                "workflow_type": self.workflow_combo.currentText(),
                "token_limit": token_limit,
                "max_retries": max_retries
            }

            # Create and save config
            wf_type = WorkflowType.SEQUENCE if self.workflow_combo.currentText() == "sequence" else WorkflowType.FULL_PARALLEL
            config = TranslationConfig(
                api_key=self.api_key_input.text().strip(),
                workflow_type=wf_type,
                token_limit=token_limit,
                max_retries=max_retries
            )
            config.save_to_settings(self.settings_file)

            self.accept()
        except ValueError as e:
            QMessageBox.warning(
                self,
                "Invalid Input",
                f"Please enter valid numbers for Token Limit and Max Retries:\n{e}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings:\n{e}"
            )

    def get_settings(self) -> dict:
        """Get current settings."""
        return self.settings
