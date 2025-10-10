# ✨ Feature Update: Export Not Found Keys

## Tóm tắt thay đổi

Đã cập nhật script merge JSON để **tự động export các keys không tìm thấy ra file riêng**.

## 🎯 Tính năng mới

### Tự động tạo file `*_not_found.json`

Khi có keys không tìm thấy trong file source, script sẽ tự động:
1. Tạo file mới với tên `<output>_not_found.json`
2. Chứa **CHỈ** các keys không tìm thấy với giá trị gốc từ file target
3. File này giúp bạn dễ dàng xác định và xử lý các keys còn thiếu

### Quy tắc đặt tên

- Input: `merged.json` → Output: `merged_not_found.json`
- Input: `data/result.json` → Output: `data/result_not_found.json`
- Input: `output` (no extension) → Output: `output_not_found.json`

### Khi nào file được tạo?

- ✅ **Có tạo**: Khi có ít nhất 1 key không tìm thấy
- ❌ **Không tạo**: Khi tất cả keys đều tìm thấy (100% match)

## 📊 Ví dụ

### Input Files

**source.json** (prefix: `UI_`):
```json
{
  "UI_HELLO": "Xin chào",
  "UI_WORLD": "Thế giới"
}
```

**target.json** (prefix: `TRA_`):
```json
{
  "TRA_HELLO": "Hello",
  "TRA_WORLD": "World",
  "TRA_GOODBYE": "Goodbye"
}
```

### Command

```bash
npm run merge -- source.json target.json output.json "UI_" "TRA_"
```

### Output Files

**output.json** (Main file):
```json
{
  "TRA_HELLO": "Xin chào",
  "TRA_WORLD": "Thế giới",
  "TRA_GOODBYE": "Goodbye"
}
```

**output_not_found.json** (Auto-generated):
```json
{
  "TRA_GOODBYE": "Goodbye"
}
```

### Console Output

```
Starting merge process...
Source file: source.json (prefix: "UI_")
Target file: target.json (prefix: "TRA_")
Output: output.json

📄 Not found keys exported to: output_not_found.json

✓ Merge completed successfully!
  - Total keys in target: 3
  - Merged from source: 2
  - Not found in source: 1

Keys not found in source file (after removing prefix "TRA_"):
  - TRA_GOODBYE (looking for: GOODBYE)
```

## 🔧 Technical Changes

### File Modified: `src/merger.ts`

**Thêm logic:**
```typescript
// Export not found keys to separate file
if (notFound.length > 0) {
  const notFoundData: Record<string, string> = {};
  notFound.forEach(key => {
    notFoundData[key] = targetData[key];
  });
  
  // Generate not found filename
  const outputPath = options.outputFile;
  const lastDotIndex = outputPath.lastIndexOf('.');
  const notFoundPath = lastDotIndex > 0
    ? outputPath.substring(0, lastDotIndex) + '_not_found' + outputPath.substring(lastDotIndex)
    : outputPath + '_not_found.json';
  
  fs.writeFileSync(notFoundPath, JSON.stringify(notFoundData, null, 2), 'utf-8');
  console.log(`\n📄 Not found keys exported to: ${notFoundPath}`);
}
```

## ✅ Testing

### Test 1: With not found keys
```bash
npm run merge -- file1_example.json file2_example.json test.json "BUI_" "TRA_"
```
**Result**: ✓ File `test_not_found.json` created with 8 keys

### Test 2: Perfect match (no not found)
```bash
npm run merge -- test_perfect_match_source.json test_perfect_match_target.json result.json "SRC_" "TGT_"
```
**Result**: ✓ No `_not_found.json` file created

### Test 3: Subdirectory output
```bash
npm run merge -- file1.json file2.json data/output.json "BUI_" "TRA_"
```
**Result**: ✓ File `data/output_not_found.json` created in same directory

### Test 4: HTML entities preservation
```bash
npm run merge -- test_complex_source.json test_complex_target.json complex.json "UI_" "MSG_"
```
**Result**: ✓ HTML entities preserved in both main and not_found files

## 📚 Documentation Updates

Đã cập nhật các file:
- ✅ `MERGE-JSON-GUIDE.md` - Thêm thông tin về file not found
- ✅ `IMPLEMENTATION-SUMMARY.md` - Thêm test cases và output format
- ✅ `QUICK-REFERENCE.md` - Thêm tip về file not found
- ✅ `README.md` - Thêm output description
- ✅ `DEMO-WORKFLOW.md` - Tạo workflow demo hoàn chỉnh

## 🎯 Benefits

1. **Tự động hóa**: Không cần filter thủ công để tìm keys chưa dịch
2. **Tách biệt**: File not found độc lập, dễ xử lý riêng
3. **Rõ ràng**: Biết chính xác keys nào cần xử lý tiếp
4. **Workflow**: Hỗ trợ quy trình dịch nhiều giai đoạn
5. **Sạch sẽ**: Không tạo file thừa khi không cần

## 🚀 Use Cases

### Use Case 1: Dịch dần dần
1. Merge lần 1 → Có file not found
2. Dịch file not found
3. Sử dụng file not found đã dịch làm source cho lần merge tiếp

### Use Case 2: Tìm nguồn khác
1. Merge lần 1 → Có file not found
2. Tìm file khác có chứa bản dịch cho các key còn thiếu
3. Merge file not found với nguồn mới

### Use Case 3: Review & QA
1. Export not found keys
2. Team review các keys này
3. Quyết định strategy cho từng key (dịch mới, copy từ đâu, skip, etc.)

## 💡 Next Steps

Người dùng có thể:
1. Sử dụng file not found để track progress
2. Dịch thủ công các keys trong file not found
3. Tìm nguồn khác để merge tiếp
4. Tạo report từ file not found

## 🎉 Status

**✅ COMPLETED & TESTED**
- Feature implemented
- All tests passed
- Documentation updated
- Ready for production use
