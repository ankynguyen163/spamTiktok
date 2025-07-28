.
├── cli.py                      # 🚀 TRUNG TÂM ĐIỀU KHIỂN: Giao diện dòng lệnh chính để chạy mọi tác vụ.
├── README.md                   # 📖 Tổng quan dự án, hướng dẫn cài đặt và sử dụng.
├── CLI.md                      # 📚 Tài liệu chi tiết về tất cả các lệnh trong `cli.py`.
├── progress.md                 # 🆕 Nhật ký tiến độ và các vấn đề cần giải quyết.
├── requirements.txt            # 📦 Danh sách các thư viện Python cần thiết.
│
├── stalkers/                   # === MODULE CÀO VIDEO (ĐÃ TÁI CẤU TRÚC) ===
│   ├── __init__.py             #  Đánh dấu đây là một Python package.
│   ├── manager.py              #  Trình quản lý chung, nhận chiến lược (fb, yt, all).
│   ├── strategies/             #  Nơi chứa các chiến lược cào dữ liệu.
│   │   ├── __init__.py         #   - Đánh dấu đây là một Python package.
│   │   ├── base.py             #   - Định nghĩa StalkerStrategy (lớp trừu tượng).
│   │   ├── facebook.py         #   - FacebookStrategy.
│   │   └── youtube.py          #   - YouTubeStrategy.
│   │
│   ├── facebook/               #  Mã nguồn cào dữ liệu cụ thể cho Facebook.
│   │   ├── stalker.py          #   - Logic chính: theo dõi một fanpage.
│   │   └── ...                 #   - (fb_vid.py, login_facebook.py, pages.txt, etc.)
│   │
│   └── youtube/                #  Mã nguồn cào dữ liệu cụ thể cho YouTube.
│       ├── stalker.py          #   - Logic chính: theo dõi một kênh.
│       └── ...                 #   - (yt_vid.py, channels.txt, etc.)
│
└── Tiktok/                     # === MODULE TIKTOK (UPLOAD & QUẢN LÝ) ===
    ├── spamUploadTiktok/       # --- Chức năng Upload ---
    │   ├── __main__.py         # Logic chính để upload video (chế độ `auto` và `manual`).
    │   └── utils.py            # Các hàm tiện ích (tạo caption, hashtag...).
    │
    ├── deleteGarbage/          # --- Chức năng Dọn dẹp ---
    │   └── delete_videos.py    # Tự động xóa các video có lượt xem thấp trên kênh TikTok.
    │
        ├── cleanStorage/           # --- Chức năng Dọn dẹp file video ---
    │   ├── __init__.py         # Package marker
    │   ├── manager.py          # Logic dọn dẹp video (pending & uploaded)
    │   ├── utils.py            # Utilities: thống kê, báo cáo, phát hiện file mồ côi
    │   └── README.md           # Tài liệu module cleanStorageng & uploaded).
    │
    ├── login_tiktok.py         # Xử lý đăng nhập TikTok và lưu profile cho một tài khoản.
    ├── config.py               # Cấu hình chính cho module TikTok (đường dẫn, UI selectors).
    ├── accounts/               # Nơi lưu trữ dữ liệu của TẤT CẢ các tài khoản TikTok.
    │   └── <account_name>/     # Mỗi tài khoản có một thư mục riêng chứa:
    │       ├── cookies.json    #   - Cookie đăng nhập.
    │       ├── history.json    #   - Lịch sử video đã upload.
    │       └── Default/        #   - Profile trình duyệt Chrome.
    │
    ├── manageHistory/          # --- Chức năng Quản lý Lịch sử ---
    │   ├── manage_history.py   #   Trình quản lý các tác vụ lịch sử (view, clear, migrate).
    │   ├── view_history.py     #   Xem lịch sử upload của một tài khoản.
    │   ├── clear_history.py    #   Xóa lịch sử upload của một tài khoản (hành động nguy hiểm).
    │   └── migrate_history.py  #   Tiện ích di chuyển lịch sử từ cấu trúc cũ sang cấu trúc mới.
    └── README.md               # Tài liệu riêng cho module TikTok.
