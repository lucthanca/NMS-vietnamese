"""
Retry policies for workflow nodes.
Định nghĩa các conditional edges để xử lý retry logic.
"""
from state import TranslationState, PatchTranslationState


def should_retry_translation(state: TranslationState) -> str:
    """
    Quyết định có nên retry translation node không (sequential workflow).
    
    Args:
        state: Current translation state
        
    Returns:
        "retry": Nếu cần retry
        "next": Nếu đã thành công, chuyển sang validate
        "failed": Nếu đã vượt quá max retries
    """
    retry_count = state.get('retry_count', 0)
    max_retries = state.get('max_retries', 3)
    errors = state.get('errors', [])
    
    # Nếu không có error, chuyển sang bước tiếp theo
    if not errors or len(errors) == 0:
        return "next"
    
    # Nếu vẫn còn retry count, retry
    if retry_count < max_retries:
        return "retry"
    
    # Đã vượt quá max retries
    return "failed"


def should_retry_validation(state: TranslationState) -> str:
    """
    Quyết định có nên retry validation node không (sequential workflow).
    
    Args:
        state: Current translation state
        
    Returns:
        "retry_translate": Nếu validation fail và cần retry từ translate
        "next": Nếu validation pass, chuyển sang patch tiếp theo hoặc merge
        "failed": Nếu đã vượt quá max retries
    """
    retry_count = state.get('retry_count', 0)
    max_retries = state.get('max_retries', 3)
    errors = state.get('errors', [])
    
    # Nếu không có error, chuyển sang bước tiếp theo
    if not errors or len(errors) == 0:
        return "next"
    
    # Nếu vẫn còn retry count, retry từ translate
    if retry_count < max_retries:
        return "retry_translate"
    
    # Đã vượt quá max retries
    return "failed"


def should_continue_or_merge(state: TranslationState) -> str:
    """
    Quyết định có nên tiếp tục translate patch tiếp theo hay merge (sequential workflow).
    
    Args:
        state: Current translation state
        
    Returns:
        "translate": Nếu còn patches chưa dịch
        "merge": Nếu đã dịch hết tất cả patches
    """
    current_index = state['current_patch_index']
    total_patches = len(state['patches'])
    
    if current_index < total_patches:
        return "translate"
    
    return "merge"


def should_retry_patch(patch_state: PatchTranslationState) -> str:
    """
    Quyết định có nên retry patch translation không (parallel workflow).
    
    Args:
        patch_state: State của patch này
        
    Returns:
        "retry": Nếu cần retry
        "done": Nếu đã thành công hoặc vượt quá max retries
    """
    validation_passed = patch_state.get('validation_passed', False)
    retry_count = patch_state.get('retry_count', 0)
    max_retries = 3  # Fixed max retries cho parallel workflow
    
    # Nếu validation pass, done
    if validation_passed:
        return "done"
    
    # Nếu vẫn còn retry count, retry
    if retry_count < max_retries:
        return "retry"
    
    # Đã vượt quá max retries, done (với lỗi)
    return "done"