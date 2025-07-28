#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clean Storage Manager - Quản lý dọn dẹp file video

Chức năng:
1. clean-pending: Xóa video chưa được upload lên bất kỳ tài khoản nào
2. clean-uploaded: Xóa video đã được upload thành công (có trong history)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Import từ config chung
from Tiktok.config import (
    VIDEO_SOURCES,
    ACCOUNTS_DIR,
    get_all_videos,
    is_uploaded,
    get_history_path
)


def get_all_uploaded_video_ids():
    """
    Lấy danh sách tất cả video_id đã được upload bởi bất kỳ tài khoản nào.
    """
    uploaded_ids = set()
    
    if not ACCOUNTS_DIR.exists():
        return uploaded_ids
    
    for account_dir in ACCOUNTS_DIR.iterdir():
        if not account_dir.is_dir():
            continue
            
        history_file = account_dir / 'history.json'
        if not history_file.exists():
            continue
            
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            for item in history:
                video_id = item.get("video_id")
                if video_id:
                    uploaded_ids.add(video_id)
                    
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Lỗi đọc history từ {history_file}: {e}")
            continue
    
    return uploaded_ids


def clean_pending_videos(dry_run=False):
    """
    Xóa các video đã tải về nhưng chưa được upload lên bất kỳ tài khoản nào.
    
    Args:
        dry_run (bool): Nếu True, chỉ hiển thị danh sách mà không thực sự xóa
    """
    print("🔍 Đang quét video pending...")
    
    all_videos = get_all_videos(silent=True)
    if not all_videos:
        print("📭 Không có video nào được tìm thấy.")
        return
    
    pending_videos = []
    uploaded_count = 0
    
    for video_path in all_videos:
        # Lấy video_id từ tên file (bỏ extension)
        video_id = video_path.stem
        
        if is_uploaded(video_id):
            uploaded_count = 1
        else:
            pending_videos.append(video_path)
    
    print(f"📊 Tổng quan:")
    print(f"   📹 Tổng số video: {len(all_videos)}")
    print(f"   ✅ Đã upload: {uploaded_count}")
    print(f"   ⏳ Pending: {len(pending_videos)}")
    
    if not pending_videos:
        print("✨ Không có video pending nào cần dọn dẹp!")
        return
    
    if dry_run:
        print(f"\n📋 Danh sách {len(pending_videos)} video pending sẽ bị xóa:")
        for video_path in pending_videos:
            # Tìm file metadata tương ứng
            metadata_files = list(video_path.parent.glob(f"{video_path.stem}.*"))
            metadata_files = [f for f in metadata_files if f.suffix.lower() in ['.json', '.txt', '.info']]
            
            print(f"   🗑️ {video_path.name}")
            for meta_file in metadata_files:
                print(f"      📄 {meta_file.name}")
        
        print(f"\n💡 Để thực hiện xóa, chạy lại lệnh mà không có --dry-run")
        return
    
    # Xác nhận trước khi xóa
    response = input(f"\n⚠️ Bạn có chắc muốn xóa {len(pending_videos)} video pending? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Hủy bỏ thao tác dọn dẹp.")
        return
    
    # Thực hiện xóa
    deleted_count = 0
    error_count = 0
    
    for video_path in pending_videos:
        try:
            # Tìm và xóa tất cả file liên quan (video  metadata)
            video_id = video_path.stem
            related_files = list(video_path.parent.glob(f"{video_id}.*"))
            
            for file_to_delete in related_files:
                file_to_delete.unlink()
                print(f"🗑️ Đã xóa: {file_to_delete.name}")
            
            deleted_count = len(related_files)
            
        except Exception as e:
            print(f"⚠️ Lỗi xóa {video_path.name}: {e}")
            error_count = 1
    
    print(f"\n✅ Hoàn thành!")
    print(f"   🗑️ Đã xóa: {deleted_count} file")
    if error_count > 0:
        print(f"   ❌ Lỗi: {error_count} file")


