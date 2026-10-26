# Tizen Stremio & Webpack App Debugging Skill

Kỹ năng chẩn đoán runtime, sửa lỗi catalog trống và tối ưu hiệu năng Stremio / Webpack Single Page Apps trên Samsung Smart TV Tizen (Chromium 56+).

## 🚀 Tính năng chính
1. **Chẩn đoán Runtime CDP không cần đoán mò:** Kết nối WebSocket trực tiếp vào nhân Chromium 56 của TV qua SDB Debug Port để trích xuất DOM, LocalStorage và Network errors.
2. **Xử lý triệt để lỗi mất Catalog (Missing Dynamic Chunks):**
   - Định vị lỗi `ERR_FILE_NOT_FOUND translationsXX.chunk.js` khi đổi ngôn ngữ (`interfaceLanguage: "vi-VN"`).
   - Tự động fallback về bộ từ điển tiếng Anh nhúng sẵn (`6330`), ngăn crash luồng reactive SolidJS.
3. **Sửa lỗi Certificate Mismatch (Error 118012):** Script dọn sạch chữ ký cũ và đóng gói lại WGT chuẩn Tizen Studio profile.
4. **Bypass Auth Guard kẹt màn hình Link Account:** Khắc phục tình trạng router SolidJS tự động redirect về `#/login` do state chưa hydrate kịp lúc boot.
5. **Tối ưu Streaming & Phụ đề chuẩn TV:** Cấu hình HLS buffer, font chữ Vietsub tương phản cao (vàng viền đen) và định tuyến CDN Debrid tránh nghẽn P2P trên chip TV đời cũ.

## 📁 Cấu trúc
```
.
├── SKILL.md                          # Hướng dẫn chi tiết & quy tắc vận hành cho AI Agent
├── README.md                         # Tài liệu tổng quan
└── scripts/
    ├── inspect_tv_runtime.py         # Kiểm tra DOM & State qua CDP (Chrome DevTools Protocol)
    └── repackage_wgt.sh              # Tự động dọn chữ ký và đóng gói lại WGT
```

## 🛠️ Hướng dẫn sử dụng nhanh

### 1. Kiểm tra trạng thái TV qua CDP
```bash
# Bật debug trên TV qua SDB
sdb -s <TV_IP:PORT> shell 0 debug <APP_ID>

# Forward port về local
sdb -s <TV_IP:PORT> forward tcp:43965 tcp:43965

# Chạy script chẩn đoán
python3 scripts/inspect_tv_runtime.py 43965
```

### 2. Đóng gói lại và cài đặt WGT
```bash
./scripts/repackage_wgt.sh /path/to/stremio_dir samsung_tv 100.113.48.14:26101
```

## 📜 Giấy phép
MIT License.
