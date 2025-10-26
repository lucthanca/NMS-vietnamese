"""
Full Parallel Workflow cho translation.
Chạy song song tất cả patches cùng lúc sử dụng subgraph pattern.

NOTE: Workflow này sử dụng subgraph với START edges để tạo true parallel execution.
Tất cả patches sẽ được dịch song song, mỗi patch có retry logic riêng.
"""
import logging
from typing import Dict, List
from langgraph.graph import StateGraph, START, END
from state import PatchTranslationState, TranslationState
from wf_nodes import (
    load_json_file,
    split_into_patches_node,
    merge_results
)
from retry_policies import (
    should_retry_translation,
    should_retry_validation
)

logger = logging.getLogger(__name__)


def create_patch_processor_node(patch_index: int):
    """
    Tạo node processor cho từng patch.
    
    Args:
        patch_index: Index của patch cần xử lý (1-based)
        
    Returns:
        Node function để process patch
    """
    def process_patch(state: TranslationState) -> Dict:
        """
        Process một patch cụ thể.
        
        IMPORTANT: Chỉ return keys cần cập nhật để tránh conflict trong parallel execution.
        """
        from wf_nodes import translate_patch
        from utils import validate_translation
        from datetime import datetime
        
        # Kiểm tra patch index hợp lệ
        if patch_index > len(state["patches"]):
            logger.warning(f"⚠️  Patch {patch_index} không tồn tại, bỏ qua")
            return {}
        
        logger.info(f"🌐 [PATCH_{patch_index}] Starting parallel processing...")
        start_time = datetime.now()
        
        # Tạo state riêng cho patch này (để process sequentially translate + validate)
        patch_state = state.copy()
        patch_state["current_patch_index"] = patch_index - 1  # Convert to 0-based
        
        # Translate và validate với retry
        max_attempts = state["max_retries"]
        for attempt in range(max_attempts):
            try:
                # Translate
                logger.info(f"🔄 [PATCH_{patch_index}] Translation attempt {attempt + 1}/{max_attempts}")
                result = translate_patch(patch_state)
                
                # translate_patch returns {"translated_patches": [patch]} - take first item
                if "translated_patches" in result and len(result["translated_patches"]) > 0:
                    translated_patch = result["translated_patches"][0]
                    
                    # Manual validation
                    original_patch = state["patches"][patch_index - 1]
                    
                    if translated_patch is not None:
                        is_valid, missing_keys = validate_translation(original_patch, translated_patch)
                        
                        if is_valid:
                            end_time = datetime.now()
                            duration = (end_time - start_time).total_seconds()
                            logger.info(f"✅ [PATCH_{patch_index}] Completed successfully in {duration:.2f}s")
                            
                            # CHỈ return key cần update
                            # Ensure list has enough space
                            updated_translations = state["translated_patches"].copy() if state["translated_patches"] else []
                            
                            # Extend list if needed
                            while len(updated_translations) < patch_index:
                                updated_translations.append(None)
                            
                            # Update at correct index
                            updated_translations[patch_index - 1] = translated_patch
                            
                            return {
                                "translated_patches": updated_translations
                            }
                        else:
                            logger.warning(f"⚠️  [PATCH_{patch_index}] Validation failed: Missing {len(missing_keys)} keys")
                    else:
                        logger.warning(f"⚠️  [PATCH_{patch_index}] Translation result is None")
                else:
                    logger.warning(f"⚠️  [PATCH_{patch_index}] No translation returned")
                
                logger.warning(f"⚠️  [PATCH_{patch_index}] Translation incomplete, retrying...")
                
            except Exception as e:
                logger.error(f"❌ [PATCH_{patch_index}] Error: {e}")
                if attempt == max_attempts - 1:
                    logger.error(f"❌ [PATCH_{patch_index}] Failed after {max_attempts} attempts")
                    # Return empty dict or mark as failed
                    updated_failures = state["failed_patches"].copy()
                    updated_failures.append({
                        "patch_index": patch_index - 1,
                        "reason": str(e)
                    })
                    return {
                        "failed_patches": updated_failures
                    }
        
        # Failed after all retries
        updated_failures = state["failed_patches"].copy()
        updated_failures.append({
            "patch_index": patch_index - 1,
            "reason": "Max retries exceeded"
        })
        return {
            "failed_patches": updated_failures
        }
    
    return process_patch


