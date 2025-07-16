# 📊 Theo Dõi Tài Nguyên FB\_STALKER

Dùng các lệnh CLI dưới đây để giám sát tiến trình `fb_stalker` trên máy Linux (Ubuntu).

---

## 🔍 Kiểm Tra Tất Cả Tiến Trình fb\_stalker

Hiển thị danh sách tiến trình đang chạy, sorted theo %CPU tiêu thụ:


ps -eo pid,pcpu,pmem,etime,cmd | grep "[f]b_stalker" | sort -k2 -r


* **pid**: Process ID
* **pcpu**: % CPU tiêu thụ
* **pmem**: % RAM tiêu thụ
* **etime**: Thời gian đã chạy
* **cmd**: Câu lệnh thực thi

---

## 📉 Kiểm Tra Gọn Dạng Bảng CPU/RAM/Command


ps -eo pcpu,pmem,cmd | grep "[f]b_stalker" | sort -k1 -r


* Sorted theo mức CPU tiêu thụ (cao xuống thấp).

---

## ⏱️ Giám Sát Real-Time (Refresh 1 giây)


watch -n 1 'ps -eo pcpu,pmem,cmd | grep "[f]b_stalker" | sort -k1 -r | head -20'


* Mỗi 1 giây cập nhật danh sách top 20 tiến trình FB\_STALKER ngốn CPU/RAM nhất.

---

## 📛 Dừng Toàn Bộ Stalker

Nếu cần dừng toàn bộ tiến trình FB\_STALKER ngay lập tức:


pkill -f fb_stalker


---

## 📌 Ghi Nhớ

* Quản lý bằng `manager.py` sẽ dễ stop/start hơn.
* Theo dõi thường xuyên để tránh **quá tải RAM hoặc CPU** nếu số lượng stalkers cao (>20).
