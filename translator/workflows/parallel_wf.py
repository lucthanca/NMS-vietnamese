"""
Full Parallel Workflow cho translation.
Chạy song song tối đa 3 patches cùng lúc.

NOTE: Parallel execution được implement bằng cách chia nhỏ patches và xử lý tuần tự
trong workflow, nhưng có thể chạy multiple instances của workflow này song song.
"""
import logging
from typing import Dict
from langgraph.graph import StateGraph, END
from state import TranslationState
from wf_nodes import (
    load_json_file,
    split_into_patches_node,
    translate_patch,
    validate_patch,
    merge_results
)
from retry_policies import (
    should_retry_translation,
    should_retry_validation,
    should_continue_or_merge
)

logger = logging.getLogger(__name__)


def create_parallel_workflow() -> StateGraph:
    """
    Tạo parallel workflow.
    
    NOTE: Workflow này tương tự sequential nhưng được optimize cho parallel execution.
    Để chạy thực sự parallel, có thể:
    1. Chạy multiple instances của script này với different input files
    2. Split large file thành smaller files và chạy parallel processes
    3. Sử dụng threading/multiprocessing trong main.py
    
    Flow:
    1. load_json_file: Load file JSON
    2. split_into_patches: Chia thành patches
    3. translate_patch: Dịch từng patch
    4. validate_patch: Validate patch vừa dịch
       - Loop qua tất cả patches
    5. merge_results: Merge và save output
    
    Returns:
        Compiled StateGraph workflow
    """
    # Tạo graph với TranslationState
    workflow = StateGraph(TranslationState)
    
    # Add nodes (giống sequential workflow)
    workflow.add_node("load_json", load_json_file)
    workflow.add_node("split_patches", split_into_patches_node)
    workflow.add_node("translate", translate_patch)
    workflow.add_node("validate", validate_patch)
    workflow.add_node("merge", merge_results)
    
    # Set entry point
    workflow.set_entry_point("load_json")
    
    # Linear flow: load -> split -> translate
    workflow.add_edge("load_json", "split_patches")
    workflow.add_edge("split_patches", "translate")
    
    # Conditional edge từ translate: kiểm tra có cần retry không
    workflow.add_conditional_edges(
        "translate",
        should_retry_translation,
        {
            "retry": "translate",      # Retry lại translation
            "next": "validate",        # Chuyển sang validation
            "failed": END              # Vượt quá max retries, kết thúc
        }
    )
    
    # Conditional edge từ validate: kiểm tra validation result
    workflow.add_conditional_edges(
        "validate",
        should_retry_validation,
        {
            "retry_translate": "translate",  # Validation fail, retry từ translate
            "next": "check_continue",        # Validation pass, kiểm tra tiếp
            "failed": END                    # Vượt quá max retries, kết thúc
        }
    )
    
    # Node helper để kiểm tra có nên tiếp tục hay merge
    def check_continue(state: TranslationState):
        """Helper node để kiểm tra flow tiếp theo."""
        return state
    
    workflow.add_node("check_continue", check_continue)
    
    # Conditional edge từ check_continue: kiểm tra còn patch nào không
    workflow.add_conditional_edges(
        "check_continue",
        should_continue_or_merge,
        {
            "translate": "translate",  # Còn patches, tiếp tục dịch
            "merge": "merge"          # Hết patches, merge kết quả
        }
    )
    
    # Merge xong thì kết thúc
    workflow.add_edge("merge", END)
    
    # Compile workflow
    app = workflow.compile()
    
    return app