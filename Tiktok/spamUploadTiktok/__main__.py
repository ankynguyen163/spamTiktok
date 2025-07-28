import asyncio
import sys
import subprocess
import time
from pathlib import Path
from playwright.async_api import async_playwright

# Import from shared modules
from Tiktok.config import (
    get_profile_dir,
    get_description,
    delete_video_file,
    is_uploaded,
    save_upload_history,
    get_all_videos,
    find_video_source,
    TT_CONFIRM_POST_BUTTON_SELECTOR,
    TT_SELECT_VIDEO_BUTTON_XPATH,
    TT_CAPTION_INPUT_SELECTOR,
    TT_UPLOAD_PROGRESS_SUCCESS_SELECTOR,
    TT_POST_BUTTON_SELECTOR,
)
from .utils import clean_caption, generate_hashtags

# --- Helper Functions (from auto_upload.py and manual_upload.py) ---

def open_chrome_for_automation(account_name: str, port=9222, url=None):
    """
    Mở Chrome với profile có sẵn để kết nối CDP.
    Có thể tùy chọn mở một URL cụ thể.
    """
    command = [
        "google-chrome",
        f"--user-data-dir={get_profile_dir(account_name)}",
        f"--remote-debugging-port={port}",
        "--new-window", # Đảm bảo cửa sổ mới
    ]
    if url:
        command.append(url)

    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"🚀 Đã mở Chrome profile trên cổng {port}. Chờ kết nối...")
    time.sleep(3)

def get_upload_candidates(account_name: str, show_list=True):
    """
    Lấy và hiển thị danh sách video có thể upload, đồng thời trả về danh sách đó.
    """
    videos = get_all_videos()
    if not videos:
        if show_list:
            print("📭 Không có video nào để upload.")
        return []

    upload_candidates = []
    if show_list:
        print("📹 Các video có sẵn để upload:")

    count = 0
    for video in videos:
        video_id = video.stem
        if is_uploaded(video_id, account_name):
            continue

        source, _ = find_video_source(video_id)
        source_display = source.upper() if source else "N/A"
        count += 1
        description = get_description(video_id) or ""
        if show_list:
            print(f"{count:2}. [{source_display}] {video.name}")

        upload_candidates.append({
            "video_path": str(video),
            "video_id": video_id,
            "source": source,
            "description": description
        })

    if not upload_candidates and show_list:
        print("✅ Tất cả video đã được đăng.")
    return upload_candidates

# --- Core Upload Logic ---

async def complete_upload_process(page, video_id, description, source, account_name):
    """
    Hàm lõi để hoàn tất quá trình upload sau khi video đã được chọn và tải lên.
    Bao gồm: điền caption, đăng, và lưu lịch sử.
    """
    print(f"📄 Video ID: {video_id} [{source.upper()}]")

    # Kiểm tra đã upload chưa bằng tài khoản này
    if is_uploaded(video_id, account_name):
        print(f"⚠️ Video {video_id} đã được tài khoản này upload. Bỏ qua.")
        return False

    # Tạo và điền caption
    clean_desc = clean_caption(description)
    full_caption = (clean_desc + "\n\n" + generate_hashtags()) if clean_desc else generate_hashtags()
    
    caption_input = page.locator(TT_CAPTION_INPUT_SELECTOR)
    await caption_input.wait_for(state="visible", timeout=30000)
    await caption_input.fill('')
    await caption_input.fill(full_caption)
    print("✍️ Đã điền caption.")

    # Chờ upload xong (thanh progress màu xanh)
    await page.wait_for_selector(TT_UPLOAD_PROGRESS_SUCCESS_SELECTOR, timeout=600_000)
    print("✅ Video đã được tải lên server TikTok.")

    # Đăng video
    post_button = page.locator(TT_POST_BUTTON_SELECTOR).first
    await post_button.wait_for(state="visible", timeout=30000)
    await post_button.click()
    print("🅿️  Đã bấm nút 'Đăng', chờ xác nhận...")
    
    # --- Xử lý modal "Đăng ngay" một cách linh hoạt ---
    # Modal này không phải lúc nào cũng xuất hiện.
    try:
        confirm_post_button = page.locator(TT_CONFIRM_POST_BUTTON_SELECTOR)
        # Chờ trong một khoảng thời gian ngắn. Nếu không xuất hiện, nó sẽ ném TimeoutError.
        await confirm_post_button.wait_for(state="visible", timeout=5000) 
        print("...Phát hiện modal xác nhận. Đang click 'Đăng ngay'...")
        await confirm_post_button.click()
        # Chờ modal biến mất để chắc chắn hành động đã được thực hiện
        await confirm_post_button.wait_for(state="hidden", timeout=10000)
    except Exception: # Bắt TimeoutError hoặc các lỗi khác
        print("...Không có modal xác nhận hoặc đã hết thời gian chờ. Tiếp tục...")

    # --- Xác nhận upload thành công ---
    # Chờ cho nút "Đăng" ban đầu biến mất hoặc bị vô hiệu hóa.
    await post_button.wait_for(state="hidden", timeout=60000)
    print(f"🚀 Đã gửi yêu cầu đăng video {video_id}.")
    
    # Lưu lịch sử
    save_upload_history(video_id, description, account_name)
    print(f"--- ✅ Hoàn tất xử lý cho: {video_id} ---")
    print("ℹ️  File video gốc vẫn được giữ lại. Dùng lệnh 'clean-uploaded' để dọn dẹp sau.")
    return True

