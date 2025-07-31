#!/bin/bash

# ==============================================================================
# SPAMTIKTOK - Health Check & Test Runner
# ==============================================================================
#
# Script này chạy một loạt các bài kiểm tra không phá hủy để xác minh rằng
# môi trường dự án đã được thiết lập đúng và các thành phần cốt lõi hoạt động.
#
# Cách dùng: ./run_tests.sh
#
# ==============================================================================

# Dừng script ngay khi có lỗi
set -e

# --- Các hàm hỗ trợ in log ---
log_step() {
    echo -e "\n\e[1;34m[BƯỚC] $1\e[0m"
}

log_check() {
    # Dùng -n để không xuống dòng, chờ kết quả
    echo -n "  -> $1..."
}

log_ok() {
    echo -e "\e[32m OK\e[0m"
}

log_error() {
    echo -e "\e[31m LỖI\e[0m"
    echo "     Lý do: $1"
    exit 1
}

# --- Hàm thiết lập và dọn dẹp môi trường test ---
TEST_ACCOUNT_NAME="_test_account"

setup_test_env() {
    log_step "Thiết lập môi trường test"
    log_check "Tạo tài khoản test ảo '$TEST_ACCOUNT_NAME'"
    mkdir -p "Tiktok/accounts/$TEST_ACCOUNT_NAME"
    # Tạo một file cookie giả để mô phỏng tài khoản đã đăng nhập
    echo '{"comment": "dummy cookie file for testing"}' > "Tiktok/accounts/$TEST_ACCOUNT_NAME/cookies.json"
    log_ok
}

cleanup_test_env() {
    log_step "Dọn dẹp môi trường test"
    log_check "Xóa tài khoản test ảo '$TEST_ACCOUNT_NAME'"
    rm -rf "Tiktok/accounts/$TEST_ACCOUNT_NAME"
    log_ok
}
# --- Logic kiểm tra chính ---

# 1. Xác minh môi trường
log_step "Xác minh môi trường"

log_check "Kiểm tra virtual environment (venv)"
if [ ! -d "venv" ]; then
    log_error "Không tìm thấy thư mục 'venv'. Vui lòng chạy 'setup_laptop.sh' trước."
fi
log_ok

log_check "Kích hoạt virtual environment"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
log_ok

log_check "Kiểm tra package Python quan trọng (rich)"
if ! python -c "import rich" &> /dev/null; then
    log_error "Không tìm thấy package 'rich'. Chạy 'pip install -r requirements.txt' trong venv."
fi
log_ok

# 2. Xác minh cấu trúc thư mục
log_step "Xác minh cấu trúc thư mục"

declare -a required_dirs=("stalkers/facebook/videos" "stalkers/youtube/videos" "Tiktok/accounts")
for dir in "${required_dirs[@]}"; do
    log_check "Kiểm tra thư mục: $dir"
    if [ ! -d "$dir" ]; then
        log_error "Không tìm thấy thư mục '$dir'. Vui lòng chạy 'setup_laptop.sh'."
    fi
    log_ok
done

# Thiết lập môi trường test (sẽ được dọn dẹp khi script kết thúc)
trap cleanup_test_env EXIT
setup_test_env

# 3. Kiểm tra các lệnh CLI cốt lõi (chế độ chỉ đọc)
log_step "Kiểm tra các lệnh CLI cốt lõi"

log_check "Chạy 'cli.py help'"
python cli.py help > /dev/null || log_error "Lệnh 'cli.py help' thất bại."
log_ok

log_check "Chạy 'cli.py status'"
python cli.py status > /dev/null || log_error "Lệnh 'cli.py status' thất bại."
log_ok

log_check "Chạy 'cli.py storage'"
python cli.py storage > /dev/null || log_error "Lệnh 'cli.py storage' thất bại."
log_ok

log_check "Chạy 'cli.py list-accounts' (phải thấy tài khoản test)"
if ! python cli.py list-accounts | grep -q "$TEST_ACCOUNT_NAME"; then
    log_error "Lệnh 'list-accounts' không hiển thị tài khoản test."
fi
log_ok

log_check "Chạy 'cli.py list $TEST_ACCOUNT_NAME'"
python cli.py list "$TEST_ACCOUNT_NAME" > /dev/null || log_error "Lệnh 'list <account>' thất bại."
log_ok

log_check "Chạy 'cli.py delete-videos --dry-run $TEST_ACCOUNT_NAME'"
python cli.py delete-videos "$TEST_ACCOUNT_NAME" --dry-run > /dev/null || log_error "Lệnh 'delete-videos --dry-run' thất bại."
log_ok

log_check "Kiểm tra cú pháp module 'facebook.login'"
python -c "import stalkers.facebook.login" > /dev/null || log_error "Module 'stalkers.facebook.login' có lỗi cú pháp."
log_ok

echo -e "\n\e[1;32m🎉 TẤT CẢ KIỂM TRA ĐÃ THÀNH CÔNG! Môi trường của bạn đã sẵn sàng.\e[0m"