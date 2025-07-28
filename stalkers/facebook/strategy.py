#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import re
import logging
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright, BrowserContext

from ..base_strategy import StalkerStrategy
from . import config as fb_config
from .fb_vid import download_video

def parse_video_id_from_href(href: str) -> str | None:
    """Trích xuất video ID từ các định dạng URL Facebook khác nhau."""
    if not href: return None
    match = re.search(r'/(?:videos|reel)/(\d+)|[?&]v=(\d+)', href)
    return match.group(1) or match.group(2) if match else None

class FacebookStrategy(StalkerStrategy):
    """
    Chiến lược cào video từ các trang Facebook, sử dụng lại profile đã đăng nhập.
    """

    def __init__(self):
        """
        Khởi tạo chiến lược.
        """
        # Đọc cấu hình từ file config
        self.interval = fb_config.SCAN_INTERVAL_SECONDS
        self.history = self._load_history()
        fb_config.FB_DIR.mkdir(exist_ok=True) # Đảm bảo thư mục tồn tại

    def get_targets(self) -> list[str]:
        """Đọc danh sách các fanpage/profile từ pages.txt."""
        if not fb_config.PAGES_FILE.exists():
            logging.warning(f"Không tìm thấy file mục tiêu tại: {fb_config.PAGES_FILE}")
            return []
        return [line.strip() for line in fb_config.PAGES_FILE.read_text().splitlines() if line.strip() and not line.startswith('#')]

    def login(self) -> bool:
        """
        Kiểm tra xem profile đăng nhập đã tồn tại chưa.
        Không thực hiện đăng nhập, chỉ kiểm tra điều kiện cần.
        """
        if not fb_config.PROFILE_DIR.exists() or not (fb_config.PROFILE_DIR / "Default").exists():
            logging.error("="*60)
            logging.error("Profile Chrome cho Facebook không tồn tại hoặc không hợp lệ.")
            logging.error(f"➡️  Vui lòng chạy lệnh: python cli.py login-fb")
            logging.error("="*60)
            return False
        logging.info("✅ Đã tìm thấy profile Facebook. Stalker sẵn sàng hoạt động.")
        return True

    def execute(self):
        """
        Entrypoint chính, được gọi bởi manager.
        Chạy một vòng lặp vô tận để cào dữ liệu.
        """
        try:
            asyncio.run(self._main_loop())
        except KeyboardInterrupt:
            logging.info("Facebook Stalker nhận được tín hiệu dừng.")

    def _load_history(self) -> set:
        """Tải lịch sử các video ID đã cào."""
        if not fb_config.HISTORY_FILE.exists():
            return set()
        try:
            return set(json.loads(fb_config.HISTORY_FILE.read_text()))
        except (json.JSONDecodeError, IOError):
            logging.warning("Không thể đọc file lịch sử, bắt đầu với lịch sử trống.")
            return set()

    def _save_history(self):
        """Lưu lịch sử các video ID đã cào."""
        fb_config.HISTORY_FILE.write_text(json.dumps(list(self.history), indent=2))
    
    def _launch_chrome(self):
        """Mở Chrome với profile và remote debugging."""
        logging.info(f"🚀 Mở Chrome với profile Facebook trên cổng {fb_config.CHROME_DEBUG_PORT}...")
        command = [
            fb_config.CHROME_EXECUTABLE,
            f"--user-data-dir={fb_config.PROFILE_DIR.resolve()}",
            f"--remote-debugging-port={fb_config.CHROME_DEBUG_PORT}",
            *fb_config.CHROME_ARGS
        ]
        return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async def _scrape_subpage(self, context: BrowserContext, base_url: str, sub_path: str, limit: int) -> bool:
        """
        Cào dữ liệu từ một trang con cụ thể (videos hoặc reels) của một mục tiêu.
        Trả về True nếu tìm thấy và tải được video mới.
        """
        page = None
        found_new_video = False
        try:
            page = await context.new_page()
            full_url = f"{base_url.strip('/')}/{sub_path}"
            logging.info(f"🕵️  Đang quét trang: {full_url}")
            await page.goto(full_url, wait_until="domcontentloaded", timeout=fb_config.PAGE_LOAD_TIMEOUT)
            await page.wait_for_timeout(fb_config.PAGE_WAIT_AFTER_LOAD) # Chờ một chút để các video tải

            # Sử dụng selector cụ thể cho từng trang con để tăng độ chính xác
            selector_map = {
                "videos": 'a[href*="/videos/"], a[href*="/watch/?v="]',
                "reels": 'a[href*="/reel/"]'
            }
            # Mặc định dùng selector chung nếu sub_path không có trong map
            selector = selector_map.get(sub_path, 'a[href*="/videos/"], a[href*="/watch/?v="], a[href*="/reel/"]')
            video_links = await page.locator(selector).all()
            logging.info(f"   -> [{sub_path.upper()}] Tìm thấy {len(video_links)} liên kết video tiềm năng.")

            # Chỉ xử lý N video đầu tiên theo cấu hình
            links_to_process = video_links[:limit]
            logging.info(f"   -> [{sub_path.upper()}] Giới hạn xử lý {len(links_to_process)} liên kết đầu tiên.")
            for link_element in links_to_process:
                href = await link_element.get_attribute("href")
                video_id = parse_video_id_from_href(href)

                if video_id and video_id not in self.history:
                    logging.info(f"   -> 🆕 Phát hiện video mới: {video_id}")
                    video_full_url = f"https://www.facebook.com{href}" if href.startswith('/') else href

                    if await download_video(video_full_url, video_id):
                        found_new_video = True
                        self.history.add(video_id)
        except Exception as e:
            logging.error(f"   -> ❌ Lỗi khi xử lý trang {full_url}: {e}", exc_info=False) # exc_info=False để log gọn hơn
        finally:
            if page:
                await page.close()
        return found_new_video

    async def _process_target(self, context: BrowserContext, target_url: str):
        """
        Điều phối việc cào dữ liệu từ các trang con (/videos, /reels) của một mục tiêu.
        """
        target_name = Path(target_url).name
        logging.info(f"--- Bắt đầu xử lý mục tiêu: {target_name} ---")
        sub_pages = fb_config.SUB_PAGES_TO_SCAN
        
        # Tạo các "agent" (task) để chạy song song cho mỗi trang con
        logging.info(f"   -> Khởi tạo các agent song song cho: {', '.join(sub_pages)}")
        tasks = [
            self._scrape_subpage(context, target_url, sub_path, limit=fb_config.MAX_VIDEOS_PER_SECTION)
            for sub_path in sub_pages
        ]
        
        # Chạy các agent và đợi kết quả
        results = await asyncio.gather(*tasks)
        any_new_video_found = any(results)

        if any_new_video_found:
            self._save_history() # Chỉ lưu lịch sử một lần sau khi quét xong tất cả các trang con
        else:
            logging.info(f"   -> ✅ Không có video mới cho mục tiêu: {target_name}")

    async def _main_loop(self):
        """Vòng lặp chính chạy Stalker, có khả năng tự khởi động lại Chrome nếu gặp sự cố."""
        while True: # Vòng lặp ngoài cùng để đảm bảo Stalker luôn chạy
            chrome_process = self._launch_chrome()
            time.sleep(5) # Chờ Chrome khởi động

            try:
                async with async_playwright() as p:
                    # Tăng timeout để có thêm thời gian kết nối
                    browser = await p.chromium.connect_over_cdp(f"http://localhost:{fb_config.CHROME_DEBUG_PORT}", timeout=60000)
                    context = browser.contexts[0]
                    logging.info("✅ Kết nối thành công tới trình duyệt Chrome.")
                    # Vòng lặp quét định kỳ
                    while True:
                        targets = self.get_targets()
                        if not targets:
                            logging.warning("Danh sách mục tiêu trống. Vui lòng thêm URL vào 'stalkers/facebook/pages.txt'.")
                            logging.info(f"Sẽ thử lại sau {self.interval} giây.")
                            await asyncio.sleep(self.interval)
                            continue

                        logging.info(f"Bắt đầu chu trình quét mới cho {len(targets)} mục tiêu, batch size = {fb_config.FACEBOOK_BATCH_SIZE}.")

                        # Chia targets thành các batch để xử lý
                        for i in range(0, len(targets), fb_config.FACEBOOK_BATCH_SIZE):
                            batch = targets[i:i + fb_config.FACEBOOK_BATCH_SIZE]
                            current_batch_num = i // fb_config.FACEBOOK_BATCH_SIZE + 1
                            total_batches = (len(targets) + fb_config.FACEBOOK_BATCH_SIZE - 1) // fb_config.FACEBOOK_BATCH_SIZE

                            logging.info(f"Đang xử lý batch [{current_batch_num}/{total_batches}] với {len(batch)} mục tiêu.")
                            tasks = [self._process_target(context, url) for url in batch]
                            await asyncio.gather(*tasks)

                            # Nếu đây không phải là batch cuối cùng, đợi một chút
                            if i + fb_config.FACEBOOK_BATCH_SIZE < len(targets):
                                logging.info(f"Đợi {fb_config.WAIT_BETWEEN_BATCHES_SECONDS} giây trước khi xử lý batch tiếp theo.")
                                await asyncio.sleep(fb_config.WAIT_BETWEEN_BATCHES_SECONDS)

                        logging.info(f"✅ Hoàn thành chu trình. Nghỉ {self.interval} giây.")
                        await asyncio.sleep(self.interval)
            except Exception as e:
                logging.error(f"Lỗi nghiêm trọng với trình duyệt hoặc kết nối: {e}. Sẽ khởi động lại sau 30 giây.")
            finally:
                logging.info("Đang dọn dẹp và đóng tiến trình Chrome hiện tại...")
                if chrome_process:
                    chrome_process.terminate()
                    chrome_process.wait()
            
            await asyncio.sleep(30) # Đợi một khoảng thời gian an toàn trước khi khởi động lại