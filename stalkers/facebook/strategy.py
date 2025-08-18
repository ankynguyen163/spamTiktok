#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module defines the FacebookStalkerStrategy, which is responsible for
scraping video links from Facebook pages (fanpages and profiles) and
triggering their download using yt-dlp. It manages browser interaction
via Playwright, handles history tracking, and orchestrates the scraping
process in an asynchronous loop.
"""
import asyncio
import json
import re
import logging
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright, BrowserContext
from ..base_strategy import StalkerStrategy
from . import config as fb_config
from .downloader import download_video

def parse_video_id_from_href(href: str) -> str | None:
    """
    Extracts the video ID from various Facebook URL formats.

    This function uses regular expressions to find the video ID from URLs
    that might be for videos, reels, or watch pages.

    Args:
        href (str): The URL string from which to extract the video ID.

    Returns:
        str | None: The extracted video ID as a string, or None if no ID is found.
    """
    if not href: return None
    # Regex to capture IDs from video, reel, or watch URLs.
    # It looks for patterns like /videos/<ID>, /reel/<ID>, or ?v=<ID>
    match = re.search(r'/(?:videos|reel)(?:/[^/]+)*/(\d+)|[?&]v=(\d+)', href)
    return match.group(1) or match.group(2) if match else None

def _get_page_type(url: str) -> str:
    """
    Determines the type of Facebook page (fanpage or profile) based on the URL structure.

    Args:
        url (str): The URL of the Facebook page.

    Returns:
        str: A string indicating the page type (e.g., 'profile' or 'fanpage').
    """
    if "profile.php" in url:
        return fb_config.PAGE_TYPE_PROFILE
    return fb_config.PAGE_TYPE_FANPAGE

class FacebookStrategy(StalkerStrategy):
    """
    Strategy for scraping videos from Facebook pages, utilizing a pre-logged-in browser profile.
    This strategy extends StalkerStrategy to provide Facebook-specific scraping logic.
    """
    def __init__(self):
        """
        Initializes the FacebookStrategy.

        Sets up the scanning interval, loads the history of already processed video IDs,
        and ensures the Facebook-specific directory exists.
        """
        # Read configuration from the config file
        self.interval = fb_config.SCAN_INTERVAL_SECONDS
        self.history = self._load_history()
        self.downloading_ids = set()  # Track IDs currently being downloaded
        self.history_lock = asyncio.Lock()  # Lock for history and downloading_ids access
        fb_config.FB_DIR.mkdir(exist_ok=True) # Ensure the Facebook specific directory exists
    def get_targets(self) -> list[str]:
        """Đọc danh sách các fanpage/profile từ pages.txt."""
        if not fb_config.PAGES_FILE.exists():
            logging.warning(f"Không tìm thấy file mục tiêu tại: {fb_config.PAGES_FILE}")
            return []
        return [line.strip() for line in fb_config.PAGES_FILE.read_text().splitlines() if line.strip() and not line.startswith('#')]
    
    def login(self) -> bool:
        """
        Checks if the required Chrome profile for Facebook login exists and is valid.
        This method does not perform a login; it only verifies the presence of the.
        """
        # Check if the user data directory and its 'Default' sub-directory exist
        if not fb_config.PROFILE_DIR.exists() or not (fb_config.PROFILE_DIR / "Default").exists():
            logging.error("="*60)
            logging.error("Chrome profile for Facebook does not exist or is invalid.")
            logging.error(f"➡️  Please run the command: python cli.py login-fb")
            logging.error("="*60)
            return False
        logging.info("✅ Facebook profile found. Stalker is ready to operate.")
        return True
    
    def execute(self):
        """
        The main entry point for the Facebook Stalker, called by the manager.
        It runs an infinite asynchronous loop to continuously scrape data.
        Handles KeyboardInterrupt to allow graceful shutdown.
        """
        try:
            asyncio.run(self._main_loop())
        except KeyboardInterrupt:
            logging.info("Facebook Stalker received stop signal.")
    def _load_history(self) -> set:
        """
        Loads the history of already processed video IDs from a JSON file.

        Returns:
            set: A set containing the video IDs that have been previously scraped.
                 Returns an empty set if the history file does not exist or is unreadable.
        """
        if not fb_config.HISTORY_FILE.exists():
            return set()
        try:
            # Load history from JSON file, converting list to set for efficient lookup
            return set(json.loads(fb_config.HISTORY_FILE.read_text()))
        except (json.JSONDecodeError, IOError):
            logging.warning("Could not read history file, starting with an empty history.")
            return set()
        
    async def _save_history(self):
        """
        Saves the current history of processed video IDs to a JSON file.
        The history set is converted to a list before saving to JSON.
        This operation is protected by a lock to ensure thread safety.
        """
        async with self.history_lock:
            logging.debug("Acquired lock to save history.")
            fb_config.HISTORY_FILE.write_text(json.dumps(list(self.history), indent=2))
            logging.debug("Released lock after saving history.")

    def _launch_chrome(self) -> subprocess.Popen:
        """
        Launches a Chrome browser instance with a specific user profile and remote debugging enabled.
        This allows Playwright to connect to and control the browser.

        Returns:
            subprocess.Popen: The Popen object representing the launched Chrome process.
        """
        logging.info(f"🚀 Launching Chrome with Facebook profile on port {fb_config.CHROME_DEBUG_PORT}...")
        command = [
            fb_config.CHROME_EXECUTABLE,
            f"--user-data-dir={fb_config.PROFILE_DIR.resolve()}", # Specify the user profile directory
            f"--remote-debugging-port={fb_config.CHROME_DEBUG_PORT}", # Enable remote debugging
            *fb_config.CHROME_ARGS # Additional Chrome arguments from config
        ]
        # The commented-out section below shows how to redirect Chrome's stdout/stderr to log files.
        # This can be useful for debugging Chrome-specific issues.
        """
        log_path = fb_config.FB_DIR / "chrome_logs"
        log_path.mkdir(exist_ok=True)
        stdout_log = open(log_path / "chrome_stdout.log", "a")
        stderr_log = open(log_path / "chrome_stderr.log", "a")
        """
        # Start the Chrome process, capturing its stdout and stderr
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    async def _scrape_page(self, context: BrowserContext, page_url: str, limit: int) -> bool:
        """
        Scrapes video data from a given target URL (fanpage or profile).

        This function navigates to the page, scrolls to load content, extracts
        unique video IDs, and triggers the download for new videos in a
        thread-safe manner.

        Args:
            context (BrowserContext): The Playwright browser context to use.
            page_url (str): The URL of the Facebook page to scrape.
            limit (int): The maximum number of potential video links to process.

        Returns:
            bool: True if at least one new video was found and successfully
                  triggered for download, False otherwise.
        """
        page = None
        found_new_video = False
        page_type = _get_page_type(page_url)
        try:
            page = await context.new_page()
            logging.info(f"🕵️  Scanning page ({page_type}): {page_url}")
            await page.goto(page_url, wait_until="domcontentloaded", timeout=fb_config.PAGE_LOAD_TIMEOUT)
            await page.wait_for_timeout(fb_config.PAGE_WAIT_AFTER_LOAD)

            for i in range(fb_config.SCROLL_COUNT):
                logging.info(f"   [{page_url}] -> Scrolling down {i + 1}...")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(fb_config.SCROLL_DELAY_SECONDS * 1000)

            selector = fb_config.SELECTOR
            video_links = await page.locator(selector).all()
            logging.info(f"   -> [{page_url}] Found {len(video_links)} potential video links.")

            unique_video_ids_on_page = set()
            for link_element in video_links:
                href = await link_element.get_attribute("href")
                if href:
                    logging.info(f"   -> [{page_url}] Found video link: {href}")
                    
                    video_id = parse_video_id_from_href(href)
                    if video_id:
                        unique_video_ids_on_page.add(video_id)
            
            logging.info(f"   -> [{page_url}] Found {len(unique_video_ids_on_page)} unique video IDs to process.")

            for video_id in unique_video_ids_on_page:
                should_attempt_download = False
                # Lock to check history and claim a video for download
                async with self.history_lock:
                    if video_id not in self.history and video_id not in self.downloading_ids:
                        self.downloading_ids.add(video_id)
                        should_attempt_download = True

                if should_attempt_download:
                    logging.info(f"   -> 🆕 New video detected, attempting download: {video_id}")
                    video_full_url = f"https://www.facebook.com/watch/?v={video_id}"
                    
                    download_successful = await download_video(video_full_url, video_id)

                    # Lock again to update history based on download result
                    async with self.history_lock:
                        self.downloading_ids.remove(video_id)  # Unclaim the video
                        if download_successful:
                            logging.info(f"   -> ✅ Download successful for {video_id}. Adding to history.")
                            self.history.add(video_id)
                            found_new_video = True  # Mark that we need to save history
                        else:
                            logging.warning(f"   -> ⚠️ Download failed for {video_id}. It will be retried next cycle.")

        except Exception as e:
            logging.error(f"   -> ❌ Error processing page {page_url}: {e}", exc_info=False)
        finally:
            if page:
                await page.close()
        return found_new_video
    
    async def _process_target(self, context: BrowserContext, target_url: str):
        """
        Điều phối việc cào dữ liệu từ trang mục tiêu.
        """
        # Lấy tên để log, xử lý cả hai dạng URL
        parsed_url = urlparse(target_url)
        if "profile.php" in target_url:
            target_name = f"profile_{parse_qs(parsed_url.query).get('id', ['unknown'])[0]}"
        else:
            target_name = Path(target_url).name
        logging.info(f"--- Bắt đầu xử lý mục tiêu: {target_name} ---")
        found_new_video = await self._scrape_page(context, target_url, limit=fb_config.MAX_LINKS_PER_SECTION)
        if found_new_video:
            await self._save_history()
        else:
            logging.info(f"   -> ✅ Không có video mới cho mục tiêu: {target_name}")
            
    async def _main_loop(self):
        """Vòng lặp chính chạy Stalker, có khả năng tự khởi động lại Chrome nếu gặp sự cố."""
        while True:
            chrome_process = self._launch_chrome()
            time.sleep(5)
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.connect_over_cdp(f"http://localhost:{fb_config.CHROME_DEBUG_PORT}", timeout=60000)
                    context = browser.contexts[0]
                    logging.info("✅ Kết nối thành công tới trình duyệt Chrome.")
                    while True:
                        targets = self.get_targets()
                        if not targets:
                            logging.warning("Danh sách mục tiêu trống. Vui lòng thêm URL vào 'stalkers/facebook/pages.txt'.")
                            logging.info(f"Sẽ thử lại sau {self.interval} giây.")
                            await asyncio.sleep(self.interval)
                            continue
                        logging.info(f"Bắt đầu chu trình quét mới cho {len(targets)} mục tiêu, batch size = {fb_config.FACEBOOK_BATCH_SIZE}.")
                        for i in range(0, len(targets), fb_config.FACEBOOK_BATCH_SIZE):
                            batch = targets[i:i + fb_config.FACEBOOK_BATCH_SIZE]
                            current_batch_num = i // fb_config.FACEBOOK_BATCH_SIZE + 1
                            total_batches = (len(targets) + fb_config.FACEBOOK_BATCH_SIZE - 1) // fb_config.FACEBOOK_BATCH_SIZE
                            logging.info(f"Đang xử lý batch [{current_batch_num}/{total_batches}] với {len(batch)} mục tiêu.")
                            tasks = [self._process_target(context, url) for url in batch]
                            await asyncio.gather(*tasks)
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
            await asyncio.sleep(30)