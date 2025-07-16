# config.py

import os
import json
from pathlib import Path

# Gốc dự án
BASE_DIR = Path(__file__).resolve().parent

# Thư mục lưu video và lịch sử
VIDEO_DIR = BASE_DIR / 'videos'
HISTORY_FILE = BASE_DIR / 'history' / 'video_history.json'

# Danh sách kênh YouTube (mỗi dòng 1 link)
CHANNELS_FILE = BASE_DIR / 'channels.txt'

# Thời gian chờ
WAIT_BETWEEN_ROUNDS = 60    # Giữa 2 vòng
DELAY_TIME = 10             # Giữa 2 kênh

# Số stalker chạy song song
BATCH_SIZE = 5

# Số video tối đa được cào trong một channel
MAX_VIDEOS = 5

# Đảm bảo thư mục tồn tại
(VIDEO_DIR).mkdir(parents=True, exist_ok=True)
(HISTORY_FILE.parent).mkdir(parents=True, exist_ok=True)

def save_metadata_to_history(metadata):
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except:
        history = []

    history.append(metadata)

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(f"💾 Đã lưu metadata vào {HISTORY_FILE}")
