# yt_vid.py – thực chất tải YouTube video

import json
import yt_dlp
import argparse
import os
from yt_stalker.config import VIDEO_DIR, HISTORY_FILE, save_metadata_to_history


def download_youtube_video(url):
    # Thiết lập yt-dlp
    ydl_opts = {
        'outtmpl': os.path.join(VIDEO_DIR, '%(id)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
        'format': 'bestvideo+bestaudio',
        'progress_with_newline': True
    }
        

    # Lấy metadata (chưa tải video)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    metadata = {
        "video_id": info.get("id"),
        "uploader": info.get("uploader"),
        "description": info.get("title"),
        "upload_date": info.get("upload_date")
    }

    # Kiểm tra video đã tồn tại chưa
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except:
        history = []

    existing_ids = {item.get("video_id") for item in history}
    if metadata["video_id"] in existing_ids:
        print(f"⚠️ Video {metadata['video_id']} đã tồn tại. Bỏ qua.")
        return metadata

    # Tải video
    print(f"📥 Tải video {metadata['video_id']} ...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Ghi metadata
    save_metadata_to_history(metadata)
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="YouTube video URL")
    args = parser.parse_args()

    os.makedirs(VIDEO_DIR, exist_ok=True)
    download_youtube_video(args.url)
