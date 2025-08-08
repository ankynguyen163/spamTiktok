import asyncio
import sys
import subprocess
import time
import logging
import os
from pathlib import Path
from playwright.async_api import async_playwright
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import from shared modules
from Tiktok.config import (
    get_profile_dir,
    get_description,
    is_uploaded,
    save_upload_history,
    get_all_videos,
    find_video_source,
    TT_CONFIRM_POST_BUTTON_SELECTOR,
    TT_SELECT_VIDEO_BUTTON_XPATH,
    TT_CAPTION_INPUT_SELECTOR,
    TT_UPLOAD_PROGRESS_SUCCESS_SELECTOR,
    TT_POST_BUTTON_SELECTOR,
    get_video_stalker_dir,
)
from .utils import clean_caption, generate_hashtags

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- Helper Functions ---

def open_chrome_for_automation(account_name: str, port=9222, url=None):
    """Mở Chrome với profile và cổng gỡ lỗi được chỉ định."""
    command = [
        "google-chrome",
        f"--user-data-dir={get_profile_dir(account_name)}",
        f"--remote-debugging-port={port}",
        "--new-window",
    ]
    if url:
        command.append(url)
    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info(f"🚀 Đã yêu cầu mở Chrome profile '{account_name}' trên cổng {port}.")
        time.sleep(3) # Chờ một chút để trình duyệt khởi động
    except FileNotFoundError:
        logging.error("Lỗi: Lệnh 'google-chrome' không được tìm thấy. Vui lòng cài đặt Google Chrome.")
        sys.exit(1)


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
    if is_uploaded(video_id, account_name):
        logging.warning(f"⚠️ Video {video_id} đã được tài khoản này upload. Bỏ qua.")
        return False

    clean_desc = clean_caption(description)
    full_caption = (clean_desc + "\n\n" + generate_hashtags()) if clean_desc else generate_hashtags()
    
    try:
        caption_input = page.locator(TT_CAPTION_INPUT_SELECTOR)
        await caption_input.wait_for(state="visible", timeout=30000)
        await caption_input.fill('')
        await caption_input.fill(full_caption)
        logging.info("✍️  Đã điền caption.")

        logging.info("⏳ Đang chờ video tải lên server TikTok (có thể mất vài phút)...")
        await page.wait_for_selector(TT_UPLOAD_PROGRESS_SUCCESS_SELECTOR, timeout=600_000)
        logging.info("✅ Video đã được tải lên server TikTok thành công.")

        post_button = page.locator(TT_POST_BUTTON_SELECTOR).first
        await post_button.wait_for(state="visible", timeout=30000)
        await post_button.click()
        logging.info("🅿️  Đã bấm nút 'Đăng', chờ xác nhận...")
        
        try:
            confirm_post_button = page.locator(TT_CONFIRM_POST_BUTTON_SELECTOR)
            await confirm_post_button.wait_for(state="visible", timeout=5000)
            logging.info("...Phát hiện modal xác nhận. Đang click 'Đăng ngay'...")
            await confirm_post_button.click()
            await confirm_post_button.wait_for(state="hidden", timeout=10000)
        except Exception:
            logging.info("...Không có modal xác nhận hoặc đã hết thời gian chờ. Tiếp tục...")

        await post_button.wait_for(state="hidden", timeout=60000)
        logging.info(f"🚀 Đã gửi yêu cầu đăng video {video_id}.")
        
        save_upload_history(video_id, description, account_name)
        logging.info(f"--- ✅ Hoàn tất xử lý cho: {video_id} ---")
        logging.info("ℹ️  File video gốc vẫn được giữ lại. Dùng lệnh 'clean-uploaded' để dọn dẹp sau.")
        return True
    except Exception as e:
        logging.error(f"❌ Lỗi trong hàm complete_upload_process cho video {video_id}: {e}")
        await page.screenshot(path=f"error_complete_upload_{video_id}.png")
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

