# AI Agent Vietnamese Translator for No Man's Sky

AI-powered translation tool sử dụng Google Gemini API để dịch JSON localization files từ English sang Vietnamese.

## Quick Start

### 1. Setup Environment

```bash
# Clone hoặc navigate vào thư mục translator
cd translator

# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Activate venv
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# Cài dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Tạo file `.env` từ template:
```bash
cp .env.example .env
```

Thêm Gemini API key vào `.env`:
```
GEMINI_API_KEY=your_api_key_here
```

### 3. Prepare Input File

Đặt file JSON cần dịch vào thư mục `input/`:
```
input/
  └── NMS_LOC_4_ENGLISH.json
```

### 4. Run Translation

#### Sequential Mode (Recommended for first use)
```bash
python main.py
```

#### Parallel Mode (Faster, 3x concurrent)
```bash
python main.py --wf-type full_parallel
```

#### Custom Options
```bash
python main.py -l YOUR_FILE.json --token-limit 50000 --max-retries 5
```

### 5. Get Output

Translated file sẽ xuất hiện trong thư mục `output/`:
```
output/
  └── NMS_LOC_4_VIETNAMESE.json
```

## Command Line Options

```bash
python main.py --help
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--wf-type` | `-wt` | `sequence` | Workflow type: `sequence` hoặc `full_parallel` |
| `--loc-filename` | `-l` | `NMS_LOC_4_ENGLISH.json` | Input filename |
| `--token-limit` | `-tl` | `100000` | Token limit per patch |
| `--max-retries` | `-mr` | `3` | Maximum retry attempts |
| `--list-workflows` | | | List available workflows |

## Workflows

### Sequential Workflow
- ✅ Chạy tuần tự từng patch
- ✅ An toàn với API rate limits  
- ⏱️ Chậm hơn nhưng ổn định

### Parallel Workflow
- ✅ Chạy 3 patches song song
- ✅ Nhanh hơn ~3x
- ⚠️ Có thể hit API rate limits

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Project Structure

```
translator/
├── main.py              # Entry point
├── state.py            # State management
├── wf_nodes.py         # Workflow nodes
├── utils.py            # Utilities
├── progress.py         # Progress display
├── workflows/          # Workflow definitions
├── tests/              # Test suite
├── input/              # Input files (place here)
├── output/             # Output files (generated)
└── example/            # Example files
```

## Documentation

- 📖 **Developer Docs**: [`DEV_DOCS.md`](DEV_DOCS.md) - Chi tiết về architecture, development workflow
- 📝 **Changelog**: [`CHANGELOG.md`](CHANGELOG.md) - Version history và changes

## Troubleshooting

### Import errors
```bash
pip install -r requirements.txt
```

### API Key errors
- Check `.env` file exists
- Verify API key is correct
- Ensure API key has quota

### 429 Quota Exceeded (NEW!)

Khi thấy lỗi quota exceeded, script sẽ **tự động xử lý**:

```
❌ [QUOTA_EXCEEDED 11/47] 429 Quota Exceeded!
📊 [QUOTA_EXCEEDED 11/47] Limit: 250 requests/day
📊 [QUOTA_EXCEEDED 11/47] Retry delay from API: 47s
⏳ [QUOTA_WAIT 11/47] Waiting 47s for quota reset...
⏳ [QUOTA_WAIT 11/47] 47s remaining...
⏳ [QUOTA_WAIT 11/47] 37s remaining...
...
✅ [QUOTA_WAIT 11/47] Wait complete, resuming...
```

**Hành động:**
- ✅ Script tự động chờ theo thời gian API yêu cầu (e.g., 42s + 5s buffer)
- ✅ Log countdown mỗi 10s để theo dõi
- ✅ Tự động retry sau khi quota reset
- ✅ Max 3 lần retry cho quota errors

**Nếu cần:**
- 🔄 Switch API key khác (update `.env`)
- 💳 Upgrade Gemini plan tại: https://ai.google.dev/pricing
- ⏰ Chờ sang ngày mới (free tier: 250 requests/day)

### Token limit too small
```bash
python main.py --token-limit 200000
```

### Rate limit errors (parallel mode)
- Switch to sequential mode
- Reduce patches by increasing token limit
- Script tự động handle quota với countdown

## Tech Stack

- **Python 3.10+**
- **Google Gemini API** (gemini-2.0-flash-exp)
- **LangChain** - LLM framework
- **LangGraph** - Workflow orchestration
- **Rich** - Terminal UI

## License

This project is for No Man's Sky Vietnamese translation community.
