# 🚀 Hướng dẫn nhanh: Dịch MXML

## Chuẩn bị

1. **Build project** (chỉ cần làm 1 lần hoặc khi code thay đổi):
```bash
npm run build
```

2. **Chuẩn bị dữ liệu:**
   - File MXML template (tiếng Anh) - ví dụ: `NMS_LOC1_ENGLISH.MXML`
   - Thư mục `data` chứa các file JSON bản dịch tiếng Việt

## Cách sử dụng nhanh

### Lệnh cơ bản:
```bash
npm start -- -m translate-mxml -t <template> -df <data-folder> -o <output>
```

### Ví dụ 1: Dịch file LOC1
```bash
npm start -- -m translate-mxml -t ../NMS_LOC1_ENGLISH.MXML -df data -o ../NMS_LOC1_VIETNAMESE.MXML
```

### Ví dụ 2: Dịch với file example
```bash
npm start -- -m translate-mxml -t examples/NMS_LOC1_ENGLISH_EXAMPLE.MXML -df data -o output/result.MXML
```

### Ví dụ 3: Chỉ định file not-found
```bash
npm start -- -m translate-mxml -t ../NMS_LOC1_ENGLISH.MXML -df data -o ../NMS_LOC1_VIETNAMESE.MXML -nf data/unused.json
```

## Kết quả

Sau khi chạy xong, bạn sẽ có:

1. **File MXML đã dịch** (output file):
   - English value = Tiếng Việt
   - French value = Tiếng Anh gốc (backup)
   - Các ngôn ngữ khác = rỗng

2. **File not_found_in_template.json**:
   - Chứa các key JSON không tìm thấy trong template
   - Giúp bạn biết key nào chưa được sử dụng

3. **Báo cáo chi tiết** hiển thị trên console:
   ```
   ═══════════════════════════════════════
   📊 TRANSLATION SUMMARY
   ═══════════════════════════════════════
   Total translations loaded: 14066
   Entries processed: 5000
   Entries not found in template: 50
   Unused translation keys: 9016
   ═══════════════════════════════════════
   ```

## Các tham số

| Tham số | Viết tắt | Mô tả | Bắt buộc |
|---------|----------|-------|----------|
| `--mode translate-mxml` | `-m translate-mxml` | Chế độ dịch MXML | ✅ |
| `--template <file>` | `-t <file>` | File MXML template | ✅ |
| `--data-folder <folder>` | `-df <folder>` | Thư mục chứa JSON | ✅ |
| `--output <file>` | `-o <file>` | File MXML output | ✅ |
| `--not-found <file>` | `-nf <file>` | File JSON not found | ❌ |

## Lưu ý quan trọng

✅ **HTML Entities tự động giữ nguyên:**
- `&lt;IMG&gt;SLASH&lt;&gt;` → giữ nguyên
- `&amp;` → giữ nguyên
- Không cần xử lý thủ công

✅ **Mã code game tự động giữ nguyên:**
- `%SYSTEM%`, `%BEACON%`, `%PROCNAME%` → giữ nguyên
- `<IMG>`, `<STELLAR>`, `<TECHNOLOGY>` → giữ nguyên

✅ **Script đọc TẤT CẢ file .json** trong thư mục data:
- Không cần merge thủ công
- Tự động gộp tất cả translations

✅ **Backup tự động:**
- English gốc luôn được lưu vào French
- Không mất dữ liệu gốc

## Troubleshooting

### Lỗi: Template file not found
```
Error: Template file not found: ../NMS_LOC1_ENGLISH.MXML
```
**Giải pháp:** Kiểm tra đường dẫn file template có đúng không.

### Lỗi: Data folder not found
```
Error: Data folder not found: data
```
**Giải pháp:** Đảm bảo thư mục `data` tồn tại và chứa file .json.

### Lỗi: JSON parse error
```
⚠ Failed to load 1-3-23.json: SyntaxError...
```
**Giải pháp:** Kiểm tra file JSON có lỗi cú pháp, sửa hoặc xóa file đó.

### Processed: 0 entries
```
✓ Processed: 0 entries
```
**Nguyên nhân:** Không có ID nào trong JSON khớp với template.

**Giải pháp:** 
- Kiểm tra key trong JSON có đúng format không (ví dụ: `SCAN_NO_TECH`)
- Kiểm tra template có các node `_id` tương ứng không

## Xem thêm

📖 **Hướng dẫn chi tiết:** [TRANSLATE-MXML-GUIDE.md](TRANSLATE-MXML-GUIDE.md)
📖 **README chính:** [../README.md](../README.md)
