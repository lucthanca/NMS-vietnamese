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
    # NOTE: Subflow sẽ được config dynamic sau khi split patches
    def create_dynamic_subflow(state: TranslationState) -> TranslationState:
        """
        Tạo và chạy subflow dynamic dựa trên số lượng patches.
        """
        num_patches = len(state["patches"])
        logger.info(f"🚀 [PARALLEL] Creating subflow for {num_patches} patches...")
        
        # CRITICAL: Initialize translated_patches with correct size BEFORE parallel execution
        # Tránh race condition khi parallel nodes cập nhật cùng lúc
        if not state["translated_patches"] or len(state["translated_patches"]) < num_patches:
            state["translated_patches"] = [None] * num_patches
            logger.info(f"📊 [PARALLEL] Initialized translated_patches with {num_patches} slots")
        
        # Tạo subflow
        subflow = StateGraph(TranslationState)
        
        # Add nodes cho từng patch
        for i in range(1, num_patches + 1):
            node_name = f"process_patch_{i}"
            subflow.add_node(node_name, create_patch_processor_node(i))
            # Connect tất cả nodes với START để chạy parallel
            subflow.add_edge(START, node_name)
            # Kết thúc sau khi xong
            subflow.add_edge(node_name, END)
        
        # Compile và chạy subflow
        subflow_app = subflow.compile()
        
        logger.info(f"⚡ [PARALLEL] Running {num_patches} patches in parallel...")
        result_state = subflow_app.invoke(state)
        
        logger.info(f"✅ [PARALLEL] All patches completed!")
        return result_state
    
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