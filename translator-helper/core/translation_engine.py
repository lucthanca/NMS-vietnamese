"""
Translation Engine Module

Handles translation using Google Gemini API with LangChain support for sequential and parallel workflows.
"""

from typing import Dict, List
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot

from translation import TranslationConfig, TranslationEngine, WorkflowType


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

    def run(self):
        """Execute translation directly without nested thread."""
        try:
            # Import here to avoid circular imports
            from translation import WorkflowType, TranslationConfig

            # Create translation config
            wf_type = WorkflowType.SEQUENCE if self.workflow_type == "sequence" else WorkflowType.FULL_PARALLEL
            config = TranslationConfig(
                api_key=self.api_key,
                workflow_type=wf_type,
                token_limit=50000,
                max_retries=3
            )

            # Create engine core (NOT a QThread)
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.1,
                google_api_key=config.api_key
            )

            # Split into patches
            from translation.utils import split_into_patches, merge_patches, validate_translation
            self.status.emit("Splitting data into patches...")
            patches = split_into_patches(self.entries_dict, config.token_limit)
            total_patches = len(patches)
            self.status.emit(f"Split into {total_patches} patches")

            # Translate patches
            translated_patches = []
            for patch_idx, patch in enumerate(patches):
                patch_num = patch_idx + 1
                self.progress.emit(patch_num, total_patches)
                self.status.emit(f"Translating patch {patch_num}/{total_patches}...")

                # Translate patch with retry
                success, translated_patch = self._translate_patch(llm, patch, config.max_retries)

                if success:
                    translated_patches.append(translated_patch)
                    self.status.emit(f"Patch {patch_num} completed")

            # Merge results
            self.status.emit("Merging results...")
            all_translations = merge_patches(translated_patches)

            # Emit completion
            self.patch_completed.emit(all_translations)
            self.finished.emit(all_translations)

        except Exception as e:
            self.error.emit(str(e))

    def _translate_patch(self, llm, patch: Dict[str, str], max_retries: int) -> tuple:
        """Translate a single patch with retry logic."""
        from translation.prompts import SYSTEM_PROMPT, get_translation_prompt
        from translation.utils import validate_translation
        from langchain_core.messages import HumanMessage, SystemMessage
        import json
        import re
        import time

        for retry in range(max_retries + 1):
            try:
                # Call Gemini API
                system_msg = SystemMessage(content=SYSTEM_PROMPT)
                human_msg = HumanMessage(content=get_translation_prompt(patch))
                messages = [system_msg, human_msg]

                response = llm.invoke(messages)
                response_text = response.content.strip()

                # Parse JSON response
                if response_text.startswith("```"):
                    lines = response_text.split("\n")
                    lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    response_text = "\n".join(lines)

                translated_patch = json.loads(response_text)

                # Validate translation
                is_valid, missing_keys = validate_translation(patch, translated_patch)
                if is_valid:
                    return True, translated_patch
                else:
                    if retry < max_retries:
                        self.status.emit(f"Validation failed, retrying ({retry + 1}/{max_retries})...")
                        time.sleep(2)
                    else:
                        return False, None

            except Exception as e:
                if retry < max_retries:
                    self.status.emit(f"Error: {str(e)}, retrying ({retry + 1}/{max_retries})...")
                    time.sleep(2)
                else:
                    raise

        return False, None


