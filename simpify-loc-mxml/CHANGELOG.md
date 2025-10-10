# Changelog

All notable changes to this project will be documented in this file.

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