async def upload_processor(queue: asyncio.Queue, account_name: str, page):
    """
    Liên tục lấy video từ hàng đợi và xử lý việc upload.
    Đây là "công nhân" chính của chế độ tự động.
    """
    while True:
        video_path_str = await queue.get()
        
        # Thêm kiểm tra file tồn tại ngay trước khi xử lý
        if not os.path.exists(video_path_str):
            logging.warning(f"⚠️ File {os.path.basename(video_path_str)} không còn tồn tại khi xử lý. Bỏ qua.")
            queue.task_done()
            continue

        video_path = Path(video_path_str)
        video_id = video_path.stem

        if is_uploaded(video_id, account_name):
            logging.info(f"🔵 Video {video_id} đã được xử lý trước đó. Bỏ qua.")
            queue.task_done()
            continue

        source, _ = find_video_source(video_id)
        description = get_description(video_id) or ""

        logging.info(f"--- 📤 Bắt đầu upload: {video_id} ---")
        try:
            await page.goto("https://www.tiktok.com/tiktokstudio/upload?from=creator_center", wait_until="domcontentloaded")

            async with page.expect_file_chooser() as fc_info:
                await page.locator(TT_SELECT_VIDEO_BUTTON_XPATH).click()
            
            file_chooser = await fc_info.value
            await file_chooser.set_files(video_path_str)
            logging.info(f"📂 Đã chọn file: {video_path.name}")

            success = await complete_upload_process(page, video_id, description, source, account_name)
            if success:
                logging.info("⏳ Chờ 5 giây trước khi xử lý video tiếp theo...")
                await asyncio.sleep(5)

        except Exception as e:
            logging.error(f"❌ Lỗi nghiêm trọng khi upload {video_id}: {e}")
            await page.screenshot(path=f"error_auto_{video_id}.png")
            logging.warning("🚨 Lỗi xảy ra, video sẽ không được thử lại tự động.")
        finally:
            queue.task_done()

async def run_auto_mode(account_name: str):
    """Chạy chế độ upload tự động hoàn toàn, sử dụng Watchdog để theo dõi video mới."""
    open_chrome_for_automation(account_name)
    
    upload_queue = asyncio.Queue()
    # Phải lấy event loop ở đây, trước khi nó bị chạy bởi async with
    loop = asyncio.get_running_loop()
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222", timeout=60000)
        except Exception as e:
            logging.error(f"❌ Không thể kết nối tới Chrome qua CDP. Hãy chắc chắn rằng bạn đã mở Chrome với lệnh được cung cấp. Lỗi: {e}")
            return
            
        context = browser.contexts[0]
        page = await context.new_page()

        processor_task = asyncio.create_task(upload_processor(upload_queue, account_name, page))

        logging.info("🔍 Quét các video đã có...")
        initial_candidates = get_upload_candidates(account_name, show_list=False)
        if initial_candidates:
            logging.info(f"📋 Tìm thấy {len(initial_candidates)} video có sẵn để đưa vào hàng đợi.")
            for video_info in initial_candidates:
                await upload_queue.put(video_info["video_path"])
        else:
            logging.info("✅ Không có video nào cần xử lý ngay.")

        # Truyền cả queue và event loop vào handler
        event_handler = VideoReadyHandler(upload_queue, loop)
        observer = Observer()
        
        facebook_video_dir = get_video_stalker_dir('fb')

        # Ẩn Youtube, chưa có nhu cầu theo dõi
        #youtube_video_dir = get_video_stalker_dir('yt')
        
        if facebook_video_dir and facebook_video_dir.exists():
            observer.schedule(event_handler, str(facebook_video_dir), recursive=True)
            logging.info(f"👁️  Đang theo dõi thư mục Facebook: {facebook_video_dir}")

        # Ẩn Youtube, chưa có nhu cầu theo dõi
 
        """
        if youtube_video_dir and youtube_video_dir.exists():
            observer.schedule(event_handler, str(youtube_video_dir), recursive=True)
            logging.info(f"👁️  Đang theo dõi thư mục YouTube: {youtube_video_dir}")
        """


        if not observer.emitters:
            logging.warning("⚠️ Không có thư mục nào được theo dõi. Watchdog sẽ không hoạt động.")
        else:
            observer.start()
            logging.info("👂 Lắng nghe video mới... (Nhấn Ctrl+C để dừng)")

        try:
            await processor_task
        except KeyboardInterrupt:
            logging.info("\n🛑 Dừng bởi người dùng.")
        finally:
            if observer.is_alive():
                observer.stop()
                observer.join()
            logging.info("✋ Đã dừng theo dõi.")

async def run_manual_mode(account_name: str):
    """Chạy chế độ upload thủ công (người dùng chọn file)."""
    open_chrome_for_automation(account_name, url="https://www.tiktok.com/tiktokstudio/upload?from=creator_center")
    logging.info("📤 Vui lòng chọn video để upload trong cửa sổ Chrome vừa mở...")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222", timeout=60000)
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
            await caption_input.wait_for(state="visible", timeout=300_000)

            logging.info("⏳ Đang chờ TikTok xử lý video và điền tên file vào caption...")
            await page.wait_for_function(
                "document.querySelector('div.public-DraftEditor-content').innerText.trim() !== ''",
                timeout=300_000
            )
            video_id = (await caption_input.inner_text()).strip()
            
            video_source, _ = find_video_source(video_id)
            description = get_description(video_id) or ""

            await complete_upload_process(page, video_id, description, video_source, account_name)

            logging.info("\n✅ Hoàn tất. Bạn có thể đóng cửa sổ Chrome hoặc upload video tiếp theo.")

        except Exception as e:
            logging.error(f"❌ Lỗi trong quá trình upload thủ công: {e}")
            await page.screenshot(path=f"error_manual.png")
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