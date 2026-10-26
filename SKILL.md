---
name: tizen-stremio-debugging
description: Use when debugging Stremio or Webpack apps on Tizen TV.
---

# Tizen Smart TV: Stremio & Webpack Runtime Debugging

Dùng khi đóng gói, tối ưu hoặc sửa lỗi màn hình trống / lỗi nạp catalog Stremio và các ứng dụng Webpack trên Tizen Smart TV (Chromium 56 - Tizen 4.0 trở lên).

## 1. Nguyên tắc cốt lõi: Tối giản (Anti-Overengineering)
- **Kiểm tra State trước khi sửa Code**: Khi app hôm trước đang xem bình thường mà hôm sau mất catalog hoặc màn hình trống, **TUYỆT ĐỐI KHÔNG** vội vàng decompile, băm nhỏ `bundle.js`, can thiệp router auth guard hay chèn script auto-login tùy tiện vào `index.html`. Việc chèn script thô bạo dễ phá vỡ hydration lifecycle của SolidJS/React, biến một lỗi cấu hình nhỏ thành sập toàn bộ app (màn hình đen thui).
- **Quy tắc `interfaceLanguage: "eng"`**: 90% lỗi catalog trống rỗng trên Stremio Tizen là do cài đặt ngôn ngữ bị đổi sang `vi-VN` (Webpack tìm file `translations46.chunk.js` không có sẵn trên TV gây unhandled rejection). Trong bundle Stremio Theater, tiếng Anh (`eng`) luôn được inline sẵn trong lõi. Nếu nghi ngờ, kiểm tra và gán lại `eng` trước tiên:
  ```javascript
  var p = JSON.parse(localStorage.getItem("profile") || "{}");
  if (p.settings && p.settings.interfaceLanguage !== "eng") {
      p.settings.interfaceLanguage = "eng";
      localStorage.setItem("profile", JSON.stringify(p));
      location.reload();
  }
  ```
- **Xử lý lỗi chữ ký khi tái sử dụng WGT (Error 118012)**: Khi cài file WGT có sẵn gặp lỗi `Certificate validation failed: 118012`, chỉ cần giải nén, xóa các file chữ ký cũ (`rm -f *signature*.xml .manifest.tmp`) rồi đóng gói lại với profile TV hiện hành:
  ```bash
  tizen package -t wgt -s samsung_tv -- <app_dir>
  tizen install -n <app_dir>/<app_name>.wgt -s <tv_ip>:<port>
  ```

## 2. Chẩn đoán Runtime qua Chrome DevTools Protocol (CDP)
Khi TV không hiện nội dung hoặc bị đơ ("chả thấy gì"), **TUYỆT ĐỐI KHÔNG đoán mò**. Hãy kết nối trực tiếp vào runtime Chromium của TV:

1. **Bật chế độ Debug qua SDB**:
   ```bash
   sdb -s <tv_ip>:<port> shell 0 debug <app_id>
   # Output trả về debug port, ví dụ: port: 39556
   ```
2. **Forward port từ TV về máy local/container**:
   ```bash
   sdb -s <tv_ip>:<port> forward tcp:<debug_port> tcp:<debug_port>
   ```
3. **Lấy WebSocket debugger URL**:
   Truy cập `http://localhost:<debug_port>/json` để lấy danh sách target và trường `webSocketDebuggerUrl`.
4. **Kiểm tra DOM và Model State trực tiếp**:
   Kết nối WebSocket gửi lệnh `Runtime.evaluate`:
   - **Lưu ý giao thức Chromium 56**: KHÔNG truyền `"awaitPromise": true` trong `Runtime.evaluate` (CDP 1.2 trên Chrome 56 chưa hỗ trợ flag này, khiến WebSocket bị đóng/lỗi). Dùng biểu thức đồng bộ hoặc gán biến toàn cục `window.__res = ...` rồi đọc lại.
   - Kiểm tra route hiện tại: `window.location.href` (nếu đang ở `file:///index.html#/login`, app bị kẹt ở màn hình Link Account).
   - Kiểm tra DOM: `document.body.innerHTML` hoặc `document.querySelector(".content-BPvBy")`.
   - Kiểm tra storage: `localStorage.getItem("profile")`.

## 3. Lỗi Webpack Dynamic Chunk trên Tizen Package (WGT)
### Cơ chế lỗi
- Khi build Webpack đóng gói vào WGT đơn file (`bundle.js`), một số module như file dịch thuật ngôn ngữ (`vi-VN.json`, `fr-FR.json`...) được tách thành chunk rời (`translationsXX.chunk.js`, chunk id `3429` cho `vi-VN`).
- Nếu tài khoản cloud hoặc `localStorage` lưu cài đặt `interfaceLanguage: "vi-VN"`, runtime Webpack sẽ gọi `__webpack_require__.e(3429)` cố nạp `translations46.chunk.js` từ hệ thống file local (`file:///translations46.chunk.js`).
- Do file chunk không tồn tại trong file WGT, lời gọi nạp script bị lỗi 404, throw `Loading chunk 3429 failed`.
- Lỗi unhandled promise rejection này làm sập toàn bộ cây component SolidJS / React từ root, khiến catalog không render và màn hình trống.

### Quy tắc xử lý
1. **Vá trực tiếp ánh xạ module dịch thuật (Locale Mapping)**:
   Thay vì chỉ bọc catch, hãy sửa trực tiếp map chunk trong `bundle.js`:
   - Tìm `"./vi-VN.json":[7300,3429]` và thay bằng `"./vi-VN.json":[6330]` (trỏ thẳng vào module từ điển tiếng Anh `6330` đã inline sẵn trong bundle).
   - Cách này giúp Webpack nạp module đồng bộ tức thì, không phát sinh bất kỳ request tải chunk nào.
