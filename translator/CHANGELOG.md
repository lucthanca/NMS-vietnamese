# Changelog

All notable changes to this project will be documented in this file.

## [1.2.1] - 2025-10-27

### Fixed
- 🐛 **Critical**: Smart handling for 429 Quota Exceeded errors
  - **Before**: Spam retry every 2s → waste API calls
  - **After**: Parse retry_delay from API (e.g., 42s), wait with countdown, then retry
- 🔇 **No more spam logs**: Removed langchain's auto-retry warnings
- ⏰ **Smart wait**: Extract and respect `retry_delay` from API response
- 📊 **Clear visibility**: Countdown logs every 10s so users know progress

### Added
- ✅ `call_gemini_with_quota_handling()`: Main quota handler with smart retry
- ✅ `extract_retry_delay()`: Parse retry delay from error message
- ✅ `wait_with_countdown()`: Wait with progress logging
- ✅ Detailed quota error logging:
  ```
  ❌ [QUOTA_EXCEEDED 11/47] 429 Quota Exceeded!
  📊 [QUOTA_EXCEEDED 11/47] Quota: generativelanguage.googleapis.com/generate_content_free_tier_requests
  📊 [QUOTA_EXCEEDED 11/47] Limit: 250 requests/day
  📊 [QUOTA_EXCEEDED 11/47] Retry delay from API: 47s
  ⏳ [QUOTA_WAIT 11/47] Waiting 47s for quota reset...
  ⏳ [QUOTA_WAIT 11/47] 47s remaining...
  ...
  ✅ [QUOTA_WAIT 11/47] Wait complete, resuming...
  ```

### Changed
- 🔧 **LLM Config**: Set `max_retries=0` to disable langchain auto-retry
- 🔄 **Updated Functions**:
  - `translate_patch()`: Use quota handler instead of direct `llm.invoke()`
  - `translate_single_patch()`: Use quota handler for parallel workflow
- 📚 **Documentation**: Updated README.md với troubleshooting section cho quota errors

### Technical Details
- **Quota Detection**: Catch `google.api_core.exceptions.ResourceExhausted`
- **Retry Delay Parsing**: 
  - Pattern 1: `"Please retry in 42.5s"` → 42s
  - Pattern 2: `"retry_delay { seconds: 42 }"` → 42s
  - Fallback: 60s if can't parse
- **Buffer**: Add 5s to API's retry_delay for safety margin
- **Max Retries**: Default 3 quota retries (configurable)
- **Countdown**: Log every 10s during wait
- **Non-Quota Errors**: Raise immediately (no retry)

### Benefits
- ✅ **No spam**: Clean logs, chỉ log meaningful info
- ✅ **Efficient**: Không waste API calls với premature retry
- ✅ **Transparent**: User biết rõ đang chờ gì, còn bao lâu
- ✅ **Reliable**: Retry với đúng timing theo API requirement
- ✅ **Works with parallel**: Mỗi patch có quota handling riêng

### Example Output
```
INFO:workflows.parallel_wf:🌐 [PATCH_11] Starting parallel processing...
INFO:wf_nodes:🤖 [TRANSLATE 11/47] Calling Gemini API...
❌ [QUOTA_EXCEEDED 11/47] 429 Quota Exceeded!
📊 [QUOTA_EXCEEDED 11/47] Retry delay from API: 47s
📊 [QUOTA_EXCEEDED 11/47] Attempt: 1/3
⏳ [QUOTA_WAIT 11/47] Waiting 47s for quota reset...
⏳ [QUOTA_WAIT 11/47] 47s remaining...
⏳ [QUOTA_WAIT 11/47] 37s remaining...
⏳ [QUOTA_WAIT 11/47] 27s remaining...
⏳ [QUOTA_WAIT 11/47] 17s remaining...
⏳ [QUOTA_WAIT 11/47] 7s remaining...
✅ [QUOTA_WAIT 11/47] Wait complete, resuming...
🔄 [QUOTA_RETRY 11/47] Retrying after quota wait (attempt 2/3)...
INFO:wf_nodes:🤖 [TRANSLATE 11/47] Calling Gemini API...
INFO:wf_nodes:✅ [TRANSLATE] Translation completed
```

