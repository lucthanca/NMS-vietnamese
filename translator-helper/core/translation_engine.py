"""
Translation Engine Module

Handles translation using Google Gemini API with LangChain support for sequential and parallel workflows.
"""

import logging
from typing import Dict, List
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot

from translation import TranslationConfig, TranslationEngine, WorkflowType

logger = logging.getLogger(__name__)


class TranslationThread(QThread):
    """
    Background thread for translation operations.
    Wraps the new TranslationEngine to maintain backward compatibility.
    """

    # Signals
    status = pyqtSignal(str)  # Status message
    progress = pyqtSignal(int, int)  # current, total
    patch_completed = pyqtSignal(dict)  # Translated patch
    finished = pyqtSignal(dict)  # All translations
    error = pyqtSignal(str)  # Error message

    def __init__(self, entries_dict: Dict[str, str], api_key: str, workflow_type: str = "sequence"):
        """
        Initialize translation thread.

        Args:
            entries_dict: Dictionary of {key: english_text} to translate
            api_key: Gemini API key
            workflow_type: "sequence" or "full_parallel"
        """
        super().__init__()
        self.entries_dict = entries_dict
        self.api_key = api_key
        self.workflow_type = workflow_type
        self.translation_engine = None
        self._cancel_flag = {'cancelled': False}

    def run(self):
        """Execute translation using translate_data_direct (no QThread nesting)."""
        try:
            # Import here to avoid circular imports
            from translation import WorkflowType, TranslationConfig, translate_data_direct
            from pathlib import Path

            # Load config from settings file to get token_limit and max_retries
            settings_file = Path.home() / ".nms_translator_settings.json"
            saved_config = TranslationConfig.load_from_settings(settings_file)

            # Create translation config with saved values
            wf_type = WorkflowType.SEQUENCE if self.workflow_type == "sequence" else WorkflowType.FULL_PARALLEL
            config = TranslationConfig(
                api_key=self.api_key,
                workflow_type=wf_type,
                token_limit=saved_config.token_limit,
                max_retries=saved_config.max_retries
            )

            logger.info(f"Starting translation with workflow: {self.workflow_type}")
            logger.info(f"Total entries: {len(self.entries_dict)}")
            logger.info(f"Token limit: {config.token_limit}")
            logger.info(f"Max retries: {config.max_retries}")

            # Run translation directly with callbacks
            translated_data = translate_data_direct(
                self.entries_dict,
                config,
                progress_callback=self._on_progress,
                patch_callback=self._on_patch_completed,
                cancel_flag=self._cancel_flag
            )

            # Check if cancelled
            if self._cancel_flag['cancelled']:
                logger.warning("=" * 80)
                logger.warning("🛑 Translation completed with cancellation - not emitting results")
                logger.warning(f"  Partial translations: {len(translated_data)} entries")
                logger.warning("=" * 80)
                return

            # Emit completion
            logger.info("=" * 80)
            logger.info("✅ TRANSLATION COMPLETED SUCCESSFULLY")
            logger.info(f"  Total translated entries: {len(translated_data)}")
            logger.info("=" * 80)
            self.patch_completed.emit(translated_data)
            self.finished.emit(translated_data)

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            self.error.emit(str(e))

    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress updates."""
        self.progress.emit(current, total)
        self.status.emit(message)

    def _on_patch_completed(self, patch_num: int, success: bool, error_msg: str):
        """Handle patch completion."""
        if success:
            self.status.emit(f"Patch {patch_num} completed")
        else:
            self.status.emit(f"Patch {patch_num} failed: {error_msg}")

    def cancel(self):
        """Cancel the translation operation."""
        logger.warning("=" * 80)
        logger.warning("🛑 CANCEL REQUESTED - Setting cancellation flag")
        logger.warning("  Workers will check flag before next API call")
        logger.warning("=" * 80)
        self._cancel_flag['cancelled'] = True


