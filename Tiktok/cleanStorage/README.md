# Clean Storage Module

Module quản lý dọn dẹp file video cho hệ thống SPAMTIKTOK.

## 🎯 Chức năng

### 1. Clean Pending (`clean-pending`)
Xóa các video đã được tải về nhưng **chưa được upload** lên bất kỳ tài khoản TikTok nào.

**Tiêu chí**: Video được coi là "pending" nếu `video_id` của nó không xuất hiện trong `history.json` của bất kỳ tài khoản nào.

### 2. Clean Uploaded (`clean-uploaded`)  
Xóa các file video gốc đã được **upload thành công** lên TikTok (có trong lịch sử).

**Tiêu chí**: Video được coi là "uploaded" nếu `video_id` của nó xuất hiện trong `history.json` của ít nhất một tài khoản.

## 🚀 Cách sử dụng

### Thông qua CLI chính

```bash
# Chế độ tương tác
python cli.py
>> cli: clean-pending        # Xóa video chưa upload
>> cli: clean-uploaded       # Xóa video đã upload

# Chế độ một lần
python cli.py clean-pending
python cli.py clean-uploaded
```

### Chạy trực tiếp module

```bash
# Clean pending videos
python -m Tiktok.cleanStorage.manager pending

# Clean uploaded videos  
python -m Tiktok.cleanStorage.manager uploaded

# Dry run (chỉ xem danh sách, không xóa)
python -m Tiktok.cleanStorage.manager pending --dry-run
python -m Tiktok.cleanStorage.manager uploaded --dry-run
```

### Báo cáo storage

```bash
# Xem báo cáo chi tiết về storage
python -m Tiktok.cleanStorage.utils report
```

## 📊 Các tính năng bổ sung

### 1. Thống kê Storage
- Tổng số video và dung lượng
- Phân loại theo trạng thái (pending/uploaded)  
- Phân loại theo nguồn (Facebook/YouTube)
- Số lượng tài khoản TikTok

### 2. Phát hiện File mồ côi
- **Metadata mồ côi**: File `.json`, `.txt`, `.info` không có video tương ứng
- **Video mồ côi**: File video không có metadata tương ứng

### 3. Phát hiện Video cũ
- Tìm video cũ hơn ngày chỉ định (mặc định 30 ngày)
- Sắp xếp theo tuổi để dễ dàng quyết định xóa

## 🔧 Cấu trúc Module

```
Tiktok/cleanStorage/
├── __init__.py          # Package marker
├── manager.py           # Chức năng chính clean-pending & clean-uploaded
├── utils.py             # Utilities: thống kê, báo cáo, phát hiện file mồ côi
└── README.md           # Tài liệu này
```

## ⚙️ Hoạt động

### Luồng Clean Pending
1. Quét tất cả video từ `stalkers/facebook/videos` và `stalkers/youtube/videos`
2. Kiểm tra từng video xem đã có trong lịch sử upload chưa
3. Lọc ra các video chưa upload (pending)
4. Xác nhận với người dùng trước khi xóa
5. Xóa cả video và metadata liên quan

### Luồng Clean Uploaded  
1. Đọc tất cả file `history.json` từ các tài khoản
2. Thu thập danh sách `video_id` đã upload
3. Quét các video và lọc ra những video đã upload
4. Xác nhận với người dùng trước khi xóa
5. Xóa cả video và metadata liên quan

## 🛡️ An toàn

- **Xác nhận bắt buộc**: Luôn yêu cầu xác nhận trước khi xóa
- **Dry run**: Hỗ trợ chế độ xem trước mà không thực sự xóa
- **Báo cáo chi tiết**: Hiển thị thống kê trước và sau khi dọn dẹp
- **Xử lý lỗi**: Báo cáo lỗi nhưng không dừng quá trình

## 📝 Ví dụ Output

### Clean Pending
```
🔍 Đang quét video pending...
📊 Tổng quan:
   📹 Tổng số video: 25
   ✅ Đã upload: 18  
   ⏳ Pending: 7

📋 Danh sách 7 video pending sẽ bị xóa:
   🗑️ video_001.mp4
      📄 video_001.json
   🗑️ video_002.mp4
      📄 video_002.json
   ...

⚠️ Bạn có chắc muốn xóa 7 video pending? (y/N): y

🗑️ Đã xóa: video_001.mp4
🗑️ Đã xóa: video_001.json
...

✅ Hoàn thành!
   🗑️ Đã xóa: 14 file
```

### Storage Report  
```
📊 === BÁO CÁO STORAGE SPAMTIKTOK ===

🎯 Tổng quan:
   📹 Tổng video: 25 (1250.5 MB)
   ⏳ Pending: 7 (350.2 MB)
   ✅ Uploaded: 18 (900.3 MB)  
   👥 Tài khoản: 3

📂 Chi tiết theo nguồn:
   ✅ FB:
      📹 Total: 15 (750.1 MB)
      ⏳ Pending: 4 (200.0 MB)
      ✅ Uploaded: 11 (550.1 MB)
   ✅ YT:
      📹 Total: 10 (500.4 MB)
      ⏳ Pending: 3 (150.2 MB)
      ✅ Uploaded: 7 (350.2 MB)

📅 Video cũ hơn 30 ngày: 3
   📹 old_video_001.mp4 (45 ngày)

🕐 Báo cáo tạo lúc: 2025-01-27 10:30:00
```

## 🔗 Tích hợp với CLI

Module được tích hợp hoàn toàn với `cli.py` thông qua:

```python
# cli.py
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
}
```