2. **Fallback an toàn trong bundle loader**:
   Trong hàm nạp module ngôn ngữ `function a(A)` của Webpack:
   ```javascript
   // Bọc .catch để fallback về module mặc định nếu thiếu chunk, không làm sập UI
   return e.e(k[1]).catch(function(){ return {}; }).then(function(){ return e.t(a, 19); });
   ```
3. **Kiểm tra chunk trước khi package**:
   Quét `bundle.js` tìm tất cả các file có đuôi `.chunk.js` trong bảng map chunk của Webpack. Đảm bảo mọi file chunk được export đều có mặt trong thư mục nguồn trước khi chạy `tizen package`.

## 4. Lỗi Router Auth Guard Redirect về `#/login` (Link Account Screen)
### Cơ chế lỗi
- Router của Stremio gán guard cho toàn bộ các route chính: `{name:"home",path:"/home",component:h,guard:k}`, với `k = function() { return A.isAuthenticated(); }`.
- Nếu model `ctx` chưa kịp nạp xong `auth.key` từ Storage lúc khởi động hoặc khi auth revalidating, guard trả về `false` và router lập tức điều hướng về `#/login` (hiển thị `Link Account - Loading ...`).

### Quy tắc xử lý
- **Bypass Route Guard**: Patch định nghĩa guard trong `bundle.js`:
  - Tìm `var k=function(){return A.isAuthenticated()}` và đổi thành `var k=function(){return!0}` (hoặc `return true`).
  - Đảm bảo app luôn render route `/home`, `/discover`, `/search` mà không bao giờ bị chặn/kẹt ở màn hình Link Account.

## 5. Khả năng tương thích Fetch & Stream trên Chromium 56 (Tizen 4.0)
- **Không dùng `response.clone()`**: Tránh viết hook `window.fetch` bọc cache RAM bằng `res.clone()`. Trên Chromium 56 của Tizen 4.0, clone stream phản hồi từ CDN/API có thể gây treo bộ nhớ đệm hoặc làm đứt gãy luồng catalog fetch.
- **Dọn dẹp `localStorage` không tương thích**: Khi chuyển đổi tài khoản hoặc cài mới WGT, chủ động xóa hoặc đồng bộ lại các key `profile`, `settings` trong `localStorage` trước khi khởi động Core.

## 6. Xử lý triệt để phát phim chậm trên Tizen 4.0 (Torrent P2P vs Debrid vs CDN 100X)
### Cơ chế nghẽn
- **CPU & RAM kiệt quệ do Torrent**: Tizen 4.0 (2018 TV) chạy chip ARM Cortex yếu với RAM khả dụng chỉ ~200-300MB. Giao thức P2P/BitTorrent đòi hỏi duy trì hàng trăm socket kết nối, tính toán checksum và ghi cache liên tục, làm CPU TV đạt 100% gây đơ giao diện và giật buffer.
- **Nhà mạng bóp băng thông P2P**: Các ISP nội địa (Viettel, FPT, VNPT) thường xuyên bóp luồng torrent quốc tế, khiến scraper không lấy đủ seed.

### Giải pháp tối ưu
1. **Với Stremio**:
   - Bắt buộc dùng Debrid (Real-Debrid / TorBox) tích hợp vào Torrentio để chuyển luồng Torrent sang Direct HTTPS CDN, loại bỏ hoàn toàn tải P2P trên TV.
   - Trong cài đặt Streaming Server: đặt Torrent Profile sang `Fast` hoặc `Ultra Fast`, Torrent Cache: `2GB` (tránh `No cache` gây giật giật màn hình).
   - Tối giản Addon: Chỉ giữ 1-2 addon chính (Torrentio + Cinemeta) để giảm đồng thời các HTTP request cào metadata trên Chromium 56.
2. **Kiến trúc VOD CDN nội địa (Phương án 100X không phụ thuộc Torrent)**:
   - Thay vì ép TV kéo torrent, đóng gói Web App Tizen thuần (`<video>` + `hls.light.min.js`) trỏ trực tiếp vào các API CDN mở (như `phimapi.com`, `nguonc.com`).
   - Luồng video dạng HLS `.m3u8` được Tizen WebKit và chip Media DSP giải mã phần cứng trực tiếp (0% CPU, buffer <0.2s, 100% Vietsub).
   - Cấu hình HLS tối ưu cho TV 2018:
     ```javascript
     var hls = new Hls({ maxBufferLength: 30, maxMaxBufferLength: 60, enableWorker: true });
     ```

## 7. Lưu ý Quyền (Privilege) khi build WGT cho Retail TV
- **Tuyệt đối không khai báo Privilege cấp Partner/Platform**: Các quyền như `http://tizen.org/privilege/packagemanager.install` hoặc `http://tizen.org/privilege/package.info` bị Tizen OS từ chối cài đặt (lỗi chữ ký / certificate verification fail) trên TV thương mại nếu ký bằng chứng chỉ public/author thông thường.
- **Chỉ giữ lại Public Privileges**: `internet`, `tv.inputdevice`, `productinfo`, `network.public`, `mediacapture`, `notification`, `fullscreen`.
- **Tránh khoảng trắng trong tên file WGT**: Khi gọi `tizen install -n <file>.wgt`, tên file chứa dấu cách dễ gây lỗi parse tham số trên SDB CLI; luôn copy/đổi tên file thành không dấu cách (vd `PhimVIP.wgt`, `TVStore.wgt`) trước khi cài.
