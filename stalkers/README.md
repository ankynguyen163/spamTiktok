# 🕵️ Stalkers Module

Đây là module chịu trách nhiệm theo dõi và tự động tải về các video mới từ nhiều nguồn khác nhau (Facebook, YouTube, v.v.). Nó được thiết kế để chạy như các tiến trình nền, liên tục cung cấp nội dung cho các module khác.

---

## 🏛️ Kiến trúc

Module này được xây dựng dựa trên mẫu thiết kế **Strategy Pattern**, cho phép mỗi nền tảng (Facebook, YouTube) được quản lý bởi một chiến lược riêng, giúp dễ dàng bảo trì và mở rộng.

1.  **`manager.py` (Trình quản lý):**
    *   Là điểm vào (`entrypoint`) của module, được gọi khi chạy lệnh `python -m stalkers <strategy>`.
    *   Đọc đối số dòng lệnh (`fb`, `yt`, `all`) để quyết định chiến lược nào sẽ được khởi chạy.
    *   Sử dụng `threading` để khởi chạy mỗi chiến lược trong một luồng (thread) riêng biệt. Điều này cho phép nhiều Stalker (ví dụ: Facebook và YouTube) có thể hoạt động **đồng thời** mà không block lẫn nhau.

2.  **`strategies/base.py` (Chiến lược cơ sở):**
    *   Định nghĩa một lớp trừu tượng `StalkerStrategy` với các phương thức chung như `login()` và `execute()`.
    *   Bất kỳ "Stalker" mới nào cũng phải kế thừa từ lớp này, đảm bảo tính nhất quán và dễ dàng tích hợp vào `manager.py`.

3.  **`strategies/facebook.py` (Chiến lược Facebook):**
    *   Sử dụng `Playwright` để điều khiển trình duyệt Chrome và `yt-dlp` để tải video.
    *   Yêu cầu đăng nhập một lần để lưu lại cookie và profile.
    *   **Để biết chi tiết về cách hoạt động, cấu hình và sử dụng, vui lòng xem README của Facebook Stalker.**

4.  **`strategies/youtube.py` (Chiến lược YouTube):**
    *   Sử dụng trực tiếp `yt-dlp` để lấy thông tin và tải video mà không cần đến trình duyệt, giúp tiết kiệm tài nguyên.
    *   **Để biết chi tiết về cách hoạt động, cấu hình và sử dụng, vui lòng xem README của YouTube Stalker.**

---

## 🚀 Cách sử dụng

Tất cả các lệnh được thực thi từ **thư mục gốc** của dự án.

### 1. Cấu hình

Vui lòng xem hướng dẫn chi tiết trong file README của từng Stalker:

*   Hướng dẫn cấu hình Facebook Stalker
*   Hướng dẫn cấu hình YouTube Stalker

### 2. Khởi chạy Stalker

Bạn nên chạy các tiến trình này trong các terminal riêng biệt hoặc sử dụng các công cụ như `tmux` hoặc `screen` để chúng có thể chạy nền liên tục.

*   **Chạy Stalker cho Facebook:**
    ```bash
    python -m stalkers fb
    ```
*   **Chạy Stalker cho YouTube:**
    ```bash
    python -m stalkers yt
    ```
*   **Chạy tất cả các Stalker:**
    ```bash
    python -m stalkers all
    ```

---

## 📂 Cấu trúc thư mục
*(Cấu trúc đã được tái cấu trúc để tăng tính module hóa và dễ bảo trì)*

```plaintext
stalkers/
├── README.md           # Tài liệu này
├── manager.py          # Entrypoint, điều phối các strategy
├── base_strategy.py    # Lớp trừu tượng StalkerStrategy (trước đây là strategies/base.py)
├── facebook/
│   ├── __init__.py
│   ├── strategy.py     # Logic cào dữ liệu chính (trước đây là strategies/facebook.py)
│   ├── login.py        # Script đăng nhập (trước đây là facebook/login_facebook.py)
│   ├── config.py       # Cấu hình riêng cho Facebook Stalker
│   ├── pages.txt       # Danh sách các trang mục tiêu
│   └── ...             # Các file dữ liệu: profile/, videos/, history.json
└── youtube/
    ├── __init__.py
    ├── strategy.py     # Logic cào dữ liệu (trước đây là strategies/youtube.py)
    ├── config.py       # Cấu hình riêng cho YouTube Stalker
    └── channels.txt    # Danh sách các kênh mục tiêu
```