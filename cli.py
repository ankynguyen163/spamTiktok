#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import shlex
import difflib
from pathlib import Path

# Thư viện để làm đẹp giao diện CLI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Import config để lấy đường dẫn accounts
from Tiktok.config import ACCOUNTS_DIR
from Tiktok.utils import get_all_videos, is_uploaded, get_upload_count

# Định nghĩa tập trung tất cả các lệnh
COMMANDS = [
    {
        "name": "login-fb",
        "description": "🔑 Đăng nhập vào Facebook (lấy cookie).",
        "handler_type": "python_module",
        "handler_info": ["stalkers.facebook.login"],
    },
    {
        "name": "login-tt",
        "description": "🔑 Đăng nhập vào TikTok cho một tài khoản.",
        "usage_suffix": "<account_name>",
        "handler_type": "python_module",
        "handler_info": ["Tiktok.login_tiktok"],
        "required_args": 1,
    },
    {
        "name": "stalk",
        "description": "🕵️  Bắt đầu cào video từ các nguồn được chỉ định.",
        "usage_suffix": "<fb|yt|all>",
        "handler_type": "python_module",
        "handler_info": ["stalkers.manager"],
        "required_args": 1,
    },
    {
        "name": "upload",
        "description": "📤 Upload video lên TikTok.",
        "usage_suffix": "<auto|manual> <account_name>",
        "handler_type": "python_module",
        "handler_info": ["Tiktok.spamUploadTiktok"],
        "required_args": 2,
    },
    {
        "name": "list",
        "description": "📋 Liệt kê các video chưa được upload cho một tài khoản.",
        "usage_suffix": "<account_name>",
        "handler_type": "python_module",
        "handler_info": ["Tiktok.spamUploadTiktok", "list"],
        "required_args": 1,
    },
    {
        "name": "clean-pending",
        "description": "🧹 Xóa các video đã tải về nhưng chưa được upload.",
        "handler_type": "python_module",
        "handler_info": ["Tiktok.cleanStorage.manager", "pending"],
    },
    {
        "name": "clean-uploaded",
        "description": "🧹 Xóa các file video gốc đã được upload thành công.",
        "handler_type": "python_module",
        "handler_info": ["Tiktok.cleanStorage.manager", "uploaded"],
    },
    {
        "name": "storage-report",
        "aliases": ["storage"],
        "description": "📊 In báo cáo chi tiết về tình trạng lưu trữ (storage).",
        "handler_type": "python_module",
        "handler_info": ["Tiktok.cleanStorage.utils", "report"],
    },
    {
        "name": "history",
        "description": "📜 Quản lý lịch sử upload (xem, xóa, di chuyển).",
        "usage_suffix": "<view|clear|migrate> [args...]",
        "handler_type": "python_module",
        "handler_info": ["Tiktok.manageHistory.manage_history"],
        "required_args": 1,
    },
    {
        "name": "list-accounts",
        "description": "👤 Liệt kê tất cả các tài khoản TikTok đã đăng nhập.",
        "handler_type": "custom",
        "handler_info": "list_accounts",
    },
    {
        "name": "status",
        "description": "📊 Hiển thị tóm tắt trạng thái của hệ thống.",
        "handler_type": "custom",
        "handler_info": "status",
    },
    {
        "name": "monitor",
        "description": "📊 Theo dõi tài nguyên các tiến trình stalker (real-time).",
        "handler_type": "shell_command",
        "handler_info": "watch -n 1 'ps -eo pcpu,pmem,cmd --sort=-pcpu | grep -E \"[s]talkers.manager (fb|yt|all)\" | head -20'",
    },
    {
        "name": "kill-stalkers",
        "description": "📛 Dừng tất cả các tiến trình cào video (stalker).",
        "handler_type": "shell_command",
        "handler_info": 'pkill -f "stalkers.manager (fb|yt|all)"',
    },
    {
        "name": "delete-videos",
        "description": "🗑️  Xóa video TikTok có lượt xem thấp.",
        "usage_suffix": "<account_name> [--threshold N] [--dry-run]",
        "handler_type": "python_module",
        "handler_info": ["Tiktok.deleteGarbage.delete_videos"],
        "required_args": 1,
    },
    {
        "name": "help",
        "aliases": ["?"],
        "description": "📖 Hiển thị hướng dẫn này.",
        "handler_type": "custom",
        "handler_info": "help",
    },
    {
        "name": "exit",
        "aliases": ["quit"],
        "description": "👋 Thoát khỏi chế độ tương tác.",
        "handler_type": "custom",
        "handler_info": "exit",
    },
]

