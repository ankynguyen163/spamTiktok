# 📹 FB\_STALKER

Một bot Python theo dõi fanpage Facebook, tự động tải video và reel mới nhất.

---

## 🚀 Cách Sử Dụng

### 1️⃣ Cài Đặt Thư Viện

```bash
pip install -r requirements.txt
```

---

### 2️⃣ Đăng Nhập Facebook (Lần Đầu)

```bash
python fb_stalker.login_facebook
```

* Mở trình duyệt → **Đăng nhập Facebook thủ công**
* Sau khi vào **newfeed / avatar / trang chủ**, đợi vài giây rồi tắt trình duyệt
* Dữ liệu đăng nhập sẽ được lưu lại tại:

  * `cookies/facebook_cookies.json`
  * `cookies/facebook_profile/`
  * `netscape/facebook_cookies_netscape.txt`

---

### 3️⃣ Thêm Danh Sách Fanpage

* Mở file `pages.txt`
* Mỗi dòng 1 link fanpage, ví dụ:

```
https://www.facebook.com/Amwaydepkhoe/
```

---

### 4️⃣ Khởi Chạy Bot Theo Dõi

```bash
python fb_stalker.manager
```

* Mỗi fanpage sẽ được quản lý bởi 1 tiến trình `stalker.py`
* Mỗi stalker:

  * Dò 3 bài post mới nhất
  * Nếu phát hiện **video** hoặc **reel** mới → tự tải về
  * Sau khi quét xong **1 lần duy nhất**, stalker sẽ tự thoát
* `manager.py` chia thành từng batch nhỏ (5 hoặc 10 fanpage mỗi đợt) để tránh quá tải CPU/RAM
* Sau khi batch hiện tại chạy xong, batch tiếp theo mới bắt đầu

---

## 📂 Cấu Trúc Thư Mục

```
fb_stalker/
├── fb_vid.py              # Tải video thường
├── fb_reel.py             # Tải reel
├── stalker.py             # Theo dõi 1 fanpage (chỉ quét 1 lần)
├── manager.py             # Điều phối nhiều fanpage (chia batch tuần tự)
├── login_facebook.py      # Đăng nhập & lưu cookies
├── pages.txt              # Danh sách fanpage
├── history/
│   └── video_history.json # Tránh tải trùng video
├── videos/                # Nơi lưu video tải về
├── cookies/
│   ├── facebook_cookies.json
│   ├── facebook_profile/
├── netscape/
│   └── facebook_cookies_netscape.txt
├── config.py              # Cấu hình chung
└── requirements.txt
```

---

## 📌 Ghi Nhớ

* `video_history.json` lưu video đã tải để không trùng
* `stalker.py` chỉ chạy **1 lần**, quét xong sẽ tự thoát
* `manager.py` chia batch, điều phối stalker tuần tự từng đợt để tránh quá tải

---

Gâu.
