"""
Translation engine using Gemini API with LangGraph-inspired architecture.
Adapted for PyQt6 threading with progress signals.
"""
import json
import time
import re
from typing import Dict, List, Optional
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from google.api_core.exceptions import ResourceExhausted

from .config import TranslationConfig, WorkflowType
from .prompts import SYSTEM_PROMPT, get_translation_prompt
from .utils import (
    split_into_patches,
    merge_patches,
    validate_translation,
    calculate_progress
)


class TranslationEngine(QThread):
    """
    Translation engine that runs in background thread with PyQt6 signals.

    Signals:
        progress_updated: Emits (current, total, message)
        patch_started: Emits (patch_index, total_patches)
        patch_completed: Emits (patch_index, success, error_msg)
        translation_completed: Emits (success, translated_data, error_msg)
    """

    progress_updated = pyqtSignal(int, int, str)
    patch_started = pyqtSignal(int, int)
    patch_completed = pyqtSignal(int, bool, str)
    translation_completed = pyqtSignal(bool, dict, str)

    def __init__(self,
                 data_to_translate: Dict[str, str],
                 config: TranslationConfig,
                 parent=None):
        """
        Initialize translation engine.

        Args:
            data_to_translate: Dictionary of entries to translate
            config: Translation configuration
            parent: Parent QObject
        """
        super().__init__(parent)
        self.data_to_translate = data_to_translate
        self.config = config
        self._should_stop = False

    def stop(self):
        """Request translation to stop."""
        self._should_stop = True

    def run(self):
        """Main translation loop (runs in thread)."""
        try:
            # Initialize Gemini API
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.1,
                google_api_key=self.config.api_key
            )

            # Split into patches
            self.progress_updated.emit(0, 100, "Splitting data into patches...")
            patches = split_into_patches(self.data_to_translate, self.config.token_limit)
            total_patches = len(patches)

            self.progress_updated.emit(0, total_patches, f"Split into {total_patches} patches")

            # Translate based on workflow type
            if self.config.workflow_type == WorkflowType.SEQUENCE:
                translated_data = self._run_sequential(llm, patches)
            else:
                # For now, parallel workflow uses same sequential approach
                # TODO: Implement true parallel processing
                translated_data = self._run_sequential(llm, patches)

            # Emit completion
            if self._should_stop:
                self.translation_completed.emit(False, {}, "Translation cancelled by user")
            else:
                self.translation_completed.emit(True, translated_data, "")

        except Exception as e:
            error_msg = f"Translation error: {str(e)}"
            self.translation_completed.emit(False, {}, error_msg)

    def _run_sequential(self, llm: ChatGoogleGenerativeAI, patches: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Run sequential translation workflow.

        Args:
            llm: Gemini API instance
            patches: List of patches to translate

        Returns:
            Merged translated dictionary
        """
        total_patches = len(patches)
        translated_patches = []

        for patch_idx, patch in enumerate(patches):
            if self._should_stop:
                break

            patch_num = patch_idx + 1
            self.patch_started.emit(patch_num, total_patches)
            self.progress_updated.emit(
                patch_num,
                total_patches,
                f"Translating patch {patch_num}/{total_patches}..."
            )

            # Translate patch with retry
            success, translated_patch, error_msg = self._translate_patch_with_retry(
                llm, patch, patch_idx, self.config.max_retries
            )

            if success:
                translated_patches.append(translated_patch)
                self.patch_completed.emit(patch_num, True, "")
            else:
                self.patch_completed.emit(patch_num, False, error_msg)
                # Continue with other patches even if one fails

        # Merge results
        self.progress_updated.emit(total_patches, total_patches, "Merging results...")
        return merge_patches(translated_patches)

    def _translate_patch_with_retry(self,
                                    llm: ChatGoogleGenerativeAI,
                                    patch: Dict[str, str],
                                    patch_idx: int,
                                    max_retries: int) -> tuple[bool, Optional[Dict[str, str]], str]:
        """
        Translate a single patch with retry logic.

        Args:
            llm: Gemini API instance
            patch: Patch to translate
            patch_idx: Patch index (for logging)
            max_retries: Maximum number of retries

        Returns:
            Tuple (success, translated_patch, error_msg)
        """
        patch_info = f" [Patch {patch_idx + 1}]"

        for retry in range(max_retries + 1):
            if self._should_stop:
                return False, None, "Cancelled"

            try:
                # Call Gemini API with quota handling
                response_text = self._call_gemini_with_quota_handling(
                    llm, patch, patch_info, max_quota_retries=3
                )

                # Parse JSON response
                translated_patch = self._parse_translation_response(response_text)

                # Validate translation
                is_valid, missing_keys = validate_translation(patch, translated_patch)

                if is_valid:
                    return True, translated_patch, ""
                else:
                    error_msg = f"Validation failed: missing keys {missing_keys}"
                    if retry < max_retries:
                        self.progress_updated.emit(
                            patch_idx + 1,
                            len(self.data_to_translate),
                            f"{patch_info} {error_msg}, retrying ({retry + 1}/{max_retries})..."
                        )
                        time.sleep(2)
                    else:
                        return False, None, error_msg

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                if retry < max_retries:
                    self.progress_updated.emit(
                        patch_idx + 1,
                        len(self.data_to_translate),
                        f"{patch_info} {error_msg}, retrying ({retry + 1}/{max_retries})..."
                    )
                    time.sleep(2)
                else:
                    return False, None, error_msg

        return False, None, "Max retries exceeded"

    def _call_gemini_with_quota_handling(self,
                                         llm: ChatGoogleGenerativeAI,
                                         patch: Dict[str, str],
                                         patch_info: str,
                                         max_quota_retries: int = 3) -> str:
        """
        Call Gemini API with smart quota retry logic.

        Args:
            llm: Gemini API instance
            patch: Patch to translate
            patch_info: Patch info for logging
            max_quota_retries: Maximum quota retries

        Returns:
            Response text from API

        Raises:
            Exception if max retries exceeded or other error
        """
        quota_retry_count = 0

        # Prepare messages
        system_msg = SystemMessage(content=SYSTEM_PROMPT)
        human_msg = HumanMessage(content=get_translation_prompt(patch))
        messages = [system_msg, human_msg]

        while quota_retry_count <= max_quota_retries:
            if self._should_stop:
                raise Exception("Translation cancelled")

            try:
                response = llm.invoke(messages)
                return response.content.strip()

            except ResourceExhausted as e:
                error_msg = str(e)
                retry_delay = self._extract_retry_delay(error_msg)

                if quota_retry_count >= max_quota_retries:
                    raise Exception(f"Quota exceeded after {max_quota_retries} retries")

                # Wait with progress update
                quota_retry_count += 1
                self._wait_with_progress(retry_delay, patch_info, quota_retry_count, max_quota_retries)

            except Exception as e:
                raise

        raise Exception(f"Failed after {max_quota_retries} quota retries")

    def _extract_retry_delay(self, error_msg: str) -> int:
        """
        Extract retry delay from API error message.

        Args:
            error_msg: Error message from API

        Returns:
            Retry delay in seconds (default: 60)
        """
        # Try to extract "Retry after 2025-01-02T12:34:56Z"
        match = re.search(r'Retry after (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', error_msg)
        if match:
            retry_time_str = match.group(1)
            try:
                retry_time = datetime.fromisoformat(retry_time_str.replace('Z', '+00:00'))
                now = datetime.now(retry_time.tzinfo)
                delay = int((retry_time - now).total_seconds())
                return max(delay, 1)  # At least 1 second
            except:
                pass

        # Default to 60 seconds
        return 60

    def _wait_with_progress(self, delay: int, patch_info: str, retry_num: int, max_retries: int):
        """
        Wait with progress updates during quota retry.

        Args:
            delay: Delay in seconds
            patch_info: Patch info for message
            retry_num: Current retry number
            max_retries: Maximum retries
        """
        for remaining in range(delay, 0, -1):
            if self._should_stop:
                return
            self.progress_updated.emit(
                0, delay,
                f"{patch_info} Quota exceeded, waiting {remaining}s (retry {retry_num}/{max_retries})..."
            )
            time.sleep(1)

    def _parse_translation_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse translation response from Gemini API.

        Args:
            response_text: Raw response text

        Returns:
            Parsed JSON dictionary

        Raises:
            Exception if parsing fails
        """
        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # Try to extract JSON from response
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            raise Exception(f"Failed to parse JSON response: {str(e)}")
