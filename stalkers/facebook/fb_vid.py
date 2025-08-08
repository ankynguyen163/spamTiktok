#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import time
import logging
from pathlib import Path

from . import config as fb_config

async def download_video(video_url: str, video_id: str) -> bool:
    """
    Tải video từ URL Facebook bằng yt-dlp.
    Lưu video và một file metadata .json chứa các thông tin cần thiết.
    Trả về True nếu tải thành công, ngược lại False.
    """
    fb_config.VIDEOS_DIR.mkdir(exist_ok=True)
    # Sử dụng with_suffix để linh hoạt hơn với định dạng file (mp4, webm, v.v.)
    # yt-dlp sẽ tự động chọn đuôi file đúng
    output_template = fb_config.VIDEOS_DIR / f"{video_id}.%(ext)s"
    info_path = fb_config.VIDEOS_DIR / f"{video_id}.info.json"
    metadata_path = fb_config.VIDEOS_DIR / f"{video_id}.json"

    # Tìm kiếm file video đã tồn tại (vì đuôi file có thể thay đổi)
    existing_videos = list(fb_config.VIDEOS_DIR.glob(f"{video_id}.*"))
    video_exists = any(not f.name.endswith(('.json', '.part')) for f in existing_videos)

    # Cải tiến logic kiểm tra:
    # 1. Nếu metadata đã tồn tại, coi như đã hoàn tất.
    # 2. Nếu chỉ có video tồn tại (lỗi ở lần chạy trước), chỉ cần tạo lại metadata.
    if metadata_path.exists():
        logging.info(f"   -> [FB] Metadata cho '{video_id}' đã tồn tại. Bỏ qua.")
        return True

    # Xây dựng command cho yt-dlp
    command = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--cookies", str(fb_config.COOKIE_FILE.resolve()),
        "-f", fb_config.YT_DLP_FORMAT,
        "--write-info-json",
        "--no-overwrites",
        "--recode-video", "mp4",
        "--postprocessor-args", "ffmpeg:-b:v 1200k",  # ví dụ bitrate ~1.2 Mbps
        "-o", str(output_template),
        video_url
    ]

    if video_exists:
        logging.warning(f"   -> [FB] ⚠️ Video '{video_id}' đã tồn tại nhưng thiếu metadata. Chỉ tạo lại metadata.")
        command.insert(1, "--skip-download") # Thêm cờ không tải lại video
    else:
        logging.info(f"   -> [FB] 📥 Bắt đầu tải video: {video_id}...")

    start_time = time.monotonic()
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    # Tìm lại file video sau khi tải xong
    final_video_path = next((f for f in fb_config.VIDEOS_DIR.glob(f"{video_id}.*") if not f.name.endswith(('.json', '.part'))), None)

    if process.returncode == 0 and info_path.exists():
        duration = time.monotonic() - start_time
        if final_video_path:
             logging.info(f"   -> [FB] ✅ Tải thành công '{final_video_path.name}' trong {duration:.2f}s.")
        
        try:
            # Xử lý metadata bất kể video có được tải lại hay không
            info_data = json.loads(info_path.read_text(encoding='utf-8'))

            # Trích xuất các trường cần thiết
            metadata_to_save = {
                "video_id": info_data.get('id', video_id),
                "uploader": info_data.get('uploader'),
                "title": info_data.get('title'),
                "description": info_data.get('description'),
                "upload_time": info_data.get('timestamp') # Unix timestamp
            }

            # Ghi file metadata .json cuối cùng
            metadata_path.write_text(
                json.dumps(metadata_to_save, indent=4, ensure_ascii=False),
                encoding='utf-8'
            )
            logging.info(f"   -> [FB] 📝 Đã tạo/cập nhật metadata: {metadata_path.name}")

            try:
                info_path.unlink() # Xóa file info.json tạm sau khi dùng xong
            except OSError as e:
                logging.warning(f"   -> [FB] ⚠️ Không thể xóa file info tạm: {info_path}. Lỗi: {e}")

            return True
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            logging.error(f"   -> [FB] ❌ Lỗi khi xử lý metadata cho '{video_id}': {e}")
            return False
    else:
        # Cung cấp log lỗi chi tiết hơn
        error_message = f"   -> [FB] ❌ Lỗi khi chạy yt-dlp cho '{video_id}' (mã lỗi: {process.returncode})."
        if stderr:
            decoded_stderr = stderr.decode(errors='ignore').strip()
            error_message += f"\n      Lỗi từ yt-dlp: {decoded_stderr.splitlines()[-1]}" # Chỉ lấy dòng lỗi cuối cùng cho gọn
            logging.debug(f"      Full yt-dlp stderr for {video_id}:\n{decoded_stderr}")
        logging.error(error_message)
        return False