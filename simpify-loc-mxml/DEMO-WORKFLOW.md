# Demo Workflow: Merge JSON with Not Found Export

## Scenario
Bạn có file `ui_vietnamese.json` với các key `UI_*` đã được dịch, và muốn áp dụng bản dịch đó cho file `translate_english.json` với các key `TRA_*`.

## Step 1: Chuẩn bị file

**ui_vietnamese.json** (Source - đã dịch):
```json
{
  "UI_HELLO": "Xin chào",
  "UI_WORLD": "Thế giới",
  "UI_WELCOME": "Chào mừng"
}
```

**translate_english.json** (Target - chưa dịch):
```json
{
  "TRA_HELLO": "Hello",
  "TRA_WORLD": "World",
  "TRA_WELCOME": "Welcome",
  "TRA_GOODBYE": "Goodbye",
  "TRA_THANKS": "Thanks"
}
```

## Step 2: Chạy merge

```bash
npm run merge -- ui_vietnamese.json translate_english.json translate_vietnamese.json "UI_" "TRA_"
```

## Step 3: Kết quả

### File 1: `translate_vietnamese.json` (Main output)
```json
{
  "TRA_HELLO": "Xin chào",      // ✓ Merged từ UI_HELLO
  "TRA_WORLD": "Thế giới",      // ✓ Merged từ UI_WORLD
  "TRA_WELCOME": "Chào mừng",   // ✓ Merged từ UI_WELCOME
  "TRA_GOODBYE": "Goodbye",     // ⚠ Không tìm thấy UI_GOODBYE
  "TRA_THANKS": "Thanks"        // ⚠ Không tìm thấy UI_THANKS
}
```

### File 2: `translate_vietnamese_not_found.json` (Auto-generated)
```json
{
  "TRA_GOODBYE": "Goodbye",
  "TRA_THANKS": "Thanks"
}
```

## Step 4: Xử lý file not found

### Option A: Dịch thủ công
Mở file `translate_vietnamese_not_found.json` và dịch:
```json
{
  "TRA_GOODBYE": "Tạm biệt",
  "TRA_THANKS": "Cảm ơn"
}
```

### Option B: Tìm nguồn khác
Nếu có file khác chứa bản dịch cho `GOODBYE` và `THANKS`, có thể merge tiếp.

## Step 5: Merge file not found đã dịch vào file chính

Có thể sử dụng các tool JSON merge hoặc edit thủ công để kết hợp file not found đã dịch vào file chính.

Hoặc có thể tạo file nguồn mới với các key đã dịch và merge lại:

**ui_additional_vietnamese.json**:
```json
{
  "UI_GOODBYE": "Tạm biệt",
  "UI_THANKS": "Cảm ơn"
}
```

Sau đó merge:
```bash
npm run merge -- ui_additional_vietnamese.json translate_vietnamese_not_found.json translate_final.json "UI_" "TRA_"
```

## Console Output

```
Starting merge process...
Source file: ui_vietnamese.json (prefix: "UI_")
Target file: translate_english.json (prefix: "TRA_")
Output: translate_vietnamese.json

📄 Not found keys exported to: translate_vietnamese_not_found.json

✓ Merge completed successfully!
  - Total keys in target: 5
  - Merged from source: 3
  - Not found in source: 2

Keys not found in source file (after removing prefix "TRA_"):
  - TRA_GOODBYE (looking for: GOODBYE)
  - TRA_THANKS (looking for: THANKS)
```

## Benefits

1. **Tự động hóa**: Không cần copy-paste thủ công từng key
2. **Rõ ràng**: Biết ngay key nào đã merge, key nào chưa
3. **Dễ xử lý**: File not found riêng biệt giúp focus vào những gì cần làm tiếp
4. **An toàn**: File gốc không bị thay đổi
5. **Linh hoạt**: Có thể merge nhiều lần từ nhiều nguồn khác nhau
