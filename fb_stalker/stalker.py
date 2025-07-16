import time
import sys
import os
import asyncio
import re
import json
import subprocess
from pathlib import Path
from time import sleep
from playwright.async_api import async_playwright

from fb_stalker.config import PROFILE_DIR, STEALTH_SCRIPT, HISTORY_FILE, WAIT_BETWEEN_ROUNDS, STALKER_MOUSE_WHEEL

MAX_POSTS = 10

def normalize_href(href: str) -> str:
    href = href.split('?')[0]
    return href if href.startswith("http") else f"https://www.facebook.com{href}"

def load_video_history():
    if Path(HISTORY_FILE).exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return {item['video_id'] for item in json.load(f)}
        except:
            return set()
    return set()

def extract_video_id(url: str) -> str | None:
    match = re.search(r'(?:videos|reel|watch/\?v=)[^\d]*(\d{5,})', url)
    return match.group(1) if match else None

def call_downloader(script: str, url: str):
    # print(f"▶️ Gọi python -m {script} {url}")
    subprocess.run(["python", "-m", script, url])

async def wait_for_articles(page, timeout=15000):
    start = time.time()
    try:
        await page.wait_for_selector('div[role="article"]', timeout=timeout)
    except Exception as e:
        print(f"Khong thay article cua {page} lan dau, thu reload...")
        await page.reload()
        await page.wait_for_selector('div[role="article"]', timeout=timeout)
    end = time.time() - start
    print(f"Thời gian tìm article mất {end:.2f} giây")

async def run_stalker_async(page_url):
    seen_ids = load_video_history()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print(f"🤫📸 Đang stalk: {page_url.strip('/').split('/')[-1]}")

        # Inject STEALTH
        with open(STEALTH_SCRIPT, "r") as f:
            stealth_script = f.read()
        await page.add_script_tag(content=stealth_script)

        start = time.time()
        await page.goto(page_url, timeout=60000)
        elapsed = time.time() - start
        print(f"⏱️ page.goto({page_url}) mất {elapsed:.2f} giây")

        try:
            await wait_for_articles(page, timeout=30000)
        except Exception:
            await page.screenshot(path="screenshot_error.png")
            print(f"📸 Đã lưu ảnh {page}.png vì không tìm thấy article.")
            await context.close()
            return

        """
        # Scroll thêm nhiều lần
        for _ in range(3):
            await page.mouse.wheel(0, STALKER_MOUSE_WHEEL)
            await asyncio.sleep(1)
        """

        posts = page.locator('div[role="article"]')
        total = await posts.count()
        print(f"🧩 Tổng số post detect được: {total}")

        # Fallback nếu không tìm được article
        if total == 0:
            print(f"⚠️ Không tìm thấy article, thử fallback selector...")
            posts = page.locator('[data-pagelet^="FeedUnit"]')
            total = await posts.count()
            print(f"🧩 Fallback detect được {total} posts.")

        if total == 0:
            print(f"❌ Không tìm thấy bài viết nào. Kết thúc stalker.")
            await context.close()
            return

        checked = 0
        for i in range(min(MAX_POSTS, total)):
            post = posts.nth(i)
            html = await post.inner_html()
            hrefs = re.findall(r'href="([^"]+)"', html)

            for href in hrefs:
                if '/videos/' in href:
                    full_url = normalize_href(href)
                    vid = extract_video_id(full_url)
                    if vid and vid not in seen_ids:
                        call_downloader('fb_stalker.fb_vid', full_url)
                        seen_ids.add(vid)
                    else:
                        print(f"⏩ Video {vid} đã có trong lịch sử.")
                    break
                elif '/reel/' in href or '/watch/?v=' in href:
                    full_url = normalize_href(href)
                    vid = extract_video_id(full_url)
                    if vid and vid not in seen_ids:
                        call_downloader('fb_stalker.fb_reel', full_url)
                        seen_ids.add(vid)
                    else:
                        print(f"⏩ Reel {vid} đã có trong lịch sử.")
                    break

            checked += 1
            if checked >= MAX_POSTS:
                break

        await context.close()


def run_stalker(page_url):
    asyncio.run(run_stalker_async(page_url))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("⚠️ Usage: python stalker.py <facebook_fanpage_url>")
        sys.exit(1)

    url = sys.argv[1]

    try:
        run_stalker(url)
    except Exception as e:
        print(f"❌ Lỗi trong stalker: {e}")

    sys.exit(0)