#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clean Storage Utilities - Các hàm tiện ích cho cleanStorage

Cung cấp các hàm helper để:
- Thống kê chi tiết về storage
- Kiểm tra tính toàn vẹn file
- Báo cáo dung lượng
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set

from Tiktok.config import (
    VIDEO_SOURCES,
    ACCOUNTS_DIR,
    get_all_videos,
    is_uploaded
)


def get_file_size_mb(file_path: Path) -> float:
    """Lấy kích thước file theo MB"""
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except:
        return 0.0


def get_storage_statistics() -> Dict:
    """
    Thống kê chi tiết về storage hiện tại.
    
    Returns:
        Dict chứa thông tin chi tiết về:
        - Tổng số video và dung lượng
        - Phân loại theo trạng thái (pending/uploaded)
        - Phân loại theo nguồn (fb/yt)
    """
    stats = {
        'total_videos': 0,
        'total_size_mb': 0.0,
        'pending_videos': 0,
        'pending_size_mb': 0.0,
        'uploaded_videos': 0,
        'uploaded_size_mb': 0.0,
        'by_source': {},
        'accounts_count': 0,
        'last_updated': datetime.now().isoformat()
    }
    
    # Đếm số tài khoản
    if ACCOUNTS_DIR.exists():
        stats['accounts_count'] = len([d for d in ACCOUNTS_DIR.iterdir() if d.is_dir()])
    
    # Thống kê theo nguồn
    for source_name, source_dir in VIDEO_SOURCES.items():
        source_stats = {
            'total_videos': 0,
            'total_size_mb': 0.0,
            'pending_videos': 0,
            'pending_size_mb': 0.0,
            'uploaded_videos': 0,
            'uploaded_size_mb': 0.0,
            'exists': source_dir.exists()
        }
        
        if source_dir.exists():
            # Lấy tất cả video từ nguồn này
            videos = [f for f in source_dir.iterdir() 
                     if f.suffix.lower() in ['.mp4', '.webm', '.mov', '.avi', '.mkv']]
            
            for video_path in videos:
                video_id = video_path.stem
                size_mb = get_file_size_mb(video_path)
                
                source_stats['total_videos'] += 1
                source_stats['total_size_mb'] += size_mb
                
                if is_uploaded(video_id):
                    source_stats['uploaded_videos'] += 1
                    source_stats['uploaded_size_mb'] += size_mb
                else:
                    source_stats['pending_videos'] += 1
                    source_stats['pending_size_mb'] += size_mb
        
        stats['by_source'][source_name] = source_stats
        
        # Cộng vào tổng
        stats['total_videos'] += source_stats['total_videos']
        stats['total_size_mb'] += source_stats['total_size_mb']
        stats['pending_videos'] += source_stats['pending_videos']
        stats['pending_size_mb'] += source_stats['pending_size_mb']
        stats['uploaded_videos'] += source_stats['uploaded_videos']
        stats['uploaded_size_mb'] += source_stats['uploaded_size_mb']
    
    return stats


def find_orphaned_metadata() -> List[Path]:
    """
    Tìm các file metadata (.json, .txt, .info) không có video tương ứng.
    
    Returns:
        List các file metadata không có video tương ứng
    """
    orphaned_files = []
    
    for source_dir in VIDEO_SOURCES.values():
        if not source_dir.exists():
            continue
            
        # Lấy tất cả file metadata
        metadata_files = []
        for ext in ['.json', '.txt', '.info']:
            metadata_files.extend(source_dir.glob(f"*{ext}"))
        
        for metadata_file in metadata_files:
            # Kiểm tra xem có video tương ứng không
            video_id = metadata_file.stem
            video_exists = False
            
            for video_ext in ['.mp4', '.webm', '.mov', '.avi', '.mkv']:
                video_path = source_dir / f"{video_id}{video_ext}"
                if video_path.exists():
                    video_exists = True
                    break
            
            if not video_exists:
                orphaned_files.append(metadata_file)
    
    return orphaned_files


def find_orphaned_videos() -> List[Path]:
    """
    Tìm các file video không có metadata tương ứng.
    
    Returns:
        List các file video không có metadata
    """
    orphaned_videos = []
    
    for source_dir in VIDEO_SOURCES.values():
        if not source_dir.exists():
            continue
            
        videos = [f for f in source_dir.iterdir() 
                 if f.suffix.lower() in ['.mp4', '.webm', '.mov', '.avi', '.mkv']]
        
        for video_path in videos:
            video_id = video_path.stem
            
            # Kiểm tra xem có file metadata không
            metadata_exists = False
            for metadata_ext in ['.json', '.txt', '.info']:
                metadata_path = source_dir / f"{video_id}{metadata_ext}"
                if metadata_path.exists():
                    metadata_exists = True
                    break
            
            if not metadata_exists:
                orphaned_videos.append(video_path)
    
    return orphaned_videos


