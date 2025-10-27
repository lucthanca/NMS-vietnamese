#!/usr/bin/env python3
"""
Test script để verify parallel workflow execution với fake API calls.
"""
import asyncio
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from state import TranslationState
from utils import get_json_data, split_into_patches, calculate_progress


def fake_translate_patch(patch_index: int, patch_data: Dict[str, str], delay: float = 2.0) -> Dict:
    """
    Fake translation function để simulate API call.
    
    Args:
        patch_index: Index của patch
        patch_data: Data cần dịch
        delay: Delay time để simulate API call
        
    Returns:
        Translated patch data
    """
    start_time = datetime.now()
    print(f"🌐 [PATCH_{patch_index}] Starting translation at {start_time.strftime('%H:%M:%S')}")
    print(f"📝 [PATCH_{patch_index}] Translating {len(patch_data)} entries...")
    
    # Simulate API call với random delay
    actual_delay = delay + random.uniform(-0.5, 0.5)
    time.sleep(actual_delay)
    
    # Fake translation: thêm "[VI]" prefix vào mỗi value
    translated = {key: f"[VI] {value}" for key, value in patch_data.items()}
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    print(f"✅ [PATCH_{patch_index}] Completed at {end_time.strftime('%H:%M:%S')} ({execution_time:.2f}s)")
    
    return translated


def test_sequential(patches: List[Dict[str, str]]) -> Dict:
    """
    Test sequential execution.
    
    Args:
        patches: List of patches to translate
        
    Returns:
        Dict with results and timing
    """
    print("\n" + "="*80)
    print("🔄 SEQUENTIAL WORKFLOW TEST")
    print("="*80 + "\n")
    
    start_time = time.time()
    translated_patches = []
    
    for i, patch in enumerate(patches):
        result = fake_translate_patch(i + 1, patch, delay=2.0)
        translated_patches.append(result)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n⏱️  Total execution time: {total_time:.2f}s")
    print(f"📊 Patches processed: {len(translated_patches)}")
    print(f"⚡ Average time per patch: {total_time / len(patches):.2f}s")
    
    return {
        "workflow": "sequential",
        "total_time": total_time,
        "patches": len(translated_patches),
        "avg_time": total_time / len(patches)
    }


def test_parallel_threads(patches: List[Dict[str, str]], max_workers: int = 3) -> Dict:
    """
    Test parallel execution using ThreadPoolExecutor.
    
    Args:
        patches: List of patches to translate
        max_workers: Maximum number of concurrent workers
        
    Returns:
        Dict with results and timing
    """
    print("\n" + "="*80)
    print(f"⚡ PARALLEL WORKFLOW TEST (ThreadPoolExecutor, max_workers={max_workers})")
    print("="*80 + "\n")
    
    start_time = time.time()
    translated_patches = [None] * len(patches)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(fake_translate_patch, i + 1, patch, 2.0): i 
            for i, patch in enumerate(patches)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                translated_patches[index] = result
                print(f"📦 [MAIN] Collected result for patch {index + 1}")
            except Exception as e:
                print(f"❌ [MAIN] Error in patch {index + 1}: {e}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n⏱️  Total execution time: {total_time:.2f}s")
    print(f"📊 Patches processed: {len([p for p in translated_patches if p])}")
    print(f"⚡ Speedup: {(len(patches) * 2.0) / total_time:.2f}x")
    
    return {
        "workflow": f"parallel_threads_{max_workers}",
        "total_time": total_time,
        "patches": len([p for p in translated_patches if p]),
        "speedup": (len(patches) * 2.0) / total_time
    }