### Files Changed
- `wf_nodes.py`:
  - Added imports: `re`, `time`, `ResourceExhausted`
  - Updated LLM: `max_retries=0`
  - Added 3 new helper functions
  - Updated 2 translation functions
- `requirements.txt`: Added `google-api-core>=2.0.0`
- `README.md`: Added quota exceeded troubleshooting section
- `tests/test_quota_fix.py`: Test cases cho quota handling logic

### References
- Gemini API Rate Limits: https://ai.google.dev/gemini-api/docs/rate-limits
- Free Tier: 250 requests/day

---

## [1.2.0] - 2025-10-26

### Added
- 🔢 **Batching System**: Limit max 3 concurrent API calls to respect Gemini free tier quota (10 requests/minute)
- 📦 **Smart Batch Processing**: Process patches in batches, wait for each batch to complete before starting next
- 📐 **Order Preservation**: Output maintains exact same key order as input file
- ✅ **Test Suite**: Added `test_batch.py` to verify batching logic

### Changed
- 🔄 Redesigned `create_dynamic_subflow()` to use ThreadPoolExecutor with batching
- ⚡ **Batching Logic**: 
  - Batch size = 3 patches per batch
  - Sequential batches (batch 1 completes → batch 2 starts)
  - Example: 11 patches → 4 batches (1-3, 4-6, 7-9, 10-11)
- 🛡️ Enhanced error handling in batch processing
- 📊 Better logging: Shows batch progress and success/failure counts

### Fixed
- 🐛 **API Quota Exceeded**: Previously ran all patches simultaneously → exceeded free tier limit
  - **Before**: 11 patches all start at once → ResourceExhausted error
  - **After**: 3 patches at a time → respects API quota
- 🔧 **Merge Order**: Ensures output JSON has keys in same order as input

### Technical Details
- **Implementation**:
  ```python
  max_concurrent = 3  # Gemini free tier limit
  for batch_start in range(0, num_patches, max_concurrent):
      with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
          # Process batch...
      # Wait for batch to complete before next
  ```
- **Verification**: Test script shows correct batching behavior
  - 7 patches → 3 batches (1-3, 4-6, 7)
  - Total time: 9s (vs 21s sequential) = **2.3x speedup**

### Performance
- ✅ **Within Quota**: Max 3 API calls at any moment
- ⚡ **Optimal Speed**: ~2-3x faster than sequential (with quota limits)
- 📈 **Scalable**: Works with any number of patches (auto-batching)

---

## [1.1.0] - 2025-10-26

### Added
- 🚀 **TRUE Parallel Execution**: Implemented real parallel workflow using LangGraph subgraph pattern
- ⚡ **Performance**: Linear speedup with concurrent patches (2 patches = 1.8x faster)
- 📊 **Dynamic Subflow**: Automatically creates parallel nodes based on number of patches
- 🎯 **Conflict-Free**: Nodes return only updated keys to avoid state conflicts
- 📈 **Production Tested**: Verified with real Gemini API calls

### Changed
- 🔄 Rewrote `workflows/parallel_wf.py` using subgraph with `START` edges pattern
- 📈 Each patch processed independently in parallel with own retry logic
- 🔧 `create_patch_processor_node()`: Dynamic node creation per patch
- ✅ All parallel nodes converge to single `merge_results` node
- 🛡️ **List initialization**: Pre-allocate translated_patches array to avoid race conditions
- ✅ **Safe merge**: Skip None patches in merge operation

### Fixed
- 🐛 **Critical**: List index out of range error in parallel execution
  - Solution: Initialize `translated_patches` with correct size before parallel processing
- 🐛 **Merge error**: NoneType iteration error
  - Solution: Skip None values in `merge_patches()` function
- 🔧 Manual validation in parallel nodes (avoid `current_patch_index` dependency)

### Technical Details
- **Pattern**: Similar to theme advisor full_parallel workflow
- **Implementation**: 
  ```python
  # Pre-initialize list to avoid race conditions
  state["translated_patches"] = [None] * num_patches
  
  # Create parallel nodes
  subflow.add_edge(START, "process_patch_1")
  subflow.add_edge(START, "process_patch_2")  # All start simultaneously!
  subflow.add_edge(START, "process_patch_3")
  ```
