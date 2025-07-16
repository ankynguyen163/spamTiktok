# yt_stalker.py – tự động quét videos/shorts của kênh

import subprocess
import json
import time
from pathlib import Path

from yt_stalker.config import CHANNELS_FILE, HISTORY_FILE, WAIT_BETWEEN_ROUNDS, MAX_VIDEOS


def load_video_history():
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return {item['video_id'] for item in json.load(f)}
    except:
        return set()


def get_videos(channel_url):
    if not channel_url.endswith('/'):
        channel_url += '/'
    subdomains = [channel_url + 'shorts', channel_url + 'videos']

    cmd_short = [
        'yt-dlp',
        '--skip-download',
        '--flat-playlist',
        '--print', '%(id)s',
        subdomains[0]
    ]

    cmd_videos = [
        'yt-dlp',
        '--skip-download',
        '--flat-playlist',
        '--print', '%(id)s',
        subdomains[1]
    ]

    result_shorts = subprocess.run(cmd_short, capture_output=True, text=True)
    result_videos = subprocess.run(cmd_videos, capture_output=True, text=True)

    short_ids = result_shorts.stdout.strip().splitlines()
    video_ids = result_videos.stdout.strip().splitlines()

    shorts = [[id, f"shorts/{id}"] for id in short_ids]
    videos = [[id, f"shorts/{id}"] for id in video_ids]

    return [vid for vid in (shorts + videos) if vid]


def download_video(vid):
    url = f"https://www.youtube.com/{vid[1]}"
    print(f"Tải từ URL: https://www.youtube.com/{vid[1]}")
    subprocess.run(['python', '-m', 'yt_stalker.yt_vid', url])


def run_stalker(channel_url):
    seen_ids = load_video_history()
    vid_list = get_videos(channel_url)
    print(f"📺 {channel_url} có {len(vid_list)} vids.")

    count = 0
    for vid in vid_list:
        if vid[0] not in seen_ids:
            print(f"🎬 Mới: {vid[0]} → Tải.")
            download_video(vid)
            time.sleep(1)
            count += 1
            if count >= MAX_VIDEOS:
                break
        else:
            print(f"⏩ {vid[0]} đã tải. Bỏ qua.")


if __name__ == "__main__":
    channels = Path(CHANNELS_FILE).read_text(encoding='utf-8').splitlines()

    for url in channels:
        url = url.strip()
        if url:
            print(f"\n🚀 Bắt đầu stalk /shorts từ: {url}")
            run_stalker(url)
            print(f"⏳ Nghỉ {WAIT_BETWEEN_ROUNDS} giây...\n")
            time.sleep(WAIT_BETWEEN_ROUNDS)
