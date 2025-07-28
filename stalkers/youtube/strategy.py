import asyncio
import json
import time
import logging
from pathlib import Path

from ..base_strategy import StalkerStrategy
from .config import (
    CHANNELS_FILE,
    VIDEOS_DIR,
    HISTORY_FILE,
    YT_DLP_PATH,
    YTDLP_OPTIONS,
    MAX_VIDEOS_PER_SECTION,
    SCAN_INTERVAL_SECONDS,
    YOUTUBE_BATCH_SIZE,
    WAIT_BETWEEN_BATCHES_SECONDS,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - (YouTube) - %(message)s')

class YouTubeStrategy(StalkerStrategy):
    """
    Chiến lược theo dõi và tải video từ các kênh YouTube.
    Sử dụng yt-dlp để hiệu quả, không cần trình duyệt.
    """
    def __init__(self):
        self.history = self._load_history()
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_history(self) -> set:
        """Tải lịch sử các video ID đã tải về."""
        if not HISTORY_FILE.exists():
            return set()
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get("downloaded_ids", []))
        except (json.JSONDecodeError, FileNotFoundError):
            logging.warning("Không thể tải file history. Bắt đầu với history trống.")
            return set()

    def _save_history(self):
        """Lưu lịch sử các video ID đã tải về."""
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump({"downloaded_ids": list(self.history)}, f, indent=2)

    async def _fetch_videos_from_section(self, channel_url: str, section: str) -> list:
        """
        Sử dụng yt-dlp để lấy danh sách video từ một mục cụ thể của kênh (videos, shorts).
        """
        section_url = f"{channel_url.rstrip('/')}/{section}"
        logging.info(f"Đang quét mục '{section}' cho kênh: {channel_url}")

        command = [
            YT_DLP_PATH,
            '--dump-json',
            '--playlist-end', str(MAX_VIDEOS_PER_SECTION),
            '--flat-playlist',
            '--quiet',
            section_url
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logging.error(f"Lỗi khi chạy yt-dlp cho {section_url}: {stderr.decode('utf-8', 'ignore')}")
            return []

        videos = []
        for line in stdout.decode('utf-8').strip().split('\n'):
            if line:
                try:
                    videos.append(json.loads(line))
                except json.JSONDecodeError:
                    logging.warning(f"Bỏ qua dòng JSON không hợp lệ từ yt-dlp: {line}")
        return videos

    async def _download_video(self, video_id: str, uploader: str):
        """Tải video và tạo file metadata."""
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        output_template = VIDEOS_DIR / f"{video_id}.%(ext)s"

        logging.info(f"Phát hiện video mới: {video_id}. Bắt đầu tải...")

        command = [
            YT_DLP_PATH,
            *YTDLP_OPTIONS,
            '-o', str(output_template),
            video_url
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            info_json_path = VIDEOS_DIR / f"{video_id}.info.json"
            if not info_json_path.exists():
                logging.warning(f"Tải video {video_id} thành công nhưng không tìm thấy file .info.json.")
                return

            try:
                with open(info_json_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                standardized_meta = {
                    "video_id": metadata.get("id"), "uploader": uploader or metadata.get("channel"),
                    "title": metadata.get("title"), "description": metadata.get("description"),
                    "upload_time": metadata.get("timestamp"),
                }
                final_json_path = VIDEOS_DIR / f"{video_id}.json"
                with open(final_json_path, 'w', encoding='utf-8') as f:
                    json.dump(standardized_meta, f, ensure_ascii=False, indent=4)
                info_json_path.unlink()
                logging.info(f"✅ Tải và xử lý metadata thành công cho video: {video_id}")
                self.history.add(video_id)
            except (json.JSONDecodeError, OSError) as e:
                logging.error(f"Lỗi khi xử lý file metadata cho video {video_id}: {e}")
        else:
            error_message = f"❌ Lỗi khi tải video {video_id} (mã lỗi: {process.returncode})."
            if stderr:
                decoded_stderr = stderr.decode('utf-8', 'ignore').strip()
                # Lấy dòng lỗi cuối cùng, thường là thông tin súc tích nhất
                last_error_line = decoded_stderr.splitlines()[-1] if decoded_stderr.splitlines() else ""
                error_message += f"\n   Lỗi từ yt-dlp: {last_error_line}"
            logging.error(error_message)
            
            # Dọn dẹp các file tạm hoặc file chưa hoàn chỉnh do yt-dlp để lại
            logging.info(f"   -> Đang dọn dẹp các file tạm của video lỗi: {video_id}")
            try:
                # Tìm tất cả các file liên quan đến video_id này (vd: .mp4, .info.json, .part)
                for file_path in VIDEOS_DIR.glob(f"{video_id}.*"):
                    file_path.unlink()
                    logging.debug(f"      Đã xóa file tạm: {file_path.name}")
            except OSError as e:
                logging.warning(f"   -> Lỗi khi dọn dẹp file cho {video_id}: {e}")

    async def _process_channel(self, channel_url: str):
        """Xử lý một kênh: quét song song các mục 'videos', 'shorts' và tải video mới."""
        logging.info(f"Bắt đầu xử lý kênh: {channel_url}")
        tasks = [
            self._fetch_videos_from_section(channel_url, "videos"), self._fetch_videos_from_section(channel_url, "shorts"),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_videos = [video for res in results if isinstance(res, list) for video in res]
        if not all_videos:
            logging.info(f"Không tìm thấy video nào cho kênh: {channel_url}")
            return

        new_videos_to_download = []
        for video_info in all_videos:
            video_id = video_info.get("id")
            if video_id and video_id not in self.history:
                # Lấy tên uploader để lưu vào metadata
                uploader = video_info.get("uploader") or video_info.get("channel")
                new_videos_to_download.append((video_id, uploader))

        if not new_videos_to_download:
            logging.info(f"✅ Không có video mới cho kênh: {channel_url}")
            return

        # Loại bỏ các video trùng lặp (ví dụ: video vừa ở tab videos, vừa ở tab shorts)
        unique_new_videos = list(dict.fromkeys(new_videos_to_download))
        logging.info(f"Phát hiện {len(unique_new_videos)} video mới cho kênh {channel_url}. Bắt đầu tải...")

        download_tasks = [self._download_video(vid, uploader) for vid, uploader in unique_new_videos]
        await asyncio.gather(*download_tasks)

        # Lưu history sau khi tất cả các video của kênh đã được xử lý
        self._save_history()

    def get_targets(self) -> list[str]:
        """Đọc danh sách các kênh từ channels.txt."""
        if not CHANNELS_FILE.exists():
            logging.warning(f"Không tìm thấy file kênh tại: {CHANNELS_FILE}")
            return []
        try:
            with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            logging.error(f"Không thể đọc file kênh {CHANNELS_FILE}: {e}")
            return []

    def login(self) -> bool:
        """Đối với YouTube, không cần đăng nhập để quét các kênh công khai."""
        logging.info("✅ YouTube Stalker không yêu cầu đăng nhập. Sẵn sàng hoạt động.")
        return True

    def execute(self):
        """Entrypoint chính, được gọi bởi manager, chạy vòng lặp quét vô tận."""
        try:
            asyncio.run(self._main_loop())
        except KeyboardInterrupt:
            logging.info("YouTube Stalker nhận được tín hiệu dừng.")

    async def _main_loop(self):
        """Vòng lặp chính, quét định kỳ tất cả các kênh mục tiêu."""
        while True:
            targets = self.get_targets()
            if not targets:
                logging.warning("Danh sách kênh trống. Vui lòng thêm kênh vào 'stalkers/youtube/channels.txt'.")
                logging.info(f"Sẽ thử lại sau {SCAN_INTERVAL_SECONDS} giây.")
                await asyncio.sleep(SCAN_INTERVAL_SECONDS)
                continue

            logging.info(f"Bắt đầu chu trình quét mới cho {len(targets)} kênh YouTube, batch size = {YOUTUBE_BATCH_SIZE}.")
            
            # Chia targets thành các batch để xử lý tuần tự
            for i in range(0, len(targets), YOUTUBE_BATCH_SIZE):
                batch = targets[i:i + YOUTUBE_BATCH_SIZE]
                current_batch_num = i // YOUTUBE_BATCH_SIZE + 1
                total_batches = (len(targets) + YOUTUBE_BATCH_SIZE - 1) // YOUTUBE_BATCH_SIZE
                
                logging.info(f"Đang xử lý batch [{current_batch_num}/{total_batches}] với {len(batch)} kênh.")
                tasks = [self._process_channel(url) for url in batch]
                await asyncio.gather(*tasks)

                # Nếu đây không phải là batch cuối cùng, đợi một chút
                if i + YOUTUBE_BATCH_SIZE < len(targets):
                    logging.info(f"Đợi {WAIT_BETWEEN_BATCHES_SECONDS} giây trước khi xử lý batch tiếp theo.")
                    await asyncio.sleep(WAIT_BETWEEN_BATCHES_SECONDS)
            
            logging.info(f"✅ Hoàn thành chu trình quét. Nghỉ {SCAN_INTERVAL_SECONDS} giây.")
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)