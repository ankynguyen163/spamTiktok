import os
import time
import subprocess
import sys
import json
import sqlite3
from pathlib import Path

from Tiktok.config import get_profile_dir, get_cookies_path


def extract_chrome_cookies(profile_dir, output_path, target_domains=None):
    """
    Trích xuất cookies từ profile Chrome.

    :param profile_dir: thư mục profile Chrome (user-data-dir)
    :param output_path: đường dẫn file JSON để lưu cookies
    :param target_domains: list các domain (hoặc None để lấy tất cả)
    """
    cookie_db = Path(profile_dir) / "Default" / "Cookies"
    if not cookie_db.exists():
        print("⚠️ Chưa phát hiện file Cookies.")
        print(f"➡️ Bước 1: Mở Chrome và đăng nhập TikTok thủ công:")
        print(f"   google-chrome --user-data-dir={profile_dir} https://tiktok.com")
        print("➡️ Bước 2: Sau khi đăng nhập xong, chạy lại script này để lưu cookies.")
        sys.exit(0)

    cookies = []
    conn = sqlite3.connect(cookie_db)
    cursor = conn.cursor()

    cursor.execute("SELECT host_key, name, value, encrypted_value, path, expires_utc, is_secure FROM cookies")

    for row in cursor.fetchall():
        domain = row[0]
        name = row[1]
        value = row[2]
        encrypted_value = row[3]
        path_c = row[4]
        expires = row[5]
        is_secure = bool(row[6])

        if target_domains and not any(domain.endswith(d) for d in target_domains):
            continue

        if not value and encrypted_value:
            try:
                value = encrypted_value.decode("utf-8")
            except Exception:
                value = encrypted_value.hex()

        cookies.append({
            "domain": domain,
            "name": name,
            "value": value,
            "path": path_c,
            "expires": expires,
            "secure": is_secure
        })

    conn.close()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(cookies, f, indent=2)

    print(f"\U0001F4BE Đã lưu {len(cookies)} cookies vào {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Usage: python -m Tiktok.login_tiktok <account_name>")
        print("   Ví dụ: python -m Tiktok.login_tiktok my_tiktok_account_1")
        sys.exit(1)

    account_name = sys.argv[1]
    print(f"🔑 Bắt đầu quá trình đăng nhập cho tài khoản: {account_name}")

    profile_path = get_profile_dir(account_name)
    profile_path.mkdir(parents=True, exist_ok=True)

    cookie_db = profile_path / "Default" / "Cookies"

    if not cookie_db.exists():
        print(f"⚠️ Chưa phát hiện file Cookies cho '{account_name}'.")
        print("➡️ Sẽ tự động mở Chrome, hãy đăng nhập TikTok trong cửa sổ đó.")
        print("➡️ Sau khi bạn đóng Chrome, cookies sẽ được tự động lưu.")

        # Mở Chrome thật bằng subprocess
        chrome_cmd = [
            "google-chrome",
            f"--user-data-dir={profile_path.resolve()}",
            "https://tiktok.com"
        ]

        chrome_proc = subprocess.Popen(chrome_cmd)
        chrome_proc.wait()  # Chờ mày login và tự đóng Chrome

        # Đợi Chrome flush cookies
        time.sleep(2)

        if not cookie_db.exists():
            print("❌ Đăng nhập thất bại: không tìm thấy file Cookies.")
            sys.exit(1)

    # Nếu cookies đã có, tiến hành trích xuất
    extract_chrome_cookies(
        profile_dir=profile_path,
        output_path=get_cookies_path(account_name),
        target_domains=["tiktok.com"]
    )