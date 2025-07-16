# list_videos.py

from pathlib import Path
import json

from tiktok_crawler.fb_config import VIDEO_DIR, HISTORY_FILE, TT_HISTORY_FILE

def list_videos():
    videos = sorted(VIDEO_DIR.glob("*.mp4"))
    if not videos:
        print("\U0001F4ED Không có video nào trong fb_stalker/videos.")
        return []

    try:
        with open(HISTORY_FILE) as f:
            history_list = json.load(f)
            history = {item["video_id"]: item for item in history_list if "video_id" in item}
    except Exception as e:
        print(f"⚠️ Lỗi đọc FB history: {e}")
        history = {}

    try:
        with open(TT_HISTORY_FILE) as f:
            tt_history = json.load(f)
    except Exception:
        tt_history = {}

    upload_candidates = []

    print(f"\U0001F4C1 Danh sách video ({len(videos)}):\n")
    for i, video in enumerate(videos, 1):
        video_id = video.stem
        if video_id in tt_history:
            continue
        meta = history.get(video_id, {})
        title = meta.get("title", "<không tiêu đề>")
        description = meta.get("description") or "<không mô tả>"
        #print(f"{i:2}. {video.name}\n     └── 🏷️ {title}\n     └── 📝 {description[:80]}{'...' if len(description) > 80 else ''}")
        upload_candidates.append({
            "video_path": str(video),
            "video_id": video_id,
            "title": title,
            "description": description
        })

    return upload_candidates

if __name__ == "__main__":
    list_videos()
