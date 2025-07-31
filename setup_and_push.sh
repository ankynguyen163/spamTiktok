#!/bin/bash

# Script để tự động hóa việc thiết lập Git và đẩy code lên nhánh 'alpha'
# Dừng script ngay khi có lỗi
set -e

# --- Cấu hình ---
# Ưu tiên dùng SSH để tránh các vấn đề xác thực với HTTPS/token.
REPO_URL="git@github.com:ankynguyen163/spamTiktok.git"
BRANCH_NAME="alpha"
DEFAULT_COMMIT_MSG="feat: Cập nhật và đồng bộ mã nguồn lên nhánh alpha"

# Lấy commit message từ tham số đầu tiên, nếu không có thì dùng message mặc định
COMMIT_MSG="${1:-$DEFAULT_COMMIT_MSG}"

# --- 0. Đảm bảo đây là một kho Git ---
if [ ! -d .git ]; then
    echo "ℹ️  Đây không phải là một kho Git. Đang khởi tạo..."
    git init
fi

# --- 1. Thiết lập .gitignore ---
echo "--> Đang kiểm tra và cập nhật .gitignore..."
GITIGNORE_FILE=".gitignore"

# Các mục cần loại trừ
declare -a ignores=(
    "venv/"
    "__pycache__/"
    "*.pyc"
    "accounts/"
    "stalkers/facebook/videos/"
    "stalkers/youtube/videos/"
    "stalkers/facebook/profile/"
    "stalkers/facebook/history.json"
    "stalkers/facebook/facebook_cookies_netscape.txt"
    "stalkers/youtube/history.json"
    "*.log"
    "*.png"
    "*.jpeg"
    "*.jpg"
)

for item in "${ignores[@]}"; do
    # Kiểm tra xem mục đã tồn tại trong file chưa, nếu chưa thì thêm vào
    grep -qxF "$item" "$GITIGNORE_FILE" || echo "$item" >> "$GITIGNORE_FILE"
done
echo "✅ .gitignore đã được cấu hình."

# --- 2. Thiết lập remote repository ---
echo -e "\n--> Đang kiểm tra remote 'origin'..."
if ! git remote -v | grep -q "^origin"; then
    echo "Remote 'origin' chưa tồn tại. Đang thêm remote..."
    git remote add origin "$REPO_URL"
elif ! git remote -v | grep -q "git@github.com"; then
    echo "⚠️  Remote 'origin' đang dùng HTTPS. Đang cập nhật sang SSH để xác thực tốt hơn..."
    git remote set-url origin "$REPO_URL"
else
    echo "Remote 'origin' đã được cấu hình."
fi
git remote -v

# --- 3. Tạo và chuyển sang nhánh 'alpha' ---
echo -e "\n--> Đang xử lý nhánh '$BRANCH_NAME'..."
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "Nhánh '$BRANCH_NAME' đã tồn tại. Chuyển sang nhánh này."
    git switch "$BRANCH_NAME"
else
    echo "Tạo và chuyển sang nhánh mới '$BRANCH_NAME'."
    git switch -c "$BRANCH_NAME"
fi
echo "✅ Đang ở trên nhánh: $(git rev-parse --abbrev-ref HEAD)"

# --- 4. Add, commit, và push ---
echo -e "\n--> Đang thêm các thay đổi vào staging area..."
git add .

echo -e "\n--> Đang commit các thay đổi..."
git commit -m "$COMMIT_MSG" || echo "✅ Không có thay đổi nào để commit."

echo -e "\n--> Đang đẩy code lên nhánh '$BRANCH_NAME'..."
git push -u origin "$BRANCH_NAME" --force

echo -e "\n🎉 Hoàn tất! Mã nguồn của bạn đã được đẩy lên nhánh '$BRANCH_NAME'."
echo "🔗 Xem tại: https://github.com/ankynguyen163/spamTiktok/tree/${BRANCH_NAME}"