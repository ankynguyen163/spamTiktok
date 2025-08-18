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


# Import config để lấy đường dẫn accounts
from Tiktok.config import ACCOUNTS_DIR, VIDEO_SOURCES
from Tiktok.utils import (
    ACCOUNTS_DIR, VIDEO_SOURCES, get_all_videos, is_uploaded, get_history_path,
    get_unique_uploaded_video_ids_across_accounts, get_video_id
)


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
    
    # Lấy danh sách ID video đã upload một lần duy nhất
    uploaded_video_ids = get_unique_uploaded_video_ids_across_accounts()

    for video_path in all_videos:
        video_id = get_video_id(video_path)
        
        if video_id in uploaded_video_ids:
            uploaded_count += 1
        else:
            pending_videos.append(video_path)
    
    print(f"📊 Tổng quan:")
    print(f"   📹 Tổng số video: {len(all_videos)}")
    print(f"   ✅ Đã upload: {uploaded_count}")
    print(f"   ⏳ Pending: {len(pending_videos)}")
    
    if not pending_videos:
        print("✨ Không có video pending nào cần dọn dẹp!")
        return
    
    # Tạo danh sách file sẽ bị xóa cho cả dry_run và xóa thật
    files_to_delete_map = {}
    for video_path in pending_videos:
        video_id = get_video_id(video_path)
        # Pattern đúng: tìm tất cả file bắt đầu bằng video_id
        related_files = list(video_path.parent.glob(f"{video_id}*"))
        if related_files:
            files_to_delete_map[video_path.name] = related_files

    if not files_to_delete_map:
        print("✨ Không tìm thấy file cụ thể nào để xóa cho các video pending.")
        return

    if dry_run:
        print(f"\n📋 Danh sách {len(files_to_delete_map)} nhóm video pending sẽ bị xóa:")
        for video_name, related_files in files_to_delete_map.items():
            print(f"   🗑️ {video_name} và các file liên quan:")
            for meta_file in related_files:
                print(f"      📄 {meta_file.name}")
        
        print(f"\n💡 Để thực hiện xóa, chạy lại lệnh mà không có --dry-run")
        return
    
    # Xác nhận trước khi xóa
    total_files_to_delete = sum(len(files) for files in files_to_delete_map.values())
    response = input(f"\n⚠️ Bạn có chắc muốn xóa {total_files_to_delete} file của {len(files_to_delete_map)} video pending? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Hủy bỏ thao tác dọn dẹp.")
        return
    
    # Thực hiện xóa
    deleted_count = 0
    error_count = 0
    
    for video_name, related_files in files_to_delete_map.items():
        for file_to_delete in related_files:
            try:
                file_to_delete.unlink()
                print(f"🗑️ Đã xóa: {file_to_delete.name}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ Lỗi xóa {file_to_delete.name}: {e}")
                error_count += 1
    
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
    
    uploaded_video_ids = get_unique_uploaded_video_ids_across_accounts()
    if not uploaded_video_ids:
        print("📭 Không có lịch sử upload nào.")
        return
    
    uploaded_videos = []
    pending_count = 0
    
    for video_path in all_videos:
        video_id = get_video_id(video_path)
        
        if video_id in uploaded_video_ids:
            uploaded_videos.append(video_path)
        else:
            pending_count += 1
    
    print(f"📊 Tổng quan:")
    print(f"   📹 Tổng số video: {len(all_videos)}")
    print(f"   ✅ Đã upload: {len(uploaded_videos)}")
    print(f"   ⏳ Pending: {pending_count}")
    
    if not uploaded_videos:
        print("✨ Không có video đã upload nào cần dọn dẹp!")
        return

    # Tạo danh sách file sẽ bị xóa cho cả dry_run và xóa thật
    files_to_delete_map = {}
    for video_path in uploaded_videos:
        video_id = get_video_id(video_path)
        # Pattern đúng: tìm tất cả file bắt đầu bằng video_id
        related_files = list(video_path.parent.glob(f"{video_id}*"))
        if related_files:
            files_to_delete_map[video_path.name] = related_files

    if not files_to_delete_map:
        print("✨ Không tìm thấy file cụ thể nào để xóa cho các video đã upload.")
        return

    if dry_run:
        print(f"\n📋 Danh sách {len(files_to_delete_map)} nhóm video đã upload sẽ bị xóa:")
        for video_name, related_files in files_to_delete_map.items():
            print(f"   🗑️ {video_name} và các file liên quan:")
            for meta_file in related_files:
                print(f"      📄 {meta_file.name}")
        
        print(f"\n💡 Để thực hiện xóa, chạy lại lệnh mà không có --dry-run")
        return
    
    # Xác nhận trước khi xóa
    total_files_to_delete = sum(len(files) for files in files_to_delete_map.values())
    response = input(f"\n⚠️ Bạn có chắc muốn xóa {total_files_to_delete} file của {len(files_to_delete_map)} video đã upload? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Hủy bỏ thao tác dọn dẹp.")
        return
    
    # Thực hiện xóa
    deleted_count = 0
    error_count = 0
    
    for video_name, related_files in files_to_delete_map.items():
        for file_to_delete in related_files:
            try:
                file_to_delete.unlink()
                print(f"🗑️ Đã xóa: {file_to_delete.name}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ Lỗi xóa {file_to_delete.name}: {e}")
                error_count += 1
    
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
