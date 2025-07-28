# SPAMTIKTOK

Một bộ công cụ tự động hóa mạnh mẽ được xây dựng bằng Python để quản lý toàn diện các kênh TikTok.

## Giới thiệu

SPAMTIKTOK không chỉ là một công cụ upload video đơn thuần. Nó là một hệ thống hoàn chỉnh giúp bạn:
- **Tự động tìm kiếm và tải về** nội dung video từ các nguồn phổ biến như Facebook và YouTube.
- **Quản lý nhiều tài khoản TikTok** một cách độc lập và an toàn.
- **Tự động hóa hoàn toàn** quy trình đăng video, từ việc điền caption, thêm hashtag cho đến khi đăng tải thành công.
- **Bảo trì kênh** bằng cách tự động xóa các video có hiệu suất thấp.

Tất cả được điều khiển thông qua một giao diện dòng lệnh (`cli.py`) tiện lợi và mạnh mẽ.

## Tính năng

✅ **Quản lý đa tài khoản**: Dễ dàng đăng nhập và quản lý nhiều tài khoản TikTok, mỗi tài khoản có profile, cookie và lịch sử riêng biệt.

✅ **Cào video tự động (Stalkers)**: Các tiến trình chạy nền liên tục theo dõi và tải về video mới từ các trang Facebook và kênh YouTube bạn đã định cấu hình.

✅ **Chế độ Upload linh hoạt**:
  - **Tự động (`auto`)**: Tự động đăng toàn bộ video mới tìm được.
  - **Thủ công (`manual`)**: Mở trình duyệt để bạn tự chọn video và kiểm soát quá trình đăng.

✅ **Bảo trì kênh thông minh**: Tự động xóa các video có lượt xem thấp hơn một ngưỡng do bạn đặt ra, giúp giữ cho kênh luôn có chất lượng cao.

✅ **Giao diện dòng lệnh (CLI) toàn diện**: Cung cấp một bộ lệnh đầy đủ để thực hiện mọi tác vụ, từ đăng nhập, cào video, upload, dọn dẹp cho đến giám sát hệ thống.

✅ **Giám sát và quản lý tiến trình**: Dễ dàng theo dõi tài nguyên (`monitor`) và dừng (`kill-stalkers`) các tiến trình cào video.

## Cài đặt

1.  **Clone a repository**:
    ```bash
    git clone <your-repo-url>
    cd spamTiktok
    ```
2.  **Tạo và kích hoạt môi trường ảo** (khuyến khích):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Cài đặt các thư viện cần thiết**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Yêu cầu hệ thống**: Cần cài đặt trình duyệt **Google Chrome**. Script sẽ tự động tương tác với nó.

## Sử dụng

Công cụ được vận hành thông qua `cli.py`. Bạn có thể chạy ở chế độ tương tác để thực hiện nhiều lệnh liên tiếp.

```bash
python cli.py
```
Sau đó, bạn có thể gõ các lệnh như `status`, `upload auto my_account_1`, v.v.

### Luồng làm việc tiêu biểu

1.  **Đăng nhập lần đầu**:
    - `login-fb` (Nếu bạn cào video từ các trang Facebook cần đăng nhập)
    - `login-tt my_account_1` (Tạo và đăng nhập vào một tài khoản TikTok)

2.  **Bật các Stalker** (chạy chúng trong các terminal riêng biệt hoặc dùng `screen`/`tmux`):
    - `stalk fb` (Để cào từ Facebook)
    - `stalk yt` (Để cào từ YouTube)
    - Hoặc `stalk all` (Để cào từ cả hai)
3.  **Kiểm tra trạng thái và upload**:
    - `status` (Xem có bao nhiêu video đang chờ)
    - `upload auto my_account_1` (Bắt đầu upload tự động)

4.  **Bảo trì và dọn dẹp**:
    - `clean-uploaded` (Xóa các file video gốc đã được đăng thành công)
    - `delete-videos my_account_1 --threshold 200` (Xóa các video trên kênh có dưới 200 lượt xem)

Để xem danh sách đầy đủ các lệnh và mô tả chi tiết, hãy tham khảo file **CLI.md**.

## Giấy phép

SPAMTIKTOK được phát hành dưới giấy phép MIT.