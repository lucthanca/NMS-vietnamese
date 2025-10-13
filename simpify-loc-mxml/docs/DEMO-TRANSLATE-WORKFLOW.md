# Demo Workflow: Dịch file MXML từ A-Z

Hướng dẫn thực tế từng bước để dịch file localization No Man's Sky.

## Tình huống thực tế

Bạn có:
- ✅ File `NMS_LOC1_ENGLISH.MXML` (13,000 entries tiếng Anh)
- ✅ Thư mục `data` với 28 file JSON (14,066 bản dịch tiếng Việt)
- 🎯 Mục tiêu: Tạo file `NMS_LOC1_VIETNAMESE.MXML` hoàn chỉnh

## Bước 1: Cài đặt và Build

```bash
# Di chuyển vào thư mục project
cd simpify-loc-mxml

# Cài đặt dependencies
npm install

# Build TypeScript
npm run build
```

**Kết quả:**
```
> nms-loc-converter@1.0.0 build
> tsc

✓ Build thành công!
```

## Bước 2: Kiểm tra dữ liệu

### Kiểm tra template MXML
```bash
# Xem 10 dòng đầu của template
head -n 10 ../NMS_LOC1_ENGLISH.MXML
```

**Kết quả mẫu:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<Data template="cTkLocalisationTable">
  <Property name="Table">
    <Property name="Table" value="TkLocalisationEntry" _id="SCAN_NO_TECH">
      <Property name="English" value="No scan technology installed" />
      ...