# --- Mode-specific Logic ---

async def run_auto_mode(account_name: str):
    """Chạy chế độ upload tự động hoàn toàn."""
    candidates = get_upload_candidates(account_name, show_list=False)
    if not candidates:
        print(f"📭 Không có video mới để upload tự động cho tài khoản '{account_name}'.")
        return

    open_chrome_for_automation(account_name)
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = await context.new_page()

        print(f"\n🤖 Bắt đầu chu trình upload tự động cho {len(candidates)} video...")
        for video_info in candidates:
            print(f"\n--- 📤 Bắt đầu upload: {video_info['video_id']} ---")
            await page.goto("https://www.tiktok.com/tiktokstudio/upload?from=creator_center", wait_until="domcontentloaded")

            try:
                async with page.expect_file_chooser() as fc_info:
                    await page.locator(TT_SELECT_VIDEO_BUTTON_XPATH).click()
                
                file_chooser = await fc_info.value
                await file_chooser.set_files(video_info["video_path"])
                print(f"📂 Đã chọn file: {Path(video_info['video_path']).name}")

                success = await complete_upload_process(page, video_info["video_id"], video_info["description"], video_info["source"], account_name)
                if success:
                    print("⏳ Chờ 10 giây trước khi upload video tiếp theo...")
                    await asyncio.sleep(10)

            except Exception as e:
                print(f"❌ Lỗi nghiêm trọng khi upload {video_info['video_id']}: {e}")
                await page.screenshot(path=f"error_auto_{video_info['video_id']}.png")
                continue # Bỏ qua video này và tiếp tục
        
        await browser.close()
        print("\n🎉 Đã upload xong tất cả video. Đóng trình duyệt.")

async def run_manual_mode(account_name: str):
    """Chạy chế độ upload thủ công (người dùng chọn file)."""
    open_chrome_for_automation(account_name, url="https://www.tiktok.com/tiktokstudio/upload?from=creator_center")
    print("📤 Vui lòng chọn video để upload trong cửa sổ Chrome vừa mở...")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        # Tìm đúng page đã mở sẵn
        page = next((pg for pg in browser.contexts[0].pages if "upload" in pg.url), None)
        if not page:
            print("❌ Không tìm thấy trang upload của TikTok. Vui lòng thử lại.")
            await browser.close()
            return
        
        await page.bring_to_front()

        try:
            # Chờ người dùng chọn file, dấu hiệu là tên file xuất hiện trong caption
            caption_input = page.locator(TT_CAPTION_INPUT_SELECTOR)
            await caption_input.wait_for(state="visible", timeout=300_000) # Chờ 5 phút

            # Chờ cho đến khi caption có nội dung (tên file)
            await page.wait_for_function(
                "document.querySelector('div.public-DraftEditor-content').innerText.trim() !== ''",
                timeout=300_000
            )
            video_id = (await caption_input.inner_text()).strip()
            
            video_source, _ = find_video_source(video_id)
            description = get_description(video_id) or ""

            await complete_upload_process(page, video_id, description, video_source, account_name)

            print("\n✅ Hoàn tất. Bạn có thể đóng cửa sổ Chrome hoặc upload video tiếp theo.")
            # Giữ trình duyệt mở để người dùng có thể upload tiếp

        except Exception as e:
            print(f"❌ Lỗi trong quá trình upload thủ công: {e}")
            await page.screenshot(path=f"error_manual.png")
        finally:
            await browser.close() # Chỉ đóng kết nối, không đóng cửa sổ Chrome
    

def print_usage():
    """In hướng dẫn sử dụng."""
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
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    # Kiểm tra số lượng đối số cho từng lệnh
    if command in ["auto", "manual", "list"] and len(sys.argv) < 3:
        print(f"❌ Lỗi: Lệnh '{command}' yêu cầu tên tài khoản.")
        print_usage()
        sys.exit(1)
    
    account_name = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        if command == "auto":
            asyncio.run(run_auto_mode(account_name))
        elif command == "manual":
            asyncio.run(run_manual_mode(account_name))
        elif command == "list":
            get_upload_candidates(account_name, show_list=True)
        else:
            print(f"❌ Lệnh không hợp lệ: '{command}'\n")
            print_usage()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Dừng bởi người dùng.")
    except Exception as e:
        print(f"\n🛑 Lỗi không xác định trong quá trình chạy: {e}")

if __name__ == "__main__":
    main()