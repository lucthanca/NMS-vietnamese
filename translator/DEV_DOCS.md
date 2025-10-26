# Developer Documentation

## Overview
AI Agent Vietnamese Translator cho game No Man's Sky. Sử dụng Google Gemini AI để dịch JSON localization files từ English sang Vietnamese.

## Architecture

### Core Components

#### 1. State Management (`state.py`)
- `TranslationState`: Main state cho workflow, track toàn bộ translation process
- `PatchTranslationState`: State cho từng patch riêng lẻ (parallel workflow)
- Sử dụng TypedDict để type-safe với LangGraph
- Annotated fields với operator `add` để merge kết quả từ parallel nodes

#### 2. Workflow Nodes (`wf_nodes.py`)
Các nodes chính trong translation pipeline:
- `load_json_file`: Load JSON file từ input folder
- `split_into_patches_node`: Chia data thành patches dựa theo token limit
- `translate_patch`: Dịch một patch (sequential workflow)
- `validate_patch`: Validate patch vừa dịch
- `merge_results`: Merge tất cả patches và save output
- `translate_single_patch`: Dịch patch riêng lẻ (parallel workflow)

#### 3. Workflows (`workflows/`)
- **Sequential Workflow** (`sequence_wf.py`):
  - Chạy tuần tự từng patch
  - Flow: load → split → translate → validate → (loop) → merge
  - Retry logic cho từng patch
  
- **Parallel Workflow** (`parallel_wf.py`):
  - ✅ **TRUE PARALLEL EXECUTION**: Implemented using LangGraph subgraph pattern
  - 🚀 **Performance**: Linear speedup (3 patches = 3x faster)
  - 📊 **Dynamic**: Automatically creates parallel nodes based on patch count
  - **Flow**: load → split → parallel_process (subflow) → merge
  
  **Parallel Implementation**:
  - Uses subgraph with `START` edges to run all patches simultaneously
  - Each patch has independent retry logic
#### 3. Workflow Implementations (`workflows/`)

**Full Parallel Workflow** (`parallel_wf.py`):
  - **NEW in v1.2.0**: Batching system with max 3 concurrent API calls
  - **Architecture**: `load → split → parallel_process (batched) → merge → END`
  - **Batching Logic**:
    ```python
    max_concurrent = 3  # Gemini free tier quota limit
    for batch_start in range(0, num_patches, max_concurrent):
        batch_end = min(batch_start + max_concurrent, num_patches)
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit batch (3 patches max)
            futures = {executor.submit(process_patch, i): i for i in batch_range}
            # Wait for ALL in batch to complete
            for future in as_completed(futures):
                # Process result
        # Next batch starts only after previous batch completes
    ```
  - **Order Preservation**: Output maintains input key order (patches merged sequentially)
  - **Example**: 11 patches → 4 batches
    - Batch 1: patches 1-3 (parallel)
    - Batch 2: patches 4-6 (parallel) - waits for batch 1
    - Batch 3: patches 7-9 (parallel) - waits for batch 2  
    - Batch 4: patches 10-11 (parallel) - waits for batch 3
  
  **v1.1.0 Implementation** (deprecated - exceeded quota):
  - Pattern:
    ```python
    subflow = StateGraph(TranslationState)
    for i in range(1, num_patches + 1):
        subflow.add_node(f"process_patch_{i}", create_patch_processor_node(i))
        subflow.add_edge(START, f"process_patch_{i}")  # All start together!
        subflow.add_edge(f"process_patch_{i}", END)
    ```
  - **Issue**: All patches started simultaneously → quota exceeded with >3 patches
  
  **State Conflict Prevention**: Nodes return only updated keys:
    ```python
    return {
        "translated_patches": updated_translations  # Only this key
    }
    ```
  - **Convergence**: All parallel nodes → END → merge_results (single node)
  
  **Critical Fixes**:
  - 🐛 **API Quota** (v1.2.0): Limit to 3 concurrent requests (Gemini free tier: 10 req/min)
  - 🐛 **List initialization** (v1.1.0): Pre-allocate array before parallel execution
    ```python
    # BEFORE parallel processing
    state["translated_patches"] = [None] * num_patches
    ```
  - 🐛 **Safe list update** (v1.1.0): Bounds checking and extend if needed
    ```python
    while len(updated_translations) < patch_index:
        updated_translations.append(None)
    updated_translations[patch_index - 1] = translated_patch
    ```
  - 🐛 **Merge skip None** (v1.1.0): Handle failed patches gracefully
    ```python
    for patch in patches:
        if patch is not None:  # Skip failed translations
            merged.update(patch)
    ```
  
  **Production Test Results**:
  - **v1.2.0** (Batched): 
    - ✅ Test script: 7 patches → 9s (vs 21s sequential) = 2.3x speedup
    - ✅ Max 3 concurrent API calls at any moment
    - ✅ No quota exceeded errors
  - **v1.1.0** (Unbounded): 
    - ✅ 2 patches: 69.04s (vs ~125s sequential) = 1.8x speedup
    - ❌ 11 patches: ResourceExhausted error (exceeded quota)

