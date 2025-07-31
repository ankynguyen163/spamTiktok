#!/bin/bash

# Setup Script cho SPAMTIKTOK trên Laptop
# Chạy script này sau khi extract project về laptop

echo "🚀 === SETUP SPAMTIKTOK TRÊN LAPTOP ==="
echo ""

# Kiểm tra Python
echo "🔍 Kiểm tra Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 không được tìm thấy. Vui lòng cài đặt Python 3.8+ trước."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION đã được tìm thấy."

# Kiểm tra Google Chrome
echo ""
echo "🔍 Kiểm tra Google Chrome..."
if command -v google-chrome &> /dev/null; then
    echo "✅ Google Chrome đã được cài đặt."
elif command -v google-chrome-stable &> /dev/null; then
    echo "✅ Google Chrome Stable đã được cài đặt."
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if [[ -d "/Applications/Google Chrome.app" ]]; then
        echo "✅ Google Chrome đã được cài đặt (macOS)."
    else
        echo "⚠️ Google Chrome chưa được cài đặt trên macOS."
        echo "   Vui lòng tải từ: https://www.google.com/chrome/"
    fi
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "⚠️ Đang chạy trên Windows. Đảm bảo Chrome đã được cài đặt."
else
    echo "⚠️ Google Chrome chưa được tìm thấy."
    echo "   Ubuntu/Debian: sudo apt install google-chrome-stable"
    echo "   CentOS/RHEL: sudo yum install google-chrome-stable"
fi

# Tạo virtual environment
echo ""
echo "📦 Tạo Python virtual environment..."
if [[ -d "venv" ]]; then
    echo "📁 Virtual environment đã tồn tại."
else
    python3 -m venv venv
    echo "✅ Đã tạo virtual environment."
fi

# Kích hoạt venv và cài packages
echo ""
echo "📥 Cài đặt dependencies..."

# Detect OS để kích hoạt venv đúng cách
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/macOS
    source venv/bin/activate
fi

# Upgrade pip
pip install --upgrade pip

# Cài đặt requirements
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    echo "✅ Đã cài đặt tất cả dependencies."
else
    echo "❌ File requirements.txt không tìm thấy!"
    exit 1
fi

# Cài đặt playwright browsers
echo ""
echo "🎭 Cài đặt Playwright browsers..."
playwright install chromium
echo "✅ Đã cài đặt Playwright browsers."

# Tạo các thư mục cần thiết
echo ""
echo "📁 Tạo cấu trúc thư mục..."
mkdir -p stalkers/facebook/videos
mkdir -p stalkers/youtube/videos
mkdir -p Tiktok/accounts
echo "✅ Đã tạo các thư mục cần thiết."

# Kiểm tra cấu hình
echo ""
echo "🔧 Kiểm tra cấu hình..."

# Kiểm tra file cấu hình stalkers
if [[ -f "stalkers/facebook/pages.txt" ]]; then
    echo "✅ Facebook pages.txt đã có sẵn."
else
    echo "⚠️ File stalkers/facebook/pages.txt chưa có."
    echo "   Tạo file này và thêm URL các fanpage Facebook cần theo dõi."
fi

if [[ -f "stalkers/youtube/channels.txt" ]]; then
    echo "✅ YouTube channels.txt đã có sẵn."
else
    echo "⚠️ File stalkers/youtube/channels.txt chưa có."
    echo "   Tạo file này và thêm URL các kênh YouTube cần theo dõi."
fi

echo ""
echo "🎉 === SETUP HOÀN THÀNH ==="
echo ""
echo "🚀 Để bắt đầu sử dụng:"
echo "   1. Kích hoạt virtual environment:"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "      source venv/Scripts/activate"
else
    echo "      source venv/bin/activate"
fi
echo "   2. Chạy CLI:"
echo "      python cli.py"
echo ""
echo "📖 Đọc README.md và CLI.md để biết cách sử dụng chi tiết."
echo ""
echo "⚠️ LƯU Ý:"
echo "   - Đảm bảo có kết nối internet khi chạy stalkers"
echo "   - Cần đăng nhập FB/TikTok trước khi sử dụng"
echo "   - Tuân thủ ToS của các nền tảng"