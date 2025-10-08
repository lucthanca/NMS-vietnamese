# NMS Localization Converter

Script TypeScript để convert các file localization của No Man's Sky giữa định dạng MXML và JSON đơn giản.

## Cài đặt

```bash
cd simpify-loc-mxml
npm install
```

## Cách sử dụng

### 1. Build TypeScript

```bash
npm run build
```

### 2. Convert MXML sang JSON

Convert file MXML thành định dạng JSON đơn giản:

```bash
npm start -- --mode mxml-to-json --input ../NMS_LOC1_ENGLISH_EXAMPLE.MXML --output output.json
```

Hoặc sử dụng short options:

```bash
npm start -- -m mxml-to-json -i ../NMS_LOC1_ENGLISH_EXAMPLE.MXML -o output.json
```

**Output JSON format:**
```json
{
  "SCAN_NO_TECH": "No scan technology installed <IMG>SLASH<>",
  "SCAN_BROKEN": "Scanner is critically damaged <IMG>SLASH<>",
  "SCAN_RECHARGE": "Scanner recharging",
  "WARP_MSG": "Discovered system in %SYSTEM%",
  "DISCOVER_BEACON": "Discovered beacon %BEACON%"
}
```

### 3. Convert JSON sang MXML

Convert file JSON trở lại định dạng MXML:

```bash
npm start -- --mode json-to-mxml --input output.json --output NMS_LOC1_NEW.MXML
```

**Với template file (khuyến nghị):**

Sử dụng template file giúp giữ nguyên cấu trúc và format của file MXML gốc:

```bash
npm start -- --mode json-to-mxml --input output.json --output NMS_LOC1_NEW.MXML --template ../NMS_LOC1_ENGLISH_EXAMPLE.MXML
```

## Options

| Option | Short | Mô tả |
|--------|-------|-------|
| `--mode` | `-m` | Chế độ convert: `mxml-to-json` hoặc `json-to-mxml` |
| `--input` | `-i` | Đường dẫn file input |
| `--output` | `-o` | Đường dẫn file output |
| `--template` | `-t` | (Optional) File MXML template khi convert json-to-mxml |
| `--help` | `-h` | Hiển thị help |

## Ví dụ Workflow

### Workflow dịch thuật:

1. Convert MXML sang JSON để dễ edit:
```bash
npm start -- -m mxml-to-json -i ../NMS_LOC1_ENGLISH.MXML -o loc1_english.json
```

2. Edit file JSON (thêm/sửa/xóa các entry)

3. Convert JSON trở lại MXML:
```bash
npm start -- -m json-to-mxml -i loc1_english.json -o ../NMS_LOC1_VIETNAMESE.MXML -t ../NMS_LOC1_ENGLISH.MXML
```

## Cấu trúc thư mục

```
simpify-loc-mxml/
├── src/
│   ├── converter.ts      # Class xử lý convert MXML ↔ JSON
│   └── index.ts          # CLI interface
├── dist/                 # Compiled JavaScript files
├── package.json
├── tsconfig.json
└── README.md
```

## Development

### Chạy trực tiếp với ts-node (không cần build):

```bash
npm run dev -- -m mxml-to-json -i ../NMS_LOC1_ENGLISH_EXAMPLE.MXML -o test.json
```

### Build lại:

```bash
npm run build
```

## Lưu ý

- File JSON output chứa ID và text tiếng Anh với **HTML entities được giữ nguyên** (ví dụ: `&lt;`, `&gt;`, `&amp;`)
- Khi convert JSON → MXML, các ngôn ngữ khác sẽ để trống (empty string)
- HTML entities sẽ được preserve chính xác giống như file MXML gốc
- Các ký tự đặc biệt trong XML như `<IMG>SLASH<>` sẽ được lưu dưới dạng `&lt;IMG&gt;SLASH&lt;&gt;` trong cả JSON và MXML

## Troubleshooting

### Lỗi "Cannot find module"
```bash
npm install
npm run build
```

### Lỗi file not found
Đảm bảo đường dẫn đến file input chính xác. Sử dụng đường dẫn tương đối từ thư mục `simpify-loc-mxml`.
