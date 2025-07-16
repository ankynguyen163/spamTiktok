# fb_vid.py tải facebook video

import json
import yt_dlp
import argparse
import os
from fb_stalker.config import VIDEO_DIR, NETSCAPE_DIR, HISTORY_FILE, save_metadata_to_history # Đảm bảo có file config.py chứa các biến này

NETSCAPE = os.path.join(NETSCAPE_DIR, 'facebook_cookies_netscape.txt')


def download_facebook_video(url):
    # Tạo thư mục history nếu chưa có
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(VIDEO_DIR, '%(id)s.%(ext)s'),
        #'cookiesfrombrowser': ('chrome', 'Default'),
        'cookiefile': NETSCAPE,
        #'listformats': True,  # 💥 yt-dlp tự in ra list format
        'quiet': True,
        'noplaylist': True,
        'concurrent_fragment_downloads': 10,
        'format': 'bestvideo+bestaudio',
        'progress_with_newline': True
    }

    # === Lấy metadata ===
    print("\n📥 Đang tải metadata...\n")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    metadata = {
        "video_id": info.get("id"),
        "uploader": info.get("uploader"),
        "title": info.get("title"),
        "description": info.get("description"),
        "upload_date": info.get("upload_date")
    }

    """
    print("📄 Metadata:")
    for k, v in metadata.items():
        print(f"  {k}: {v}")
    """

    # print(f"[DEBUG]: {HISTORY_FILE}")
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
        existing_ids = {item.get("video_id") for item in history}
        if metadata["video_id"] in existing_ids:
            print(f"⚠️ Video {metadata['video_id']} đã tồn tại trong lịch sử. Bỏ qua tải lại.\n")
            return metadata
        else:
            # === Tải video ===
            print("\n🎞️🎞️🎞️🎞️🎞️  Đang tải video...\n")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            save_metadata_to_history(metadata)

    except Exception as e:
        print(f"⚠️ Lỗi khi đọc lịch sử: {e} → bỏ qua kiểm tra.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Facebook video URL")
    args = parser.parse_args()

    os.makedirs(VIDEO_DIR, exist_ok=True)
    download_facebook_video(args.url)
