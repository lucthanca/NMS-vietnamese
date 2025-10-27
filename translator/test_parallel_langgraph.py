#!/usr/bin/env python3
"""
Test parallel workflow với fake API trong LangGraph.
"""
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict
from langgraph.graph import StateGraph, START, END
from state import TranslationState
from utils import get_json_data, split_into_patches

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fake_translate_patch_node(patch_index: int):
    """
    Tạo node để fake translate một patch cụ thể.
    
    Args:
        patch_index: Index của patch (1-based)
        
    Returns:
        Node function
    """
    def process(state: TranslationState) -> Dict:
        """
        Fake translation với sleep.
        
        IMPORTANT: Chỉ return keys cần cập nhật để tránh conflict trong parallel execution.
        """
        logger.info(f"🌐 [PATCH_{patch_index}] Starting translation at {datetime.now().strftime('%H:%M:%S')}")
        
        # Simulate API call
        time.sleep(2.0)
        
        # Fake translation: thêm prefix
        patch_data = state["patches"][patch_index - 1]
        translated = {key: f"[VI] {value}" for key, value in patch_data.items()}
        
        logger.info(f"✅ [PATCH_{patch_index}] Completed at {datetime.now().strftime('%H:%M:%S')}")
        
        # CHỈ return key cần update để avoid conflict
        # Update translated_patches list tại đúng index
        updated_translations = state["translated_patches"].copy()
        updated_translations[patch_index - 1] = translated
        
        return {
            "translated_patches": updated_translations
        }
    
    return process


def test_langgraph_parallel():
    """Test parallel workflow trong LangGraph."""
    print("\n" + "="*80)
    print("🚀 LangGraph Parallel Workflow Test")
    print("="*80 + "\n")
    
    # Load và split data
    test_file = Path("input/test_200.json")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📂 Loading test data from {test_file}...")
    data = get_json_data(test_file)
    print(f"✅ Loaded {len(data)} entries\n")
    
    print("🔪 Splitting into patches (token_limit=5000 - để tạo nhiều patches test parallel)...")
    patches = split_into_patches(data, token_limit=5000)
    print(f"✅ Created {len(patches)} patches\n")
    
    # Giới hạn số patches để test
    max_patches = 3
    if len(patches) > max_patches:
        print(f"⚠️  Limiting to {max_patches} patches for faster testing\n")
        patches = patches[:max_patches]
    
    # Tạo initial state
    initial_state = {
        "input_file": str(test_file),
        "output_file": "output/test_parallel.json",
        "token_limit": 25000,
        "max_retries": 3,
        "data": data,
        "patches": patches,
        "current_patch_index": 0,
        "translated_patches": [None] * len(patches),
        "failed_patches": []
    }
    
    # Tạo subflow với parallel nodes
    print(f"📊 Creating subflow with {len(patches)} parallel nodes...")
    subflow = StateGraph(TranslationState)
    
    for i in range(1, len(patches) + 1):
        node_name = f"translate_patch_{i}"
        subflow.add_node(node_name, fake_translate_patch_node(i))
        # Connect với START để chạy parallel
        subflow.add_edge(START, node_name)
        # Kết thúc sau khi xong
        subflow.add_edge(node_name, END)
    
    # Compile và run
    app = subflow.compile()
    
    print("⚡ Running parallel translation...\n")
    start_time = time.time()
    
    result = app.invoke(initial_state)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Kiểm tra kết quả
    successful = sum(1 for p in result["translated_patches"] if p is not None)
    
    print(f"\n⏱️  Total execution time: {total_time:.2f}s")
    print(f"📊 Patches processed: {successful}/{len(patches)}")
    print(f"⚡ Expected sequential time: ~{len(patches) * 2.0:.1f}s")
    print(f"🚀 Speedup: {(len(patches) * 2.0) / total_time:.2f}x")
    
    print("\n" + "="*80)
    if total_time < len(patches) * 2.0 * 0.7:  # Nếu nhanh hơn 70% sequential
        print("✅ TRUE PARALLEL EXECUTION CONFIRMED!")
    else:
        print("⚠️  Still running sequentially")
    print("="*80)


if __name__ == "__main__":
    test_langgraph_parallel()
