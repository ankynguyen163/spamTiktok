# stalkers/youtube/config.py

from pathlib import Path

# Đường dẫn gốc của module youtube
YOUTUBE_DIR = Path(__file__).parent.resolve()

# File chứa danh sách các kênh YouTube cần theo dõi
CHANNELS_FILE = YOUTUBE_DIR / "channels.txt"

# Thư mục lưu trữ video và metadata tải về
VIDEOS_DIR = YOUTUBE_DIR / "videos"

# File lưu lịch sử các video đã được tải
HISTORY_FILE = YOUTUBE_DIR / "history.json"

# --- Cấu hình cho yt-dlp ---

# Đường dẫn đến file thực thi yt-dlp.
# Nếu yt-dlp đã có trong PATH của hệ thống, bạn có thể để là "yt-dlp".
YT_DLP_PATH = "yt-dlp"

# Các tùy chọn dòng lệnh cho yt-dlp khi tải video.
# - Ghi file .info.json để lấy metadata.
# - Không ghi đè video đã tồn tại.
# - Chọn định dạng video tốt nhất (lên đến 1080p) và audio tốt nhất.
YTDLP_OPTIONS = [
    '--write-info-json',
    '--no-overwrites',
    '-f', 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
]

# Số lượng video mới nhất cần kiểm tra trong mỗi mục (videos, shorts).
MAX_VIDEOS_PER_SECTION = 2

# --- Cấu hình Stalker ---
# Thời gian (giây) chờ giữa mỗi lần quét tất cả các kênh
SCAN_INTERVAL_SECONDS = 1800  # 30 phút

# Số lượng kênh xử lý đồng thời trong một batch.
# Đặt giá trị lớn (ví dụ: 999) để xử lý tất cả cùng lúc.
YOUTUBE_BATCH_SIZE = 5

# Thời gian (giây) chờ giữa các batch để tránh bị giới hạn
WAIT_BETWEEN_BATCHES_SECONDS = 10