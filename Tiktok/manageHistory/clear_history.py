#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Thêm thư mục gốc của dự án vào sys.path để có thể import từ các module khác
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from rich.console import Console
from Tiktok.config import ACCOUNTS_DIR
from Tiktok.utils import get_history_path

console = Console()

def clear_account_history(account_name: str, force: bool = False, before_days: int = None):
    """
    Xóa lịch sử upload của một tài khoản.
    - Mặc định: Xóa toàn bộ lịch sử.
    - Nếu before_days được cung cấp: Chỉ xóa các mục cũ hơn N ngày.
    - force=True: Bỏ qua mọi bước xác nhận.
    """
    # Kiểm tra tài khoản có tồn tại không
    account_dir = ACCOUNTS_DIR / account_name
    if not account_dir.is_dir():
        console.print(f"❌ [bold red]Lỗi: Không tìm thấy tài khoản '{account_name}'.[/bold red]")
        console.print("➡️  Sử dụng lệnh [cyan]list-accounts[/cyan] để xem các tài khoản có sẵn.")
        return

    history_path = get_history_path(account_name)

    if not history_path.exists():
        console.print(f"✅ [blue]Lịch sử của tài khoản '{account_name}' đã trống (không tìm thấy file history.json).[/blue]")
        return

    # --- Chế độ: Dọn dẹp các mục cũ ---
    if before_days is not None:
        try:
            with open(history_path, 'r+', encoding='utf-8') as f:
                try:
                    history_data = json.load(f)
                except json.JSONDecodeError:
                    console.print(f"❌ [bold red]Lỗi: File lịch sử '{history_path.name}' của tài khoản '{account_name}' bị hỏng.[/bold red]")
                    return

                if not history_data:
                    console.print(f"✅ [blue]Lịch sử của tài khoản '{account_name}' đã trống.[/blue]")
                    return

                cutoff_date = datetime.now() - timedelta(days=before_days)
                kept_entries = []
                deleted_count = 0

                for entry in history_data:
                    upload_time_str = entry.get('upload_time')
                    if not upload_time_str:
                        kept_entries.append(entry) # Giữ lại các mục không có thời gian cho an toàn
                        continue
                    
                    try:
                        # Bỏ timezone info (nếu có) để so sánh an toàn
                        upload_time = datetime.fromisoformat(upload_time_str).replace(tzinfo=None)
                        if upload_time >= cutoff_date:
                            kept_entries.append(entry)
                        else:
                            deleted_count += 1
                    except ValueError:
                        kept_entries.append(entry) # Giữ lại nếu định dạng thời gian lỗi

                if deleted_count == 0:
                    console.print(f"✅ Không có mục lịch sử nào cũ hơn {before_days} ngày để xóa cho tài khoản '{account_name}'.")
                    return

                if not force:
                    console.print(f"⚠️  [yellow]CẢNH BÁO: Bạn sắp xóa vĩnh viễn {deleted_count} mục lịch sử cũ hơn {before_days} ngày của tài khoản '{account_name}'.[/yellow]")
                    confirm_input = console.input("➡️  Nhập 'yes' để xác nhận: ").strip().lower()
                    if confirm_input != 'yes':
                        console.print("🚫 Thao tác đã bị hủy.")
                        return
                
                f.seek(0)
                json.dump(kept_entries, f, indent=4)
                f.truncate()
                console.print(f"✅ Đã xóa thành công {deleted_count} mục lịch sử cũ của tài khoản '{account_name}'.")

        except Exception as e:
            console.print(f"❌ [bold red]Lỗi khi dọn dẹp lịch sử: {e}[/bold red]")
        return

    # --- Chế độ: Xóa toàn bộ lịch sử (mặc định) ---
    confirmed = False
    if force:
        console.print(f"⚠️  [yellow]CẢNH BÁO: Xóa toàn bộ lịch sử cho tài khoản '{account_name}' với tùy chọn --yes.[/yellow]")
        confirmed = True
    else:
        console.print(f"⚠️  [bold red]CẢNH BÁO: Bạn sắp xóa TOÀN BỘ lịch sử upload của tài khoản '{account_name}'.[/bold red]")
        console.print("   Hành động này không thể hoàn tác. Tất cả video sẽ được coi là 'chưa upload' đối với tài khoản này.")
        confirm_input = console.input(f"➡️  Nhập tên tài khoản '[cyan]{account_name}[/cyan]' để xác nhận: ").strip()

        if confirm_input == account_name:
            confirmed = True
        else:
            console.print("🚫 Tên tài khoản không khớp. Thao tác đã bị hủy.")
            return

    if confirmed:
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump([], f) # Ghi một mảng rỗng vào file
            console.print(f"✅ Đã xóa thành công toàn bộ lịch sử cho tài khoản '{account_name}'.")
        except Exception as e:
            console.print(f"❌ [bold red]Lỗi khi xóa lịch sử: {e}[/bold red]")

def main():
    # This main is for direct script execution, which is less common now.
    # The main logic is in manage_history.py
    console.print("[yellow]Vui lòng sử dụng 'cli.py' để chạy lệnh này.[/yellow]")
    console.print("Ví dụ: [cyan]python cli.py history clear my_account --before 30[/cyan]")

if __name__ == "__main__":
    main()