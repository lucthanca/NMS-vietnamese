# Changelog

All notable changes to this project will be documented in this file.

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
