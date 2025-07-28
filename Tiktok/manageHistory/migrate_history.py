#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
import sys
import os

# Thêm thư mục gốc của dự án vào sys.path để có thể import từ các module khác
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from Tiktok.config import ACCOUNTS_DIR, get_history_path

# Đường dẫn tuyệt đối đến file lịch sử cũ
OLD_HISTORY_FILE = project_root / 'Tiktok' / 'spamUploadTiktok' / 'history' / 'video_history.json'

def migrate():
    """
    Di chuyển các mục từ file lịch sử global cũ sang file history.json của một tài khoản cụ thể.
    """
    # 1. Kiểm tra xem file lịch sử cũ có tồn tại không
    if not OLD_HISTORY_FILE.exists():
        print(f"✅ Không tìm thấy file lịch sử cũ tại: {OLD_HISTORY_FILE}")
        print("Không có gì để di chuyển.")
        return

    # 2. Liệt kê các tài khoản có sẵn và nhận input từ người dùng
    if not ACCOUNTS_DIR.exists() or not any(ACCOUNTS_DIR.iterdir()):
        print("❌ Không tìm thấy tài khoản nào trong thư mục 'accounts'.")
        print("Vui lòng chạy 'login-tt' để tạo tài khoản trước khi di chuyển lịch sử.")
        return

    print("Các tài khoản TikTok hiện có:")
    accounts = [d.name for d in ACCOUNTS_DIR.iterdir() if d.is_dir()]
    for acc in sorted(accounts):
        print(f"  - {acc}")

    target_account = input("\n➡️  Vui lòng nhập tên tài khoản bạn muốn chuyển lịch sử cũ vào: ").strip()

    if not target_account or target_account not in accounts:
        print(f"❌ Tên tài khoản không hợp lệ hoặc không tồn tại. Đã hủy.")
        return

    # 3. Tải dữ liệu từ file lịch sử cũ và file lịch sử của tài khoản đích
    try:
        with open(OLD_HISTORY_FILE, 'r', encoding='utf-8') as f:
            old_history = json.load(f)
        print(f"🔎 Tìm thấy {len(old_history)} mục trong file lịch sử cũ.")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"❌ Lỗi khi đọc file lịch sử cũ: {e}")
        return

    target_history_path = get_history_path(target_account)
    new_history = []
    if target_history_path.exists():
        try:
            with open(target_history_path, 'r', encoding='utf-8') as f:
                new_history = json.load(f)
            print(f"ℹ️  Tài khoản '{target_account}' đã có {len(new_history)} mục lịch sử.")
        except json.JSONDecodeError:
            print(f"⚠️ Lỗi khi đọc file lịch sử của tài khoản '{target_account}'. Sẽ tạo file mới.")

    # 4. Hợp nhất lịch sử, tránh trùng lặp
    new_history_video_ids = {item.get('video_id') for item in new_history}
    migrated_count = 0
    for old_entry in old_history:
        if old_entry.get('video_id') and old_entry['video_id'] not in new_history_video_ids:
            old_entry['account_name'] = target_account  # Thêm thông tin tài khoản
            new_history.append(old_entry)
            new_history_video_ids.add(old_entry['video_id'])
            migrated_count += 1

    if migrated_count > 0:
        with open(target_history_path, 'w', encoding='utf-8') as f:
            json.dump(new_history, f, indent=2, ensure_ascii=False)
        print(f"\n🎉 Đã di chuyển thành công {migrated_count} mục lịch sử vào tài khoản '{target_account}'.")
    else:
        print("\n✅ Không có mục lịch sử mới nào cần di chuyển (có thể đã được di chuyển trước đó).")

    # 5. Đề nghị đổi tên file cũ để tránh chạy lại
    rename_choice = input(f"\n❔ Bạn có muốn đổi tên file lịch sử cũ thành '{OLD_HISTORY_FILE.name}.migrated' không? (y/n): ").lower()
    if rename_choice == 'y':
        new_name = OLD_HISTORY_FILE.with_suffix(OLD_HISTORY_FILE.suffix + '.migrated')
        OLD_HISTORY_FILE.rename(new_name)
        print(f"✅ Đã đổi tên file cũ thành: {new_name.name}")

if __name__ == "__main__":
    migrate()