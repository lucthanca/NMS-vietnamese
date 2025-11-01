"""
Utility functions for translation operations.
"""
import json
from typing import Dict, List, Tuple


def count_tokens(text: str) -> int:
    """
    Estimate token count for Gemini API.

    Uses conservative estimate: 1 token ≈ 3 chars, with 10% buffer.

    Args:
        text: Text string to count tokens

    Returns:
        Estimated token count
    """
    char_count = len(text)
    estimated_tokens = int(char_count / 3 * 1.1)
    return estimated_tokens


def count_tokens_in_dict(data: Dict[str, str]) -> int:
    """
    Count total tokens in a dictionary.

    Args:
        data: Dictionary containing key-value pairs

    Returns:
        Estimated total token count
    """
    json_str = json.dumps(data, ensure_ascii=False)
    return count_tokens(json_str)


def split_into_patches(data: Dict[str, str], token_limit: int = 50000) -> List[Dict[str, str]]:
    """
    Split large dictionary into smaller patches based on token limit.

    Strategy:
    - Iterate through key-value pairs
    - Accumulate in current patch until near token_limit
    - Reserve 20% tokens for system prompt and response overhead

    NOTE: Default limit 50000 is safe for Gemini output limit 65,535 tokens

    Args:
        data: Original dictionary to split
        token_limit: Token limit per patch (default: 50000)

    Returns:
        List of patches (each patch is a smaller dict)
    """
    patches: List[Dict[str, str]] = []
    current_patch: Dict[str, str] = {}
    current_tokens = 0

    # Reserve 20% tokens for system prompt and overhead
    effective_limit = int(token_limit * 0.8)

    for key, value in data.items():
        # Count tokens for this entry (including key and value)
        entry_dict = {key: value}
        entry_tokens = count_tokens_in_dict(entry_dict)

        # If this entry exceeds limit (extremely rare case)
        if entry_tokens > effective_limit:
            # Must add as separate patch
            if current_patch:
                patches.append(current_patch)
                current_patch = {}
                current_tokens = 0
            patches.append(entry_dict)
            continue

        # If adding this entry would exceed limit, create new patch
        if current_tokens + entry_tokens > effective_limit and current_patch:
            patches.append(current_patch)
            current_patch = {}
            current_tokens = 0

        # Add entry to current patch
        current_patch[key] = value
        current_tokens += entry_tokens

    # Add final patch if any
    if current_patch:
        patches.append(current_patch)

    return patches


def merge_patches(patches: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Merge patches back into a single dictionary.

    Args:
        patches: List of patches to merge (may contain None values)

    Returns:
        Merged dictionary
    """
    merged = {}
    for patch in patches:
        if patch is not None:
            merged.update(patch)
    return merged


def validate_translation(original: Dict[str, str], translated: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate if translation has all keys from original.

    Args:
        original: Original dictionary
        translated: Translated dictionary

    Returns:
        Tuple (is_valid, missing_keys)
        - is_valid: True if all keys present
        - missing_keys: List of missing keys
    """
    original_keys = set(original.keys())
    translated_keys = set(translated.keys())

    missing_keys = original_keys - translated_keys

    if missing_keys:
        return False, list(missing_keys)

    return True, []


def find_missing_entries(main_data: Dict[str, str], translation_data: Dict[str, str]) -> Dict[str, str]:
    """
    Find entries in main_data that are not in translation_data.

    Args:
        main_data: Main dictionary (original entries)
        translation_data: Translation dictionary

    Returns:
        Dictionary of missing entries (key-value pairs)
    """
    missing = {}
    for key, value in main_data.items():
        if key not in translation_data:
            missing[key] = value
    return missing


def calculate_progress(current: int, total: int) -> float:
    """
    Calculate progress percentage.

    Args:
        current: Number completed
        total: Total number

    Returns:
        Progress percentage (0-100)
    """
    if total == 0:
        return 100.0
    return round((current / total) * 100, 2)
