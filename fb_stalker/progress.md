# Progress of FB Stalker Project

## 1. Current Structure

### Directory Layout

.
├── config.py # Cấu hình chung, gồm thư mục lưu trữ, định dạng cookie
├── cookies # Thư mục chứa cookies và profile của Facebook
│ ├── facebook_cookies.json # Cookies của Facebook
│ └── facebook_profile # Profile Facebook (nếu cần thiết cho login)
├── fb_reel.py # Tải video dạng Reel từ Facebook
├── fb_vid.py # Tải video từ Facebook page
├── history
│ └── video_history.json # Lưu trữ thông tin video đã tải
├── login_facebook.py # Đăng nhập Facebook, lưu cookies và profile
├── login_tiktok_qr.py # Đăng nhập TikTok bằng mã QR
├── pages.txt # Danh sách các Facebook page cần theo dõi
├── stealth.js # Script tránh bị phát hiện khi sử dụng headless browser
└── videos # Thư mục lưu trữ các video đã tải


### Progress Summary:
- **`config.py`**: Đã cấu hình thành công các đường dẫn cho video, lịch sử, cookie, profile và script stealth.js 
- **`login_facebook.py`**: Đã hoàn thành chức năng đăng nhập Facebook và lưu cookie vào thư mục `/cookies/facebook_cookies.json`, netscape cookies vào `/netscape/facebook_cookies_netscape`  profile vào `/cookies/facebook_profile`.
- **Cookies Conversion**: Đã hoàn thành hàm `convert_json_to_netscape` trong `config.py` để chuyển đổi cookies từ định dạng JSON sang Netscape cho việc tải video và reel.
  
## 2. Đã Hoàn Thành:

- **`fb_vid.py`**: Sử dụng yt-dlp để lấy metadata (ID video, title, description, thời gian upload) và lưu vào thư mục `videos/`. Lưu lại thông tin video vào `video_history.json`.
- **`fb_reel.py`**: Tải video dạng Facebook Reel từ URL `/reel/<id>` hoặc `/watch/?v=<id>`, dùng cookies dạng Netscape (`/netscape/facebook_cookies_netscape.txt`).  
  Móc `video_id`, tải về `videos/`, lưu metadata vào `video_history.json` nếu chưa có.
- **`stalker.py`**: Chỉ rình một fanpage duy nhất, dò 3 post mới nhất, thấy video hoặc reel là tải về ngay

## 3. Next Steps:
### 3.1. **Error Handling**
  - Cần xây dựng cơ chế bắt lỗi để xử lý các trường hợp không tải được video (e.g., cookies hết hạn, link không hợp lệ).

### 3.2. **Testing and Debugging**
- ...

## 4. Issues/Concerns:
- **Cookies Expiration**: Cần xác định phương thức duy trì session lâu dài cho bot, đặc biệt là đối với Facebook và TikTok. Có thể cần cập nhật cookie định kỳ hoặc sử dụng các phương thức khác để duy trì trạng thái đăng nhập.
- **Chuyển đổi cookies**: Cần chắc chắn rằng định dạng Netscape được chuyển đổi chính xác và phù hợp với yêu cầu của `yt-dlp` và các công cụ tải video.
- **Tốc độ tải video**: Cần tối ưu hóa tốc độ tải video và giảm thiểu thời gian chờ giữa các lần tải video (có thể điều chỉnh các tham số `yt-dlp`).

## 5. Pending Tasks:
- Cập nhật và kiểm tra việc tải video từ các trang Facebook khác nhau.
- Xây dựng hệ thống log chi tiết để dễ dàng debug và theo dõi tiến độ tải video.



# TỔNG KẾT:
- XONG!!!! Một đội quân paparazzi đi rình videos, reels các fanpage chôm về