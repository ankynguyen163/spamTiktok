# /home/k/PROJECT/spamTiktok/stalkers/manager.py

# -*- coding: utf-8 -*-

import logging
import sys
import threading
from .logger_setup import setup_stalker_logger
# Import các strategy từ vị trí module mới
from .facebook.strategy import FacebookStrategy
from .youtube.strategy import YouTubeStrategy

# --- Constants ---
STRATEGY_MAP = {
    'fb': FacebookStrategy,
    'yt': YouTubeStrategy,
}

def run_stalker(strategy_class):
    """Hàm chính để chạy một chiến lược cụ thể, có thể trong một vòng lặp vô tận."""
    try:
        strategy_instance = strategy_class()
        # Bước 1: Kiểm tra điều kiện (ví dụ: đã đăng nhập chưa?)
        if strategy_instance.login():
            # Bước 2: Nếu ổn, giao toàn bộ quyền kiểm soát cho phương thức execute
            strategy_instance.execute()
        else:
            logging.warning(f"Điều kiện để chạy Stalker {strategy_class.__name__} chưa được đáp ứng. Stalker sẽ không khởi động.")
    except Exception as e:
        logging.error(f"Lỗi nghiêm trọng trong Stalker {strategy_class.__name__}: {e}", exc_info=True)

def main():
    # Khởi tạo logger ngay khi chương trình bắt đầu
    setup_stalker_logger()

    if len(sys.argv) < 2:
        logging.error("Cần chỉ định stalker để chạy (ví dụ: fb, yt, all).")
        logging.info(f"Cách dùng: python -m {__package__} <{'|'.join(STRATEGY_MAP.keys())}|all>")
        sys.exit(1)

    target_stalker = sys.argv[1].lower()
    threads = []

    if target_stalker == 'all':
        logging.info("Bắt đầu tất cả các Stalker...")
        for key, strategy_class in STRATEGY_MAP.items():
            logging.info(f"   -> Khởi chạy Stalker cho: {key}")
            thread = threading.Thread(target=run_stalker, args=(strategy_class,), daemon=True)
            threads.append(thread)
            thread.start()
    elif target_stalker in STRATEGY_MAP:
        strategy_class = STRATEGY_MAP[target_stalker]
        logging.info(f"Bắt đầu Stalker cho: {target_stalker}")
        run_stalker(strategy_class)
    else:
        logging.error(f"Không tìm thấy Stalker nào có tên '{target_stalker}'.")
        logging.info(f"Các lựa chọn có sẵn: {', '.join(list(STRATEGY_MAP.keys()) + ['all'])}")
        sys.exit(1)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Đảm bảo logger đã được thiết lập để ghi lại thông báo cuối cùng
        setup_stalker_logger()
        logging.info("Nhận được tín hiệu dừng. Đang thoát...")
        sys.exit(0)