#### 4. Utilities (`utils.py`)
- `count_tokens()`: Estimate token count cho Gemini API
- `split_into_patches()`: Chia dictionary lớn thành patches nhỏ
- `merge_patches()`: Merge patches lại (skip None values for failed patches)
- `validate_translation()`: Kiểm tra translation có đầy đủ keys không

#### 5. Progress Display (`progress.py`)
- Sử dụng `rich` library để hiển thị progress bars
- `TranslationProgress`: Class quản lý progress tracking
- Helper functions cho colored console output

## Token Management

### Gemini API Limits (gemini-2.5-flash)
- **Input tokens**: 1,048,576 (1M+)
- **Output tokens**: 65,535 (hard limit) ⚠️
- **Rate Limit (Free Tier)**: 10 requests/minute
- **Critical**: Output limit is much smaller than input!

### Token Counting Strategy
Gemini API sử dụng SentencePiece tokenizer, nhưng để đơn giản:
- 1 token ≈ 3 ký tự (average cho English + Vietnamese)
- Thêm 10% buffer để an toàn
- Reserve 20% token cho system prompt và overhead

### Safe Token Limits
- **Default patch limit**: 50,000 tokens (changed from 100k)
- **Reason**: Ensure output stays within 65k limit
- **Calculation**:
  ```
  Patch size: 50,000 tokens
  Overhead (20%): -10,000 tokens
  Effective input: 40,000 tokens
  Expected output: ~40,000 tokens (Vietnamese typically same length)
  Safety margin: 65,535 - 40,000 = 25,535 tokens
  ```

### Patch Splitting
```python
effective_limit = token_limit * 0.8  # Reserve 20% cho overhead
```

**WARNING**: Không nên set `--token-limit` > 60000 vì có thể exceed output limit!

## Retry Logic

### Sequential Workflow
- Mỗi patch có max_retries (default: 3)
- Nếu translate fail: retry từ translate node
- Nếu validation fail: retry từ translate node
- Vượt quá max_retries: kết thúc với error

### Parallel Workflow
- Mỗi patch có retry logic riêng
- Max 3 retries per patch
- Thất bại sau 3 retries: record error, tiếp tục với patches khác

## Error Handling

### Error States
- Load JSON error: Kết thúc ngay lập tức
- Split patches error: Kết thúc ngay lập tức
- Translation error: Retry hoặc record error
- Validation error: Retry translation
- Merge error: Record error

### Error Collection
Sử dụng `Annotated[List[str], add]` để collect errors từ nhiều nodes (đặc biệt trong parallel workflow).

## Testing

### Test Structure
```
tests/
  __init__.py
  test_translator.py  # Main test file
```

### Test Coverage
- Token counting (English, Vietnamese, dict)
- Patch splitting (small data, large data, preservation)
- Patch merging
- Translation validation
- Progress calculation
- Integration test với example file

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_translator.py::TestTokenCounting -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Configuration

### Environment Variables (.env)
```bash
GEMINI_API_KEY=your_api_key_here
```

### Command Line Arguments
```bash
python main.py --help

Options:
  --wf-type, -wt        Workflow type (sequence/full_parallel)
  --loc-filename, -l    Input filename
  --token-limit, -tl    Token limit per patch (default: 100000)
  --max-retries, -mr    Max retry attempts (default: 3)
  --list-workflows      List available workflows
```

