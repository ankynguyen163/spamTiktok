# 🕵️ Facebook Stalker

Module này chịu trách nhiệm theo dõi các trang (Page) và trang cá nhân (Profile) trên Facebook, tự động tải về các video và Reels mới nhất.

---

## ⚙️ Cơ chế hoạt động

- **Giả lập trình duyệt:** Stalker sử dụng `Playwright` để điều khiển một trình duyệt Chrome (chạy ở chế độ `headless`) để tương tác với Facebook như một người dùng thật.
- **Yêu cầu đăng nhập:** Để có thể xem video và không bị chặn, Stalker cần sử dụng một profile trình duyệt đã đăng nhập sẵn. Một script tiện ích được cung cấp để giúp bạn thực hiện việc này một cách dễ dàng.
- **Tải video bằng `yt-dlp`:** Sau khi tìm thấy link video mới trên trang, Stalker sẽ sử dụng `yt-dlp` cùng với cookie đã được trích xuất từ trình duyệt để tải video. Điều này giúp vượt qua các cơ chế bảo vệ của Facebook.
- **Quét đa mục:** Tự động quét cả hai mục `/videos` và `/reels` của mỗi mục tiêu.
- **Quản lý lịch sử:** Sử dụng file `stalker_history.json` để theo dõi các video đã tải, tránh tải lại.
- **Metadata chi tiết:** Mỗi video tải về đều đi kèm một file `.json` chứa các thông tin như tiêu đề, mô tả, và thời gian đăng.

---

## 🛠️ Cấu hình

1.  **`pages.txt`**: Thêm URL của các trang hoặc profile bạn muốn theo dõi vào file này, mỗi URL một dòng.
    ```
    https://www.facebook.com/some.page
    https://www.facebook.com/profile.php?id=1000...
    ```

2.  **`config.py`**: File này chứa các tùy chọn cấu hình quan trọng:
    *   `SCAN_INTERVAL_SECONDS`: Thời gian nghỉ giữa các chu trình quét.
    *   `FACEBOOK_BATCH_SIZE`: Số lượng trang được xử lý đồng thời để tránh quá tải.
    *   `MAX_VIDEOS_PER_SECTION`: Số lượng video/reel mới nhất cần kiểm tra trong mỗi lần quét.
    *   `CHROME_EXECUTABLE`: Tên file thực thi của trình duyệt (ví dụ: `google-chrome` trên Linux, `chrome.exe` trên Windows).

---

## 🚀 Cách sử dụng

Quá trình thiết lập gồm 3 bước đơn giản:

### Bước 1: Đăng nhập (Bắt buộc - Chỉ làm 1 lần)

Chạy lệnh sau từ thư mục gốc của dự án. Một cửa sổ trình duyệt sẽ hiện ra.

```bash
python -m stalkers.facebook.login
```

Hãy đăng nhập vào tài khoản Facebook của bạn. Sau khi đăng nhập thành công, script sẽ tự động phát hiện, lưu lại profile trình duyệt và cookie cần thiết, sau đó tự đóng.

### Bước 2: Thêm mục tiêu

Mở file `stalkers/facebook/pages.txt` và dán các URL bạn muốn theo dõi vào đó.

### Bước 3: Chạy Stalker

Từ thư mục gốc của dự án, chạy lệnh:

```bash
python -m stalkers fb
```

Stalker sẽ bắt đầu chạy nền, tự động mở Chrome headless, quét các mục tiêu và tải video mới vào thư-mục `stalkers/facebook/videos/`.

---

## 📂 Cấu trúc thư mục

```plaintext
facebook/
├── README.md                       # Tài liệu này
├── strategy.py                     # Logic chính của Stalker
├── login.py                        # Script hỗ trợ đăng nhập lần đầu
├── config.py                       # File cấu hình
├── pages.txt                       # Danh sách trang/profile mục tiêu
├── stalker_history.json            # Lịch sử các video đã tải
├── facebook_cookies_netscape.txt   # Cookie được yt-dlp sử dụng
├── profile/                        # Thư mục chứa dữ liệu profile trình duyệt
└── videos/                         # Thư mục chứa video và metadata (.json)
    ├── video_id_1.mp4
    ├── video_id_1.json
    └── ...
```