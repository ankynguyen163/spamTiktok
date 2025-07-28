# 📦 Hướng dẫn Download Project về Laptop

## 🎯 TÓM TẮT NHANH

Bạn có **3 cách** để copy project về laptop:

---

## 🚀 **CÁCH 1: Git Clone (Khuyến nghị)**

```bash
git clone https://github.com/ankynguyen163/spamTiktok.git
cd spamTiktok
git checkout alpha
./setup_laptop.sh
```

**Ưu điểm:** Dễ cập nhật sau này với `git pull`

---

## 📦 **CÁCH 2: Download Archive**

1. **Download file:** `spamTiktok_project.tar.gz` (50KB)
2. **Extract:** 
   ```bash
   tar -xzf spamTiktok_project.tar.gz
   cd spamTiktok
   ```
3. **Setup:**
   ```bash
   chmod +x setup_laptop.sh
   ./setup_laptop.sh
   ```

---

## 💾 **CÁCH 3: Copy Manual Files**

Nếu 2 cách trên không được, copy thủ công các file:

### Files cần thiết:
```
📁 Cấu trúc tối thiểu:
├── cli.py
├── requirements.txt
├── setup_laptop.sh
├── INSTALL_LAPTOP.md
├── README.md
├── CLI.md
├── stalkers/
└── Tiktok/
```

### Sau khi copy:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p stalkers/facebook/videos stalkers/youtube/videos Tiktok/accounts
```

---

## ✅ **Kiểm tra sau khi cài đặt:**

```bash
source venv/bin/activate
python cli.py status
```

Nếu thấy CLI hiện ra mà không lỗi = **Thành công!** 🎉

---

## 🚨 **Nếu gặp lỗi:**

1. **Lỗi Python:** Cài Python 3.8+ từ python.org
2. **Lỗi Chrome:** Cài Google Chrome
3. **Lỗi pip:** `pip install --upgrade pip`
4. **Lỗi permission:** `chmod +x setup_laptop.sh`

---

## 📞 **Files download có sẵn:**

- ✅ `spamTiktok_project.tar.gz` - Archive đầy đủ (50KB)
- ✅ `setup_laptop.sh` - Script setup tự động  
- ✅ `INSTALL_LAPTOP.md` - Hướng dẫn chi tiết

**Chọn cách nào cũng được, nhưng khuyến nghị dùng Git để dễ cập nhật!**