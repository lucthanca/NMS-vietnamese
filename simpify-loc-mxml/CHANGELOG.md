# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2025-10-11

### Added ⭐
- **Translate MXML Mode**: Tính năng mới dịch file MXML từ tiếng Anh sang tiếng Việt
  - Đọc tất cả file JSON trong thư mục data (auto-load)
  - Tìm kiếm và ánh xạ theo `_id` trong MXML với key trong JSON
  - Chuyển English value hiện tại → French (backup original)
  - Thay thế English value = bản dịch tiếng Việt từ JSON
  - Export file JSON chứa các key không tìm thấy trong template
  - Báo cáo chi tiết: processed, not found, unused keys
- CLI Options cho translate-mxml:
  - `--template` / `-t`: Template MXML file (required)
  - `--data-folder` / `-df`: Folder chứa JSON translations (required)
  - `--not-found` / `-nf`: Output file cho unused keys (optional)
- Documentation:
  - `TRANSLATE-MXML-GUIDE.md`: Hướng dẫn chi tiết đầy đủ
  - `QUICK-START-TRANSLATE.md`: Hướng dẫn nhanh bằng tiếng Việt
- Test Files:
  - `tests/test_translation.json`: Sample translation data
  - `tests/test_data/`: Test data folder
  - `tests/NMS_LOC1_VIETNAMESE_TEST.MXML`: Test output

### Changed
- Updated `README.md`: Thêm section "Translate MXML với JSON data"
- Updated `package.json`: Thêm script shortcut `translate`
- Updated help message: Thêm hướng dẫn cho translate-mxml mode

### Technical
- New file: `src/translator.ts` - MXMLTranslator class
  - Method: `loadAllJsonData()` - Load all JSON from folder
  - Method: `translate()` - Main translation logic
  - Smart regex matching preserving HTML entities
  - French backup mechanism
- Updated: `src/index.ts` - Extended CLI with translate-mxml mode
  - New mode validation
  - New argument parsing for translate options
  - Integration with MXMLTranslator class

### Features Details
- **Auto-load JSON**: Tự động đọc tất cả file `.json` trong folder, không cần merge thủ công
- **HTML Entities Safe**: Giữ nguyên `&lt;`, `&gt;`, `&amp;` và các entities khác
- **Game Code Preservation**: Giữ nguyên các mã như `%SYSTEM%`, `<IMG>`, etc.
- **Backup Original**: English gốc luôn được backup vào French field
- **Not Found Tracking**: Track và export các translation keys không được sử dụng
- **Detailed Reporting**: Console output với emoji và thống kê chi tiết

## [1.1.0] - 2025-10-10

### Added
- **Export Not Found Keys**: Tự động tạo file `*_not_found.json` chứa các keys không tìm thấy trong quá trình merge
  - File chỉ được tạo khi có ít nhất 1 key không tìm thấy
  - Tên file theo format: `<output_name>_not_found.<ext>`
  - Giữ nguyên đường dẫn thư mục của file output
- Documentation: Thêm `FEATURE-NOT-FOUND-EXPORT.md` giải thích chi tiết tính năng mới
- Demo: Thêm `DEMO-WORKFLOW.md` minh họa workflow sử dụng
- Quick Reference: Thêm `QUICK-REFERENCE.md` cho tra cứu nhanh

### Changed
- Console output: Hiển thị emoji 📄 khi export not found file
- Documentation: Cập nhật tất cả guides với thông tin về file not found

### Technical
- Updated `src/merger.ts`: Logic export not found keys
- All tests passed including:
  - Basic merge with not found keys
  - Perfect match (no not found)
  - Subdirectory output paths
  - HTML entities preservation

## [1.0.0] - 2025-10-10

### Added
- **Merge JSON Mode**: Chức năng merge translations giữa 2 file JSON dựa trên prefix
  - Support cho prefix matching thông minh
  - Bảo toàn HTML entities
  - Báo cáo chi tiết keys không tìm thấy
- CLI Options:
  - `--source-file` / `-sf`: Source JSON file
  - `--target-file` / `-tf`: Target JSON file  
  - `--source-prefix` / `-sp`: Source key prefix
  - `--target-prefix` / `-tp`: Target key prefix
- Quick Script: `npm run merge` cho cú pháp ngắn gọn
- Documentation:
  - `MERGE-JSON-GUIDE.md`: Hướng dẫn chi tiết
  - `IMPLEMENTATION-SUMMARY.md`: Tổng kết kỹ thuật
- Test Files:
  - `file1_example.json` & `file2_example.json`
  - `test_complex_*.json` cho HTML entities test

### Technical
- New file: `src/merger.ts` - JSONMerger class
- Updated: `src/index.ts` - Extended CLI with merge-json mode
- New file: `merge.js` - Quick helper script
- Updated: `package.json` - Added "merge" script

## [0.1.0] - Initial Release

### Added
- MXML to JSON conversion
- JSON to MXML conversion
- HTML entities preservation
- Template support for MXML generation
- CLI interface with full and short options
- Basic documentation
