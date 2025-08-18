import asyncio
import sys
import time
import logging
import os
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError, Page, BrowserContext
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# Import from shared modules
from Tiktok.config import (
    TT_STUDIO_UPLOAD_URL,
    TT_CONFIRM_POST_BUTTON_SELECTOR,
    TT_SELECT_VIDEO_BUTTON_XPATH,
    TT_CAPTION_INPUT_SELECTOR,
    TT_UPLOAD_PROGRESS_SUCCESS_SELECTOR,
    TT_POST_BUTTON_SELECTOR,
    CHROME_DEBUG_PORT,
    MAX_CONCURRENT_UPLOADS
)
from Tiktok.utils import (
    get_profile_dir, open_chrome_for_automation, get_video_id,
    get_id_from_stem, get_video_stalker_dir, get_description,
    is_uploaded, save_upload_history, get_all_videos, find_video_source
)
from .utils import clean_caption, generate_hashtags
# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
# --- Helper Functions ---

        
def get_upload_candidates(account_name: str, show_list=True):
    """Lấy danh sách các video có thể upload (chưa được upload bởi tài khoản này)."""
    videos = get_all_videos()
    if not videos:
        if show_list:
            logging.info("📭 Không có video nào để upload.")
        return []
    upload_candidates = []
    if show_list:
        logging.info("📹 Các video có sẵn để upload:")
    count = 0
    for video in videos:
        video_id = video.stem
        # Chấp nhận upload trùng video cũ đề phòng đang phát live ?????
        if is_uploaded(video_id, account_name):
            continue
        source, _ = find_video_source(video_id)
        source_display = source.upper() if source else "N/A"
        count += 1
        description = get_description(video_id) or ""
        if show_list:
            logging.info(f"{count:2}. [{source_display}] {video.name}")
        upload_candidates.append({
            "video_path": str(video),
            "video_id": video_id,
            "source": source,
            "description": description
        })
    if not upload_candidates and show_list:
        logging.info("✅ Tất cả video đã được đăng.")
    return upload_candidates



# --- Core Upload Logic ---

async def complete_upload_process(page, video_id, description, source, account_name):
    """Hoàn tất các bước cuối của quá trình upload sau khi đã chọn file."""
    logging.info(f"📄 Bắt đầu hoàn tất upload cho Video ID: {video_id} [{source.upper()}]")
    logging.info(f"   📝 Mô tả: {description if description else 'Không có mô tả'}")
    if is_uploaded(video_id, account_name):
        logging.warning(f"⚠️ Video {video_id} đã được tài khoản này upload. Bỏ qua.")
        return False
    clean_desc = clean_caption(description)
    full_caption = (clean_desc + "\n\n" + generate_hashtags()) if description else generate_hashtags()
    try:
        caption_input = page.locator(TT_CAPTION_INPUT_SELECTOR)
        try:
            await caption_input.wait_for(state="visible", timeout=30000)
        except TimeoutError:
            logging.error(f"❌ Timeout: Không tìm thấy ô nhập caption cho video {video_id}.")
            try:
                await page.screenshot(path=f"error_caption_timeout_{video_id}.png")
            except Exception as screenshot_error:
                logging.error(f"📸 Không thể chụp ảnh màn hình: {screenshot_error}")
            return False
        await caption_input.fill('')
        await caption_input.fill(full_caption)
        logging.info("✍️  Đã điền caption.")
        logging.info("⏳ Đang chờ video tải lên server TikTok (có thể mất vài phút)...")
        try:
            await page.wait_for_selector(TT_UPLOAD_PROGRESS_SUCCESS_SELECTOR, timeout=600_000)
        except TimeoutError:
            logging.error(f"❌ Timeout: Video {video_id} tải lên server TikTok quá lâu.")
            try:
                await page.screenshot(path=f"error_upload_timeout_{video_id}.png")
            except Exception as screenshot_error:
                logging.error(f"📸 Không thể chụp ảnh màn hình: {screenshot_error}")
            return False
        logging.info("✅ Video đã được tải lên server TikTok thành công.")
        post_button = page.locator(TT_POST_BUTTON_SELECTOR).first
        try:
            await post_button.wait_for(state="visible", timeout=30000)
        except TimeoutError:
            logging.error(f"❌ Timeout: Không tìm thấy nút 'Đăng' cho video {video_id}.")
            try:
                await page.screenshot(path=f"error_post_button_timeout_{video_id}.png")
            except Exception as screenshot_error:
                logging.error(f"📸 Không thể chụp ảnh màn hình: {screenshot_error}")
            return False
        await post_button.click()
        logging.info("🅿️  Đã bấm nút 'Đăng', chờ xác nhận...")
        try:
            confirm_post_button = page.locator(TT_CONFIRM_POST_BUTTON_SELECTOR)
            await confirm_post_button.wait_for(state="visible", timeout=5000)
            logging.info("...Phát hiện modal xác nhận. Đang click 'Đăng ngay'...")
            await confirm_post_button.click()
            await confirm_post_button.wait_for(state="hidden", timeout=10000)
        except (TimeoutError, Exception):
            logging.info("...Không có modal xác nhận hoặc đã hết thời gian chờ. Tiếp tục...")

        try:
            await post_button.wait_for(state="hidden", timeout=60000)
        except TimeoutError:
            logging.warning(f"⚠️ Timeout: Nút 'Đăng' không biến mất sau khi click cho video {video_id}. Có thể video vẫn đang được xử lý.")
            try:
                await page.screenshot(path=f"error_post_disappear_timeout_{video_id}.png")
            except Exception as screenshot_error:
                logging.error(f"📸 Không thể chụp ảnh màn hình: {screenshot_error}")
            
        logging.info(f"🚀 Đã gửi yêu cầu đăng video {video_id}.")
        save_upload_history(video_id, description, account_name)
        logging.info(f"--- ✅ Hoàn tất xử lý cho: {video_id} ---")
        logging.info("ℹ️  File video gốc vẫn được giữ lại. Dùng lệnh 'clean-uploaded' để dọn dẹp sau.")
        return True
    except Exception as e:
        logging.error(f"❌ Lỗi trong hàm complete_upload_process cho video {video_id}: {e}")
        try:
            await page.screenshot(path=f"error_complete_upload_{video_id}.png")
        except Exception as screenshot_error:
            logging.error(f"📸 Không thể chụp ảnh màn hình: {screenshot_error}")
        return False
    



