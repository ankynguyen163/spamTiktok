#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time
import subprocess
import argparse
from pathlib import Path
from playwright.async_api import async_playwright

from Tiktok.config import (
    get_profile_dir,
    TT_VIEWS_HEADER_SELECTOR,
    TT_STUDIO_CONTENT_URL,
    TT_VIDEO_ROW_SELECTOR,
    TT_VIEW_COUNT_SELECTOR,
    TT_MORE_OPTIONS_BUTTON_SELECTOR,
    TT_DELETE_MENU_ITEM_SELECTOR,
    TT_CONFIRM_DELETE_BUTTON_SELECTOR
)

def parse_view_count(text: str) -> int:
    """
    Chuyển đổi văn bản lượt xem (ví dụ: '1.2K', '10M', '99') thành số nguyên.
    """
    text = text.upper().strip().replace(',', '.') # Handle cases like '1,2K'
    if 'K' in text:
        return int(float(text.replace('K', '')) * 1000)
    if 'M' in text:
        return int(float(text.replace('M', '')) * 1000000)
    if text.isdigit():
        return int(text)
    return 0

def open_chrome_for_automation(profile_path: Path, port: int):
    """Mở một cửa sổ Chrome thật với remote debugging để Playwright kết nối vào."""
    print(f"🚀 Mở Chrome với profile và cổng gỡ lỗi {port}...")
    # Lệnh này sẽ mở một cửa sổ Chrome mới. Playwright sẽ kết nối vào cửa sổ này.
    command = [
        "google-chrome",
        f"--user-data-dir={profile_path.resolve()}",
        f"--remote-debugging-port={port}"
        # Không mở URL cụ thể, để script tự điều hướng sau, giống hệt cơ chế upload.
    ]
    # Dùng Popen để nó chạy nền, không block script chính
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)  # Đợi một chút cho Chrome khởi động hoàn toàn
    return process

