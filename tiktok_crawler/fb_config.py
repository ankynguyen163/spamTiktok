# config.py

import os
import json
from pathlib import Path
from http.cookies import SimpleCookie

# Gốc của module fb_stalker (absolute path)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tiktok cookies, profile
COOKIES_PATH = os.path.join(BASE_DIR, 'cookies', 'tiktok_cookies.json')
PROFILE_DIR = os.path.join(BASE_DIR, 'cookies', 'tiktok_profile')
DUMP_JSON_PATH = Path("tiktok_crawler/dump/upload_requests.json")

# Định nghĩa thư mục chứa video cần upload, lịch sử upload, file chứa cookies, profile
VIDEO_DIR = Path("fb_stalker/videos") # Đường dẫn chứa video tải về từ facebook
HISTORY_FILE = Path("fb_stalker/history/video_history.json") # Lịch sử video tải về từ facebook
TT_HISTORY_FILE = Path("tiktok_crawler/history/video_history.json") # Lịch sử những video đã up lên tiktok
STEALTH_SCRIPT = os.path.join(BASE_DIR, 'stealth.js') # Bản stealth chống anti bot





