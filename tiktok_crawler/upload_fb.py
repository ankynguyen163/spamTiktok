import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

from tiktok_crawler.fb_config import VIDEO_DIR, HISTORY_FILE, TT_HISTORY_FILE, PROFILE_DIR
from tiktok_crawler.utils import clean_caption, generate_hashtags

from playwright.async_api import async_playwright

def open_chrome(profile_dir):
    subprocess.Popen([
        "google-chrome",
        f"--user-data-dir={profile_dir}",
        "--remote-debugging-port=9222",
        "--new-window",
        "https://www.tiktok.com/tiktokstudio/upload?from=creator_center"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("🚀 Đã mở Chrome thật với profile giữ session login.")
    time.sleep(3)  # Đảm bảo Chrome mở xong

def is_uploaded(video_id):
    try:
        with open(TT_HISTORY_FILE) as f:
            tt_history = json.load(f)
        return any(item.get("video_id") == video_id for item in tt_history)
    except:
        return False    

def get_description(video_id):
    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)
        for item in history:
            if item.get("video_id") == video_id:
                return item.get("description", "")
    except:
        pass
    return ""

def save_upload_history(video_id, description):
    try:
        with open(TT_HISTORY_FILE) as f:
            tt_history = json.load(f)
    except:
        tt_history = []
    tt_history.append({
        "video_id": video_id,
        "description": description,
        "upload_time": datetime.now().isoformat()
    })
    with open(TT_HISTORY_FILE, 'w') as f:
        json.dump(tt_history, f, ensure_ascii=False, indent=2)
    print("✅ Đã ghi vào TT_HISTORY_FILE.")

def delete_uploaded_file(video_id):
    video_dir = Path(VIDEO_DIR)
    deleted = False
    for file in video_dir.iterdir():
        if file.is_file() and file.name.startswith(video_id):
            try:
                file.unlink()
                print(f"🗑️ Đã xoá file: {file.name}")
                deleted = True
            except Exception as e:
                print(f"⚠️ Không thể xoá file {file.name}: {e}")
    if not deleted:
        print(f"⚠️ Không tìm thấy file bắt đầu bằng {video_id} để xoá.")

async def auto_upload():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]  # Không mở tab mới, điều khiển tab có sẵn
        await page.bring_to_front()

        # Bấm nút chọn video
        button_choose = await page.wait_for_selector('div.Button__content:has-text("Chọn video")')
        await button_choose.click()
        print("📤 Đã click 'Chọn video'. Chờ mày tự chọn file...")

        # Chờ caption hiện ra (caption ban đầu chính là tên file = video_id)
        print("⏳ Đang chờ caption load...")
        caption_div = await page.wait_for_selector('div[contenteditable="true"]')
        caption_raw = await caption_div.inner_text()
        video_id = caption_raw.strip()

        print(f"📄 Đã lấy video_id từ caption: {video_id}")

        # Đoạn này check video_id có trong TT_HISTORY_FILE không, nếu có, xoá video trong VIDEO_DIR -> quit hàm()
        if is_uploaded(video_id):
            print(f"⚠️ Video_id {video_id} đã upload trước đó. Xoá file và skip.")
            delete_uploaded_file(video_id)
            return
        
        try:
            description = clean_caption(get_description(video_id))
            full_caption = description + "\n\n" + generate_hashtags()
        except:
            full_caption = generate_hashtags()

        # Ghi đè caption
        await caption_div.fill('')
        await caption_div.type(full_caption)
        print("✍️ Đã ghi đè caption.")

        # Bấm nút Đăng
        button_dang = await page.wait_for_selector('div.Button__content:has-text("Đăng")')

        # Chờ upload thành công (div có class 'info-progress success')
        await page.wait_for_selector('div.info-progress.success', timeout=600_000)
        print("✅ Video đã upload thành công, chuẩn bị bấm nút Đăng.")

        save_upload_history(video_id, description)
        delete_uploaded_file(video_id)
        
        # Bấm nút Đăng
        button_dang = await page.wait_for_selector('div.Button__content:has-text("Đăng")')
        await button_dang.click()
        print("🚀 Đã bấm nút Đăng.")

        print("✅ Hoàn tất quá trình upload cho video_id: ", video_id)

        print("💤 Đang chờ Chrome thật đóng...")
        while True:
            try:
                await page.title()  # ping tab
                await asyncio.sleep(2)
            except:
                print("🛑 Phát hiện Chrome đã đóng. Kết thúc script.")
                break

if __name__ == "__main__":
    while True:
        try:
            open_chrome(PROFILE_DIR)
            asyncio.run(auto_upload())
        except:
            print("🛑 Tắt Chrome. Kết thúc script.")
            break