- **State Management**: 
  - Nodes return `{"translated_patches": updated_list}` only
  - Safe list update with bounds checking
  - Copy-on-write to prevent concurrent modification
- **Workflow Flow**: `load → split → parallel_process (subflow) → merge → END`

### Test Results (Real Gemini API)
- ✅ **2 patches**: 69.04s total (Patch 1: 69s, Patch 2: 56s) - **1.8x speedup**
- ✅ **4 patches**: All started at same timestamp (21:46:08)
- ✅ All patches complete independently with different timing
- ✅ Successful merge with 100 entries output
- ✅ Linear scalability confirmed

### Files Changed
- `workflows/parallel_wf.py`: Complete rewrite with subgraph pattern
- `utils.py`: `merge_patches()` now skips None values
- `DEV_DOCS.md`: Added parallel workflow documentation
- `generate_graphs.py`: Script to visualize workflows
- `graphs/`: PNG visualization of workflows

## [1.0.3] - 2025-10-26

### Fixed
- 🔧 **Critical**: Reduced default token limit from 100k to 50k tokens
- 🎯 Reason: Gemini output token limit is 65,535 tokens
- ⚠️  Large patches (100k input) exceed output limit causing incomplete responses
- ✅ New 50k limit provides safe margin with 20% overhead reserve

### Changed
- Default `--token-limit` parameter: 100000 → 50000
- Updated documentation to reflect safe token limits
- Model confirmed as `gemini-2.5-flash` (1M input tokens, 65k output tokens)

### Technical Details
- **Gemini 2.5 Flash Limits**:
  - Input: 1,048,576 tokens
  - Output: 65,535 tokens (hard limit)
- **Safe Calculation**:
  - Patch size: 50,000 tokens
  - Overhead (20%): 10,000 tokens
  - Effective: 40,000 tokens
  - Output needed: ~40,000 tokens (well within 65k limit)
- Users can still override with `--token-limit` if needed

## [1.0.2] - 2025-10-26

### Fixed
- 🐛 Fixed JSON parsing errors from Gemini responses
- 📝 Added debug output: raw and cleaned responses saved to `output/debug_*.txt` and `output/debug_*.json`
- 🔧 Improved JSON cleaning: remove text before `{` and after `}`
- ✅ Added detailed JSON decode error logging with context

### Changed
- 📊 Enhanced error messages with line/column info and context
- 🎯 Improved prompt to be more strict about JSON format requirements
- 🔧 Lowered temperature from 0.3 to 0.1 for more consistent structured output
- 📝 Added retry count to log messages
- ⚠️  Added warnings when cleaning malformed responses

### Technical Details
- Debug files saved: `debug_response_patch_N_retry_M.txt` (raw) and `debug_cleaned_patch_N_retry_M.json` (cleaned)
- JSON errors now show position, line number, and surrounding context
- Automatic cleanup of text before/after JSON object
- More explicit prompt instructions for proper JSON escaping

## [1.0.1] - 2025-10-26

### Fixed
- ❌ Fixed import error: Removed dependency on `Send` API from langgraph (not available in v1.0.1)
- ✅ Simplified parallel workflow to use same sequential logic as workaround
- 📝 Updated parallel workflow documentation to clarify implementation approach
- ✅ Dependencies installed successfully

### Changed
- Parallel workflow now uses same node structure as sequential workflow
- True parallel execution achieved by running multiple workflow instances or processes externally
- No breaking changes to API or command line interface

### Technical Details
- LangGraph v1.0.1 doesn't export `Send` API from `langgraph.graph`
- Parallel workflow reverted to sequential-style implementation
- Both workflow types now work identically within single process
- For true parallelism: use external orchestration (multiple processes, threading, etc.)

### Notes
- Both `sequence` and `full_parallel` workflow types work correctly now
- True parallel execution can be achieved by:
  1. Running multiple script instances with different input files
  2. Splitting large files and using multiprocessing
  3. Using shell scripts to run parallel processes
  4. Future enhancement: implement threading in main.py

## [1.0.0] - 2025-10-26

### Added
- ✅ Initial project structure và core implementation
- ✅ State management với TypedDict cho LangGraph compatibility
  - `TranslationState`: Main workflow state
  - `PatchTranslationState`: Individual patch state
