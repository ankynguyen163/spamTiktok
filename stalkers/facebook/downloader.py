#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import time
import logging
from pathlib import Path
import re

from . import config as fb_config

def sanitize_filename(name: str) -> str:
    r"""
    Sanitizes a string to be a valid filename.
    - Removes illegal characters: \/*?:"<>|
    - Replaces whitespace sequences with a single underscore.
    - Limits length to avoid issues with filesystems.
    """
    if not name:
        return ""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', '_', name).strip('_')
    return name[:150]

async def download_video(video_url: str, video_id: str) -> bool:
    """
    Tải video từ URL Facebook bằng yt-dlp.
    """
    fb_config.VIDEOS_DIR.mkdir(exist_ok=True)
    output_template = fb_config.VIDEOS_DIR / f"{video_id}.%(ext)s"
    info_path = fb_config.VIDEOS_DIR / f"{video_id}.info.json"

    # --- Logic kiểm tra và dọn dẹp ---
    # 1. Ưu tiên kiểm tra metadata cuối cùng. Nếu có là đã xong.
    final_metadata_files = list(fb_config.VIDEOS_DIR.glob(f"{video_id}_*.json"))
    if final_metadata_files:
        logging.info(f"   -> [FB] Metadata cho '{video_id}' đã tồn tại: {final_metadata_files[0].name}. Bỏ qua.")
        return True

    # 2. Dọn dẹp file video "mồ côi" từ các lần chạy lỗi trước.
    # File mồ côi là file video không có file metadata cuối cùng tương ứng.
    video_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
    orphan_videos = [f for f in fb_config.VIDEOS_DIR.glob(f"{video_id}*") if f.suffix.lower() in video_extensions]
    if orphan_videos:
        logging.warning(f"   -> [FB] ⚠️  Phát hiện {len(orphan_videos)} file video mồ côi cho ID {video_id}. Sẽ xóa và tải lại.")
        for f in orphan_videos:
            try:
                f.unlink()
            except OSError as e:
                logging.error(f"   -> [FB] ❌ Không thể xóa file mồ côi '{f.name}': {e}")

    # --- Bắt đầu quá trình tải ---
    command = [
        "yt-dlp", "--quiet", "--no-warnings",
        "--progress",
        "--concurrent-fragments", "10",
        "--cookies", str(fb_config.COOKIE_FILE.resolve()),
        "-f", fb_config.YT_DLP_FORMAT,
        "--write-info-json", "--no-overwrites",
        "-o", str(output_template), video_url
    ]

    logging.info(f"   -> [FB] 📥 Bắt đầu tải video: {video_id}...")
    start_time = time.monotonic()
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    temp_video_path = next((f for f in fb_config.VIDEOS_DIR.glob(f"{video_id}.*") if f.suffix.lower() in video_extensions), None)

    if process.returncode == 0 and info_path.exists():
        try:
            info_data = json.loads(info_path.read_text(encoding='utf-8'))
            original_title = info_data.get('title') or ""
            description = info_data.get('description') or ""

            name_part = ""
            if description and "facebook_live" not in description.lower():
                name_part = description
            elif original_title and "facebook_live" not in original_title.lower():
                name_part = original_title

            # Loại bỏ extension có sẵn trong tên và sanitize
            name_part_cleaned = Path(name_part).stem
            sanitized_name = sanitize_filename(name_part_cleaned)

            if not sanitized_name:
                sanitized_name = f"video_{video_id}"

            new_base_name = f"{video_id}_{sanitized_name}"

            if temp_video_path:
                try:
                    new_video_name = f"{new_base_name}{temp_video_path.suffix}"
                    new_video_path = temp_video_path.with_name(new_video_name)
                    if not new_video_path.exists():
                        temp_video_path.rename(new_video_path)
                        logging.info(f"   -> [FB] ✅ Đổi tên thành công: '{new_video_path.name}'")
                    else:
                        logging.warning(f"   -> [FB] ⚠️ Tên file đích đã tồn tại, không đổi tên: {new_video_path.name}")
                except OSError as e:
                    logging.error(f"   -> [FB] ❌ Lỗi khi đổi tên file: {e}")

            duration = time.monotonic() - start_time
            logging.info(f"   -> [FB] ✅ Tải và xử lý thành công '{new_base_name}' trong {duration:.2f}s.")

            metadata_to_save = {
                "video_id": info_data.get('id', video_id),
                "uploader": info_data.get('uploader'),
                "title": original_title,
                "description": description,
                "upload_time": info_data.get('timestamp')
            }

            metadata_path = fb_config.VIDEOS_DIR / f"{new_base_name}.json"
            metadata_path.write_text(json.dumps(metadata_to_save, indent=4, ensure_ascii=False), encoding='utf-8')
            logging.info(f"   -> [FB] 📝 Đã tạo metadata: {metadata_path.name}")

            try:
                info_path.unlink()
            except OSError as e:
                logging.warning(f"   -> [FB] ⚠️ Không thể xóa file info tạm: {info_path}. Lỗi: {e}")

            return True
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            logging.error(f"   -> [FB] ❌ Lỗi khi xử lý metadata cho '{video_id}': {e}")
            return False
    else:
        error_message = f"   -> [FB] ❌ Lỗi khi chạy yt-dlp cho '{video_id}' (mã lỗi: {process.returncode})."
        if stderr:
            decoded_stderr = stderr.decode(errors='ignore').strip()
            if decoded_stderr:
                error_message += f"\n      Lỗi từ yt-dlp: {decoded_stderr.splitlines()[-1]}"
                logging.debug(f"      Full yt-dlp stderr for {video_id}:\n{decoded_stderr}")
        logging.error(error_message)
        return False