#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from datetime import datetime
from pathlib import Path

# Thêm thư mục gốc của dự án vào sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from rich.console import Console
from rich.table import Table

from Tiktok.config import get_history_path, ACCOUNTS_DIR

console = Console()

def view_account_history(account_name: str, limit: int = None):
    """
    Hiển thị lịch sử upload của một tài khoản cụ thể dưới dạng bảng.
    """
    # Kiểm tra tài khoản có tồn tại không
    account_dir = ACCOUNTS_DIR / account_name
    if not account_dir.is_dir():
        console.print(f"❌ [bold red]Lỗi: Không tìm thấy tài khoản '{account_name}'.[/bold red]")
        console.print("➡️  Sử dụng lệnh [cyan]list-accounts[/cyan] để xem các tài khoản có sẵn.")
        return

    history_path = get_history_path(account_name)

    if not history_path.exists():
        console.print(f"✅ [blue]Lịch sử của tài khoản '{account_name}' trống (không tìm thấy file history.json).[/blue]")
        return

    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history_data = json.load(f)

        if not history_data:
            console.print(f"✅ [blue]Lịch sử của tài khoản '{account_name}' trống.[/blue]")
            return

        # --- Sắp xếp và giới hạn dữ liệu ---
        # Sắp xếp lịch sử theo thời gian upload, mới nhất lên đầu.
        # Những mục không có 'upload_time' sẽ được coi là cũ nhất.
        history_data.sort(
            key=lambda x: x.get('upload_time', '1970-01-01T00:00:00'),
            reverse=True
        )

        # Áp dụng giới hạn nếu có
        if limit is not None and limit > 0:
            history_data = history_data[:limit]

        title = f"📜 Lịch sử Upload của '{account_name}'"
        if limit:
            title += f" (hiển thị {len(history_data)} mục gần nhất)"
        table = Table(title=title, show_header=True, header_style="bold magenta", border_style="blue", show_lines=True)
        table.add_column("STT", style="dim", width=5)
        table.add_column("Thời gian Upload", style="green", no_wrap=True, width=18)
        table.add_column("Video ID", style="cyan", no_wrap=True)
        table.add_column("Mô tả (Description)", style="default")

        for i, entry in enumerate(history_data, 1):
            video_id = entry.get('video_id', 'N/A')
            description = entry.get('description', '')

            upload_time_str = entry.get('upload_time')
            formatted_time = "[dim]N/A[/dim]"
            if upload_time_str:
                try:
                    # Chuyển đổi chuỗi ISO 8601 thành đối tượng datetime
                    dt_object = datetime.fromisoformat(upload_time_str)
                    # Định dạng lại cho dễ đọc (Ngày-Tháng-Năm Giờ:Phút)
                    formatted_time = dt_object.strftime("%d-%m-%Y %H:%M")
                except (ValueError, TypeError):
                    formatted_time = "[red]Lỗi định dạng[/red]"

            table.add_row(str(i), formatted_time, video_id, description)

        console.print(table)

    except json.JSONDecodeError:
        console.print(f"❌ [bold red]Lỗi: File lịch sử '{history_path}' bị hỏng hoặc không phải là file JSON hợp lệ.[/bold red]")
    except Exception as e:
        console.print(f"❌ [bold red]Đã xảy ra lỗi không mong muốn: {e}[/bold red]")

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m Tiktok.manageHistory.view_history <account_name>")
        sys.exit(1)
    
    account_name = sys.argv[1]
    view_account_history(account_name)

if __name__ == "__main__":
    main()