"""Test batching logic với fake delays"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def fake_translate(patch_index: int) -> dict:
    """Fake translation with delay"""
    print(f"🌐 [PATCH_{patch_index}] Starting at {time.strftime('%H:%M:%S')}")
    time.sleep(3)  # Simulate API call
    print(f"✅ [PATCH_{patch_index}] Completed at {time.strftime('%H:%M:%S')}")
    return {
        "patch_index": patch_index,
        "data": f"Translated patch {patch_index}"
    }

def test_batching():
    """Test batching với max 3 concurrent"""
    num_patches = 7
    max_concurrent = 3
    results = [None] * num_patches
    
    print(f"🚀 Processing {num_patches} patches with max {max_concurrent} concurrent\n")
    
    for batch_start in range(0, num_patches, max_concurrent):
        batch_end = min(batch_start + max_concurrent, num_patches)
        batch_indices = range(batch_start + 1, batch_end + 1)  # 1-based
        
        print(f"📦 Batch: patches {batch_start + 1}-{batch_end}")
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_index = {
                executor.submit(fake_translate, i): i
                for i in batch_indices
            }
            
            for future in as_completed(future_to_index):
                patch_index = future_to_index[future]
                result = future.result()
                results[patch_index - 1] = result
                print(f"   ✅ Patch {patch_index} done")
        
        print(f"✅ Batch complete!\n")
    
    print(f"🎉 All done! Results: {len([r for r in results if r is not None])}/{num_patches}")

if __name__ == "__main__":
    start = time.time()
    test_batching()
    print(f"\n⏱️  Total time: {time.time() - start:.2f}s")
