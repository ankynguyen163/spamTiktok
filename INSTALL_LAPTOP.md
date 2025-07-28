# 💻 Hướng dẫn cài đặt SPAMTIKTOK trên Laptop

## 🚀 Cách 1: Clone từ Git (Khuyến nghị)

```bash
# Clone project
git clone https://github.com/ankynguyen163/spamTiktok.git
cd spamTiktok

# Chuyển sang nhánh alpha (nếu cần)
git checkout alpha

# Chạy script setup tự động
./setup_laptop.sh
```

## 📦 Cách 2: Download Archive

1. **Download file `spamTiktok_project.tar.gz`** từ server/cloud
2. **Extract project:**
   ```bash
   tar -xzf spamTiktok_project.tar.gz
   cd spamTiktok
   ```
3. **Chạy setup:**
   ```bash
   chmod +x setup_laptop.sh
   ./setup_laptop.sh
   ```

## 🛠️ Yêu cầu hệ thống

### Bắt buộc:
- **Python 3.8+** 
- **Google Chrome** (mới nhất)
- **Git** (nếu clone từ repository)

### Cài đặt dependencies:

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv google-chrome-stable git
```

#### macOS:
```bash
# Cài Homebrew nếu chưa có
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Cài dependencies
brew install python git
# Download Chrome từ: https://www.google.com/chrome/
```

#### Windows:
- Download Python từ: https://python.org
- Download Chrome từ: https://www.google.com/chrome/
- Download Git từ: https://git-scm.com/

## ⚙️ Setup thủ công (nếu script tự động lỗi)

1. **Tạo virtual environment:**
   ```bash
   python3 -m venv venv
   
   # Linux/macOS
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

2. **Cài đặt packages:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Tạo thư mục:**
   ```bash
   mkdir -p stalkers/facebook/videos
   mkdir -p stalkers/youtube/videos
   mkdir -p Tiktok/accounts
   ```

## 🎯 Kiểm tra cài đặt

```bash
# Kích hoạt venv
source venv/bin/activate  # Linux/macOS
# hoặc: venv\Scripts\activate  # Windows

# Test CLI
python cli.py status

# Test import
python -c "from Tiktok.cleanStorage.manager import main; print('✅ OK')"
```

## 🔧 Cấu hình ban đầu

### 1. Cấu hình Stalkers

**Facebook** - Sửa file `stalkers/facebook/pages.txt`:
```
https://www.facebook.com/page1
https://www.facebook.com/page2
```

**YouTube** - Sửa file `stalkers/youtube/channels.txt`:
```
https://www.youtube.com/@channel1
https://www.youtube.com/@channel2
```

### 2. Đăng nhập lần đầu

```bash
python cli.py
>> cli: login-fb              # Đăng nhập Facebook
>> cli: login-tt my_account   # Tạo tài khoản TikTok đầu tiên
```

## 🚦 Chạy thử nghiệm

```bash
# Kích hoạt venv
source venv/bin/activate

# Chạy CLI
python cli.py

# Kiểm tra status
>> cli: status

# Test cào video (chạy 1 lần)
>> cli: stalk fb
# Ctrl+C để dừng sau vài phút

# Xem video đã tải
>> cli: list my_account
```

## 📂 Cấu trúc project sau khi cài đặt

```
spamTiktok/
├── venv/                    # Virtual environment
├── stalkers/
│   ├── facebook/
│   │   ├── videos/         # Video FB tải về
│   │   └── pages.txt       # Danh sách fanpage
│   └── youtube/
│       ├── videos/         # Video YT tải về  
│       └── channels.txt    # Danh sách kênh
├── Tiktok/
│   ├── accounts/           # Profile các tài khoản TT
│   └── cleanStorage/       # Module dọn dẹp mới
├── cli.py                  # Giao diện chính
├── requirements.txt        # Dependencies
└── setup_laptop.sh         # Script setup
```

## 🚨 Troubleshooting

### Lỗi Python
```bash
# Kiểm tra Python version
python3 --version

# Nếu < 3.8, cần upgrade
```

### Lỗi Chrome
```bash
# Ubuntu: Cài Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install google-chrome-stable
```

### Lỗi Playwright
```bash
# Cài lại Playwright browsers
playwright install chromium --force
```

### Lỗi Permission (Linux/macOS)
```bash
# Cho phép thực thi script
chmod +x setup_laptop.sh

# Fix quyền thư mục
chmod -R 755 stalkers/ Tiktok/
```

## 🔄 Cập nhật project

### Từ Git:
```bash
git pull origin alpha
pip install -r requirements.txt  # Cập nhật dependencies nếu có
```

### Từ Archive:
1. Backup thư mục `Tiktok/accounts/` (chứa profile tài khoản)
2. Extract archive mới
3. Copy lại thư mục `Tiktok/accounts/`
4. Chạy lại `./setup_laptop.sh`

## 💡 Tips

- **Backup thường xuyên** thư mục `Tiktok/accounts/`
- **Dùng virtual environment** để tránh conflict
- **Đọc log** khi có lỗi để debug
- **Tuân thủ ToS** của các nền tảng

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra log trong terminal
2. Đảm bảo đã cài đặt đủ dependencies  
3. Kiểm tra kết nối internet
4. Đọc README.md và CLI.md