async def fake_translate_patch_async(patch_index: int, patch_data: Dict[str, str], delay: float = 2.0) -> Dict:
    """
    Async fake translation function.
    
    Args:
        patch_index: Index của patch
        patch_data: Data cần dịch
        delay: Delay time để simulate API call
        
    Returns:
        Translated patch data
    """
    start_time = datetime.now()
    print(f"🌐 [PATCH_{patch_index}] Starting async translation at {start_time.strftime('%H:%M:%S')}")
    print(f"📝 [PATCH_{patch_index}] Translating {len(patch_data)} entries...")
    
    # Simulate async API call
    actual_delay = delay + random.uniform(-0.5, 0.5)
    await asyncio.sleep(actual_delay)
    
    # Fake translation
    translated = {key: f"[VI] {value}" for key, value in patch_data.items()}
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    print(f"✅ [PATCH_{patch_index}] Completed at {end_time.strftime('%H:%M:%S')} ({execution_time:.2f}s)")
    
    return translated


async def test_parallel_async(patches: List[Dict[str, str]], max_concurrent: int = 3) -> Dict:
    """
    Test parallel execution using asyncio.
    
    Args:
        patches: List of patches to translate
        max_concurrent: Maximum number of concurrent tasks
        
    Returns:
        Dict with results and timing
    """
    print("\n" + "="*80)
    print(f"⚡ PARALLEL WORKFLOW TEST (asyncio, max_concurrent={max_concurrent})")
    print("="*80 + "\n")
    
    start_time = time.time()
    
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def translate_with_semaphore(index: int, patch: Dict[str, str]):
        async with semaphore:
            return await fake_translate_patch_async(index + 1, patch, 2.0)
    
    # Run all tasks
    tasks = [translate_with_semaphore(i, patch) for i, patch in enumerate(patches)]
    translated_patches = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n⏱️  Total execution time: {total_time:.2f}s")
    print(f"📊 Patches processed: {len(translated_patches)}")
    print(f"⚡ Speedup: {(len(patches) * 2.0) / total_time:.2f}x")
    
    return {
        "workflow": f"parallel_async_{max_concurrent}",
        "total_time": total_time,
        "patches": len(translated_patches),
        "speedup": (len(patches) * 2.0) / total_time
    }


def main():
    """Main test function."""
    print("🚀 Parallel Workflow Test")
    print("Testing với fake API calls để verify parallel execution\n")
    
    # Load test data
    test_file = Path("input/NMS_LOC_4_ENGLISH.json")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📂 Loading test data from {test_file}...")
    data = get_json_data(test_file)
    print(f"✅ Loaded {len(data)} entries\n")
    
    # Split into patches (use smaller token limit for testing)
    print("🔪 Splitting into patches (token_limit=25000)...")
    patches = split_into_patches(data, token_limit=25000)
    print(f"✅ Created {len(patches)} patches\n")
    
    # Giới hạn số patches để test nhanh hơn
    max_patches_to_test = 5
    if len(patches) > max_patches_to_test:
        print(f"⚠️  Limiting to {max_patches_to_test} patches for faster testing\n")
        patches = patches[:max_patches_to_test]
    
    results = []
    
    # Test 1: Sequential
    result_seq = test_sequential(patches)
    results.append(result_seq)
    
    # Test 2: Parallel with threads (max 2 workers)
    result_par2 = test_parallel_threads(patches, max_workers=2)
    results.append(result_par2)
    
    # Test 3: Parallel with threads (max 3 workers)
    result_par3 = test_parallel_threads(patches, max_workers=3)
    results.append(result_par3)
    
    # Test 4: Parallel with asyncio (max 3 concurrent)
    result_async = asyncio.run(test_parallel_async(patches, max_concurrent=3))
    results.append(result_async)
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"\nNumber of patches: {len(patches)}")
    print(f"Expected sequential time: ~{len(patches) * 2.0:.1f}s (each patch ~2s)\n")
    
    print("Results:")
    print("-" * 80)
    for result in results:
        workflow = result['workflow']
        total_time = result['total_time']
        speedup = result.get('speedup', 1.0)
        print(f"{workflow:30s}: {total_time:6.2f}s (speedup: {speedup:.2f}x)")
    
    print("\n" + "="*80)
    print("💡 Observations:")
    print("="*80)
    print("1. Sequential: Chạy tuần tự, time = n * 2s")
    print("2. Parallel (threads/async): Chạy song song, time ≈ ceil(n/workers) * 2s")
    print("3. Speedup tối đa = min(n, max_workers)")
    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