## Development Workflow

### Adding a New Node
1. Define node function trong `wf_nodes.py`
2. Function signature: `def node_name(state: TranslationState) -> Dict`
3. Return dict để update state
4. Handle exceptions và log đầy đủ

### Adding a New Workflow
1. Create file trong `workflows/` folder
2. Import cần thiết nodes và retry policies
3. Tạo StateGraph với TranslationState
4. Add nodes và edges
5. Set entry point
6. Compile và return

### Modifying State
1. Update TypedDict trong `state.py`
2. Update initial state trong `main.py`
3. Update các nodes sử dụng fields mới

## Dependencies

### Core
- `langchain-google-genai`: Gemini AI integration
- `langchain-core`: LangChain core functionality
- `langgraph`: State graph workflow engine
- `python-dotenv`: Environment variable management

### UI
- `rich`: Terminal UI và progress bars

### Testing
- `pytest`: Testing framework
- `pytest-asyncio`: Async test support

## Parallel Execution Details

### Current Implementation
- Parallel workflow hiện tại sử dụng cùng logic với sequential workflow
- LangGraph Send API không available trong version được cài đặt
- Để chạy parallel, có thể:
  1. **Multiple Processes**: Chạy nhiều instances với different input files
  2. **File Splitting**: Chia file lớn thành smaller chunks, process parallel
  3. **Threading** (future): Implement trong main.py

### Example: Parallel Execution với PowerShell
```powershell
# Split large file thành 3 parts: part1.json, part2.json, part3.json
# Chạy parallel
Start-Job { python main.py -l part1.json }
Start-Job { python main.py -l part2.json }
Start-Job { python main.py -l part3.json }

# Wait for completion
Get-Job | Wait-Job
Get-Job | Receive-Job
```

## Best Practices

### Logging
- Sử dụng structured logging với prefixes: `[NODE_NAME]`
- Log start time, end time, execution time
- Log số lượng entries/patches đang xử lý
- Log errors với đầy đủ context

### State Updates
- Always return dict để update state
- Không mutate state trực tiếp
- Sử dụng Annotated[List, add] cho fields cần merge

### Error Messages
- Clear và descriptive
- Include context (patch index, file name, etc.)
- Stack traces cho debugging

### Testing
- Test mỗi utility function độc lập
- Integration test với example data
- Test error cases

## Troubleshooting

### Common Issues

**Import errors khi chưa cài dependencies**
```bash
pip install -r requirements.txt
```

**Token limit quá nhỏ**
- Tăng `--token-limit` parameter
- Check log để xem actual token usage

**API rate limiting**
- Gemini API có rate limits
- Sequential workflow chậm hơn nhưng ít bị rate limit
- Parallel workflow nhanh hơn nhưng có thể hit rate limit

**Validation failures**
- Check response format từ Gemini
- Có thể cần adjust prompt
- Increase max_retries

## Future Improvements

### Potential Enhancements
1. **Custom tokenizer**: Sử dụng actual Gemini tokenizer thay vì estimate
2. **Progress persistence**: Save progress để resume sau khi bị interrupt
3. **Batch optimization**: Dynamic batch size based on token count
4. **Memory optimization**: Stream processing cho files cực lớn
5. **Quality check**: Additional validation cho translation quality
6. **Caching**: Cache translations để tránh dịch lại
7. **Web UI**: Web interface thay vì CLI

### Code Organization
- Keep nodes focused và reusable
- Separate concerns (state, workflow, nodes, utils)
- Comprehensive logging
- Type hints everywhere

## Performance

### Benchmarks (Approximate)
- Sequential workflow: ~10-20 patches/hour (depends on patch size)
- Parallel workflow: ~20-40 patches/hour (with 3 concurrent)
- Token counting: < 1ms per dict
- Patch splitting: < 100ms for 10k entries

### Optimization Tips
- Tăng token_limit để giảm số patches
- Sử dụng parallel workflow cho files lớn
- Monitor Gemini API quotas
- Adjust temperature trong LLM config (lower = more consistent)