async def delete_low_view_videos(page, threshold: int, dry_run: bool, debug: bool):
    """
    Cuộn, tìm và xóa các video có lượt xem thấp hơn ngưỡng.
    """
    def d_print(msg):
        if debug:
            print(f"[DEBUG] {msg}")

    print(f"🌍 Đang điều hướng đến trang quản lý nội dung...")
    await page.goto(TT_STUDIO_CONTENT_URL, wait_until="domcontentloaded")

    d_print(f"Đã ở trên trang {page.url}")

    # KIỂM TRA QUAN TRỌNG: Phát hiện nếu bị chuyển hướng đến trang đăng nhập
    if "/login" in page.url or "/signup" in page.url:
        print("\n❌ Bị chuyển hướng đến trang đăng nhập/đăng ký.")
        print("   Phiên đăng nhập (session) trong profile của bạn có thể đã hết hạn.")
        print("➡️  Vui lòng chạy lại lệnh `python cli.py login-tt` để làm mới phiên đăng nhập và thử lại.")
        return

    try:
        await page.locator(TT_VIDEO_ROW_SELECTOR).first.wait_for(timeout=30000)
        d_print("Bảng video đã tải thành công.")
    except Exception:
        print("❌ Không thể tải trang nội dung hoặc không có video nào. Nếu bạn chắc chắn đã đăng nhập, có thể giao diện TikTok đã thay đổi.")
        return

    print("📊 Sắp xếp video theo lượt xem từ thấp đến cao...")
    try:
        views_header = page.locator(TT_VIEWS_HEADER_SELECTOR)
        await views_header.wait_for(state="visible", timeout=10000)

        # --- Logic sắp xếp thông minh ---
        # Xác định trạng thái sắp xếp hiện tại bằng cách kiểm tra màu của icon mũi tên.
        up_arrow_svg = views_header.locator('span[data-icon="ArrowUpSmall"] svg')
        down_arrow_svg = views_header.locator('span[data-icon="ArrowDownSmall"] svg')

        # Màu của icon khi không được chọn (inactive)
        placeholder_color = "var(--ui-text-placeholder)"

        up_arrow_fill = await up_arrow_svg.get_attribute("fill")
        d_print(f"Màu mũi tên lên (thấp->cao): {up_arrow_fill}")

        if up_arrow_fill != placeholder_color:
            # Đã sắp xếp đúng chiều (thấp -> cao)
            print("✅ Video đã được sắp xếp từ thấp đến cao.")
        else:
            down_arrow_fill = await down_arrow_svg.get_attribute("fill")
            d_print(f"Màu mũi tên xuống (cao->thấp): {down_arrow_fill}")

            if down_arrow_fill != placeholder_color:
                # Đang sắp xếp cao -> thấp, chỉ cần click 1 lần để đảo ngược
                print("...Đang sắp xếp cao->thấp. Click 1 lần để đổi chiều...")
                await views_header.click()
                await page.wait_for_timeout(2500) # Chờ UI cập nhật
            else:
                # Trạng thái mặc định (chưa sắp xếp), click 2 lần
                print("...Chưa sắp xếp theo lượt xem. Click 2 lần...")
                await views_header.click() # Lần 1: cao -> thấp
                await page.wait_for_timeout(1500)
                await views_header.click() # Lần 2: thấp -> cao
                await page.wait_for_timeout(2500)
        d_print("Sắp xếp hoàn tất.")
    except Exception as e:
        print(f"⚠️ Không thể sắp xếp video, sẽ tiếp tục mà không sắp xếp. Lỗi: {e}")

    print(f"🔎 Bắt đầu kiểm tra và xóa video (ngưỡng: < {threshold} lượt xem)...")
    if dry_run:
        print("💧 Chế độ DRY RUN đang bật. Sẽ không có video nào bị xóa thật.")
    
    deleted_count = 0
    processed_rows = set()
    all_videos_above_threshold = False

    while not all_videos_above_threshold:
        video_rows = await page.locator(TT_VIDEO_ROW_SELECTOR).all()
        new_rows = [row for row in video_rows if row not in processed_rows]

        if not new_rows:
            d_print("Không có video mới sau khi cuộn, kết thúc.")
            break

        print(f"⏬ Đã tải {len(new_rows)} video mới. Đang xử lý...")

        for video_card in new_rows:
            processed_rows.add(video_card)
            try:
                view_count_text = await video_card.locator(TT_VIEW_COUNT_SELECTOR).inner_text(timeout=5000)
                views = parse_view_count(view_count_text)
                d_print(f"Kiểm tra video có {views} lượt xem.")

                if views < threshold:
                    deleted_count += 1
                    if dry_run:
                        print(f"💧 [DRY RUN] Sẽ xóa video có {views} lượt xem.")
                    else:
                        print(f"🔻 Video có {views} lượt xem (dưới {threshold}). Chuẩn bị xóa...")
                        await video_card.locator(TT_MORE_OPTIONS_BUTTON_SELECTOR).click()
                        delete_button = page.locator(TT_DELETE_MENU_ITEM_SELECTOR)
                        await delete_button.wait_for(state="visible", timeout=5000)
                        await delete_button.click()
                        confirm_button = page.locator(TT_CONFIRM_DELETE_BUTTON_SELECTOR)
                        await confirm_button.wait_for(state="visible", timeout=5000)
                        await confirm_button.click()
                        await confirm_button.wait_for(state="hidden", timeout=10000)
                        print("🗑️  Đã xóa thành công.")
                        await asyncio.sleep(1) # Chờ UI ổn định
                else:
                    print(f"👍 Video có {views} lượt xem. Dừng cuộn vì đã vượt ngưỡng.")
                    all_videos_above_threshold = True
                    break # Dừng vòng lặp for

            except Exception as e:
                print(f"⚠️ Lỗi khi xử lý một video: {e}. Có thể video đã bị xóa hoặc UI thay đổi.")
                d_print(f"Ngoại lệ chi tiết: {repr(e)}")
                continue
        
        if not all_videos_above_threshold:
            d_print("Cuộn xuống để tải thêm video...")
            await page.evaluate("window.scrollBy(0, window.innerHeight);")
            await page.wait_for_timeout(2000) # Chờ video mới tải

    print(f"\n🎉 Hoàn tất! Đã {('xóa' if not dry_run else 'xác định sẽ xóa')} tổng cộng {deleted_count} video.")

