#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

# Thêm thư mục gốc của dự án vào sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from rich.console import Console

# Import các hàm xử lý cụ thể từ các module khác
from Tiktok.manageHistory.view_history import view_account_history
from Tiktok.manageHistory.clear_history import clear_account_history
from Tiktok.manageHistory.migrate_history import migrate

console = Console()

def print_usage():
    """In ra hướng dẫn sử dụng cho lệnh history."""
    console.print("[bold]Quản lý lịch sử upload video[/bold]")
    console.print("Cách dùng: [cyan]history <lệnh_phụ> [tham_số][/cyan]")
    console.print("\n[bold]Các lệnh phụ có sẵn:[/bold]")
    console.print("  - [yellow]view <account_name> [--limit N][/yellow]   : Xem lịch sử của một tài khoản (giới hạn N mục gần nhất).")
    console.print("  - [yellow]clear <account_name> [--before N] [--yes][/yellow]  : Xóa lịch sử. Mặc định xóa toàn bộ. `--before N` chỉ xóa mục cũ hơn N ngày.")
    console.print("  - [yellow]migrate[/yellow]              : Di chuyển lịch sử từ cấu trúc file cũ.")

def main():
    """Hàm chính để điều hướng các lệnh phụ liên quan đến history."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    subcommand = sys.argv[1]
    args = sys.argv[2:]

    if subcommand == "view":
        account_name = None
        limit = None

        # Phân tích đối số đơn giản cho 'view'
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == '--limit':
                if i + 1 < len(args) and args[i+1].isdigit():
                    limit = int(args[i+1])
                    i += 2  # Bỏ qua --limit và giá trị của nó
                else:
                    console.print("[bold red]Lỗi: Tùy chọn '--limit' yêu cầu một số nguyên.[/bold red]")
                    print_usage()
                    return
            elif account_name is None:
                account_name = arg
                i += 1
            else:
                i += 1 # Bỏ qua các đối số không mong muốn khác

        if not account_name:
            console.print("[bold red]Lỗi: Lệnh 'view' yêu cầu ít nhất tên tài khoản.[/bold red]")
            print_usage()
        else:
            view_account_history(account_name, limit=limit)
    elif subcommand == "clear":
        args_list = list(args)
        before_days = None

        # Phân tích đối số --before
        try:
            before_index = args_list.index('--before')
            # Đảm bảo có giá trị đi kèm và giá trị đó là số
            if before_index + 1 < len(args_list) and args_list[before_index + 1].isdigit():
                before_days = int(args_list[before_index + 1])
                # Xóa flag và giá trị của nó khỏi danh sách để xử lý phần còn lại
                args_list.pop(before_index)
                args_list.pop(before_index)
            else:
                console.print("[bold red]Lỗi: Tùy chọn '--before' yêu cầu một số nguyên (số ngày).[/bold red]")
                print_usage()
                return
        except ValueError:
            # Không tìm thấy '--before', tiếp tục bình thường
            pass

        # Xử lý các đối số còn lại
        flags = {arg for arg in args_list if arg.startswith('-')}
        positional_args = [arg for arg in args_list if not arg.startswith('-')]

        if not positional_args:
            console.print("[bold red]Lỗi: Lệnh 'clear' yêu cầu tên tài khoản.[/bold red]")
            print_usage()
            return

        account_name = positional_args[0]
        # Chấp nhận nhiều kiểu flag để tiện lợi
        force_clear = '--yes' in flags or '-y' in flags or '--force' in flags

        clear_account_history(account_name, force=force_clear, before_days=before_days)

    elif subcommand == "migrate":
        migrate()
    else:
        console.print(f"[bold red]Lỗi: Lệnh phụ không xác định '{subcommand}'.[/bold red]")
        print_usage()

if __name__ == "__main__":
    main()