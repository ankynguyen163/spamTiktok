# fb_yt.py – TikTok uploader đa nguồn videos FB + YT

import asyncio
import json
import subprocess
import time
from datetime import datetime

from tiktok_crawler.fb_yt_config import (
    PROFILE_DIR,
    TT_HISTORY_FILE,
    get_description_from_sources,
    delete_uploaded_file
)

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
    time.sleep(3)


def is_uploaded(video_id):
    try:
        with open(TT_HISTORY_FILE) as f:
            history = json.load(f)
        return any(item.get("video_id") == video_id for item in history)
    except:
        return False


def save_upload_history(video_id, description):
    try:
        with open(TT_HISTORY_FILE) as f:
            history = json.load(f)
    except:
        history = []

    history.append({
        "video_id": video_id,
        "description": description,
        "upload_time": datetime.now().isoformat()
    })

    with open(TT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print("✅ Đã ghi vào TT_HISTORY_FILE.")


async def auto_upload():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]
        await page.bring_to_front()

        button_choose = await page.wait_for_selector('div.Button__content:has-text("Chọn video")')
        await button_choose.click()
        print("📤 Đã click 'Chọn video'. Chờ mày tự chọn file...")

        """
        # Tự bấm enter chọn tệp đầu
        await asyncio.sleep(5)  # chờ 2 giây cho dialog hiện (tuỳ chỉnh)
        await page.keyboard.press("Enter")  # gửi phím Enter
        print("🔑 Đã gửi phím Enter giả lập.")        
        """

        print("⏳ Đang chờ caption load...")
        caption_div = await page.wait_for_selector('div[contenteditable="true"]')
        caption_raw = await caption_div.inner_text()
        video_id = caption_raw.strip()

        print(f"📄 Đã lấy video_id từ caption: {video_id}")

        if is_uploaded(video_id):
            print(f"⚠️ Video_id {video_id} đã upload trước đó. Xoá file và skip.")
            delete_uploaded_file(video_id)
            return

        try:
            description = clean_caption(get_description_from_sources(video_id))
            full_caption = description + "\n\n" + generate_hashtags()
        except:
            full_caption = generate_hashtags()

        await caption_div.fill('')
        await caption_div.type(full_caption)
        print("✍️ Đã ghi đè caption.")

        await page.wait_for_selector('div.info-progress.success', timeout=600_000)
        print("✅ Video đã upload thành công, chuẩn bị bấm nút Đăng.")

        save_upload_history(video_id, description)
        delete_uploaded_file(video_id)

        button_dang = await page.wait_for_selector('div.Button__content:has-text("Đăng")')
        await button_dang.click()
        print(f"🚀 Đã bấm nút Đăng cho video_id {video_id}")

        print("💤 Đang chờ Chrome thật đóng...")
        while True:
            try:
                await page.title()
                await asyncio.sleep(3)
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
