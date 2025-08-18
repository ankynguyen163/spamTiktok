#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# flake8: noqa
from pathlib import Path
import socket
import platform
import shutil
import os

def _get_chrome_executable_path():
    """
    Tự động phát hiện đường dẫn đến Chrome executable dựa trên hệ điều hành.
    Ưu tiên biến môi trường, sau đó tìm kiếm trong các đường dẫn phổ biến.
    """
    # 1. Ưu tiên biến môi trường
    executable_path = os.environ.get("CHROME_EXECUTABLE_PATH")
    if executable_path and shutil.which(executable_path):
        return executable_path

    system = platform.system()
    
    # 2. Tìm kiếm trên Linux
    if system == "Linux":
        for exe in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
            path = shutil.which(exe)
            if path:
                return path

    # 3. Tìm kiếm trên Windows
    elif system == "Windows":
        common_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        # Fallback to shutil.which for Windows
        path = shutil.which("chrome")
        if path:
            return path

    # 4. Tìm kiếm trên macOS
    elif system == "Darwin":
        mac_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(mac_path):
            return mac_path
        # Fallback to shutil.which for macOS
        path = shutil.which("Google Chrome")
        if path:
            return path

    raise FileNotFoundError(
        "Không thể tìm thấy Google Chrome. "
        "Vui lòng cài đặt Chrome hoặc đặt biến môi trường 'CHROME_EXECUTABLE_PATH' "
        "trỏ đến file thực thi của Chrome."
    )

# Thư mục chứa các file liên quan đến Facebook Stalker
FB_DIR = Path(__file__).resolve().parent
# Đường dẫn đến thư mục profile trình duyệt đã đăng nhập
PROFILE_DIR = FB_DIR / "profile"
# Đường dẫn đến file cookie định dạng Netscape, được yt-dlp sử dụng
COOKIE_FILE = FB_DIR / "facebook_cookies_netscape.txt"
# Đường dẫn đến file chứa danh sách các trang/profile mục tiêu
PAGES_FILE = FB_DIR / "pages.txt"
# Đường dẫn đến file lưu lịch sử các video ID đã cào
HISTORY_FILE = FB_DIR / "history.json"
# --- Cấu hình cho Stalker Strategy (strategies/facebook.py) ---
# Số giây nghỉ giữa mỗi chu trình quét tất cả các mục tiêu
SCAN_INTERVAL_SECONDS = 10
# Số lượng mục tiêu (fanpage/profile) xử lý đồng thời trong một batch.
# Giúp tránh mở quá nhiều tab cùng lúc, giảm tải cho hệ thống.
FACEBOOK_BATCH_SIZE = 5
# Thời gian (giây) chờ giữa các batch để tránh bị Facebook giới hạn.
WAIT_BETWEEN_BATCHES_SECONDS = 5
# Tên file thực thi của trình duyệt Chrome
CHROME_EXECUTABLE = _get_chrome_executable_path()
# Cổng debug từ xa cho Chrome (nên dùng cổng riêng cho mỗi stalker)
def find_free_port():
    """Finds a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


CHROME_DEBUG_PORT = find_free_port()

# Các tham số dòng lệnh khi khởi chạy Chrome
CHROME_ARGS = [
    "--headless=new", 
    "--disable-gpu"
    ]
# Giới hạn số lượng links mới nhất cần kiểm tra trên mỗi trang
MAX_LINKS_PER_SECTION = 1000
# Timeout (ms) khi tải một trang fanpage
PAGE_LOAD_TIMEOUT = 60000
# Thời gian chờ (ms) sau khi trang đã tải xong để các element động (video) xuất hiện
PAGE_WAIT_AFTER_LOAD = 5000
# Số lần cuộn trang xuống để tải thêm video
SCROLL_COUNT = 1
# Thời gian chờ (giây) giữa mỗi lần cuộn
SCROLL_DELAY_SECONDS = 2
# --- Cấu hình cho CSS Selectors ---
SELECTOR = 'a[href*="/videos/"], a[href*="/watch/?v="]'
# Định nghĩa các loại trang
PAGE_TYPE_FANPAGE = 'fanpage'
PAGE_TYPE_PROFILE = 'profile'
# --- Cấu hình cho Video Downloader (facebook/fb_vid.py) ---
VIDEOS_DIR = FB_DIR / "videos"
YT_DLP_FORMAT = "bv*+ba/b"