async def main_async(account_name: str, threshold: int, dry_run: bool, debug: bool):
    """Hàm async chính để chạy tự động hóa trình duyệt."""
    profile = get_profile_dir(account_name)
    port = 9223  # Dùng cổng khác 9222 để tránh xung đột với các script upload
    print(f"ℹ️  Sử dụng profile Chrome cho tài khoản '{account_name}' tại: {profile.resolve()}")
    if not profile.exists() or not (profile / "Default").exists():
        print(f"❌ Lỗi: Thư mục profile cho tài khoản '{account_name}' không hợp lệ hoặc chưa được khởi tạo.")
        print(f"➡️  Vui lòng chạy lệnh `python cli.py login-tt {account_name}` để tạo và đăng nhập profile trước.")
        return

    # Mở một tiến trình Chrome thật để "trốn" khỏi sự phát hiện của TikTok
    chrome_process = open_chrome_for_automation(profile, port)

    browser = None
    try:
        async with async_playwright() as p:
            print(f"🔌 Đang kết nối tới Chrome trên cổng {port}...")
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")

            # Bắt chước y hệt auto_upload.py: tạo một tab mới để làm việc.
            context = browser.contexts[0]
            print("📄 Tạo tab mới để làm việc...")
            page = await context.new_page()

            # Chạy logic chính trên tab mới này
            await delete_low_view_videos(page, threshold, dry_run, debug)

    except Exception as e:
        # Bắt lỗi kết nối phổ biến
        if "ECONNREFUSED" in str(e):
            print(f"❌ Lỗi kết nối: Không thể kết nối tới Chrome trên cổng {port}.")
            print("   Vui lòng đảm bảo không có tiến trình nào khác đang dùng cổng này và Chrome đã được cài đặt.")
        else:
            raise e  # Ném lại các lỗi khác để khối ngoài xử lý
    finally:
        if browser:
            await browser.close()  # Chỉ đóng kết nối, không đóng trình duyệt
            print("🔌 Đã ngắt kết nối với trình duyệt.")
        if chrome_process:
            # KHÔNG đóng trình duyệt, để nó mở giống như các script upload.
            # Người dùng sẽ tự đóng hoặc dùng lệnh kill-stalkers.
            print("✅ Hoàn tất. Cửa sổ Chrome vẫn đang mở.")

def main():
    parser = argparse.ArgumentParser(
        description="Xóa video TikTok có lượt xem thấp.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'account_name',
        type=str,
        help='Tên tài khoản TikTok cần dọn dẹp video.'
    )
    parser.add_argument(
        '--threshold',
        type=int,
        default=100,
        help='Ngưỡng lượt xem để xóa video (mặc định: 100).'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Chạy ở chế độ xem trước, không xóa thật.'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Bật chế độ debug để in thêm thông tin.'
    )
    args = parser.parse_args()

    try:
        asyncio.run(main_async(args.account_name, args.threshold, args.dry_run, args.debug))
    except KeyboardInterrupt:
        print("\n🛑 Dừng bởi người dùng.")
    except Exception as e:
        print(f"\n❌ Lỗi không xác định: {e}")
        print(f"Vui lòng đảm bảo bạn đã đăng nhập TikTok cho tài khoản '{args.account_name}' và đã đóng hết các cửa sổ Chrome sử dụng profile này.")

if __name__ == "__main__":
    main()