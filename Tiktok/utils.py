import re
import random
import subprocess
import time
import logging
import sys
import json 
import os 
from pathlib import Path
from datetime import datetime
from Tiktok.config import VIDEO_SOURCES, ACCOUNTS_DIR, CHROME_EXECUTABLE, CHROME_DEBUG_PORT, MAX_CONCURRENT_UPLOADS


def open_chrome_for_automation(account_name: str, port=CHROME_DEBUG_PORT, url=None):
    """Mở Chrome với profile và cổng gỡ lỗi được chỉ định."""
    command = [
        CHROME_EXECUTABLE,
        #"--headless=true",
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

def get_id_from_stem(stem: str) -> str:
    """Trích xuất ID từ tên file (phần trước dấu gạch dưới đầu tiên)."""
    return stem.split('_')[0]

def get_video_id(video_path: Path) -> str:
    """Lấy ID video từ một đối tượng Path."""
    return get_id_from_stem(video_path.stem)

def get_video_stalker_dir(source_name: str) -> Path:
    """Lấy đường dẫn đến thư mục video của một nguồn stalker."""
    return VIDEO_SOURCES.get(source_name.lower())

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
    Lấy mô tả của video bằng cách trích xuất từ tên file.
    Tên file được giả định có định dạng: <video_id>_<description>.<ext>
    """
    for source_dir in VIDEO_SOURCES.values():
        # Tìm bất kỳ file video nào (mp4, webm, etc.) bắt đầu bằng video_id
        video_files = list(source_dir.glob(f"{video_id}_*.*mp4"))
        if not video_files:
            video_files = list(source_dir.glob(f"{video_id}_*.*webm"))

        if video_files:
            video_path = video_files[0]
            # Tên file không bao gồm extension: 1431607971405798_description_part
            stem = video_path.stem
            
            # Xây dựng prefix để loại bỏ: "1431607971405798_"
            prefix = f"{video_id}_"
            
            if stem.startswith(prefix):
                # Lấy phần description đã được sanitize
                sanitized_description = stem[len(prefix):]
                # Thay thế gạch dưới bằng khoảng trắng để trả về câu gốc
                description = sanitized_description.replace('_', ' ')
                return description.strip() # Trả về và bỏ các khoảng trắng thừa
            
    # Nếu không tìm thấy file video phù hợp
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

def get_uploaded_videos(account_name: str) -> list:
    """Lấy danh sách các video đã upload của một tài khoản."""
    history_path = get_history_path(account_name)
    if not history_path.exists():
        return []
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return history
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def remove_from_history(video_id: str, account_name: str):
    """Xóa một video khỏi lịch sử upload của tài khoản."""
    history_file = get_history_path(account_name)
    if not history_file.exists():
        print(f"Lịch sử upload của tài khoản '{account_name}' không tồn tại.")
        return

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except json.JSONDecodeError:
        print("Lỗi đọc file lịch sử. File có thể bị hỏng.")
        return

    initial_len = len(history)
    history = [item for item in history if item.get("video_id") != video_id]

    if len(history) < initial_len:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"🗑️ Đã xóa video '{video_id}' khỏi lịch sử upload của tài khoản '{account_name}'.")
    else:
        print(f"Video '{video_id}' không tìm thấy trong lịch sử upload của tài khoản '{account_name}'.")

def clear_history(account_name: str):
    """Xóa toàn bộ lịch sử upload của một tài khoản."""
    history_file = get_history_path(account_name)
    if history_file.exists():
        try:
            history_file.unlink()
            print(f"🗑️ Đã xóa toàn bộ lịch sử upload của tài khoản '{account_name}'.")
        except Exception as e:
            print(f"Lỗi khi xóa file lịch sử: {e}")
    else:
        print(f"Lịch sử upload của tài khoản '{account_name}' không tồn tại.")

def migrate_history(old_account_name: str, new_account_name: str):
    """Di chuyển lịch sử upload từ tài khoản cũ sang tài khoản mới."""
    old_history_file = get_history_path(old_account_name)
    new_history_file = get_history_path(new_account_name)

    if not old_history_file.exists():
        print(f"Lịch sử của tài khoản cũ '{old_account_name}' không tồn tại. Không có gì để di chuyển.")
        return

    try:
        with open(old_history_file, 'r', encoding='utf-8') as f:
            old_history = json.load(f)
    except json.JSONDecodeError:
        print("Lỗi đọc file lịch sử cũ. File có thể bị hỏng.")
        return

    try:
        with open(new_history_file, 'r', encoding='utf-8') as f:
            new_history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        new_history = []

    # Cập nhật account_name trong lịch sử cũ và thêm vào lịch sử mới
    for item in old_history:
        item["account_name"] = new_account_name
        if item not in new_history: # Tránh trùng lặp nếu đã có
            new_history.append(item)

    try:
        with open(new_history_file, 'w', encoding='utf-8') as f:
            json.dump(new_history, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã di chuyển lịch sử từ '{old_account_name}' sang '{new_account_name}'.")
        # Tùy chọn: Xóa lịch sử cũ sau khi di chuyển thành công
        # old_history_file.unlink()
        # print(f"Đã xóa lịch sử cũ của '{old_account_name}'.")
    except Exception as e:
        print(f"Lỗi khi ghi file lịch sử mới: {e}")
        
def get_all_accounts():
    """Lấy danh sách tất cả các tài khoản đã tạo."""
    if not ACCOUNTS_DIR.exists():
        return []
    return [d.name for d in ACCOUNTS_DIR.iterdir() if d.is_dir()]

def get_account_status(account_name: str):
    """Lấy trạng thái của một tài khoản (số video đã upload)."""
    upload_count = get_upload_count(account_name)
    return f"Tài khoản '{account_name}': {upload_count} video đã upload."

def get_all_accounts_status():
    """Lấy trạng thái của tất cả các tài khoản."""
    accounts = get_all_accounts()
    if not accounts:
        return "Chưa có tài khoản nào được tạo."
    
    status_messages = ["Trạng thái các tài khoản:"]
    for account in accounts:
        status_messages.append(f"- {get_account_status(account)}")
    return "\n".join(status_messages)

def get_all_uploaded_videos_across_accounts():
    """Lấy danh sách tất cả các video đã upload trên tất cả các tài khoản."""
    all_uploaded = []
    accounts = get_all_accounts()
    for account in accounts:
        all_uploaded.extend(get_uploaded_videos(account))
    return all_uploaded

def get_unique_uploaded_video_ids_across_accounts():
    """Lấy danh sách các ID video duy nhất đã upload trên tất cả các tài khoản."""
    all_uploaded = get_all_uploaded_videos_across_accounts()
    return list(set(item["video_id"] for item in all_uploaded))

def get_unuploaded_videos_across_accounts():
    """Lấy danh sách các video chưa được upload bởi bất kỳ tài khoản nào."""
    all_videos = get_all_videos(silent=True)
    uploaded_ids = get_unique_uploaded_video_ids_across_accounts()
    
    unuploaded = []
    for video_path in all_videos:
        video_id = get_video_id(video_path)
        if video_id not in uploaded_ids:
            unuploaded.append(video_path)
    return unuploaded

def get_unuploaded_videos_count_across_accounts():
    """Đếm số lượng video chưa được upload bởi bất kỳ tài khoản nào."""
    return len(get_unuploaded_videos_across_accounts())

def get_unuploaded_videos_by_account(account_name: str):
    """Lấy danh sách các video chưa được upload bởi một tài khoản cụ thể."""
    all_videos = get_all_videos(silent=True)
    uploaded_by_account = [item["video_id"] for item in get_uploaded_videos(account_name)]
    
    unuploaded = []
    for video_path in all_videos:
        video_id = get_video_id(video_path)
        if video_id not in uploaded_by_account:
            unuploaded.append(video_path)
    return unuploaded

def get_unuploaded_videos_count_by_account(account_name: str):
    """Đếm số lượng video chưa được upload bởi một tài khoản cụ thể."""
    return len(get_unuploaded_videos_by_account(account_name))

def get_video_info(video_id: str):
    """Lấy thông tin chi tiết về một video (mô tả, nguồn, trạng thái upload)."""
    description = get_description(video_id)
    source, video_path = find_video_source(video_id)
    
    uploaded_by_accounts = []
    accounts = get_all_accounts()
    for account in accounts:
        if is_uploaded(video_id, account):
            uploaded_by_accounts.append(account)
            
    status = "Đã upload" if uploaded_by_accounts else "Chưa upload"
    
    return {
        "video_id": video_id,
        "description": description,
        "source": source,
        "path": str(video_path) if video_path else None,
        "status": status,
        "uploaded_by": uploaded_by_accounts
    }

def get_all_video_info():
    """Lấy thông tin chi tiết về tất cả các video có sẵn."""
    all_videos = get_all_videos(silent=True)
    all_info = []
    for video_path in all_videos:
        video_id = get_video_id(video_path)
        all_info.append(get_video_info(video_id))
    return all_info

def get_video_history(video_id: str):
    """Lấy lịch sử upload của một video cụ thể trên tất cả các tài khoản."""
    all_uploaded = get_all_uploaded_videos_across_accounts()
    return [item for item in all_uploaded if item["video_id"] == video_id]

def get_account_history(account_name: str):
    """Lấy toàn bộ lịch sử upload của một tài khoản cụ thể."""
    return get_uploaded_videos(account_name)

def get_account_history_summary(account_name: str):
    """Lấy tóm tắt lịch sử upload của một tài khoản."""
    history = get_account_history(account_name)
    if not history:
        return f"Tài khoản '{account_name}' chưa upload video nào."
    
    summary = [f"Tóm tắt lịch sử upload của tài khoản '{account_name}':"]
    summary.append(f"Tổng số video đã upload: {len(history)}")
    
    # Đếm số lượng video từ mỗi nguồn
    source_counts = {}
    for item in history:
        video_id = item["video_id"]
        source, _ = find_video_source(video_id)
        source_counts[source] = source_counts.get(source, 0) + 1
    
    if source_counts:
        summary.append("Phân loại theo nguồn:")
        for source, count in source_counts.items():
            summary.append(f"- {source.upper()}: {count} video")
            
    return "\n".join(summary)

def get_all_accounts_history_summary():
    """Lấy tóm tắt lịch sử upload của tất cả các tài khoản."""
    accounts = get_all_accounts()
    if not accounts:
        return "Chưa có tài khoản nào được tạo."
    
    all_summaries = ["Tóm tắt lịch sử upload của tất cả các tài khoản:"]
    for account in accounts:
        all_summaries.append(get_account_history_summary(account))
        all_summaries.append("-" * 30) # Dòng phân cách
    return "\n".join(all_summaries)

def get_video_stalker_dirs():
    """Trả về danh sách các thư mục stalker video."""
    return list(VIDEO_SOURCES.values())

def get_video_stalker_names():
    """Trả về danh sách tên các nguồn stalker video."""
    return list(VIDEO_SOURCES.keys())

def get_video_stalker_info():
    """Trả về thông tin về các thư mục stalker video."""
    info = ["Thông tin thư mục video nguồn:"]
    for name, path in VIDEO_SOURCES.items():
        info.append(f"- {name.upper()}: {path} (Tồn tại: {path.exists()})")
    return "\n".join(info)

def get_config_info():
    """Trả về thông tin cấu hình chính."""
    info = ["Thông tin cấu hình chính:"]
    info.append(f"- Thư mục tài khoản: {ACCOUNTS_DIR} (Tồn tại: {ACCOUNTS_DIR.exists()})")
    info.append(f"- Đường dẫn Chrome: {CHROME_EXECUTABLE}")
    info.append(f"- Cổng Debug Chrome: {CHROME_DEBUG_PORT}")
    info.append(f"- Số lượng upload song song tối đa: {MAX_CONCURRENT_UPLOADS}")
    info.append("\n" + get_video_stalker_info())
    return "\n".join(info)

def get_system_info():
    """Trả về thông tin hệ thống cơ bản."""
    info = ["Thông tin hệ thống:"]
    info.append(f"-Hệ điều hành: {sys.platform}")
    info.append(f"- Phiên bản Python: {sys.version}")
    info.append(f"- Thư mục làm việc hiện tại: {os.getcwd()}")
    return "\n".join(info)

def get_full_status_report():
    """Tạo báo cáo trạng thái đầy đủ của hệ thống."""
    report = [
        "--- BÁO CÁO TRẠNG THÁI HỆ THỐNG ---",
        get_system_info(),
        "",
        get_config_info(),
        "",
        get_all_accounts_status(),
        "",
        get_all_accounts_history_summary(),
        "",
        f"Tổng số video chưa upload bởi bất kỳ tài khoản nào: {get_unuploaded_videos_count_across_accounts()}",
        "--- KẾT THÚC BÁO CÁO ---"
    ]
    return "\n".join(report)

def get_video_list_for_display(account_name: str):
    """Lấy danh sách video chưa upload cho một tài khoản để hiển thị."""
    videos = get_unuploaded_videos_by_account(account_name)
    if not videos:
        return "✅ Tất cả video đã được đăng bởi tài khoản này."
    
    display_list = [f"📋 Các video chưa được upload bởi tài khoản '{account_name}':"]
    for i, video in enumerate(videos):
        video_id = get_video_id(video)
        source, _ = find_video_source(video_id)
        source_display = source.upper() if source else "N/A"
        description = get_description(video_id) or "Không có mô tả"
        display_list.append(f"{i+1:2}. [{source_display}] {video.name} - Mô tả: {description}")
    return "\n".join(display_list)

def get_all_videos_for_display():
    """Lấy danh sách tất cả video có sẵn để hiển thị."""
    videos = get_all_videos(silent=True)
    if not videos:
        return "📭 Không có video nào trong các thư mục nguồn."
    
    display_list = ["📋 Tất cả video có sẵn trong hệ thống:"]
    for i, video in enumerate(videos):
        video_id = get_video_id(video)
        source, _ = find_video_source(video_id)
        source_display = source.upper() if source else "N/A"
        description = get_description(video_id) or "Không có mô tả"
        display_list.append(f"{i+1:2}. [{source_display}] {video.name} - Mô tả: {description}")
    return "\n".join(display_list)

def get_uploaded_videos_for_display(account_name: str):
    """Lấy danh sách các video đã upload bởi một tài khoản để hiển thị."""
    history = get_uploaded_videos(account_name)
    if not history:
        return f"Tài khoản '{account_name}' chưa upload video nào."
    
    display_list = [f"📋 Các video đã upload bởi tài khoản '{account_name}':"]
    for i, item in enumerate(history):
        video_id = item["video_id"]
        description = item.get("description", "Không có mô tả")
        upload_time = item.get("upload_time", "N/A")
        source, _ = find_video_source(video_id)
        source_display = source.upper() if source else "N/A"
        display_list.append(f"{i+1:2}. [{source_display}] ID: {video_id} - Mô tả: {description} - Thời gian: {upload_time}")
    return "\n".join(display_list)

def get_all_uploaded_videos_across_accounts_for_display():
    """Lấy danh sách tất cả các video đã upload trên tất cả các tài khoản để hiển thị."""
    all_uploaded = get_all_uploaded_videos_across_accounts()
    if not all_uploaded:
        return "Chưa có video nào được upload trên bất kỳ tài khoản nào."
    
    display_list = ["📋 Tất cả video đã upload trên các tài khoản:"]
    for i, item in enumerate(all_uploaded):
        video_id = item["video_id"]
        description = item.get("description", "Không có mô tả")
        upload_time = item.get("upload_time", "N/A")
        account_name = item.get("account_name", "N/A")
        source, _ = find_video_source(video_id)
        source_display = source.upper() if source else "N/A"
        display_list.append(f"{i+1:2}. [{source_display}] ID: {video_id} - Mô tả: {description} - Tài khoản: {account_name} - Thời gian: {upload_time}")
    return "\n".join(display_list)

def get_unique_uploaded_video_ids_across_accounts_for_display():
    """Lấy danh sách các ID video duy nhất đã upload trên tất cả các tài khoản để hiển thị."""
    unique_ids = get_unique_uploaded_video_ids_across_accounts()
    if not unique_ids:
        return "Chưa có video nào được upload trên bất kỳ tài khoản nào."
    
    display_list = ["📋 Các ID video duy nhất đã upload trên các tài khoản:"]
    for i, video_id in enumerate(unique_ids):
        display_list.append(f"{i+1:2}. {video_id}")
    return "\n".join(display_list)

def get_unuploaded_videos_across_accounts_for_display():
    """Lấy danh sách các video chưa được upload bởi bất kỳ tài khoản nào để hiển thị."""
    unuploaded = get_unuploaded_videos_across_accounts()
    if not unuploaded:
        return "✅ Tất cả video đã được đăng bởi ít nhất một tài khoản."
    
    display_list = ["📋 Các video chưa được upload bởi bất kỳ tài khoản nào:"]
    for i, video_path in enumerate(unuploaded):
        video_id = get_video_id(video_path)
        source, _ = find_video_source(video_id)
        source_display = source.upper() if source else "N/A"
        description = get_description(video_id) or "Không có mô tả"
        display_list.append(f"{i+1:2}. [{source_display}] {video_path.name} - Mô tả: {description}")
    return "\n".join(display_list)

def get_video_info_for_display(video_id: str):
    """Lấy thông tin chi tiết về một video để hiển thị."""
    info = get_video_info(video_id)
    if not info["path"]:
                return f"❌ Không tìm thấy video với ID: {video_id}"
    
    display_info = [f"--- Thông tin chi tiết video ID: {video_id} ---"]
    display_info.append(f"Mô tả: {info['description'] or 'Không có mô tả'}")
    display_info.append(f"Nguồn: {info['source'].upper() if info['source'] else 'N/A'}")
    display_info.append(f"Đường dẫn: {info['path']}")
    display_info.append(f"Trạng thái: {info['status']}")
    if info['uploaded_by']:
                display_info.append(f"Đã upload bởi các tài khoản: {', '.join(info['uploaded_by'])}")
    else:
        display_info.append("Chưa được upload bởi bất kỳ tài khoản nào.")
    display_info.append("---")
    return "\n".join(display_info)

def get_all_video_info_for_display():
    """Lấy thông tin chi tiết về tất cả các video có sẵn để hiển thị."""
    all_info = get_all_video_info()
    if not all_info:
        return "📭 Không có video nào trong các thư mục nguồn."
    
    display_list = ["--- Thông tin chi tiết tất cả video ---"]
    for info in all_info:
        display_list.append(get_video_info_for_display(info["video_id"]))
    return "\n".join(display_list)

def get_video_history_for_display(video_id: str):
    """Lấy lịch sử upload của một video cụ thể trên tất cả các tài khoản để hiển thị."""
    history = get_video_history(video_id)
    if not history:
        return f"Video ID '{video_id}' chưa được upload bởi bất kỳ tài khoản nào."
    
    display_list = [f"--- Lịch sử upload của video ID: {video_id} ---"]
    for i, item in enumerate(history):
        description = item.get("description", "Không có mô tả")
        upload_time = item.get("upload_time", "N/A")
        account_name = item.get("account_name", "N/A")
        display_list.append(f"{i+1:2}. Tài khoản: {account_name} - Mô tả: {description} - Thời gian: {upload_time}")
    display_list.append("---")
    return "\n".join(display_list)

def get_account_history_for_display(account_name: str):
    """Lấy toàn bộ lịch sử upload của một tài khoản cụ thể để hiển thị."""
    return get_uploaded_videos_for_display(account_name)

def get_account_history_summary_for_display(account_name: str):
    """Lấy tóm tắt lịch sử upload của một tài khoản để hiển thị."""
    return get_account_history_summary(account_name)

def get_all_accounts_history_summary_for_display():
    """Lấy tóm tắt lịch sử upload của tất cả các tài khoản để hiển thị."""
    return get_all_accounts_history_summary()

def get_full_status_report_for_display():
    """Tạo báo cáo trạng thái đầy đủ của hệ thống để hiển thị."""
    return get_full_status_report()

def get_video_stalker_info_for_display():
    """Trả về thông tin về các thư mục stalker video để hiển thị."""
    return get_video_stalker_info()

def get_config_info_for_display():
    """Trả về thông tin cấu hình chính để hiển thị."""
    return get_config_info()

def get_system_info_for_display():
    """Trả về thông tin hệ thống cơ bản để hiển thị."""
    return get_system_info()