def create_parallel_workflow() -> StateGraph:
    """
    Tạo TRUE parallel workflow sử dụng subgraph pattern.
    
    Flow:
    1. load_json_file: Load file JSON
    2. split_into_patches: Chia thành patches
    3. subflow: Process TẤT CẢ patches SONG SONG
       - Mỗi patch có retry logic riêng
    4. merge_results: Merge và save output
    
    Returns:
        Compiled StateGraph workflow
    """
    # Tạo main workflow
    workflow = StateGraph(TranslationState)
    
    # Add preprocessing nodes
    workflow.add_node("load_json", load_json_file)
    workflow.add_node("split_patches", split_into_patches_node)
    
    # Tạo subflow cho parallel processing
    # NOTE: Subflow với batching để tránh vượt quá API quota
    def create_dynamic_subflow(state: TranslationState) -> TranslationState:
        """
        Tạo và chạy subflow dynamic với batching.
        Chạy tối đa 3 patches song song cùng lúc, sau đó chờ xong mới chạy batch tiếp theo.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        num_patches = len(state["patches"])
        max_concurrent = 3  # Gemini free tier limit
        logger.info(f"🚀 [PARALLEL] Processing {num_patches} patches with max {max_concurrent} concurrent...")
        
        # CRITICAL: Initialize translated_patches with correct size BEFORE parallel execution
        if not state["translated_patches"] or len(state["translated_patches"]) < num_patches:
            state["translated_patches"] = [None] * num_patches
            logger.info(f"📊 [PARALLEL] Initialized translated_patches with {num_patches} slots")
        
        # Process patches in batches of max_concurrent
        successful_count = 0
        failed_count = 0
        
        for batch_start in range(0, num_patches, max_concurrent):
            batch_end = min(batch_start + max_concurrent, num_patches)
            batch_indices = range(batch_start + 1, batch_end + 1)  # 1-based
            
            logger.info(f"📦 [PARALLEL] Processing batch: patches {batch_start + 1}-{batch_end}")
            
            # Create ThreadPoolExecutor for this batch
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                # Submit all patches in this batch
                # NOTE: create_patch_processor_node returns a function, need to call it with state
                future_to_index = {
                    executor.submit(create_patch_processor_node(i), state): i
                    for i in batch_indices
                }
                
                # Wait for all in this batch to complete
                for future in as_completed(future_to_index):
                    patch_index = future_to_index[future]
                    try:
                        result = future.result()
                        
                        # Update state with result from this patch
                        if "translated_patches" in result and result["translated_patches"]:
                            # Merge translated_patches carefully
                            for idx, translated_patch in enumerate(result["translated_patches"]):
                                if translated_patch is not None and idx < len(state["translated_patches"]):
                                    state["translated_patches"][idx] = translated_patch
                            successful_count += 1
                            logger.info(f"✅ [PARALLEL] Patch {patch_index} completed successfully")
                        elif "failed_patches" in result and result["failed_patches"]:
                            state["failed_patches"].extend(result["failed_patches"])
                            failed_count += 1
                            logger.error(f"❌ [PARALLEL] Patch {patch_index} failed")
                        else:
                            # No result, mark as failed
                            failed_count += 1
                            logger.error(f"❌ [PARALLEL] Patch {patch_index} returned empty result")
                    except Exception as e:
                        logger.error(f"❌ [PARALLEL] Error processing patch {patch_index}: {e}")
                        failed_count += 1
            
            logger.info(f"✅ [PARALLEL] Batch complete: patches {batch_start + 1}-{batch_end}")
        
        logger.info(f"✅ [PARALLEL] All patches completed! Success: {successful_count}, Failed: {failed_count}")
        return state
    
    workflow.add_node("parallel_process", create_dynamic_subflow)
    workflow.add_node("merge", merge_results)
    
    # Set entry point
    workflow.set_entry_point("load_json")
    
    # Linear flow
    workflow.add_edge("load_json", "split_patches")
    workflow.add_edge("split_patches", "parallel_process")
    workflow.add_edge("parallel_process", "merge")
    workflow.add_edge("merge", END)
    
    # Compile workflow
    app = workflow.compile()
    
    return app