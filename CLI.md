# Công Cụ Dòng Lệnh (CLI)

Công cụ `cli.py` là trung tâm điều khiển cho toàn bộ hệ thống. Nó cung cấp một giao diện nhất quán để thực thi tất cả các tác vụ.

## Cách sử dụng

Bạn có thể chạy CLI ở hai chế độ:

1.  **Chế độ tương tác (khuyến khích)**: Chạy nhiều lệnh liên tiếp mà không cần gõ lại `python cli.py`.
    ```bash
    python cli.py
    >> cli: status
    >> cli: upload auto my_account_1
    ```
2.  **Chế độ một lần**: Thực thi một lệnh duy nhất và thoát.
    ```bash
    python cli.py status
    python cli.py upload auto my_account_1
    ```

---

## Tham khảo các lệnh

### Quản lý tài khoản

*   `login-fb`: Mở trình duyệt để bạn đăng nhập vào Facebook. Cần thiết để cào video từ các trang yêu cầu đăng nhập.
*   `login-tt <account_name>`: Mở trình duyệt để bạn đăng nhập vào một tài khoản TikTok. Thao tác này sẽ tạo một profile mới cho tài khoản đó.
*   `list-accounts`: Liệt kê tất cả các tài khoản TikTok đã được cấu hình.

### Cào video (Stalkers)
*   `stalk <fb|yt|all>`: Bắt đầu tiến trình chạy nền để cào video từ các nguồn đã chỉ định.
    *   `stalk fb`: Cào video từ Facebook.
    *   `stalk yt`: Cào video từ YouTube.
    *   `stalk all`: Cào video từ tất cả các nguồn.
### Upload và quản lý nội dung

*   `upload <auto|manual> <account_name>`: Bắt đầu quá trình upload video.
    *   `auto`: Tự động upload tất cả video mới.
    *   `manual`: Mở trình duyệt để bạn tự chọn video và kiểm soát quá trình đăng.
*   `list <account_name>`: Liệt kê danh sách các video đã tải về và sẵn sàng để upload cho một tài khoản cụ thể.

### Dọn dẹp và bảo trì

*   `history <lệnh_phụ> [tham_số]`: Quản lý lịch sử upload.
    *   `view <account_name> [--limit N]`: Hiển thị lịch sử các video đã được upload bởi một tài khoản. Tùy chọn `--limit` sẽ chỉ hiển thị N video gần nhất.
    *   `clear <account_name> [--yes]`: Xóa toàn bộ lịch sử upload của một tài khoản. **Hành động này không thể hoàn tác.** Dùng `--yes` để bỏ qua bước xác nhận.
    *   `migrate`: Di chuyển dữ liệu từ file lịch sử cũ (global) sang cấu trúc lịch sử mới theo từng tài khoản.
*   `clean-pending`: Xóa các file video đã được tải về nhưng chưa được upload lên bất kỳ tài khoản nào.
*   `clean-uploaded`: Xóa các file video gốc đã được upload thành công (dựa trên lịch sử của tất cả các tài khoản).
*   `storage-report` hoặc `storage`: In báo cáo chi tiết về tình trạng lưu trữ, bao gồm dung lượng, số lượng video, và các file mồ côi.
*   `delete-videos <account_name> [tùy chọn]`: Xóa các video có hiệu suất thấp trực tiếp trên kênh TikTok.
    *   `--threshold <số>`: Đặt ngưỡng lượt xem để xóa (mặc định: 100).
    *   `--dry-run`: Chạy thử, chỉ liệt kê video sẽ bị xóa mà không thực hiện hành động xóa.
    *   `--debug`: Hiển thị thêm thông tin chi tiết để gỡ lỗi.

### Hệ thống & Tiện ích

*   `status`: Hiển thị bảng tóm tắt trạng thái của hệ thống: số tài khoản, số video chờ upload, và trạng thái của các tiến trình stalker.
*   `monitor`: Theo dõi tài nguyên CPU và bộ nhớ của các tiến trình stalker theo thời gian thực.
*   `kill-stalkers`: Dừng tất cả các tiến trình `stalk-fb` và `stalk-yt` đang chạy.
*   `help` hoặc `?`: Hiển thị danh sách tất cả các lệnh có sẵn.
*   `exit` hoặc `quit`: Thoát khỏi chế độ tương tác.