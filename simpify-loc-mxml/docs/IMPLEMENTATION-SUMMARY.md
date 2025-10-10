# Tổng Kết Chức Năng Merge JSON

## Mục đích
Script `merge-json` được tạo ra để tự động hóa việc sao chép bản dịch giữa các file JSON có cùng key nhưng khác prefix.

## Các file đã tạo

### 1. `src/merger.ts`
Class `JSONMerger` xử lý logic merge:
- Đọc 2 file JSON (source và target)
- Loại bỏ prefix từ key để so khớp
- Copy giá trị từ source sang target khi tìm thấy khớp
- Giữ nguyên giá trị cũ khi không tìm thấy
- Xuất danh sách các key không tìm thấy

### 2. `src/index.ts` (cập nhật)
CLI interface được mở rộng:
- Thêm mode `merge-json`
- Thêm các tham số mới:
  - `--source-file` / `-sf`: File JSON nguồn
  - `--target-file` / `-tf`: File JSON đích
  - `--source-prefix` / `-sp`: Prefix của file nguồn
  - `--target-prefix` / `-tp`: Prefix của file đích
- Validation và error handling
- Help message được cập nhật

### 3. `merge.js`
Script helper giúp sử dụng nhanh hơn:
```bash
npm run merge -- <source> <target> <output> <src-prefix> <tgt-prefix>
```

### 4. `MERGE-JSON-GUIDE.md`
Hướng dẫn chi tiết cách sử dụng chức năng merge với:
- Giải thích cách hoạt động
- Ví dụ minh họa
- Bảng tham số đầy đủ
- Use cases thực tế

### 5. Files ví dụ
- `file1_example.json` - File nguồn với prefix `BUI_`
- `file2_example.json` - File đích với prefix `TRA_`
- `test_complex_source.json` - Test HTML entities
- `test_complex_target.json` - Test HTML entities

## Tính năng chính

✅ **So khớp thông minh**: Tự động loại bỏ prefix để tìm key tương ứng
✅ **Bảo toàn HTML entities**: Giữ nguyên các ký tự đặc biệt như `&lt;`, `&gt;`, `&amp;`, `&quot;`
✅ **Báo cáo chi tiết**: Xuất danh sách các key không tìm thấy
✅ **Export not found**: Tự động tạo file `*_not_found.json` chứa các key không tìm thấy
✅ **An toàn**: Không ghi đè file gốc, tạo file mới
✅ **Linh hoạt**: Hỗ trợ nhiều cách gọi (full options, short options, quick script)

## Cách sử dụng

### Quick script (Nhanh nhất)
```bash
npm run merge -- source.json target.json output.json "PREFIX1_" "PREFIX2_"
```

### Full command
```bash
npm start -- --mode merge-json \
  --source-file source.json \
  --target-file target.json \
  --output output.json \
  --source-prefix "PREFIX1_" \
  --target-prefix "PREFIX2_"
```

### Short options
```bash
npm start -- -m merge-json -sf source.json -tf target.json -o output.json -sp "PREFIX1_" -tp "PREFIX2_"
```

## Ví dụ thực tế

Giả sử bạn có:
- File `loc_ui_vietnamese.json` với các key `UI_*` đã được dịch
- File `loc_translate_english.json` với các key `TRA_*` chưa dịch

Bạn có thể merge:
```bash
npm run merge -- loc_ui_vietnamese.json loc_translate_english.json loc_translate_vietnamese.json "UI_" "TRA_"
```

## Test cases đã chạy

### Test 1: Basic merge
```bash
npm run merge -- file1_example.json file2_example.json test_merged.json "BUI_" "TRA_"
```
✅ Kết quả: 3/11 keys được merge, 8 keys không tìm thấy
✅ File not found: `test_merged_not_found.json` được tạo tự động

### Test 2: HTML entities preservation
```bash
npm start -- -m merge-json -sf test_complex_source.json -tf test_complex_target.json -o test_complex_result.json -sp "UI_" -tp "MSG_"
```
✅ Kết quả: HTML entities được giữ nguyên hoàn toàn
✅ File not found: `test_complex_result_not_found.json` chứa key chưa tìm thấy

### Test 3: Subdirectory output
```bash
npm run merge -- file1_example.json file2_example.json data/merged_output.json "BUI_" "TRA_"
```
✅ Kết quả: File output tại `data/merged_output.json`
✅ File not found: `data/merged_output_not_found.json` trong cùng thư mục

## Output console

Script xuất thông tin chi tiết:
```
Starting merge process...
Source file: file1.json (prefix: "BUI_")
Target file: file2.json (prefix: "TRA_")
Output: merged.json

📄 Not found keys exported to: merged_not_found.json

✓ Merge completed successfully!
  - Total keys in target: 11
  - Merged from source: 3
  - Not found in source: 8

Keys not found in source file (after removing prefix "TRA_"):
  - TRA_9A (looking for: 9A)
  - TRA_ABANDON (looking for: ABANDON)
  ...
```

## Files được tạo ra

1. **File merged chính**: Chứa tất cả keys với giá trị đã được merge
2. **File not found** (nếu có): `<output>_not_found.json` - Chỉ chứa các keys không tìm thấy để dễ dàng xử lý tiếp

## Lưu ý kỹ thuật

1. **Prefix matching**: Case-sensitive, phải khớp chính xác
2. **JSON format**: Chuẩn JSON format, sử dụng 2 spaces indent
3. **Encoding**: UTF-8
4. **Performance**: Xử lý nhanh với file lớn (O(n) complexity)

## Tương lai

Có thể mở rộng thêm:
- [x] Export not found keys ra file riêng ✓
- [ ] Hỗ trợ regex cho prefix matching
- [ ] Batch merge nhiều file cùng lúc
- [ ] Export report ra file CSV
- [ ] Dry-run mode để preview trước khi merge
- [ ] Interactive mode để chọn file và prefix
- [ ] Merge ngược: lấy file not found đã dịch merge vào file chính