def clean_orphaned_metadata(dry_run=False) -> int:
    """
    Dọn dẹp các file metadata không có video tương ứng.
    
    Args:
        dry_run (bool): Chỉ hiển thị danh sách, không thực sự xóa
        
    Returns:
        int: Số file đã xóa
    """
    orphaned_files = find_orphaned_metadata()
    
    if not orphaned_files:
        print("✨ Không có file metadata mồ côi nào!")
        return 0
    
    print(f"🔍 Tìm thấy {len(orphaned_files)} file metadata mồ côi:")
    
    if dry_run:
        for file_path in orphaned_files:
            print(f"   📄 {file_path.name}")
        print("\n💡 Để thực hiện xóa, chạy lại mà không có --dry-run")
        return 0
    
    # Xác nhận
    response = input(f"\n⚠️ Bạn có chắc muốn xóa {len(orphaned_files)} file metadata mồ côi? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Hủy bỏ thao tác.")
        return 0
    
    # Thực hiện xóa
    deleted_count = 0
    for file_path in orphaned_files:
        try:
            file_path.unlink()
            print(f"🗑️ Đã xóa: {file_path.name}")
            deleted_count = 1
        except Exception as e:
            print(f"⚠️ Lỗi xóa {file_path.name}: {e}")
    
    print(f"✅ Đã xóa {deleted_count} file metadata mồ côi!")
    return deleted_count


def get_old_videos(days_old: int = 30) -> List[Tuple[Path, int]]:
    """
    Tìm các video cũ hơn số ngày chỉ định.
    
    Args:
        days_old (int): Số ngày để coi là "cũ"
        
    Returns:
        List[(video_path, days_since_modified)]
    """
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.now() - timedelta(days=days_old)
    old_videos = []
    
    all_videos = get_all_videos(silent=True)
    
    for video_path in all_videos:
        try:
            modified_time = datetime.fromtimestamp(video_path.stat().st_mtime)
            if modified_time < cutoff_time:
                days_since = (datetime.now() - modified_time).days
                old_videos.append((video_path, days_since))
        except:
            continue
    
    # Sắp xếp theo tuổi (cũ nhất trước)
    old_videos.sort(key=lambda x: x[1], reverse=True)
    return old_videos


def print_storage_report():
    """In báo cáo chi tiết về storage hiện tại"""
    print("📊 === BÁO CÁO STORAGE SPAMTIKTOK ===\n")
    
    stats = get_storage_statistics()
    
    # Tổng quan
    print(f"🎯 Tổng quan:")
    print(f"   📹 Tổng video: {stats['total_videos']} ({stats['total_size_mb']:.1f} MB)")
    print(f"   ⏳ Pending: {stats['pending_videos']} ({stats['pending_size_mb']:.1f} MB)")
    print(f"   ✅ Uploaded: {stats['uploaded_videos']} ({stats['uploaded_size_mb']:.1f} MB)")
    print(f"   👥 Tài khoản: {stats['accounts_count']}")
    
    # Chi tiết theo nguồn
    print(f"\n📂 Chi tiết theo nguồn:")
    for source_name, source_stats in stats['by_source'].items():
        status = "✅" if source_stats['exists'] else "❌"
        print(f"   {status} {source_name.upper()}:")
        if source_stats['exists']:
            print(f"      📹 Total: {source_stats['total_videos']} ({source_stats['total_size_mb']:.1f} MB)")
            print(f"      ⏳ Pending: {source_stats['pending_videos']} ({source_stats['pending_size_mb']:.1f} MB)")
            print(f"      ✅ Uploaded: {source_stats['uploaded_videos']} ({source_stats['uploaded_size_mb']:.1f} MB)")
        else:
            print(f"      📁 Thư mục không tồn tại")
    
    # Kiểm tra file mồ côi
    orphaned_metadata = find_orphaned_metadata()
    orphaned_videos = find_orphaned_videos()
    
    if orphaned_metadata or orphaned_videos:
        print(f"\n⚠️ File mồ côi:")
        if orphaned_metadata:
            print(f"   📄 Metadata không có video: {len(orphaned_metadata)}")
        if orphaned_videos:
            print(f"   📹 Video không có metadata: {len(orphaned_videos)}")
    
    # Video cũ
    old_videos = get_old_videos(30)
    if old_videos:
        print(f"\n📅 Video cũ hơn 30 ngày: {len(old_videos)}")
        if len(old_videos) <= 5:
            for video_path, days in old_videos:
                print(f"   📹 {video_path.name} ({days} ngày)")
        else:
            print(f"   📹 Cũ nhất: {old_videos[0][0].name} ({old_videos[0][1]} ngày)")
    
    print(f"\n🕐 Báo cáo tạo lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        print_storage_report()
    else:
        print("💡 Sử dụng: python utils.py report")