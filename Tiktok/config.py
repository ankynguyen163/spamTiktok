# config.py - Unified config cho TikTok uploader
import json
import os
from pathlib import Path
import socket

# Base paths
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent


# --- TikTok UI Selectors (for delete_videos.py) ---
# These selectors are based on TikTok Studio's UI. They may change and require updates.
TT_STUDIO_UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload?from=creator_center"
TT_STUDIO_CONTENT_URL = "https://www.tiktok.com/tiktokstudio/content"
TT_VIEWS_HEADER_SELECTOR = 'div[data-tt="components_PostTableHeader_FlexRow"]:has-text("Lượt xem")'
TT_VIDEO_ROW_SELECTOR = 'div[data-tt="components_PostTable_Absolute"]'
TT_VIEW_COUNT_SELECTOR = 'div[data-tt="components_RowLayout_FlexRow_6"] span.TUXText'
TT_MORE_OPTIONS_BUTTON_SELECTOR = 'button[data-tt="components_ActionCell_Clickable"]'
TT_DELETE_MENU_ITEM_SELECTOR = 'div[data-tt="components_ActionCell_FlexRow"]:has-text("Xóa")'
TT_CONFIRM_DELETE_BUTTON_SELECTOR = 'button[data-tt="components_Modal_TUXButton"]:has-text("Xóa")'


# --- Selectors for Upload Process ---
TT_SELECT_VIDEO_BUTTON_XPATH = '//div[contains(text(), "Chọn video")]/ancestor::button'
TT_CAPTION_INPUT_SELECTOR = 'div.public-DraftEditor-content[contenteditable="true"]'
TT_UPLOAD_PROGRESS_SUCCESS_SELECTOR = 'div.info-progress.success'
TT_POST_BUTTON_SELECTOR = 'button.Button__root:has-text("Đăng")'
TT_CONFIRM_POST_BUTTON_SELECTOR = 'button.TUXButton--primary:has-text("Đăng ngay")' # Modal "Đăng ngay"


# --- Chrome Debugging ---
# Đường dẫn đến Chrome executable và cổng debug
# Cần đảm bảo Chrome đã được cài đặt và có thể truy cập từ đường dẫn
# Ưu tiên sử dụng biến môi trường CHROME_EXECUTABLE_PATH nếu có
import platform
import shutil
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

CHROME_EXECUTABLE = _get_chrome_executable_path()

# Cổng debug từ xa cho Chrome (nên dùng cổng riêng cho mỗi stalker)
def find_free_port():
    """Finds a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


CHROME_DEBUG_PORT = find_free_port()

# Số lượng video upload song song trong chế độ 'auto'
# Đặt giá trị cao có thể yêu cầu nhiều tài nguyên hệ thống (CPU, RAM)
# và có thể bị TikTok giới hạn. Bắt đầu với 2 hoặc 3 là hợp lý.
MAX_CONCURRENT_UPLOADS = 3
# Video sources
VIDEO_SOURCES = {
    'fb': PROJECT_ROOT / 'stalkers' / 'facebook' / 'videos',
    #'yt': PROJECT_ROOT / 'stalkers' / 'youtube' / 'videos'
}
# Directory to store accounts
ACCOUNTS_DIR = BASE_DIR / 'accounts'
# Tạo thư mục nếu chưa có
ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)