```

### Kiểm tra JSON data
```bash
# Đếm số file JSON
ls data/*.json | wc -l

# Xem nội dung file đầu tiên
cat data/1-2-1.json | head -n 20
```

**Kết quả mẫu:**
```json
{
  "WARN_TECH_DAMAGED": "Công nghệ này bị hư hại nghiêm trọng",
  "TELEPORT_VERB": "TELEPORT",
  "OPTS_REVERT_TO_CURRENT": "Tải lại hiện tại [ %TIMESTAMP% ]",
  ...
}
```

## Bước 3: Chạy translation

```bash
npm start -- --mode translate-mxml \
  --template ../NMS_LOC1_ENGLISH.MXML \
  --data-folder data \
  --output ../NMS_LOC1_VIETNAMESE.MXML
```

**Hoặc dùng short options:**
```bash
npm start -- -m translate-mxml -t ../NMS_LOC1_ENGLISH.MXML -df data -o ../NMS_LOC1_VIETNAMESE.MXML
```

## Bước 4: Xem output trong quá trình chạy

Script sẽ hiển thị progress:

```
🚀 Starting translation process...

📂 Found 28 JSON files in data
  ✓ Loaded 1-2-1.json: 1573 entries
  ✓ Loaded 1-2-2.json: 499 entries
  ✓ Loaded 1-2-3.json: 427 entries
  ✓ Loaded 1-3-1.json: 99 entries
  ✓ Loaded 1-3-2.json: 99 entries
  ... (23 files more)
  ⚠ Failed to load 1-3-23.json: SyntaxError...
  ✓ Loaded 1-3-25.json: 109 entries

📊 Total loaded entries: 14066

📖 Reading template MXML...
  ✓ Template loaded

🔄 Processing translations...
  ✓ Processed: 12500 entries
  ℹ Not found: 500 entries

💾 Writing output MXML...
  ✓ Output saved: ../NMS_LOC1_VIETNAMESE.MXML

📝 Writing unused translation keys...
  ✓ Unused keys saved: ../not_found_in_template.json
  ℹ Total unused: 1566 entries

═══════════════════════════════════════
📊 TRANSLATION SUMMARY
═══════════════════════════════════════
Total translations loaded: 14066
Entries processed: 12500
Entries not found in template: 500
Unused translation keys: 1566
═══════════════════════════════════════

✅ Translation completed successfully!
```

## Bước 5: Kiểm tra kết quả

### Kiểm tra file MXML output

```bash
# Xem một entry đã dịch
grep -A 20 'SCAN_NO_TECH' ../NMS_LOC1_VIETNAMESE.MXML
```

**Kết quả:**
```xml
<Property name="Table" value="TkLocalisationEntry" _id="SCAN_NO_TECH">
  <Property name="Id" value="SCAN_NO_TECH" />
  <Property name="English" value="Chưa cài đặt công nghệ quét" />
  <Property name="French" value="No scan technology installed" />
  <Property name="Italian" value="" />
  ...
</Property>
```

**Nhận xét:**
- ✅ English = Tiếng Việt (đã dịch)
- ✅ French = Tiếng Anh gốc (backup)
- ✅ HTML entities được giữ nguyên

### Kiểm tra file not found

```bash
# Xem các key chưa dùng
cat ../not_found_in_template.json | jq 'keys | length'
```

**Kết quả:** `1566` - Có 1566 keys trong JSON nhưng không có trong template

```bash
# Xem 5 keys đầu tiên
cat ../not_found_in_template.json | jq 'keys[:5]'
```

**Kết quả mẫu:**
```json
[
  "NEW_FEATURE_KEY_1",
  "NEW_FEATURE_KEY_2",
  "UNUSED_OLD_KEY",
  "DEBUG_STRING",
  "TEST_VALUE"
]
```

## Bước 6: Xử lý các trường hợp đặc biệt

### Case 1: File JSON có lỗi syntax

**Triệu chứng:**
```
⚠ Failed to load 1-3-23.json: SyntaxError: Expected ',' or '}' after property value
```

**Giải pháp:**
```bash
# Mở file và fix lỗi
code data/1-3-23.json

# Hoặc xóa file nếu không cần
rm data/1-3-23.json

# Chạy lại
npm start -- -m translate-mxml -t ../NMS_LOC1_ENGLISH.MXML -df data -o ../NMS_LOC1_VIETNAMESE.MXML
```

### Case 2: Cần custom not-found output path

```bash
npm start -- -m translate-mxml \
  -t ../NMS_LOC1_ENGLISH.MXML \
  -df data \
  -o ../NMS_LOC1_VIETNAMESE.MXML \
  -nf data/unused_translations.json
```

### Case 3: Test với file nhỏ trước

```bash
# Tạo test data folder
mkdir tests/test_data

# Copy vài file JSON vào
cp data/1-2-1.json tests/test_data/
cp data/1-2-2.json tests/test_data/

# Test với example file
npm start -- -m translate-mxml \
  -t examples/NMS_LOC1_ENGLISH_EXAMPLE.MXML \
  -df tests/test_data \
  -o tests/output_test.MXML
```

## Bước 7: Kiểm tra chất lượng dịch

### So sánh trước và sau

**Terminal 1 - File gốc:**
```bash
grep -A 5 'SCAN_NO_TECH' ../NMS_LOC1_ENGLISH.MXML
```

**Terminal 2 - File đã dịch:**
```bash
grep -A 5 'SCAN_NO_TECH' ../NMS_LOC1_VIETNAMESE.MXML
```

### Đếm số entries đã dịch

```bash
# Đếm entries có French value (= đã dịch)
grep -c 'Property name="French" value="[^"]' ../NMS_LOC1_VIETNAMESE.MXML
```

### Kiểm tra HTML entities

```bash
# Tìm entries có HTML entities
grep -n '&lt;\|&gt;\|&amp;' ../NMS_LOC1_VIETNAMESE.MXML | head -n 10
```

## Bước 8: Deploy

```bash
# Backup file cũ nếu có
mv ../NMS_LOC1_VIETNAMESE.MXML ../NMS_LOC1_VIETNAMESE.MXML.backup

# Copy file mới
cp ../NMS_LOC1_VIETNAMESE.MXML [game-folder]/GAMEDATA/LANGUAGE/

# Hoặc dùng tool compile nếu cần
# MBINCompiler.exe NMS_LOC1_VIETNAMESE.MXML
```

## Tips & Tricks

### 1. Tối ưu hiệu suất

Nếu có nhiều file JSON lớn, có thể chia nhỏ:

```bash
# Dịch từng phần
npm start -- -m translate-mxml -t ../NMS_LOC1_ENGLISH.MXML -df data/part1 -o output1.MXML
npm start -- -m translate-mxml -t ../NMS_LOC1_ENGLISH.MXML -df data/part2 -o output2.MXML
```

### 2. Script automation

Tạo file `translate.sh`:
```bash
#!/bin/bash
cd simpify-loc-mxml
npm run build
npm start -- -m translate-mxml -t ../NMS_LOC1_ENGLISH.MXML -df data -o ../NMS_LOC1_VIETNAMESE.MXML
echo "✅ Done!"
```

Chạy:
```bash
chmod +x translate.sh
./translate.sh
```

### 3. Logging

```bash
# Save log ra file
npm start -- -m translate-mxml \
  -t ../NMS_LOC1_ENGLISH.MXML \
  -df data \
  -o ../NMS_LOC1_VIETNAMESE.MXML \
  2>&1 | tee translation.log
```

## Kết luận

Workflow hoàn chỉnh:

1. ✅ **Setup**: Install + Build
2. ✅ **Prepare**: Check template + data
3. ✅ **Execute**: Run translation
4. ✅ **Verify**: Check output quality
5. ✅ **Review**: Handle not found keys
6. ✅ **Deploy**: Use in game

**Thời gian ước tính:**
- Setup: 2 phút
- Translation (14K entries): 10-30 giây
- Verification: 5 phút
- **Tổng: ~10 phút**

🎉 **Chúc bạn dịch game vui vẻ!**
