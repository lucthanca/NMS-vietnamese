# MXML Translator - Hướng dẫn sử dụng

## Chức năng mới: translate-mxml

Script này sẽ dịch file MXML từ tiếng Anh sang tiếng Việt bằng cách:

1. **Đọc template MXML** - File MXML tiếng Anh gốc
2. **Load tất cả JSON** - Đọc tất cả file .json trong thư mục data
3. **Xử lý dịch**:
   - Tìm các node có `_id` trùng với key trong JSON
   - Chuyển giá trị English hiện tại → French (backup)
   - Thay thế English value = giá trị tiếng Việt từ JSON
4. **Ghi file output**:
   - File MXML mới với nội dung đã dịch
   - File JSON chứa các key không tìm thấy trong template

## Cú pháp

```bash
npm start -- --mode translate-mxml --template <template-file> --data-folder <data-folder> --output <output-file> [--not-found <not-found-file>]
```

### Tham số bắt buộc:

- `-m, --mode translate-mxml` : Chế độ dịch MXML
- `-t, --template <file>` : File MXML template (tiếng Anh)
- `-df, --data-folder <folder>` : Thư mục chứa các file JSON dịch
- `-o, --output <file>` : File MXML output (sau khi dịch)

### Tham số tùy chọn:

- `-nf, --not-found <file>` : File JSON lưu các key không dùng (mặc định: `not_found_in_template.json`)

## Ví dụ sử dụng

### Ví dụ 1: Dịch với file example

```bash
npm start -- --mode translate-mxml --template examples/NMS_LOC1_ENGLISH_EXAMPLE.MXML --data-folder data --output output/NMS_LOC1_VIETNAMESE.MXML
```

### Ví dụ 2: Dịch file LOC1 chính thức

```bash
npm start -- --mode translate-mxml --template ../NMS_LOC1_ENGLISH.MXML --data-folder data --output ../NMS_LOC1_VIETNAMESE_NEW.MXML
```

### Ví dụ 3: Dịch với custom not-found output

```bash
npm start -- --mode translate-mxml --template ../NMS_LOC1_ENGLISH.MXML --data-folder data --output ../NMS_LOC1_VIETNAMESE_NEW.MXML --not-found data/unused_keys.json
```

## Workflow thực tế

### Bước 1: Chuẩn bị dữ liệu
- Đặt file MXML tiếng Anh vào thư mục làm việc
- Đảm bảo thư mục `data` chứa các file JSON với bản dịch tiếng Việt

### Bước 2: Chạy script
```bash
cd simpify-loc-mxml
npm run build
npm start -- --mode translate-mxml --template ../NMS_LOC1_ENGLISH.MXML --data-folder data --output ../NMS_LOC1_VIETNAMESE.MXML
```

### Bước 3: Kiểm tra kết quả
- File `NMS_LOC1_VIETNAMESE.MXML` sẽ được tạo với:
  - English value = bản dịch tiếng Việt
  - French value = nội dung tiếng Anh gốc (backup)
- File `not_found_in_template.json` chứa các bản dịch không tìm thấy ID tương ứng

## Cấu trúc file JSON input

```json
{
  "SCAN_NO_TECH": "Chưa cài đặt công nghệ quét <IMG>SLASH<>",
  "SCAN_BROKEN": "Máy quét bị hư hỏng nghiêm trọng <IMG>SLASH<>",
  "SCAN_RECHARGE": "Đang sạc lại máy quét"
}
```

## Cấu trúc file MXML

### Input (template):
```xml
<Property name="Table" value="TkLocalisationEntry" _id="SCAN_NO_TECH">
  <Property name="Id" value="SCAN_NO_TECH" />
  <Property name="English" value="No scan technology installed &lt;IMG&gt;SLASH&lt;&gt;" />
  <Property name="French" value="" />
  ...
</Property>
```

### Output (sau khi dịch):
```xml
<Property name="Table" value="TkLocalisationEntry" _id="SCAN_NO_TECH">
  <Property name="Id" value="SCAN_NO_TECH" />
  <Property name="English" value="Chưa cài đặt công nghệ quét &lt;IMG&gt;SLASH&lt;&gt;" />
  <Property name="French" value="No scan technology installed &lt;IMG&gt;SLASH&lt;&gt;" />
  ...
</Property>
```

## Lưu ý quan trọng

1. **HTML Entities**: Script tự động giữ nguyên các HTML entities như `&lt;`, `&gt;`, `&amp;`
2. **Mã code trong game**: Các mã như `<IMG>SLASH<>`, `%SYSTEM%` được giữ nguyên
3. **Tên khoa học**: Theo hướng dẫn trong `.github/instructions/context.instructions.md`
4. **Backup**: English gốc luôn được lưu vào French để backup

## Thống kê sau khi chạy

Script sẽ hiển thị báo cáo chi tiết:
```
═══════════════════════════════════════
📊 TRANSLATION SUMMARY
═══════════════════════════════════════
Total translations loaded: 1575
Entries processed: 1200
Entries not found in template: 50
Unused translation keys: 375
═══════════════════════════════════════
```

## Xử lý lỗi

- **Template không tồn tại**: Kiểm tra đường dẫn file MXML
- **Data folder không tồn tại**: Kiểm tra đường dẫn thư mục data
- **JSON parse error**: Kiểm tra format của file JSON trong thư mục data
- **Không tìm thấy _id**: Key trong JSON không khớp với ID trong MXML (sẽ được ghi vào not_found.json)
