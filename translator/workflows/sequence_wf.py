"""
Sequential Workflow cho translation.
Chạy tuần tự: load -> split -> translate patch 1 -> validate -> ... -> merge
"""
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


def create_sequence_workflow() -> StateGraph:
    """
    Tạo sequential workflow với đầy đủ retry logic.
    
    Flow:
    1. load_json_file: Load file JSON
    2. split_into_patches: Chia thành patches
    3. translate_patch: Dịch một patch
    4. validate_patch: Validate patch vừa dịch
       - Nếu fail và còn retry: quay lại translate_patch
       - Nếu pass: kiểm tra còn patch nào không
         - Nếu còn: quay lại translate_patch với patch tiếp theo
         - Nếu hết: chuyển sang merge_results
    5. merge_results: Merge tất cả patches và save output
    
    Returns:
        Compiled StateGraph workflow
    """
    # Tạo graph với TranslationState
    workflow = StateGraph(TranslationState)
    
    # Add nodes
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