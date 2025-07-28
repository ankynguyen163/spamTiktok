# config.py - Unified config cho TikTok uploader

import json
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
STEALTH_SCRIPT = BASE_DIR / 'stealth.js'

# --- TikTok UI Selectors (for delete_videos.py) ---
# These selectors are based on TikTok Studio's UI. They may change and require updates.
TT_STUDIO_CONTENT_URL = "https://www.tiktok.com/tiktokstudio/content"
TT_VIEWS_HEADER_SELECTOR = 'div[data-tt="components_PostTableHeader_FlexRow"]:has-text("Lượt xem")'
TT_VIDEO_ROW_SELECTOR = 'div[data-tt="components_PostTable_Absolute"]'
TT_VIEW_COUNT_SELECTOR = 'div[data-tt="components_RowLayout_FlexRow_6"] span.TUXText'
TT_MORE_OPTIONS_BUTTON_SELECTOR = 'button[data-tt="components_ActionCell_Clickable"]'
TT_DELETE_MENU_ITEM_SELECTOR = 'div[data-tt="components_ActionCell_FlexRow"]:has-text("Xóa")'
TT_CONFIRM_DELETE_BUTTON_SELECTOR = 'button[data-tt="components_Modal_TUXButton"]:has-text("Xóa")'

# --- Selectors for Upload Process ---
TT_SELECT_VIDEO_BUTTON_XPATH = '//div[contains(text(), "Chọn video")]/ancestor::button'
TT_CAPTION_INPUT_SELECTOR = 'div.public-DraftEditor-content[contenteditable="true"]'
TT_UPLOAD_PROGRESS_SUCCESS_SELECTOR = 'div.info-progress.success'
TT_POST_BUTTON_SELECTOR = 'button.Button__root:has-text("Đăng")'
TT_CONFIRM_POST_BUTTON_SELECTOR = 'button.TUXButton--primary:has-text("Đăng ngay")' # Modal "Đăng ngay"

# Video sources
VIDEO_SOURCES = {
    'fb': PROJECT_ROOT / 'stalkers' / 'facebook' / 'videos',
    'yt': PROJECT_ROOT / 'stalkers' / 'youtube' / 'videos'
}

# Directory to store accounts
ACCOUNTS_DIR = BASE_DIR / 'accounts'

# Tạo thư mục nếu chưa có
ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)

def get_profile_dir(account_name: str) -> Path:
    """Lấy đường dẫn đến thư mục profile của một tài khoản."""
    return ACCOUNTS_DIR / account_name

def get_cookies_path(account_name: str) -> Path:
    """Lấy đường dẫn đến file cookies JSON của một tài khoản."""
    return get_profile_dir(account_name) / 'cookies.json'

def get_history_path(account_name: str) -> Path:
    """Lấy đường dẫn đến file history.json của một tài khoản."""
    return get_profile_dir(account_name) / 'history.json'

def get_all_videos(silent=False):
    """Lấy tất cả video từ các nguồn"""
    videos = []
    for source_dir in VIDEO_SOURCES.values():
        if source_dir.exists():
            if not silent:
                print(f"📂 Đang quét video từ: {source_dir}")
            videos.extend([f for f in source_dir.iterdir() if f.suffix.lower() in ['.mp4', '.webm', '.mov', '.avi', '.mkv']])
    return sorted(videos)

def get_description(video_id: str) -> str:
    """
    Tìm description của video bằng cách đọc file metadata (.json) tương ứng.
    File metadata được giả định có cùng tên với file video nhưng có phần mở rộng là .json
    và được lưu cùng thư mục với video.
    """
    for source_dir in VIDEO_SOURCES.values():
        metadata_path = source_dir / f"{video_id}.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                return metadata.get("description", "")
            except (json.JSONDecodeError, IOError):
                continue # Nếu file lỗi, tiếp tục tìm ở nguồn khác
    return ""

def find_video_source(video_id):
    """Tìm nguồn video (fb/yt) từ video_id"""
    for source_name, source_dir in VIDEO_SOURCES.items():
        if source_dir.exists():
            for file in source_dir.glob(f"{video_id}*"):
                return source_name, file
    return None, None

def delete_video_file(video_id, source_hint=None):
    """Xóa video đã upload, có thể chỉ định nguồn để tối ưu"""
    if source_hint:
        # Xóa từ nguồn cụ thể
        source_dir = VIDEO_SOURCES.get(source_hint)
        if source_dir and source_dir.exists():
            for file in source_dir.glob(f"{video_id}*"):
                try:
                    file.unlink()
                    print(f"🗑️ Đã xóa [{source_hint.upper()}]: {file.name}")
                    return True
                except Exception as e:
                    print(f"⚠️ Lỗi xóa {file.name}: {e}")
    
    # Fallback: tìm trong tất cả nguồn
    deleted = False
    for source_dir in VIDEO_SOURCES.values():
        for file in source_dir.glob(f"{video_id}*"):
            try:
                file.unlink()
                print(f"🗑️ Đã xóa: {file.name}")
                deleted = True
            except Exception as e:
                print(f"⚠️ Lỗi xóa {file.name}: {e}")
    return deleted

def is_uploaded(video_id: str, account_name: str = None) -> bool:
    """
    Kiểm tra video đã upload lên TikTok chưa.
    - Nếu account_name được cung cấp, chỉ kiểm tra cho tài khoản đó.
    - Nếu không, kiểm tra xem có bất kỳ tài khoản nào đã upload chưa.
    """
    def _check_history_file(file_path: Path) -> bool:
        if not file_path.exists():
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return any(item.get("video_id") == video_id for item in history)
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    if account_name:
        # Check history for a specific account
        return _check_history_file(get_history_path(account_name))
    else:
        # Check history for all accounts
        if not ACCOUNTS_DIR.exists():
            return False
        for account_dir in ACCOUNTS_DIR.iterdir():
            if account_dir.is_dir():
                if _check_history_file(account_dir / 'history.json'):
                    return True
        return False

def save_upload_history(video_id: str, description: str = "", account_name: str = None):
    """Lưu lịch sử upload TikTok vào file history của tài khoản."""
    if not account_name:
        raise ValueError("account_name is required to save upload history.")

    history_file = get_history_path(account_name)
    history_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    
    from datetime import datetime
    history.append({
        "video_id": video_id,
        "description": description,
        "upload_time": datetime.now().isoformat(),
        "account_name": account_name,
    })
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Đã lưu {video_id} (tài khoản: {account_name}) vào TT history")

def get_upload_count(account_name: str) -> int:
    """Đếm số lượng video đã upload của một tài khoản."""
    history_path = get_history_path(account_name)
    if not history_path.exists():
        return 0
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return len(history)
    except (json.JSONDecodeError, FileNotFoundError):
        return 0