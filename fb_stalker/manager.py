# fb_stalker/manager.py

import subprocess
import time
import os
from itertools import islice


from fb_stalker.config import FANPAGES, DELAY_TIME, BATCH_SIZE


def load_pages(file_path=FANPAGES):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def start_stalkers(pages):
    procs = []
    for url in pages:
        page_name = url.strip('/').split('/')[-1]
        print(f"🥷  Cử stalker theo dõi: {page_name}")

        p = subprocess.Popen(["python", "-m", "fb_stalker.stalker", url])
        procs.append((page_name, p))
        time.sleep(DELAY_TIME)  # delay nhẹ giữa các launch

    return procs


def batch_pages(pages, size):
    pages = iter(pages)
    return iter(lambda: list(islice(pages, size)), [])


if __name__ == "__main__":
    pages = load_pages()

    if not pages:
        print("⚠️ Không tìm thấy fanpage nào trong pages.txt")
        exit(1)

    print(f"👥 Tổng cộng {len(pages)} fanpage. Bắt đầu rình... Nhấn Ctrl+C để thoát.")

    try:
        while True:
            for batch in batch_pages(pages, BATCH_SIZE):
                procs = []
                print(f"🚀 Nhóm mới: {len(batch)} fanpage sẽ được stalk song song.")

                for page in batch:
                    print(f"🥷 Cử nhẫn giả: {page.strip('/').split('/')[-1]}")
                    proc = subprocess.Popen(["python", "-m", "fb_stalker.stalker", page])
                    procs.append(proc)

                for proc in procs:
                    proc.wait()

                print(f"⏳ Nhóm xong. Nghỉ {DELAY_TIME} giây trước nhóm tiếp theo...")
                time.sleep(DELAY_TIME)

    except KeyboardInterrupt:
        print("\n🛑 Nhận lệnh Ctrl+C, dừng manager...")
        for proc in procs:
            proc.terminate()
        print("✅ Đã dừng tất cả tiến trình stalker.")
        exit(0)

        