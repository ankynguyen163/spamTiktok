# 🕵️ YouTube Stalker

Module này chịu trách nhiệm theo dõi các kênh YouTube được chỉ định và tự động tải về các video và shorts mới nhất.

---

## ⚙️ Cơ chế hoạt động

- **Không cần trình duyệt:** Stalker sử dụng trực tiếp công cụ dòng lệnh `yt-dlp` để lấy thông tin và tải video. Cách tiếp cận này rất nhẹ, nhanh và hiệu quả, không tốn tài nguyên để chạy một trình duyệt đầy đủ.
- **Quét đa mục:** Tự động quét cả hai mục `/videos` và `/shorts` của mỗi kênh để không bỏ lỡ bất kỳ nội dung nào.
- **Quản lý lịch sử:** Sử dụng file `history.json` để lưu lại ID của các video đã được tải. Điều này đảm bảo mỗi video chỉ được tải về một lần duy nhất.
- **Metadata chi tiết:** Khi tải một video, một file `.json` tương ứng cũng được tạo ra, chứa các thông tin hữu ích như tiêu đề, mô tả, tên kênh, và thời gian đăng.
- **Xử lý đồng thời:** Sử dụng `asyncio` để quét và tải video từ nhiều kênh một cách hiệu quả.

---

## 🛠️ Cấu hình

1.  **`channels.txt`**: Đây là nơi bạn định nghĩa các kênh mục tiêu. Thêm URL đầy đủ của mỗi kênh YouTube vào file này, mỗi URL trên một dòng.
    ```
    https://www.youtube.com/@channel1
    https://www.youtube.com/c/channel2
    ```

2.  **`config.py`**: File này chứa các tùy chọn cấu hình quan trọng:
    *   `YTDLP_OPTIONS`: Cho phép bạn tùy chỉnh các tham số cho `yt-dlp`. Mặc định, nó được cấu hình để tải video MP4 với chất lượng tốt nhất (lên đến 1080p).
    *   `MAX_VIDEOS_PER_SECTION`: Số lượng video/short mới nhất cần kiểm tra trong mỗi lần quét. Đặt giá trị nhỏ (ví dụ: 5) để quét nhanh hơn.
    *   `SCAN_INTERVAL_SECONDS`: Thời gian (giây) nghỉ giữa các chu trình quét.
    *   `YOUTUBE_BATCH_SIZE`: Số lượng kênh được xử lý đồng thời.

---

## 🚀 Cách sử dụng

1.  **Thêm kênh:** Mở file `stalkers/youtube/channels.txt` và thêm các URL kênh bạn muốn theo dõi.
2.  **Chạy Stalker:** Từ thư mục gốc của dự án, chạy lệnh sau:
    ```bash
    python -m stalkers yt
    ```
    Stalker sẽ bắt đầu chạy nền, quét các kênh theo định kỳ và tải video mới vào thư mục `stalkers/youtube/videos/`.

---

## 📂 Cấu trúc thư mục

```plaintext
youtube/
├── README.md           # Tài liệu này
├── strategy.py         # Logic chính của Stalker
├── config.py           # File cấu hình
├── channels.txt        # Danh sách kênh mục tiêu
├── history.json        # Lịch sử các video đã tải
└── videos/             # Thư mục chứa video và metadata (.json)
    ├── video_id_1.mp4
    ├── video_id_1.json
    └── ...
```