#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# flake8: noqa

from pathlib import Path

# Thư mục chứa các file liên quan đến Facebook Stalker
FB_DIR = Path(__file__).resolve().parent

# Đường dẫn đến thư mục profile trình duyệt đã đăng nhập
PROFILE_DIR = FB_DIR / "profile"

# Đường dẫn đến file cookie định dạng Netscape, được yt-dlp sử dụng
COOKIE_FILE = FB_DIR / "facebook_cookies_netscape.txt"

# Đường dẫn đến file chứa danh sách các trang/profile mục tiêu
PAGES_FILE = FB_DIR / "pages.txt"

# Đường dẫn đến file lưu lịch sử các video ID đã cào
HISTORY_FILE = FB_DIR / "stalker_history.json"

# --- Cấu hình cho Stalker Strategy (strategies/facebook.py) ---

# Số giây nghỉ giữa mỗi chu trình quét tất cả các mục tiêu
SCAN_INTERVAL_SECONDS = 10

# Số lượng mục tiêu (fanpage/profile) xử lý đồng thời trong một batch.
# Giúp tránh mở quá nhiều tab cùng lúc, giảm tải cho hệ thống.
FACEBOOK_BATCH_SIZE = 5

# Thời gian (giây) chờ giữa các batch để tránh bị Facebook giới hạn.
WAIT_BETWEEN_BATCHES_SECONDS = 10

# Tên file thực thi của trình duyệt Chrome
CHROME_EXECUTABLE = "google-chrome"

# Cổng debug từ xa cho Chrome (nên dùng cổng riêng cho mỗi stalker)
CHROME_DEBUG_PORT = 9225

# Các tham số dòng lệnh khi khởi chạy Chrome
CHROME_ARGS = ["--headless=new", "--disable-gpu"]

# Các trang con cần quét trên mỗi fanpage
SUB_PAGES_TO_SCAN = ["videos"]#, "reels"]

# Giới hạn số lượng links mới nhất cần kiểm tra trên mỗi trang con
MAX_LINKS_PER_SECTION = 5

# Timeout (ms) khi tải một trang fanpage
PAGE_LOAD_TIMEOUT = 60000

# Thời gian chờ (ms) sau khi trang đã tải xong để các element động (video) xuất hiện
PAGE_WAIT_AFTER_LOAD = 5000

# --- Cấu hình cho CSS Selectors ---

# Định nghĩa các loại trang
PAGE_TYPE_FANPAGE = 'fanpage'
PAGE_TYPE_PROFILE = 'profile'

# Selector để tìm các link video trên các loại trang khác nhau
# Sử dụng cấu trúc dict để dễ dàng mở rộng
VIDEO_SELECTORS = {
    PAGE_TYPE_FANPAGE: {
        "videos": 'a[href*="/videos/"], a[href*="/watch/?v="]',
        "reels": 'a[href*="/reel/"]',
    },
    PAGE_TYPE_PROFILE: {
        "videos": 'a[href*="&sk=videos"]',
        "reels": 'a[href*="&sk=reels_tab"]',
    }
}

# --- Cấu hình cho Video Downloader (facebook/fb_vid.py) ---
VIDEOS_DIR = FB_DIR / "videos"
YT_DLP_FORMAT = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"