def clean_uploaded_videos(dry_run=False):
    """
    Xóa các file video gốc đã được upload thành công (có trong history).
    
    Args:
        dry_run (bool): Nếu True, chỉ hiển thị danh sách mà không thực sự xóa
    """
    print("🔍 Đang quét video đã upload...")
    
    all_videos = get_all_videos(silent=True)
    if not all_videos:
        print("📭 Không có video nào được tìm thấy.")
        return
    
    uploaded_video_ids = get_all_uploaded_video_ids()
    if not uploaded_video_ids:
        print("📭 Không có lịch sử upload nào.")
        return
    
    uploaded_videos = []
    pending_count = 0
    
    for video_path in all_videos:
        video_id = video_path.stem
        
        if video_id in uploaded_video_ids:
            uploaded_videos.append(video_path)
        else:
            pending_count = 1
    
    print(f"📊 Tổng quan:")
    print(f"   📹 Tổng số video: {len(all_videos)}")
    print(f"   ✅ Đã upload: {len(uploaded_videos)}")
    print(f"   ⏳ Pending: {pending_count}")
    
    if not uploaded_videos:
        print("✨ Không có video đã upload nào cần dọn dẹp!")
        return
    
    if dry_run:
        print(f"\n📋 Danh sách {len(uploaded_videos)} video đã upload sẽ bị xóa:")
        for video_path in uploaded_videos:
            # Tìm file metadata tương ứng
            metadata_files = list(video_path.parent.glob(f"{video_path.stem}.*"))
            metadata_files = [f for f in metadata_files if f.suffix.lower() in ['.json', '.txt', '.info']]
            
            print(f"   🗑️ {video_path.name}")
            for meta_file in metadata_files:
                print(f"      📄 {meta_file.name}")
        
        print(f"\n💡 Để thực hiện xóa, chạy lại lệnh mà không có --dry-run")
        return
    
    # Xác nhận trước khi xóa
    response = input(f"\n⚠️ Bạn có chắc muốn xóa {len(uploaded_videos)} video đã upload? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Hủy bỏ thao tác dọn dẹp.")
        return
    
    # Thực hiện xóa
    deleted_count = 0
    error_count = 0
    
    for video_path in uploaded_videos:
        try:
            # Tìm và xóa tất cả file liên quan (video  metadata)
            video_id = video_path.stem
            related_files = list(video_path.parent.glob(f"{video_id}.*"))
            
            for file_to_delete in related_files:
                file_to_delete.unlink()
                print(f"🗑️ Đã xóa: {file_to_delete.name}")
            
            deleted_count = len(related_files)
            
        except Exception as e:
            print(f"⚠️ Lỗi xóa {video_path.name}: {e}")
            error_count = 1
    
    print(f"\n✅ Hoàn thành!")
    print(f"   🗑️ Đã xóa: {deleted_count} file")
    if error_count > 0:
        print(f"   ❌ Lỗi: {error_count} file")


def main():
    """Entry point chính cho module cleanStorage"""
    if len(sys.argv) < 2:
        print("❌ Thiếu tham số. Sử dụng: 'pending' hoặc 'uploaded'")
        return
    
    action = sys.argv[1].lower()
    dry_run = '--dry-run' in sys.argv
    
    if action == "pending":
        print("🧹 Bắt đầu dọn dẹp video pending...")
        clean_pending_videos(dry_run=dry_run)
        
    elif action == "uploaded":
        print("🧹 Bắt đầu dọn dẹp video đã upload...")
        clean_uploaded_videos(dry_run=dry_run)
        
    else:
        print(f"❌ Hành động không hợp lệ: {action}")
        print("💡 Sử dụng 'pending' để xóa video chưa upload")
        print("💡 Sử dụng 'uploaded' để xóa video đã upload thành công")


if __name__ == "__main__":
    main()
