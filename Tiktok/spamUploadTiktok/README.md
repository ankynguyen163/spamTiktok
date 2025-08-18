# Tiktok Spam Upload Tool

Công cụ này được thiết kế để tự động hóa quá trình tải video lên TikTok, hỗ trợ cả chế độ thủ công và tự động. Nó sử dụng Playwright để tương tác với trình duyệt Chrome và quản lý lịch sử tải lên cho từng tài khoản.

## Tính năng chính

-   **Tải lên thủ công**: Cho phép bạn chọn và tải lên video một cách thủ công thông qua giao diện Chrome.
-   **Tải lên tự động**: Tự động theo dõi các thư mục video nguồn (ví dụ: video từ Facebook) và tải lên các video mới ngay khi chúng xuất hiện.
-   **Quản lý tài khoản**: Hỗ trợ nhiều tài khoản TikTok, mỗi tài khoản có profile và lịch sử tải lên riêng.
-   **Quản lý lịch sử**: Theo dõi các video đã được tải lên để tránh tải lên trùng lặp.
-   **Tạo caption và hashtag**: Tự động làm sạch mô tả video và tạo hashtag liên quan.

## Yêu cầu

-   Python 3.x
-   Google Chrome (để kết nối qua cổng gỡ lỗi)
-   Các thư viện Python được liệt kê trong `requirements.txt` (Playwright, watchdog, v.v.)

## Cài đặt

1.  **Cài đặt các thư viện Python**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Cài đặt trình duyệt Playwright**:
    ```bash
    playwright install chromium
    ```

3.  **Chuẩn bị Chrome cho tự động hóa**:
    Công cụ này kết nối với một phiên Chrome đang chạy thông qua cổng gỡ lỗi. Bạn cần mở Chrome với một profile cụ thể và bật cổng gỡ lỗi.
    Ví dụ, để mở Chrome với profile `my_tiktok_account` và cổng `9222`:
    ```bash
    google-chrome --user-data-dir=/path/to/your/profile/directory/my_tiktok_account --remote-debugging-port=9222 --new-window
    ```
    Thay `/path/to/your/profile/directory/my_tiktok_account` bằng đường dẫn thực tế đến thư mục profile của bạn. Thư mục này sẽ được tạo tự động nếu chưa tồn tại khi bạn chạy lệnh `manual` hoặc `auto` lần đầu tiên.

    **Lưu ý**: Đảm bảo rằng không có phiên Chrome nào khác đang sử dụng cùng một profile hoặc cổng gỡ lỗi.

## Cấu hình

Các cấu hình chính được định nghĩa trong `Tiktok/config.py`. Bạn có thể cần điều chỉnh:

-   `VIDEO_SOURCES`: Đường dẫn đến các thư mục chứa video nguồn (ví dụ: video tải về từ Facebook, YouTube).
-   `ACCOUNTS_DIR`: Thư mục chứa profile của các tài khoản TikTok.
-   `CHROME_EXECUTABLE`: Đường dẫn đến file thực thi của Chrome (nếu không phải là `google-chrome` mặc định).
-   `CHROME_DEBUG_PORT`: Cổng gỡ lỗi mà Chrome đang lắng nghe.
-   `MAX_CONCURRENT_UPLOADS`: Số lượng video có thể được tải lên đồng thời (chỉ áp dụng cho chế độ tự động).

## Cách sử dụng

Công cụ được chạy dưới dạng một module Python.

```bash
python -m Tiktok.spamUploadTiktok <command> <account_name> [options]
```

### Các lệnh

-   `manual <account_name>`:
    Bắt đầu quá trình tải lên thủ công cho `<account_name>`.
    Công cụ sẽ mở một cửa sổ Chrome và điều hướng đến trang tải lên của TikTok. Bạn sẽ cần tự chọn file video trong trình duyệt. Sau khi chọn, công cụ sẽ tự động điền caption, hashtag và hoàn tất quá trình đăng.

    Ví dụ:
    ```bash
    python -m Tiktok.spamUploadTiktok manual my_tiktok_account_1
    ```

-   `auto <account_name>`:
    Bắt đầu quá trình tải lên tự động cho `<account_name>`.
    Công cụ sẽ theo dõi các thư mục video được cấu hình trong `VIDEO_SOURCES`. Khi một video mới được thêm vào, nó sẽ tự động được đưa vào hàng đợi và tải lên TikTok. Nhiều worker có thể chạy song song để xử lý các video.

    Ví dụ:
    ```bash
    python -m Tiktok.spamUploadTiktok auto my_tiktok_account_2
    ```

-   `list <account_name>`:
    Liệt kê tất cả các video có sẵn trong các thư mục nguồn mà chưa được tải lên bởi `<account_name>`.

    Ví dụ:
    ```bash
    python -m Tiktok.spamUploadTiktok list my_tiktok_account_1
    ```

### Quản lý lịch sử tải lên

Mỗi tài khoản sẽ có một file `history.json` trong thư mục profile của nó (`ACCOUNTS_DIR/<account_name>/history.json`). File này ghi lại các video đã được tải lên, bao gồm ID video, mô tả, thời gian tải lên và tên tài khoản.

Các video đã được ghi vào lịch sử sẽ không được tải lên lại bởi cùng một tài khoản.

## Phát triển và Gỡ lỗi

-   **Logging**: Công cụ sử dụng logging để ghi lại các hoạt động và lỗi. Bạn có thể xem output trên console.
-   **Ảnh chụp màn hình**: Trong trường hợp lỗi, công cụ có thể tự động chụp ảnh màn hình để hỗ trợ gỡ lỗi.
-   **Test**: Các unit test cho các hàm tiện ích có thể được tìm thấy trong `test_utils.py`. Bạn có thể chạy chúng bằng `pytest`.
