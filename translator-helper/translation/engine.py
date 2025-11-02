"""
Translation engine using Gemini API with LangGraph-inspired architecture.
Adapted for PyQt6 threading with progress signals.
"""
import json
import time
import re
import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# Configure verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
        self._signal_lock = threading.Lock()  # Thread-safe signal emission

    def stop(self):
        """Request translation to stop."""
        self._should_stop = True

    def _emit_progress(self, current: int, total: int, message: str):
        """Thread-safe progress emission."""
        with self._signal_lock:
            self.progress_updated.emit(current, total, message)

    def _emit_patch_started(self, patch_num: int, total: int):
        """Thread-safe patch started emission."""
        with self._signal_lock:
            self.patch_started.emit(patch_num, total)

    def _emit_patch_completed(self, patch_num: int, success: bool, error_msg: str):
        """Thread-safe patch completed emission."""
        with self._signal_lock:
            self.patch_completed.emit(patch_num, success, error_msg)

    def run(self):
        """Main translation loop (runs in thread)."""
        try:
            logger.info("=" * 80)
            logger.info("TRANSLATION ENGINE STARTED")
            logger.info("=" * 80)

            # Initialize Gemini API
            logger.info(f"Initializing Gemini API...")
            logger.info(f"  Model: gemini-2.5-flash")
            logger.info(f"  Temperature: 0.1")
            logger.info(f"  API Key: {self.config.api_key[:10]}...{self.config.api_key[-4:] if len(self.config.api_key) > 14 else '****'}")
            logger.info(f"  Workflow Type: {self.config.workflow_type.value}")
            logger.info(f"  Token Limit: {self.config.token_limit}")
            logger.info(f"  Max Retries: {self.config.max_retries}")

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.1,
                google_api_key=self.config.api_key
            )
            logger.info("✓ Gemini API initialized successfully")

            # Split into patches
            logger.info("-" * 80)
            logger.info("SPLITTING DATA INTO PATCHES")
            logger.info(f"  Total entries to translate: {len(self.data_to_translate)}")
            logger.info(f"  Token limit per patch: {self.config.token_limit}")

            self.progress_updated.emit(0, 100, "Splitting data into patches...")
            patches = split_into_patches(self.data_to_translate, self.config.token_limit)
            total_patches = len(patches)

            logger.info(f"✓ Split into {total_patches} patches")
            for idx, patch in enumerate(patches, 1):
                logger.info(f"  Patch {idx}: {len(patch)} entries")

            self.progress_updated.emit(0, total_patches, f"Split into {total_patches} patches")

            # Translate based on workflow type
            if self.config.workflow_type == WorkflowType.SEQUENCE:
                logger.info("🔄 Using SEQUENTIAL workflow (one patch at a time)")
                translated_data = self._run_sequential(llm, patches)
            else:
                logger.info("⚡ Using PARALLEL workflow (max 3 patches concurrently)")
                translated_data = self._run_parallel(llm, patches)

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
                f"• Starting patch {patch_num}/{total_patches} ({len(patch)} entries)..."
            )

            # Translate patch with retry
            success, translated_patch, error_msg = self._translate_patch_with_retry(
                llm, patch, patch_idx, self.config.max_retries
            )

            if success:
                translated_patches.append(translated_patch)
                self.patch_completed.emit(patch_num, True, "")
                self.progress_updated.emit(
                    patch_num,
                    total_patches,
                    f"✓ Patch {patch_num}/{total_patches} completed ({len(translated_patch)} entries)"
                )
            else:
                self.patch_completed.emit(patch_num, False, error_msg)
                self.progress_updated.emit(
                    patch_num,
                    total_patches,
                    f"✗ Patch {patch_num}/{total_patches} failed: {error_msg[:50]}..."
                )
                # Continue with other patches even if one fails

        # Merge results
        self.progress_updated.emit(total_patches, total_patches, f"Merging {len(translated_patches)} patches...")
        return merge_patches(translated_patches)

    def _run_parallel(self, llm: ChatGoogleGenerativeAI, patches: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Run parallel translation workflow with rolling execution (max 3 workers).
        When a worker finishes, it immediately picks up the next patch from queue.

        Args:
            llm: Gemini API instance
            patches: List of patches to translate

        Returns:
            Merged translated dictionary
        """
        logger.info("=" * 80)
        logger.info("STARTING PARALLEL WORKFLOW (Max 3 concurrent patches)")
        logger.info(f"  Total patches: {len(patches)}")
        logger.info(f"  Max workers: 3")
        logger.info("=" * 80)

        total_patches = len(patches)
        translated_patches = [None] * total_patches  # Preserve order
        completed_count = 0
        max_workers = min(3, total_patches)  # Max 3 workers or fewer if less patches

        self._emit_progress(
            0,
            total_patches,
            f"Starting parallel translation (max {max_workers} concurrent)..."
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all patches with their indices
            future_to_patch = {
                executor.submit(
                    self._translate_patch_with_retry,
                    llm,
                    patch,
                    patch_idx,
                    self.config.max_retries
                ): (patch_idx, patch)
                for patch_idx, patch in enumerate(patches)
            }

            logger.info(f"✓ Submitted {len(future_to_patch)} patches to executor")
            logger.info(f"  Active workers: {max_workers}")

            # Process results as they complete (rolling parallel)
            for future in as_completed(future_to_patch):
                if self._should_stop:
                    logger.warning("Translation cancelled by user, stopping all workers...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                patch_idx, patch = future_to_patch[future]
                patch_num = patch_idx + 1

                try:
                    success, translated_patch, error_msg = future.result()

                    if success:
                        translated_patches[patch_idx] = translated_patch
                        completed_count += 1
                        self._emit_patch_completed(patch_num, True, "")
                        logger.info(f"✓ Patch {patch_num}/{total_patches} completed successfully")
                        logger.debug(f"  Translated entries: {len(translated_patch)}")

                        # Show detailed completion message
                        self._emit_progress(
                            completed_count,
                            total_patches,
                            f"✓ Patch {patch_num} completed ({len(translated_patch)} entries) - {completed_count}/{total_patches} done"
                        )
                    else:
                        self._emit_patch_completed(patch_num, False, error_msg)
                        logger.error(f"✗ Patch {patch_num}/{total_patches} failed: {error_msg}")
                        # Continue with other patches even if one fails

                        self._emit_progress(
                            completed_count,
                            total_patches,
                            f"✗ Patch {patch_num} failed: {error_msg[:50]}... - {completed_count}/{total_patches} done"
                        )

                except Exception as e:
                    error_msg = f"Unexpected error processing patch {patch_num}: {str(e)}"
                    logger.error(error_msg)
                    self._emit_patch_completed(patch_num, False, error_msg)

        logger.info("=" * 80)
        logger.info(f"PARALLEL WORKFLOW COMPLETED")
        logger.info(f"  Successfully translated: {completed_count}/{total_patches} patches")
        logger.info("=" * 80)

        # Merge results (filter out None for failed patches)
        self._emit_progress(total_patches, total_patches, "Merging results...")
        valid_patches = [p for p in translated_patches if p is not None]
        return merge_patches(valid_patches)

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
                # Show retry attempt info
                if retry > 0:
                    self.progress_updated.emit(
                        patch_idx + 1,
                        len(self.data_to_translate),
                        f"• Patch {patch_idx + 1}: Retrying (attempt {retry + 1}/{max_retries + 1})..."
                    )

                # Show API call start
                self.progress_updated.emit(
                    patch_idx + 1,
                    len(self.data_to_translate),
                    f"• Patch {patch_idx + 1}: Calling Gemini API ({len(patch)} entries)..."
                )

                # Call Gemini API with quota handling
                start_time = time.time()
                response_text = self._call_gemini_with_quota_handling(
                    llm, patch, patch_info, max_quota_retries=3
                )
                elapsed = time.time() - start_time

                # Show API response received
                self.progress_updated.emit(
                    patch_idx + 1,
                    len(self.data_to_translate),
                    f"• Patch {patch_idx + 1}: API response received ({elapsed:.1f}s, {len(response_text)} chars)"
                )

                # Parse JSON response
                translated_patch = self._parse_translation_response(response_text)

                # Show parsing success
                self.progress_updated.emit(
                    patch_idx + 1,
                    len(self.data_to_translate),
                    f"• Patch {patch_idx + 1}: Parsed {len(translated_patch)} translations"
                )

                # Validate translation
                is_valid, missing_keys = validate_translation(patch, translated_patch)

                if is_valid:
                    self.progress_updated.emit(
                        patch_idx + 1,
                        len(self.data_to_translate),
                        f"• Patch {patch_idx + 1}: ✓ Validation passed"
                    )
                    return True, translated_patch, ""
                else:
                    error_msg = f"missing keys: {missing_keys[:3]}{'...' if len(missing_keys) > 3 else ''}"
                    if retry < max_retries:
                        self.progress_updated.emit(
                            patch_idx + 1,
                            len(self.data_to_translate),
                            f"• Patch {patch_idx + 1}: ⚠ Validation failed ({error_msg}), retrying..."
                        )
                        time.sleep(2)
                    else:
                        return False, None, f"Validation failed: {error_msg}"

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                if retry < max_retries:
                    self.progress_updated.emit(
                        patch_idx + 1,
                        len(self.data_to_translate),
                        f"• Patch {patch_idx + 1}: ✗ Error ({error_msg}), retrying..."
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

        logger.info(f"{patch_info} Preparing API call...")
        logger.debug(f"{patch_info} System prompt length: {len(SYSTEM_PROMPT)} chars")
        logger.debug(f"{patch_info} Human prompt length: {len(human_msg.content)} chars")
        logger.debug(f"{patch_info} Patch keys: {list(patch.keys())[:5]}{'...' if len(patch) > 5 else ''}")

        while quota_retry_count <= max_quota_retries:
            if self._should_stop:
                raise Exception("Translation cancelled")

            try:
                logger.info(f"{patch_info} Calling Gemini API (attempt {quota_retry_count + 1}/{max_quota_retries + 1})...")
                start_time = time.time()

                response = llm.invoke(messages)

                elapsed = time.time() - start_time
                logger.info(f"{patch_info} ✓ API call successful ({elapsed:.2f}s)")
                logger.debug(f"{patch_info} Response length: {len(response.content)} chars")
                logger.debug(f"{patch_info} Response preview: {response.content[:200]}...")

                return response.content.strip()

            except ResourceExhausted as e:
                error_msg = str(e)
                retry_delay = self._extract_retry_delay(error_msg)

                logger.warning(f"{patch_info} ⚠️ ResourceExhausted error")
                logger.warning(f"{patch_info} Error message: {error_msg}")
                logger.warning(f"{patch_info} Retry delay: {retry_delay}s")
                logger.warning(f"{patch_info} Quota retry count: {quota_retry_count + 1}/{max_quota_retries + 1}")

                if quota_retry_count >= max_quota_retries:
                    logger.error(f"{patch_info} ✗ Max quota retries exceeded")
                    raise Exception(f"Quota exceeded after {max_quota_retries} retries")

                # Wait with progress update
                quota_retry_count += 1
                self._wait_with_progress(retry_delay, patch_info, quota_retry_count, max_quota_retries)

            except Exception as e:
                logger.error(f"{patch_info} ✗ API call failed: {type(e).__name__}: {str(e)}")
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
                f"• {patch_info}: ⏳ API quota exceeded, waiting {remaining}s before retry {retry_num}/{max_retries}..."
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
        logger.debug("Parsing translation response...")
        logger.debug(f"Raw response length: {len(response_text)} chars")

        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```"):
            logger.debug("Response contains markdown code blocks, removing...")
            lines = response_text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)
            logger.debug(f"Cleaned response length: {len(response_text)} chars")

        # Try to parse JSON
        try:
            result = json.loads(response_text)
            logger.info(f"✓ Successfully parsed JSON: {len(result)} entries")
            logger.debug(f"Parsed keys sample: {list(result.keys())[:5]}{'...' if len(result) > 5 else ''}")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON directly: {str(e)}")
            logger.debug(f"Response preview: {response_text[:500]}...")

            # Try to extract JSON from response
            logger.debug("Attempting to extract JSON using regex...")
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(0))
                    logger.info(f"✓ Successfully extracted and parsed JSON: {len(result)} entries")
                    return result
                except Exception as ex:
                    logger.error(f"Failed to parse extracted JSON: {str(ex)}")

            logger.error("✗ All parsing attempts failed")
            raise Exception(f"Failed to parse JSON response: {str(e)}")


def translate_data_direct(
    data_to_translate: Dict[str, str],
    config: TranslationConfig,
    progress_callback=None,
    patch_callback=None,
    cancel_flag=None
) -> Dict[str, str]:
    """
    Standalone translation function without QThread dependency.
    Can be called directly from any thread.

    Args:
        data_to_translate: Dictionary to translate
        config: Translation configuration
        progress_callback: Optional callback(current, total, message)
        patch_callback: Optional callback(patch_num, success, error_msg)
        cancel_flag: Optional dict with 'cancelled' key to check for cancellation

    Returns:
        Translated dictionary
    """
    logger.info("=" * 80)
    logger.info("STARTING DIRECT TRANSLATION (No QThread)")
    logger.info(f"  Model: gemini-2.5-flash")
    logger.info(f"  Temperature: 0.1")
    logger.info(f"  Workflow Type: {config.workflow_type.value}")
    logger.info(f"  Token Limit: {config.token_limit}")
    logger.info(f"  Max Retries: {config.max_retries}")

    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        google_api_key=config.api_key
    )
    logger.info("✓ Gemini API initialized successfully")

    # Split into patches
    logger.info("-" * 80)
    logger.info("SPLITTING DATA INTO PATCHES")
    logger.info(f"  Total entries to translate: {len(data_to_translate)}")
    logger.info(f"  Token limit per patch: {config.token_limit}")

    if progress_callback:
        progress_callback(0, 100, "Splitting data into patches...")

    patches = split_into_patches(data_to_translate, config.token_limit)
    total_patches = len(patches)

    logger.info(f"✓ Split into {total_patches} patches")
    for idx, patch in enumerate(patches, 1):
        logger.info(f"  Patch {idx}: {len(patch)} entries")

    if progress_callback:
        progress_callback(0, total_patches, f"Split into {total_patches} patches")

    # Translate based on workflow type
    if config.workflow_type == WorkflowType.SEQUENCE:
        logger.info("🔄 Using SEQUENTIAL workflow (one patch at a time)")
        translated_data = _run_sequential_direct(llm, patches, config, progress_callback, patch_callback, cancel_flag)
    else:
        logger.info("⚡ Using PARALLEL workflow (max 3 patches concurrently)")
        translated_data = _run_parallel_direct(llm, patches, config, progress_callback, patch_callback, cancel_flag)

    return translated_data


def _run_sequential_direct(
    llm: ChatGoogleGenerativeAI,
    patches: List[Dict[str, str]],
    config: TranslationConfig,
    progress_callback=None,
    patch_callback=None,
    cancel_flag=None
) -> Dict[str, str]:
    """Sequential workflow for direct translation."""
    total_patches = len(patches)
    translated_patches = []

    for patch_idx, patch in enumerate(patches):
        # Check cancellation
        if cancel_flag and cancel_flag.get('cancelled', False):
            logger.warning("=" * 80)
            logger.warning("🛑 TRANSLATION CANCELLED BY USER (Sequential)")
            logger.warning(f"  Completed patches: {len(translated_patches)}/{total_patches}")
            logger.warning(f"  Remaining patches: {total_patches - len(translated_patches)}")
            logger.warning("=" * 80)
            if progress_callback:
                progress_callback(len(translated_patches), total_patches, "Translation cancelled")
            break

        patch_num = patch_idx + 1

        if progress_callback:
            progress_callback(patch_num, total_patches, f"Translating patch {patch_num}/{total_patches}...")

        # Translate patch with retry
        success, translated_patch, error_msg = _translate_patch_with_retry_direct(
            llm, patch, patch_idx, config.max_retries, cancel_flag
        )

        if success:
            translated_patches.append(translated_patch)
            if patch_callback:
                patch_callback(patch_num, True, "")
        else:
            if patch_callback:
                patch_callback(patch_num, False, error_msg)

    # Check if workflow was cancelled
    was_cancelled = cancel_flag and cancel_flag.get('cancelled', False)
    completed = len(translated_patches)

    if was_cancelled:
        logger.warning("=" * 80)
        logger.warning(f"SEQUENTIAL WORKFLOW STOPPED (CANCELLED)")
        logger.warning(f"  Successfully translated: {completed}/{total_patches} patches")
        logger.warning(f"  Remaining: {total_patches - completed} patches not processed")
        logger.warning("=" * 80)

    # Merge results
    if progress_callback:
        if was_cancelled:
            progress_callback(completed, total_patches, f"Cancelled - {completed} patches completed")
        else:
            progress_callback(total_patches, total_patches, "Merging results...")
    return merge_patches(translated_patches)


def _run_parallel_direct(
    llm: ChatGoogleGenerativeAI,
    patches: List[Dict[str, str]],
    config: TranslationConfig,
    progress_callback=None,
    patch_callback=None,
    cancel_flag=None
) -> Dict[str, str]:
    """Parallel workflow for direct translation with rolling execution."""
    logger.info("=" * 80)
    logger.info("STARTING PARALLEL WORKFLOW (Max 3 concurrent patches)")
    logger.info(f"  Total patches: {len(patches)}")
    logger.info(f"  Max workers: 3")
    logger.info("=" * 80)

    total_patches = len(patches)
    translated_patches = [None] * total_patches
    completed_count = 0
    max_workers = min(3, total_patches)

    if progress_callback:
        progress_callback(0, total_patches, f"Starting parallel translation (max {max_workers} concurrent)...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all patches
        future_to_patch = {
            executor.submit(
                _translate_patch_with_retry_direct,
                llm,
                patch,
                patch_idx,
                config.max_retries,
                cancel_flag
            ): (patch_idx, patch)
            for patch_idx, patch in enumerate(patches)
        }

        logger.info(f"✓ Submitted {len(future_to_patch)} patches to executor")
        logger.info(f"  Active workers: {max_workers}")

        # Process results as they complete
        for future in as_completed(future_to_patch):
            # Check cancellation
            if cancel_flag and cancel_flag.get('cancelled', False):
                logger.warning("=" * 80)
                logger.warning("🛑 TRANSLATION CANCELLED BY USER")
                logger.warning(f"  Completed patches: {completed_count}/{total_patches}")
                logger.warning(f"  Cancelling remaining {total_patches - completed_count} patches...")
                logger.warning("=" * 80)
                executor.shutdown(wait=False, cancel_futures=True)
                if progress_callback:
                    progress_callback(completed_count, total_patches, "Translation cancelled")
                break

            patch_idx, patch = future_to_patch[future]
            patch_num = patch_idx + 1

            try:
                success, translated_patch, error_msg = future.result()

                if success:
                    translated_patches[patch_idx] = translated_patch
                    completed_count += 1
                    if patch_callback:
                        patch_callback(patch_num, True, "")
                    logger.info(f"✓ Patch {patch_num}/{total_patches} completed successfully")
                    logger.debug(f"  Translated entries: {len(translated_patch)}")
                else:
                    if patch_callback:
                        patch_callback(patch_num, False, error_msg)
                    logger.error(f"✗ Patch {patch_num}/{total_patches} failed: {error_msg}")

                if progress_callback:
                    progress_callback(completed_count, total_patches, f"Completed {completed_count}/{total_patches} patches...")

            except Exception as e:
                error_msg = f"Unexpected error processing patch {patch_num}: {str(e)}"
                logger.error(error_msg)
                if patch_callback:
                    patch_callback(patch_num, False, error_msg)

    # Check if workflow was cancelled
    was_cancelled = cancel_flag and cancel_flag.get('cancelled', False)

    logger.info("=" * 80)
    if was_cancelled:
        logger.warning(f"PARALLEL WORKFLOW STOPPED (CANCELLED)")
        logger.warning(f"  Successfully translated: {completed_count}/{total_patches} patches")
        logger.warning(f"  Cancelled/Failed: {total_patches - completed_count} patches")
    else:
        logger.info(f"PARALLEL WORKFLOW COMPLETED")
        logger.info(f"  Successfully translated: {completed_count}/{total_patches} patches")
    logger.info("=" * 80)

    # Merge results
    if progress_callback:
        if was_cancelled:
            progress_callback(completed_count, total_patches, f"Cancelled - {completed_count} patches completed")
        else:
            progress_callback(total_patches, total_patches, "Merging results...")
    valid_patches = [p for p in translated_patches if p is not None]
    return merge_patches(valid_patches)


def _translate_patch_with_retry_direct(
    llm: ChatGoogleGenerativeAI,
    patch: Dict[str, str],
    patch_idx: int,
    max_retries: int,
    cancel_flag=None
) -> tuple[bool, Optional[Dict[str, str]], str]:
    """Translate patch with retry - direct version without QThread signals."""
    patch_num = patch_idx + 1

    for retry_count in range(max_retries + 1):
        # Check cancellation
        if cancel_flag and cancel_flag.get('cancelled', False):
            logger.warning(f"🛑 Patch {patch_num} - Detected cancellation flag, aborting API call")
            return False, None, "Cancelled by user"

        try:
            # Log API call details
            logger.info(f"→ Calling Gemini API for Patch {patch_num} (attempt {retry_count + 1}/{max_retries + 1})")
            logger.debug(f"  Patch size: {len(patch)} entries")
            logger.debug(f"  Sample keys: {list(patch.keys())[:3]}...")

            # Call Gemini API
            system_msg = SystemMessage(content=SYSTEM_PROMPT)
            human_msg = HumanMessage(content=get_translation_prompt(patch))
            messages = [system_msg, human_msg]

            system_tokens = len(SYSTEM_PROMPT) // 4  # Rough estimate
            user_tokens = len(get_translation_prompt(patch)) // 4
            logger.debug(f"  Estimated tokens: ~{system_tokens + user_tokens} (system: {system_tokens}, user: {user_tokens})")
            logger.debug(f"  Model: gemini-2.5-flash, Temperature: 0.1")

            start_time = time.time()
            response = llm.invoke(messages)
            elapsed = time.time() - start_time
            response_text = response.content.strip()

            logger.info(f"← API response received for Patch {patch_num} ({elapsed:.2f}s)")
            logger.debug(f"  Response size: {len(response_text)} chars")
            logger.debug(f"  Response preview: {response_text[:100]}...")

            # Check cancellation immediately after API call
            if cancel_flag and cancel_flag.get('cancelled', False):
                logger.warning(f"🛑 Patch {patch_num} - Detected cancellation after API response, discarding result")
                return False, None, "Cancelled by user"

            # Parse response
            translated_patch = _parse_json_response(response_text)

            # Validate
            is_valid, missing_keys = validate_translation(patch, translated_patch)
            if is_valid:
                return True, translated_patch, ""
            else:
                error_msg = f"Validation failed: missing keys {missing_keys}"
                logger.warning(error_msg)
                if retry_count < max_retries:
                    time.sleep(2)
                    continue
                else:
                    return False, None, error_msg

        except ResourceExhausted as e:
            logger.warning(f"Quota exceeded: {str(e)}")
            if retry_count < max_retries:
                wait_time = 60
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                return False, None, f"Quota exceeded after {max_retries} retries"

        except Exception as e:
            logger.error(f"Translation error: {type(e).__name__}: {str(e)}")
            if retry_count < max_retries:
                time.sleep(2)
            else:
                return False, None, str(e)

    return False, None, "Max retries exceeded"


def _parse_json_response(response_text: str) -> Dict[str, str]:
    """Helper to parse JSON response (without logging - called from worker threads)."""
    # Remove markdown code blocks
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)

    # Try to parse JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise
