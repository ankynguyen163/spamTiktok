# config_1.py – Đa nguồn videos YT cho TikTok uploader

import os
import json
from pathlib import Path

# Gốc dự án
BASE_DIR = Path(__file__).parent.parent

# Danh sách thư mục chứa video (đa nguồn)
VIDEO_DIRS = [
    BASE_DIR / "fb_stalker" / "videos",
    BASE_DIR / "yt_stalker" / "videos",
]

# Danh sách file lịch sử video (đa nguồn)
HISTORY_FILES = [
    BASE_DIR / "fb_stalker" / "history" / "video_history.json",
    BASE_DIR / "yt_stalker" / "history" / "video_history.json",
]

# File lịch sử upload TikTok
TT_HISTORY_FILE = BASE_DIR / "tiktok_crawler" / "history" / "video_history.json"

# Hồ sơ giữ session đăng nhập TikTok (Chrome profile)
PROFILE_DIR = BASE_DIR / "tiktok_crawler" / "cookies" / "tiktok_profile"

# Hàm gom toàn bộ video từ các nguồn
def list_all_videos():
    all_videos = []
    for folder in VIDEO_DIRS:
        if folder.exists():
            all_videos.extend([f for f in folder.iterdir() if f.is_file() and f.suffix.lower() == '.mp4'])
    return sorted(all_videos)


# Hàm tra mô tả từ nhiều history source
def get_description_from_sources(video_id):
    for history_file in HISTORY_FILES:
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            for item in history:
                if item.get("video_id") == video_id:
                    return item.get("description", "")
        except:
            pass
    return ""


# Hàm xoá video đã upload
def delete_uploaded_file(video_id):
    deleted = False
    for video_dir in VIDEO_DIRS:
        for file in video_dir.glob(f"{video_id}*"):
            if file.is_file():
                try:
                    file.unlink()
                    print(f"🗑️ Đã xoá file: {file.name}")
                    deleted = True
                except Exception as e:
                    print(f"⚠️ Không thể xoá file {file.name}: {e}")
    if not deleted:
        print(f"⚠️ Không tìm thấy file {video_id} để xoá.")
