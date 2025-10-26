"""
Utility functions for the translator application.
"""
import json
import logging
from typing import Dict, List, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_json_data(file_path: str | Path) -> Dict[str, str]:
    """
    Đọc dữ liệu JSON từ file.
    
    Args:
        file_path: Đường dẫn đến file JSON
        
    Returns:
        Dict chứa dữ liệu JSON (key-value pairs)
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def write_json_data(file_path: str | Path, data: Dict[str, str], indent: int = 2) -> None:
    """
    Ghi dữ liệu JSON ra file.
    
    Args:
        file_path: Đường dẫn file cần ghi
        data: Dữ liệu JSON cần ghi
        indent: Số space để indent (mặc định: 2)
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=indent)


def count_tokens(text: str) -> int:
    """
    Đếm số token cho Gemini API.
    
    Gemini API sử dụng SentencePiece tokenizer, nhưng để đơn giản,
    ta sẽ estimate bằng cách:
    - 1 token ≈ 4 ký tự (cho English)
    - 1 token ≈ 2-3 ký tự (cho Vietnamese với dấu)
    
    Để an toàn, ta sẽ dùng estimate thấp hơn (1 token = 3 chars).
    
    Args:
        text: Chuỗi text cần đếm token
        
    Returns:
        Số token estimate
    """
    # Đếm theo ký tự và chia cho 3
    # Thêm 10% buffer để đảm bảo an toàn
    char_count = len(text)
    estimated_tokens = int(char_count / 3 * 1.1)
    return estimated_tokens


def count_tokens_in_dict(data: Dict[str, str]) -> int:
    """
    Đếm tổng số token trong một dictionary.
    
    Args:
        data: Dictionary chứa key-value pairs
        
    Returns:
        Tổng số token estimate
    """
    # Chuyển dict thành JSON string và đếm token
    json_str = json.dumps(data, ensure_ascii=False)
    return count_tokens(json_str)


def split_into_patches(data: Dict[str, str], token_limit: int = 50000) -> List[Dict[str, str]]:
    """
    Chia dictionary lớn thành các patches nhỏ dựa theo token limit.
    
    Strategy:
    - Duyệt qua từng key-value pair
    - Tích lũy vào patch hiện tại cho đến khi gần đạt token_limit
    - Khi gần đạt limit, tạo patch mới
    - Reserve 20% token cho system prompt và response overhead
    
    NOTE: Default limit là 50000 để an toàn với Gemini output limit 65,535 tokens
    
    Args:
        data: Dictionary gốc cần chia
        token_limit: Giới hạn token cho mỗi patch (mặc định: 50000)
        
    Returns:
        List các patches (mỗi patch là một dict nhỏ hơn)
    """
    patches: List[Dict[str, str]] = []
    current_patch: Dict[str, str] = {}
    current_tokens = 0
    
    # Reserve 20% token cho system prompt và overhead
    effective_limit = int(token_limit * 0.8)
    
    logger.info(f"📦 Splitting data into patches with limit: {token_limit} tokens (effective: {effective_limit})")
    
    for key, value in data.items():
        # Đếm token cho entry này (bao gồm cả key và value)
        entry_dict = {key: value}
        entry_tokens = count_tokens_in_dict(entry_dict)
        
        # Nếu entry này vượt quá limit (trường hợp cực kỳ hiếm)
        if entry_tokens > effective_limit:
            logger.warning(f"⚠️ Entry '{key}' has {entry_tokens} tokens, exceeding limit!")
            # Vẫn phải thêm vào một patch riêng
            if current_patch:
                patches.append(current_patch)
                current_patch = {}
                current_tokens = 0
            patches.append(entry_dict)
            continue
        
        # Nếu thêm entry này vào sẽ vượt limit, tạo patch mới
        if current_tokens + entry_tokens > effective_limit and current_patch:
            patches.append(current_patch)
            logger.info(f"✅ Created patch {len(patches)} with {len(current_patch)} entries ({current_tokens} tokens)")
            current_patch = {}
            current_tokens = 0
        
        # Thêm entry vào patch hiện tại
        current_patch[key] = value
        current_tokens += entry_tokens
    
    # Thêm patch cuối cùng nếu có
    if current_patch:
        patches.append(current_patch)
        logger.info(f"✅ Created patch {len(patches)} with {len(current_patch)} entries ({current_tokens} tokens)")
    
    total_entries = sum(len(patch) for patch in patches)
    logger.info(f"📊 Split complete: {len(patches)} patches, {total_entries} total entries")
    
    return patches


def merge_patches(patches: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Merge các patches lại thành một dictionary duy nhất.
    
    Args:
        patches: List các patches cần merge (có thể chứa None values)
        
    Returns:
        Dictionary đã merge
    """
    merged = {}
    for patch in patches:
        # Skip None patches (failed translations)
        if patch is not None:
            merged.update(patch)
    return merged


def validate_translation(original: Dict[str, str], translated: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate xem translation có đầy đủ keys như original không.
    
    Args:
        original: Dictionary gốc
        translated: Dictionary đã dịch
        
    Returns:
        Tuple (is_valid, missing_keys)
        - is_valid: True nếu tất cả keys đều có
        - missing_keys: List các keys bị thiếu
    """
    original_keys = set(original.keys())
    translated_keys = set(translated.keys())
    
    missing_keys = original_keys - translated_keys
    
    if missing_keys:
        return False, list(missing_keys)
    
    return True, []


def calculate_progress(current: int, total: int) -> float:
    """
    Tính progress percentage.
    
    Args:
        current: Số lượng đã hoàn thành
        total: Tổng số lượng
        
    Returns:
        Progress percentage (0-100)
    """
    if total == 0:
        return 100.0
    return round((current / total) * 100, 2)