# --- Watchdog Event Handler (FINAL FIX) ---

class VideoReadyHandler(FileSystemEventHandler):
    """
    Chỉ xử lý sự kiện khi file video đã được ghi xong và đóng lại.
    Sử dụng asyncio.run_coroutine_threadsafe để giao tiếp an toàn với luồng chính.
    Bỏ qua các file tạm (.temp.mp4).
    """
    def __init__(self, upload_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self.upload_queue = upload_queue
        self.loop = loop
        self.video_extensions = ('.mp4', '.mov', '.avi', '.mkv')

    def _is_valid_file(self, file_path: str) -> bool:
        """Kiểm tra xem file có phải là file video hợp lệ và không phải file tạm."""
        # Bỏ qua nếu không phải là video extension
        if not file_path.endswith(self.video_extensions):
            return False
        # Bỏ qua nếu là file tạm
        if ".temp." in file_path or file_path.endswith(".tmp"):
            logging.info(f"🔎 Phát hiện file tạm, bỏ qua: {os.path.basename(file_path)}")
            return False
        return True
    
    def on_closed(self, event):
        """Được gọi khi một file đã được mở để ghi và sau đó được đóng."""
        if event.is_directory:
            return
        if self._is_valid_file(event.src_path):
            try:
                # Đảm bảo file có kích thước > 0 để tránh các file tạm rỗng
                if os.path.getsize(event.src_path) > 1024: # Kích thước tối thiểu 1KB
                    logging.info(f"✅ File đã ổn định: {os.path.basename(event.src_path)}. Đang đưa vào hàng đợi...")
                    # Sử dụng cầu nối an toàn để đưa item vào queue từ luồng của Watchdog
                    asyncio.run_coroutine_threadsafe(self.upload_queue.put(event.src_path), self.loop)
                else:
                    logging.warning(f"⚠️ Bỏ qua file có kích thước nhỏ: {event.src_path}")
            except (IOError, OSError) as e:
                logging.error(f"⚠️ Không thể truy cập file '{event.src_path}' ngay sau khi đóng: {e}")

    def on_moved(self, event):
        """Được gọi khi file được di chuyển hoặc đổi tên."""
        if event.is_directory:
            return
        # Sự kiện on_moved quan trọng vì file .temp.mp4 được đổi tên thành .mp4
        logging.info(f"🚚 File đã được di chuyển/đổi tên tới: {os.path.basename(event.dest_path)}")
        # Gọi lại logic của on_closed cho file đích
        self.on_closed(type('obj', (object,), {'src_path': event.dest_path, 'is_directory': False}))


# --- Mode-specific Logic ---

async def upload_processor(queue: asyncio.Queue, account_name: str, context: BrowserContext, worker_id: int):
    """
    Một "công nhân" lấy video từ hàng đợi và xử lý việc upload trên một tab riêng.
    Worker sẽ tự phục hồi bằng cách tạo tab mới nếu gặp lỗi nghiêm trọng.
    """
    page = await context.new_page()
    logging.info(f"[Worker {worker_id}] Bắt đầu, điều hướng đến trang upload...")
    await page.goto(TT_STUDIO_UPLOAD_URL, wait_until="domcontentloaded")

    while True:
        video_path_str = await queue.get()
        video_path = Path(video_path_str)
        video_id = get_video_id(video_path)
        logging.info(f"[Worker {worker_id}] Đã nhận video: {video_id}")

        try:
            if not os.path.exists(video_path_str):
                logging.warning(f"⚠️ [Worker {worker_id}] File {os.path.basename(video_path_str)} không còn tồn tại. Bỏ qua.")
                continue
            if is_uploaded(video_id, account_name):
                logging.info(f"🔵 [Worker {worker_id}] Video {video_id} đã được xử lý. Bỏ qua.")
                continue

            source, _ = find_video_source(video_id)
            description = get_description(video_id) or ""
            logging.info(f"--- 📤 [Worker {worker_id}] Bắt đầu upload: {video_id} ---")

            # Đảm bảo trang không bị treo
            if page.is_closed():
                logging.warning(f"[Worker {worker_id}] Trang đã bị đóng. Tạo lại trang mới...")
                page = await context.new_page()
                await page.goto(TT_STUDIO_UPLOAD_URL, wait_until="domcontentloaded")

            # Chọn file và upload
            await page.locator(TT_SELECT_VIDEO_BUTTON_XPATH).wait_for(state="visible", timeout=60000)
            async with page.expect_file_chooser(timeout=30000) as fc_info:
                await page.locator(TT_SELECT_VIDEO_BUTTON_XPATH).click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(video_path_str, timeout=30000)
            
            logging.info(f"📂 [Worker {worker_id}] Đã chọn file: {video_path.name}")
            success = await complete_upload_process(page, video_id, description, source, account_name)
            
            if success:
                logging.info(f"✅ [Worker {worker_id}] Upload thành công {video_id}.")
                await page.goto(TT_STUDIO_UPLOAD_URL, wait_until="domcontentloaded")
            else:
                logging.warning(f"⚠️ [Worker {worker_id}] Upload thất bại cho {video_id}. Tải lại trang.")
                await page.goto(TT_STUDIO_UPLOAD_URL, wait_until="domcontentloaded")

        except Exception as e:
            error_message = str(e)
            logging.error(f"❌ [Worker {worker_id}] Lỗi nghiêm trọng khi upload {video_id}: {error_message}")
            try:
                await page.screenshot(path=f"error_auto_worker_{worker_id}_{video_id}.png")
            except Exception as screenshot_error:
                logging.error(f"📸 Không thể chụp ảnh màn hình (trang có thể đã crash): {screenshot_error}")

            # Logic xử lý lỗi và retry
            if "Cannot transfer files larger than 50Mb" in error_message:
                logging.error(f"🚫 [Worker {worker_id}] File quá lớn, sẽ không thử lại video này.")
            else:
                logging.warning(f"🚨 [Worker {worker_id}] Lỗi không xác định, sẽ thử lại video sau.")
                await queue.put(video_path_str) # Đưa video lại hàng đợi
            
            # Phục hồi worker để xử lý video tiếp theo
            logging.warning(f"🚨 [Worker {worker_id}] Đang cố gắng khởi tạo lại tab cho worker...")
            try:
                if not page.is_closed():
                    await page.close()
                page = await context.new_page()
                await page.goto(TT_STUDIO_UPLOAD_URL, wait_until="domcontentloaded")
                logging.info(f"✅ [Worker {worker_id}] Đã tạo lại tab thành công và sẵn sàng cho video tiếp theo.")
            except Exception as recovery_error:
                logging.critical(f"💀 [Worker {worker_id}] KHÔNG THỂ PHỤC HỒI. Worker này sẽ dừng. Lỗi: {recovery_error}")
                break # Thoát khỏi vòng lặp while, kết thúc worker này
        finally:
            queue.task_done()

async def run_auto_mode(account_name: str):
    """Chạy chế độ upload tự động hoàn toàn, sử dụng Watchdog và nhiều worker song song."""

    upload_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
 
    open_chrome_for_automation(account_name)
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{CHROME_DEBUG_PORT}", timeout=60000)
            context = browser.contexts[0]
        except TimeoutError:
            logging.error(f"❌ Timeout: Không thể kết nối tới Chrome qua CDP trong 60 giây.")
            logging.error("Hãy chắc chắn rằng Chrome đã được mở và cổng gỡ lỗi là chính xác.")
            return
        except Exception as e:
            logging.error(f"❌ Không thể kết nối tới Chrome qua CDP. Lỗi: {e}")
            logging.error("Hãy chắc chắn rằng không có tiến trình Chrome nào khác đang chạy với cùng một profile hoặc cổng gỡ lỗi.")
            return

        # --- Worker Pool Setup ---
        num_workers = MAX_CONCURRENT_UPLOADS
        logging.info(f"🚀 Khởi tạo {num_workers} worker(s) để upload song song.")
        tasks = []
        for i in range(num_workers):
            # Truyền context vào mỗi worker để chúng có thể tự tạo lại page
            task = asyncio.create_task(upload_processor(upload_queue, account_name, context, worker_id=i+1))
            tasks.append(task)
            
        logging.info("🔍 Quét các video đã có...")
        initial_candidates = get_upload_candidates(account_name, show_list=False)
        if initial_candidates:
            logging.info(f"📋 Tìm thấy {len(initial_candidates)} video có sẵn để đưa vào hàng đợi.")
            for video_info in initial_candidates:
                await upload_queue.put(video_info["video_path"])
        else:
            logging.info("✅ Không có video nào cần xử lý ngay.")
        # --- Watchdog Setup ---
        event_handler = VideoReadyHandler(upload_queue, loop)
        observer = Observer()
        facebook_video_dir = get_video_stalker_dir('fb')
        if facebook_video_dir and facebook_video_dir.exists():
            observer.schedule(event_handler, str(facebook_video_dir), recursive=True)
            logging.info(f"👁️  Đang theo dõi thư mục Facebook: {facebook_video_dir}")
        if not observer.emitters:
            logging.warning("⚠️ Không có thư mục nào được theo dõi. Watchdog sẽ không hoạt động.")
        else:
            observer.start()
            logging.info("👂 Lắng nghe video mới... (Nhấn Ctrl+C để dừng)")
        try:
            # Chạy tất cả các worker cho đến khi bị ngắt
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logging.info("\n🛑 Dừng bởi người dùng.")
        finally:
            if observer.is_alive():
                observer.stop()
                observer.join()
            logging.info("✋ Đã dừng theo dõi.")
            # Hủy các task còn chạy
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await context.close()
            logging.info("✅ Đã đóng trình duyệt và dọn dẹp.")

async def run_manual_mode(account_name: str):
    """Chạy chế độ upload thủ công (người dùng chọn file)."""
    open_chrome_for_automation(account_name, url=TT_STUDIO_UPLOAD_URL)
    logging.info("📤 Vui lòng chọn video để upload trong cửa sổ Chrome vừa mở...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{CHROME_DEBUG_PORT}", timeout=60000)
        except TimeoutError:
            logging.error(f"❌ Timeout: Không thể kết nối tới Chrome qua CDP trong 60 giây.")
            logging.error("Hãy chắc chắn rằng Chrome đã được mở và cổng gỡ lỗi là chính xác.")
            return
        except Exception as e:
            logging.error(f"❌ Không thể kết nối tới Chrome qua CDP. Lỗi: {e}")
            return
        page = next((pg for pg in browser.contexts[0].pages if "upload" in pg.url), None)
        if not page:
            logging.error("❌ Không tìm thấy trang upload của TikTok. Vui lòng thử lại.")
            await browser.close()
            return
        await page.bring_to_front()
        try:
            logging.info("⏳ Đang chờ bạn chọn file video trong trình duyệt...")
            caption_input = page.locator(TT_CAPTION_INPUT_SELECTOR)
            try:
                await caption_input.wait_for(state="visible", timeout=300_000)
            except TimeoutError:
                logging.error("❌ Timeout: Bạn đã không chọn file video trong 5 phút.")
                try:
                    await page.screenshot(path="error_manual_no_file_selected.png")
                except Exception as screenshot_error:
                    logging.error(f"📸 Không thể chụp ảnh màn hình: {screenshot_error}")
                return

            logging.info("⏳ Đang chờ TikTok xử lý video và điền tên file vào caption...")
            try:
                await page.wait_for_function(
                    "document.querySelector('div.public-DraftEditor-content').innerText.trim() !== ''",
                    timeout=300_000
                )
            except TimeoutError:
                logging.error("❌ Timeout: TikTok đã không xử lý video và điền caption sau 5 phút.")
                try:
                    await page.screenshot(path="error_manual_caption_fill_timeout.png")
                except Exception as screenshot_error:
                    logging.error(f"📸 Không thể chụp ảnh màn hình: {screenshot_error}")
                return

            video_id_full = (await caption_input.inner_text()).strip()
            video_id = get_id_from_stem(video_id_full)
            video_source, _ = find_video_source(video_id)
            description = get_description(video_id) or ""
            logging.info(f"   📝 Mô tả: {description or 'Không có mô tả'}")
            await complete_upload_process(page, video_id, description, video_source, account_name)
            logging.info("\n✅ Hoàn tất. Bạn có thể đóng cửa sổ Chrome hoặc upload video tiếp theo.")
        except Exception as e:
            logging.error(f"❌ Lỗi trong quá trình upload thủ công: {e}")
            try:
                await page.screenshot(path=f"error_manual.png")
            except Exception as screenshot_error:
                logging.error(f"📸 Không thể chụp ảnh màn hình: {screenshot_error}")
        finally:
            await browser.close()

def print_usage():
    """In hướng dẫn sử dụng."""
    # This is the old usage string as requested
    print("Usage: python -m Tiktok.spamUploadTiktok <command> <account_name> [options]")
    print("\nCommands:")
    print("  manual <account>      - 🚀 Bắt đầu quá trình upload thủ công cho một tài khoản.")
    print("  auto   <account>      - 🤖 Bắt đầu quá trình upload tự động cho một tài khoản.")
    print("  list   <account>      - 📋 Liệt kê các video chưa được upload cho một tài khoản.")
    print("\nVí dụ:")
    print("  python -m Tiktok.spamUploadTiktok auto my_account_1")
    print("  python -m Tiktok.spamUploadTiktok list my_account_2")

def main():
    """Hàm main chính, điều hướng dựa trên đối số dòng lệnh."""
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    command = sys.argv[1].lower()
    account_name = sys.argv[2]
    # --- Account Validation ---
    profile_dir = get_profile_dir(account_name)
    if not profile_dir.is_dir():
        logging.error(f"❌ Lỗi: Tài khoản '{account_name}' không tồn tại.")
        logging.error(f"   Kiểm tra lại trong thư mục: {profile_dir.parent}")
        sys.exit(1)
    logging.info(f"✅ Sử dụng tài khoản: {account_name}")
    try:
        if command == "auto":
            asyncio.run(run_auto_mode(account_name))
        elif command == "manual":
            asyncio.run(run_manual_mode(account_name))
        elif command == "list":
            get_upload_candidates(account_name, show_list=True)
        else:
            logging.error(f"❌ Lệnh không hợp lệ: '{command}'\n")
            print_usage()
            sys.exit(1)
    except KeyboardInterrupt:
        logging.info("\n🛑 Dừng bởi người dùng.")
    except Exception as e:
        logging.critical(f"\n🛑 Lỗi không xác định trong quá trình chạy: {e}", exc_info=True)
if __name__ == "__main__":
    main()