# Tạo một map để tra cứu lệnh nhanh hơn, bao gồm cả aliases
COMMAND_MAP = {}
for cmd in COMMANDS:
    COMMAND_MAP[cmd["name"]] = cmd
    for alias in cmd.get("aliases", []):
        COMMAND_MAP[alias] = cmd

# Khởi tạo console của Rich để in màu và các thành phần UI khác
console = Console()

def run_python_module(module_parts):
    """
    Chạy một module Python bằng cách sử dụng trình thông dịch hiện tại.
    Điều này đảm bảo sử dụng đúng virtual environment.
    """
    try:
        python_executable = sys.executable
        command = [python_executable, "-m"] + module_parts
        console.print(f"[dim]🚀 Đang thực thi: {' '.join(command)}[/dim]")
        process = subprocess.Popen(command)
        process.wait()
    except KeyboardInterrupt:
        console.print(f"\n[yellow]🛑 Người dùng đã dừng tiến trình.[/yellow]")
        try:
            # Cố gắng chấm dứt tiến trình con một cách nhẹ nhàng
            process.terminate()
            process.wait(timeout=5)
        except (subprocess.TimeoutExpired, NameError, AttributeError):
            # Nếu không được, hoặc tiến trình chưa kịp tạo, bỏ qua
            pass
    except Exception as e:
        console.print(f"[bold red]❌ Đã xảy ra lỗi khi chạy lệnh: {e}[/bold red]")

def run_shell_command(command_str):
    """Chạy một lệnh shell phức tạp."""
    console.print(f"[dim]🚀 Đang thực thi: {command_str}[/dim]")
    try:
        # subprocess.run an toàn và linh hoạt hơn os.system
        subprocess.run(command_str, shell=True, check=True)
    except KeyboardInterrupt:
        console.print("\n[green]✅ Đã dừng giám sát.[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Lệnh shell thất bại với mã lỗi {e.returncode}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Đã xảy ra lỗi khi chạy lệnh: {e}[/bold red]")

def print_help():
    """In ra hướng dẫn sử dụng công cụ CLI."""
    console.print("\n[bold]Công cụ dòng lệnh để quản lý các tác vụ của SPAMTIKTOK[/bold]")
    console.print("Chạy `python cli.py` để vào chế độ tương tác, hoặc `python cli.py <lệnh> [tham số]` để chạy trực tiếp.\n")

    table = Table(title="Danh sách lệnh", show_header=True, header_style="bold magenta", show_lines=True, border_style="blue")
    table.add_column("Lệnh (Command)", style="cyan", no_wrap=True)
    table.add_column("Tham số (Parameters)", style="green")
    table.add_column("Mô tả (Description)", style="default")

    for cmd in COMMANDS:
        name_part = cmd["name"]
        if "aliases" in cmd:
            name_part += f" / {', '.join(cmd['aliases'])}"
        
        usage_suffix = cmd.get("usage_suffix", "")
        description = cmd["description"]

        table.add_row(name_part, usage_suffix, description)

    console.print(table)

    console.print("\n[bold]Ví dụ (chế độ tương tác):[/bold]")
    console.print("  [cyan]>> cli: [/cyan][yellow]stalk-fb[/yellow]")
    console.print("  [cyan]>> cli: [/cyan][yellow]upload auto my_account_1[/yellow]")

