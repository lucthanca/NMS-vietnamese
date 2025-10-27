"""
Workflow nodes for the translation pipeline.
Mỗi node là một function nhận state và trả về dict để update state.
"""
import logging
import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import ResourceExhausted
import os
from dotenv import load_dotenv

from state import TranslationState, PatchTranslationState
from prompts import SYSTEM_PROMPT, get_translation_prompt
from utils import (
    get_json_data, 
    write_json_data, 
    split_into_patches, 
    merge_patches,
    validate_translation,
    calculate_progress
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Gemini LLM
# NOTE: Disable auto-retry cho ResourceExhausted (429) để tự xử lý smart wait
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.1,  # Thấp hơn để consistent và structured output
    max_retries=0  # Disable auto-retry, tự handle retry logic
)


def extract_retry_delay(error_message: str) -> int:
    """
    Extract retry delay (seconds) từ ResourceExhausted error message.
    
    Args:
        error_message: Error message từ Google API
        
    Returns:
        Số giây cần chờ, default 60s nếu không parse được
    """
    # Pattern: "Please retry in 42.363447542s" hoặc "retry_delay { seconds: 42 }"
    patterns = [
        r'Please retry in (\d+(?:\.\d+)?)s',
        r'retry_delay\s*{\s*seconds:\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_message)
        if match:
            delay = float(match.group(1))
            return int(delay) + 5  # Thêm 5s buffer cho an toàn
    
    # Default fallback
    return 60


def wait_with_countdown(seconds: int, patch_info: str = ""):
    """
    Chờ với countdown log để user biết progress.
    
    Args:
        seconds: Số giây cần chờ
        patch_info: Thông tin về patch đang xử lý (để log)
    """
    logger.warning(f"⏳ [QUOTA_WAIT{patch_info}] Waiting {seconds}s for quota reset...")
    
    # Log countdown mỗi 10s
    for remaining in range(seconds, 0, -10):
        if remaining <= seconds:
            logger.info(f"⏳ [QUOTA_WAIT{patch_info}] {remaining}s remaining...")
        time.sleep(min(10, remaining))
    
    logger.info(f"✅ [QUOTA_WAIT{patch_info}] Wait complete, resuming...")


def call_gemini_with_quota_handling(messages: List, patch_info: str = "", max_quota_retries: int = 3) -> str:
    """
    Gọi Gemini API với xử lý thông minh cho quota exceeded.
    
    Args:
        messages: Messages để gửi đến API
        patch_info: Thông tin patch đang dịch (để log)
        max_quota_retries: Số lần retry tối đa cho quota errors
        
    Returns:
        Response text từ API
        
    Raises:
        Exception nếu vượt quá max retries hoặc gặp lỗi khác
    """
    quota_retry_count = 0
    
    while quota_retry_count <= max_quota_retries:
        try:
            logger.info(f"🤖 [TRANSLATE{patch_info}] Calling Gemini API...")
            response = llm.invoke(messages)
            return response.content.strip()
            
        except ResourceExhausted as e:
            error_msg = str(e)
            
            # Extract retry delay từ error
            retry_delay = extract_retry_delay(error_msg)
            
            # Log chi tiết về quota error
            logger.error(f"❌ [QUOTA_EXCEEDED{patch_info}] 429 Quota Exceeded!")
            logger.error(f"📊 [QUOTA_EXCEEDED{patch_info}] Quota: generativelanguage.googleapis.com/generate_content_free_tier_requests")
            logger.error(f"📊 [QUOTA_EXCEEDED{patch_info}] Limit: 250 requests/day")
            logger.error(f"📊 [QUOTA_EXCEEDED{patch_info}] Model: gemini-2.5-flash")
            logger.error(f"📊 [QUOTA_EXCEEDED{patch_info}] Retry delay from API: {retry_delay}s")
            logger.error(f"📊 [QUOTA_EXCEEDED{patch_info}] Attempt: {quota_retry_count + 1}/{max_quota_retries + 1}")
            
            # Kiểm tra có còn retry không
            if quota_retry_count >= max_quota_retries:
                logger.error(f"❌ [QUOTA_EXCEEDED{patch_info}] Max quota retries reached ({max_quota_retries})")
                raise
            
            # Wait với countdown
            quota_retry_count += 1
            wait_with_countdown(retry_delay, patch_info)
            logger.info(f"🔄 [QUOTA_RETRY{patch_info}] Retrying after quota wait (attempt {quota_retry_count + 1}/{max_quota_retries + 1})...")
            
        except Exception as e:
            # Các lỗi khác (network, timeout, etc.) - không retry
            logger.error(f"❌ [TRANSLATE{patch_info}] API Error: {type(e).__name__}: {str(e)}")
            raise
    
    # Should not reach here
    raise Exception(f"Failed after {max_quota_retries} quota retries")



def load_json_file(state: TranslationState) -> Dict:
    """
    Node 1: Load JSON file từ input folder.
    
    Args:
        state: Current translation state
        
    Returns:
        Dict update cho state với original_data
    """
    start_time = datetime.now()
    loc_name = state['loc_name']
    
    logger.info(f"🚀 [LOAD_JSON] Loading file: {loc_name}")
    logger.info(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Đường dẫn đến file input
        loc_file = Path("input") / loc_name
        
        if not loc_file.exists():
            error_msg = f"File not found: {loc_file}"
            logger.error(f"❌ [LOAD_JSON] {error_msg}")
            return {
                "errors": [error_msg],
                "completed": True
            }
        
        # Load dữ liệu JSON
        data = get_json_data(loc_file)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ [LOAD_JSON] Loaded {len(data)} entries")
        logger.info(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        return {
            "original_data": data
        }
        
    except Exception as e:
        error_msg = f"Error loading JSON: {str(e)}"
        logger.error(f"❌ [LOAD_JSON] {error_msg}")
        return {
            "errors": [error_msg],
            "completed": True
        }


def split_into_patches_node(state: TranslationState) -> Dict:
    """
    Node 2: Chia dữ liệu thành các patches nhỏ dựa theo token limit.
    
    Args:
        state: Current translation state
        
    Returns:
        Dict update cho state với patches
    """
    start_time = datetime.now()
    logger.info(f"🔪 [SPLIT_PATCHES] Splitting data into patches")
    logger.info(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        original_data = state['original_data']
        token_limit = state.get('token_limit', 100000)
        
        # Split thành patches
        patches = split_into_patches(original_data, token_limit)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ [SPLIT_PATCHES] Created {len(patches)} patches")
        logger.info(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        return {
            "patches": patches,
            "current_patch_index": 0
        }
        
    except Exception as e:
        error_msg = f"Error splitting patches: {str(e)}"
        logger.error(f"❌ [SPLIT_PATCHES] {error_msg}")
        return {
            "errors": [error_msg],
            "completed": True
        }


def translate_patch(state: TranslationState) -> Dict:
    """
    Node 3: Dịch một patch (cho sequential workflow).
    
    Args:
        state: Current translation state
        
    Returns:
        Dict update cho state
    """
    start_time = datetime.now()
    current_index = state['current_patch_index']
    patches = state['patches']
    retry_count = state.get('retry_count', 0)
    
    patch_info = f" {current_index + 1}/{len(patches)}"
    
    logger.info(f"🌐 [TRANSLATE] Translating patch {current_index + 1}/{len(patches)} (retry: {retry_count})")
    logger.info(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Lấy patch hiện tại
        current_patch = patches[current_index]
        
        logger.info(f"📝 [TRANSLATE] Patch has {len(current_patch)} entries")
        
        # Tạo prompt
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=get_translation_prompt(current_patch))
        ]
        
        # Gọi LLM với quota handling
        response_text = call_gemini_with_quota_handling(messages, patch_info)
        
        # Ghi raw response ra file để debug
        debug_file = Path("output") / f"debug_response_patch_{current_index + 1}_retry_{retry_count}.txt"
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response_text)
        logger.info(f"📝 [TRANSLATE] Raw response saved to {debug_file}")
        
        # Xử lý markdown code block nếu có
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Bỏ ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Bỏ ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Bỏ ```
        
        response_text = response_text.strip()
        
        # Attempt to fix common JSON issues
        # 1. Remove any text before first {
        if '{' in response_text:
            first_brace = response_text.index('{')
            if first_brace > 0:
                logger.warning(f"⚠️  [TRANSLATE] Removing {first_brace} chars before first {{")
                response_text = response_text[first_brace:]
        
        # 2. Remove any text after last }
        if '}' in response_text:
            last_brace = response_text.rindex('}')
            if last_brace < len(response_text) - 1:
                logger.warning(f"⚠️  [TRANSLATE] Removing {len(response_text) - last_brace - 1} chars after last }}")
                response_text = response_text[:last_brace + 1]
        
        # Ghi cleaned response ra file để debug
        clean_file = Path("output") / f"debug_cleaned_patch_{current_index + 1}_retry_{retry_count}.json"
        with open(clean_file, 'w', encoding='utf-8') as f:
            f.write(response_text)
        logger.info(f"📝 [TRANSLATE] Cleaned response saved to {clean_file}")
        
        # Parse JSON
        try:
            translated_patch = json.loads(response_text)
        except json.JSONDecodeError as je:
            # Log chi tiết lỗi JSON
            logger.error(f"❌ [TRANSLATE] JSON decode error at line {je.lineno}, col {je.colno}: {je.msg}")
            logger.error(f"❌ [TRANSLATE] Error position: {je.pos}")
            
            # Lấy context xung quanh vị trí lỗi
            start_pos = max(0, je.pos - 100)
            end_pos = min(len(response_text), je.pos + 100)
            context = response_text[start_pos:end_pos]
            logger.error(f"❌ [TRANSLATE] Context: ...{context}...")
            
            raise
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ [TRANSLATE] Translation completed")
        logger.info(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        # Store translated patch để validate
        return {
            "translated_patches": [translated_patch],
            "retry_count": 0  # Reset retry count sau khi thành công
        }
        
    except Exception as e:
        error_msg = f"Error translating patch {current_index + 1}: {str(e)}"
        logger.error(f"❌ [TRANSLATE] {error_msg}")
        
        # Tăng retry count
        retry_count = state.get('retry_count', 0) + 1
        
        return {
            "errors": [error_msg],
            "retry_count": retry_count
        }


def validate_patch(state: TranslationState) -> Dict:
    """
    Node 4: Validate patch vừa dịch xem có thiếu keys không.
    
    Args:
        state: Current translation state
        
    Returns:
        Dict update cho state
    """
    start_time = datetime.now()
    current_index = state['current_patch_index']
    patches = state['patches']
    translated_patches = state['translated_patches']
    
    logger.info(f"🔍 [VALIDATE] Validating patch {current_index + 1}/{len(patches)}")
    logger.info(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        original_patch = patches[current_index]
        translated_patch = translated_patches[current_index]
        
        # Validate
        is_valid, missing_keys = validate_translation(original_patch, translated_patch)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if is_valid:
            logger.info(f"✅ [VALIDATE] Validation passed")
            logger.info(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
            
            # Tính progress
            progress = calculate_progress(current_index + 1, len(patches))
            
            return {
                "current_patch_index": current_index + 1,
                "retry_count": 0,
                "progress": progress
            }
        else:
            error_msg = f"Validation failed: Missing {len(missing_keys)} keys: {missing_keys[:5]}"
            logger.error(f"❌ [VALIDATE] {error_msg}")
            
            # Tăng retry count
            retry_count = state.get('retry_count', 0) + 1
            
            return {
                "errors": [error_msg],
                "retry_count": retry_count
            }
            
    except Exception as e:
        error_msg = f"Error validating patch {current_index + 1}: {str(e)}"
        logger.error(f"❌ [VALIDATE] {error_msg}")
        
        retry_count = state.get('retry_count', 0) + 1
        
        return {
            "errors": [error_msg],
            "retry_count": retry_count
        }


def merge_results(state: TranslationState) -> Dict:
    """
    Node 5: Merge tất cả patches đã dịch và lưu file output.
    
    Args:
        state: Current translation state
        
    Returns:
        Dict update cho state
    """
    start_time = datetime.now()
    logger.info(f"🔗 [MERGE] Merging all translated patches")
    logger.info(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        translated_patches = state['translated_patches']
        loc_name = state['loc_name']
        
        # Merge patches
        merged_data = merge_patches(translated_patches)
        
        # Tạo output filename (thay ENGLISH bằng VIETNAMESE)
        output_name = loc_name.replace("_ENGLISH", "_VIETNAMESE")
        output_path = Path("output") / output_name
        
        # Tạo thư mục output nếu chưa có
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Lưu file
        write_json_data(output_path, merged_data)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ [MERGE] Saved {len(merged_data)} entries to {output_path}")
        logger.info(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        return {
            "completed": True,
            "progress": 100.0
        }
        
    except Exception as e:
        error_msg = f"Error merging results: {str(e)}"
        logger.error(f"❌ [MERGE] {error_msg}")
        return {
            "errors": [error_msg],
            "completed": True
        }


# ============================================================================
# Parallel Workflow Nodes
# ============================================================================

def translate_single_patch(patch_state: PatchTranslationState) -> PatchTranslationState:
    """
    Node để dịch một patch riêng lẻ (dùng cho parallel workflow).
    
    Args:
        patch_state: State của patch này
        
    Returns:
        Updated patch state
    """
    start_time = datetime.now()
    patch_index = patch_state['patch_index']
    
    patch_info = f" PATCH_{patch_index}"
    
    logger.info(f"🌐 [TRANSLATE_PATCH_{patch_index}] Starting translation")
    logger.info(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        patch_data = patch_state['patch_data']
        
        logger.info(f"📝 [TRANSLATE_PATCH_{patch_index}] Translating {len(patch_data)} entries")
        
        # Tạo prompt
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=get_translation_prompt(patch_data))
        ]
        
        # Gọi LLM với quota handling
        response_text = call_gemini_with_quota_handling(messages, patch_info)
        
        # Xử lý markdown code block
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        translated_data = json.loads(response_text)
        
        # Validate
        is_valid, missing_keys = validate_translation(patch_data, translated_data)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if is_valid:
            logger.info(f"✅ [TRANSLATE_PATCH_{patch_index}] Translation & validation successful")
            logger.info(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
            
            return {
                **patch_state,
                "translated_data": translated_data,
                "validation_passed": True,
                "retry_count": 0
            }
        else:
            error_msg = f"Validation failed: Missing {len(missing_keys)} keys"
            logger.error(f"❌ [TRANSLATE_PATCH_{patch_index}] {error_msg}")
            
            return {
                **patch_state,
                "validation_passed": False,
                "retry_count": patch_state['retry_count'] + 1,
                "error": error_msg
            }
            
    except Exception as e:
        error_msg = f"Translation error: {str(e)}"
        logger.error(f"❌ [TRANSLATE_PATCH_{patch_index}] {error_msg}")
        
        return {
            **patch_state,
            "validation_passed": False,
            "retry_count": patch_state['retry_count'] + 1,
            "error": error_msg
        }
