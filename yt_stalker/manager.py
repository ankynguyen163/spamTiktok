# yt_stalker/manager.py

import subprocess
import time
from itertools import islice

from yt_stalker.config import CHANNELS_FILE, DELAY_TIME, BATCH_SIZE


def load_channels(file_path=CHANNELS_FILE):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def batch_channels(channels, size):
    channels = iter(channels)
    return iter(lambda: list(islice(channels, size)), [])


if __name__ == "__main__":
    channels = load_channels()

    if not channels:
        print("⚠️ Không có channel nào trong channels.txt")
        exit(1)

    print(f"📺 Tổng cộng {len(channels)} kênh. Bắt đầu theo dõi...")

    try:
        while True:
            for batch in batch_channels(channels, BATCH_SIZE):
                procs = []
                print(f"\n🚀 Nhóm mới: {len(batch)} kênh.")

                for url in batch:
                    channel_name = url.strip('/').split('/')[-1]
                    print(f"🥷 Theo dõi kênh: {channel_name}")
                    proc = subprocess.Popen(["python", "-m", "yt_stalker.stalker", url])
                    procs.append(proc)
                    time.sleep(DELAY_TIME)

                for proc in procs:
                    proc.wait()

                print(f"⏳ Nhóm hoàn tất. Nghỉ {DELAY_TIME} giây trước nhóm tiếp theo...")
                time.sleep(DELAY_TIME)

    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C nhận được. Dừng toàn bộ tiến trình.")
        for proc in procs:
            proc.terminate()
        print("✅ Đã dừng tất cả stalkers.")
        exit(0)