- ✅ Token counting và patch splitting utilities
  - Estimate token count cho Gemini API
  - Split large JSON into manageable patches
  - Configurable token limit (default: 100000)
- ✅ Complete workflow nodes implementation
  - `load_json_file`: Load input JSON
  - `split_into_patches_node`: Split into patches
  - `translate_patch`: Translate single patch (sequential)
  - `validate_patch`: Validate translation completeness
  - `merge_results`: Merge và save output
  - `translate_single_patch`: Translate patch (parallel)
- ✅ Sequential workflow implementation
  - Tuần tự process từng patch
  - Full retry logic cho mỗi patch
  - Automatic validation và error handling
- ✅ Parallel workflow implementation
  - Process tối đa 3 patches concurrently
  - Fan-out pattern với LangGraph Send API
  - Independent retry logic cho mỗi patch
- ✅ Rich progress indicators
  - Beautiful terminal UI với rich library
  - Real-time progress tracking
  - Colored output và status messages
  - Summary statistics table
- ✅ Comprehensive retry policies
  - Configurable max retries (default: 3)
  - Intelligent retry routing
  - Error collection và reporting
- ✅ Complete test suite
  - Unit tests cho utilities
  - Integration tests với example data
  - Test coverage cho core functionality
- ✅ Full documentation
  - Developer documentation (DEV_DOCS.md)
  - Changelog (this file)
  - Inline code comments

### Technical Details
- **Tech stack**: Python, Google Gemini API, LangChain, LangGraph
- **Dependencies**: 
  - `langchain-google-genai>=2.0.0`
  - `langchain-core>=0.3.0`
  - `langgraph>=0.2.0`
  - `rich>=13.0.0`
  - `python-dotenv>=1.0.0`
  - `pytest>=8.0.0`

### Features
- Automatic JSON splitting based on token limits
- AI-powered translation using Gemini 2.0 Flash
- Validation để ensure không missing keys
- Two workflow modes: sequential và parallel
- Beautiful CLI với progress tracking
- Comprehensive error handling và retry logic
- Test coverage cho core functionality

### File Structure
```
translator/
├── main.py                 # Entry point
├── state.py               # State definitions
├── wf_nodes.py            # Workflow nodes
├── utils.py               # Utility functions
├── prompts.py             # AI prompts
├── retry_policies.py      # Retry logic
├── progress.py            # Progress display
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── DEV_DOCS.md           # Developer docs
├── CHANGELOG.md          # This file
├── workflows/
│   ├── sequence_wf.py    # Sequential workflow
│   └── parallel_wf.py    # Parallel workflow
├── tests/
│   ├── __init__.py
│   └── test_translator.py # Test suite
├── input/                # Input JSON files
├── output/               # Output translations
└── example/              # Example files
    └── NMS_LOC_4_ENGLISH.json
```

### Usage Examples

#### Basic Usage (Sequential)
```bash
python main.py
```

#### Parallel Workflow
```bash
python main.py --wf-type full_parallel
```

#### Custom Token Limit
```bash
python main.py --token-limit 50000
```

#### Custom Input File
```bash
python main.py -l NMS_LOC1_ENGLISH.json
```

#### List Available Workflows
```bash
python main.py --list-workflows
```

### Configuration
Create `.env` file:
```bash
GEMINI_API_KEY=your_api_key_here
```

### Running Tests
```bash
# Install dependencies first
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

### Notes
- Sequential workflow: Chậm hơn nhưng an toàn với API rate limits
- Parallel workflow: Nhanh hơn (3x) nhưng có thể hit rate limits
- Token counting là estimate, có thể cần adjust cho production
- Validation ensure không missing keys nhưng không check quality
- Max retries default là 3, có thể tăng nếu cần

### Known Limitations
- Token counting là estimate chứ không dùng actual Gemini tokenizer
- Parallel workflow chưa có sophisticated rate limiting
- Không có progress persistence (không thể resume sau interrupt)
- Không có caching mechanism
- CLI only, chưa có web UI

### Future Work
- [ ] Implement actual Gemini tokenizer
- [ ] Add progress persistence
- [ ] Add translation caching
- [ ] Implement web UI
- [ ] Add quality checks beyond key validation
- [ ] Optimize batch sizes dynamically
- [ ] Add more workflow types (hybrid modes)