def execute_command(command, args):
    """Thực thi một lệnh dựa trên input."""
    cmd_def = COMMAND_MAP.get(command)

    if not cmd_def:
        console.print(f"[bold red]❌ Lệnh không hợp lệ: '{command}'[/bold red]")
        # --- Gợi ý lệnh thông minh ---
        suggestions = difflib.get_close_matches(command, COMMAND_MAP.keys())
        if suggestions:
            console.print(f"Có phải bạn muốn nói: [bold yellow]{suggestions[0]}[/bold yellow]?")
        return

    # Kiểm tra các tham số bắt buộc một cách tập trung
    required_args_count = cmd_def.get("required_args")
    if required_args_count is not None and len(args) < required_args_count:
        full_command_usage = f"{cmd_def['name']} {cmd_def.get('usage_suffix', '')}".strip()
        console.print(f"[bold red]❌ Lỗi: Lệnh '{cmd_def['name']}' yêu cầu {required_args_count} tham số nhưng chỉ nhận được {len(args)}.[/bold red]")
        console.print(f"   [dim]Cách dùng đúng: {full_command_usage}[/dim]")
        return

    handler_type = cmd_def["handler_type"]
    handler_info = cmd_def["handler_info"]

    if handler_type == "python_module":
        run_python_module(handler_info + args)
    elif handler_type == "shell_command":
        if 'pkill' in handler_info:
             console.print("[yellow]🛑 Đang gửi lệnh dừng tất cả tiến trình cào video...[/yellow]")
             run_shell_command(handler_info)
             console.print("[green]✅ Đã gửi lệnh dừng.[/green]")
        else:
            run_shell_command(handler_info)
    elif handler_type == "custom":
        if handler_info == "help":
            print_help()
        elif handler_info == "list_accounts":
            if not ACCOUNTS_DIR.exists() or not any(ACCOUNTS_DIR.iterdir()):
                console.print("[blue]ℹ️ Chưa có tài khoản TikTok nào được đăng nhập.[/blue]")
                console.print("➡️  Sử dụng lệnh: [cyan]login-tt <tên_tài_khoản_mới>[/cyan]")
            else:
                console.print("[bold]👤 Các tài khoản TikTok đã cấu hình:[/bold]")
                for account_dir in sorted(ACCOUNTS_DIR.iterdir()):
                    if account_dir.is_dir():
                        console.print(f"  - [green]{account_dir.name}[/green]")
        elif handler_info == "status":
            status_text = ""

            # 1. Số lượng tài khoản và chi tiết
            accounts_details = []
            num_accounts = 0
            if ACCOUNTS_DIR.exists():
                for account_dir in sorted(ACCOUNTS_DIR.iterdir()):
                    if account_dir.is_dir():
                        account_name = account_dir.name
                        upload_count = get_upload_count(account_name)
                        accounts_details.append(f"  - [green]{account_name}[/green] (đã upload: [bold yellow]{upload_count}[/bold yellow])")
                        num_accounts += 1
            status_text += f"👤 [bold]Tài khoản TikTok[/bold]: {num_accounts}\n"
            if accounts_details:
                status_text += "\n".join(accounts_details)
            
            status_text += "\n\n"

            # 2. Số video chờ upload
            pending_videos = 0
            all_video_paths = get_all_videos(silent=True)
            for video_path in all_video_paths:
                if not is_uploaded(video_path.stem):
                    pending_videos += 1
            status_text += f"📹 [bold]Video chờ upload[/bold]: [bold yellow]{pending_videos}[/bold yellow]\n\n"

            # 3. Trạng thái các tiến trình stalker
            def check_process(name):
                try:
                    subprocess.run(['pgrep', '-f', name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return "[bold green]🟢 Đang chạy[/bold green]"
                except subprocess.CalledProcessError:
                    return "[bold red]🔴 Đã dừng[/bold red]"
                except FileNotFoundError:
                    return "[dim]⚪ Không rõ (thiếu pgrep)[/dim]"
            
            status_text += f"🕵️  [bold]Facebook Stalker[/bold]: {check_process('stalkers.manager fb')}\n"
            status_text += f"📺 [bold]YouTube Stalker[/bold]:  {check_process('stalkers.manager yt')}"

            console.print(Panel(status_text, title="📊 Trạng Thái Hệ Thống", border_style="blue", expand=False))

        # Các lệnh 'exit', 'quit' được xử lý trong interactive_shell
    else:
        console.print(f"[bold red]Lỗi: Không có handler cho loại '{handler_type}'[/bold red]")

def interactive_shell():
    """Chạy chế độ dòng lệnh tương tác."""
    console.print("[bold green]Chào mừng đến với CLI của SPAMTIKTOK![/bold green]")
    console.print("Gõ [yellow]help[/yellow] hoặc [yellow]?[/yellow] để xem các lệnh. Gõ [yellow]exit[/yellow] hoặc [yellow]quit[/yellow] để thoát.")
    while True:
        try:
            line = console.input("\n[bold cyan]>> cli: [/bold cyan]")
            if not line.strip():
                continue
            
            # Dùng shlex để phân tích lệnh, hỗ trợ tham số trong ngoặc kép
            parts = shlex.split(line)
            command = parts[0].lower()
            args = parts[1:]

            if COMMAND_MAP.get(command, {}).get("handler_info") == "exit":
                console.print("[bold]👋 Tạm biệt![/bold]")
                break
            
            execute_command(command, args)

        except KeyboardInterrupt:
            # Bấm Ctrl+C ở dấu nhắc
            console.print("\n[yellow]Bấm Ctrl+D hoặc gõ 'exit' để thoát.[/yellow]")
            continue
        except EOFError:
            # Bấm Ctrl+D
            console.print("\n[bold]👋 Tạm biệt![/bold]")
            break

def main():
    """Hàm chính điều hướng các lệnh."""
    if len(sys.argv) == 1:
        # Không có tham số, chạy chế độ tương tác
        interactive_shell()
    else:
        # Có tham số, chạy chế độ một lần
        command = sys.argv[1]
        args = sys.argv[2:]
        if command in ['-h', '--help']:
            command = 'help'
        execute_command(command, args)

if __name__ == "__main__":
    main()