# Hướng dẫn sử dụng chức năng Merge JSON

## Mô tả
Chức năng `merge-json` cho phép bạn sao chép nội dung dịch từ file JSON nguồn sang file JSON đích dựa trên việc so khớp key (sau khi loại bỏ prefix).

## Cách hoạt động

### Ví dụ:
**File nguồn** (`file1_example.json` với prefix `BUI_`):
```json
{
  "BUI_A": "một",
  "BUI_ABORT": "hủy",
  "BUI_ABOUT": "về"
}
```

**File đích** (`file2_example.json` với prefix `TRA_`):
```json
{
  "TRA_A": "a",
  "TRA_ABORT": "abort",
  "TRA_ABOUT": "about",
  "TRA_SPECIAL": "special"
}
```

**Kết quả sau khi merge**:
```json
{
  "TRA_A": "một",         // ← Tìm thấy BUI_A, lấy giá trị "một"
  "TRA_ABORT": "hủy",     // ← Tìm thấy BUI_ABORT, lấy giá trị "hủy"
  "TRA_ABOUT": "về",      // ← Tìm thấy BUI_ABOUT, lấy giá trị "về"
  "TRA_SPECIAL": "special" // ← Không tìm thấy BUI_SPECIAL, giữ nguyên giá trị cũ
}
```

**Console output** sẽ hiển thị:
```
📄 Not found keys exported to: merged_result_not_found.json

✓ Merge completed successfully!
  - Total keys in target: 4
  - Merged from source: 3
  - Not found in source: 1

Keys not found in source file (after removing prefix "TRA_"):
  - TRA_SPECIAL (looking for: SPECIAL)
```

**File `merged_result_not_found.json` sẽ chứa:**
```json
{
  "TRA_SPECIAL": "special"
}
```

## Cách sử dụng

### Cú pháp
```bash
npm start -- --mode merge-json \
  --source-file <đường-dẫn-file-nguồn> \
  --target-file <đường-dẫn-file-đích> \
  --output <đường-dẫn-file-kết-quả> \
  --source-prefix <prefix-của-file-nguồn> \
  --target-prefix <prefix-của-file-đích>
```

### Ví dụ cụ thể
```bash
npm start -- --mode merge-json \
  --source-file file1_example.json \
  --target-file file2_example.json \
  --output merged_result.json \
  --source-prefix "BUI_" \
  --target-prefix "TRA_"
```

### Tham số ngắn gọn
```bash
npm start -- -m merge-json \
  -sf file1_example.json \
  -tf file2_example.json \
  -o merged_result.json \
  -sp "BUI_" \
  -tp "TRA_"
```

## Các tham số

| Tham số dài | Tham số ngắn | Bắt buộc | Mô tả |
|------------|-------------|---------|-------|
| `--mode` | `-m` | ✓ | Phải là `merge-json` |
| `--source-file` | `-sf` | ✓ | File JSON chứa bản dịch gốc |
| `--target-file` | `-tf` | ✓ | File JSON cần được cập nhật |
| `--output` | `-o` | ✓ | File kết quả sau khi merge |
| `--source-prefix` | `-sp` | ✓ | Prefix của các key trong file nguồn (ví dụ: "BUI_") |
| `--target-prefix` | `-tp` | ✓ | Prefix của các key trong file đích (ví dụ: "TRA_") |

## Output

Script sẽ tạo ra:
1. **File kết quả** tại đường dẫn `--output` với nội dung đã được merge
2. **File not found** (nếu có): `<output>_not_found.json` chứa các key không tìm thấy
   - Ví dụ: nếu output là `merged.json`, file not found sẽ là `merged_not_found.json`
   - Nếu output là `data/result.json`, file not found sẽ là `data/result_not_found.json`
3. **Thông tin console**:
   - Tổng số key trong file đích
   - Số key đã được merge thành công
   - Số key không tìm thấy trong file nguồn
   - Danh sách chi tiết các key không tìm thấy

## Lưu ý quan trọng

1. **Prefix phải chính xác**: Prefix phải khớp với phần đầu của key trong file tương ứng
2. **Giữ nguyên structure**: File kết quả sẽ giữ nguyên thứ tự key từ file đích
3. **Không tìm thấy = giữ nguyên**: Các key không tìm thấy sẽ giữ nguyên giá trị cũ từ file đích
4. **HTML Entities được bảo toàn**: Các HTML entities (như `&amp;`, `&lt;`, v.v.) sẽ được giữ nguyên
5. **File not found tự động**: Các key không tìm thấy sẽ được export tự động ra file `*_not_found.json`

## Use Case thực tế

Khi bạn có nhiều file localization với các prefix khác nhau:
- `BUI_*` - UI elements
- `TRA_*` - Translations
- `MSG_*` - Messages
- v.v.

Và bạn đã dịch một số prefix, bây giờ muốn áp dụng bản dịch đó cho các prefix khác có cùng key (không tính prefix), tool này sẽ giúp bạn tự động hóa quá trình đó.

### Workflow với file not found

1. Chạy merge lần đầu để có bản dịch tự động
2. Script tự động tạo file `*_not_found.json` chứa các key chưa tìm thấy
3. Bạn có thể:
   - Dịch thủ công các key trong file `*_not_found.json`
   - Hoặc tìm từ nguồn khác để merge tiếp
4. Merge file `*_not_found.json` đã dịch vào file chính
