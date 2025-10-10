# Quick Reference - Merge JSON

## 🚀 Cách nhanh nhất

```bash
npm run merge -- <source> <target> <output> <src-prefix> <tgt-prefix>
```

## 📋 Ví dụ thực tế

### Merge từ BUI_ sang TRA_
```bash
npm run merge -- ui_vietnamese.json translate_english.json translate_vietnamese.json "BUI_" "TRA_"
```

### Merge từ MSG_ sang DLG_
```bash
npm run merge -- messages.json dialogs.json dialogs_merged.json "MSG_" "DLG_"
```

## 🔍 Cách hoạt động

**Input:**
- Source: `{ "BUI_HELLO": "Xin chào" }`
- Target: `{ "TRA_HELLO": "Hello" }`

**Output:**
- Merged: `{ "TRA_HELLO": "Xin chào" }` ✓

## 📊 Output

- ✅ Số key đã merge
- ⚠️ Danh sách key không tìm thấy
- 📄 File output mới
- 📄 File `*_not_found.json` (tự động tạo nếu có key không tìm thấy)

## 💡 Tips

1. **Prefix phải khớp chính xác** (case-sensitive)
2. **File gốc không bị thay đổi** (tạo file mới)
3. **HTML entities được bảo toàn** (`&lt;`, `&gt;`, etc.)
4. **File not found tự động tạo** - Dễ dàng xử lý các key chưa tìm thấy
5. **Backup trước khi merge** (nếu cần)

## 🔗 Đọc thêm

- [MERGE-JSON-GUIDE.md](MERGE-JSON-GUIDE.md) - Hướng dẫn chi tiết
- [README.md](README.md) - Tài liệu đầy đủ
- [IMPLEMENTATION-SUMMARY.md](IMPLEMENTATION-SUMMARY.md) - Tổng kết kỹ thuật
