"""
State definition for the translation workflow.
Uses TypedDict for type safety with LangGraph.
"""
from typing import TypedDict, List, Dict, Optional, Annotated
from operator import add


class TranslationState(TypedDict):
    """
    State object cho translation workflow.
    
    Attributes:
        loc_name: Tên file localization (ví dụ: NMS_LOC1_ENGLISH.json)
        token_limit: Giới hạn token cho mỗi patch (mặc định: 50000, an toàn cho Gemini output limit 65,535)
        original_data: Dữ liệu JSON gốc (dict với key-value pairs)
        patches: List các patch đã được chia nhỏ
        current_patch_index: Index của patch đang xử lý (cho sequential workflow)
        translated_patches: List các patch đã dịch xong
        failed_patches: List các patch bị lỗi kèm thông tin retry
        retry_count: Số lần retry cho patch hiện tại
        max_retries: Số lần retry tối đa (mặc định: 3)
        errors: List các error messages
        completed: Boolean flag để đánh dấu hoàn thành
        progress: Progress percentage (0-100)
    """
    loc_name: str
    token_limit: int
    original_data: Optional[Dict[str, str]]
    patches: List[Dict[str, str]]
    current_patch_index: int
    translated_patches: Annotated[List[Dict[str, str]], add]  # Sử dụng operator add để merge kết quả từ parallel nodes
    failed_patches: List[Dict]
    retry_count: int
    max_retries: int
    errors: Annotated[List[str], add]  # Sử dụng operator add để collect errors từ nhiều nodes
    completed: bool
    progress: float


class PatchTranslationState(TypedDict):
    """
    State cho việc dịch một patch riêng lẻ (dùng cho parallel workflow).
    
    Attributes:
        patch_index: Index của patch này
        patch_data: Dữ liệu của patch (dict với key-value pairs)
        translated_data: Dữ liệu đã dịch
        validation_passed: Flag đánh dấu validation có pass không
        retry_count: Số lần retry
        error: Error message nếu có
    """
    patch_index: int
    patch_data: Dict[str, str]
    translated_data: Optional[Dict[str, str]]
    validation_passed: bool
    retry_count: int
    error: Optional[str]