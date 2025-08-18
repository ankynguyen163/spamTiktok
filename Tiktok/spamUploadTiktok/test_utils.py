# Tiktok/test_utils.py
from pathlib import Path
# Chúng ta import trực tiếp các hàm và biến cần thiết từ module `utils`
# bằng cách sử dụng import tương đối. Dấu `.` đại diện cho thư mục hiện tại (Tiktok/spamUploadTiktok/).
from . import utils

# --- Test Case 1: get_profile_dir ---
# Tên hàm test luôn bắt đầu bằng `test_` để pytest có thể tự động tìm thấy.
def test_get_profile_dir():
    """
    Kiểm tra xem hàm get_profile_dir có trả về đúng đường dẫn cho một tài khoản không.
    Đây là một "happy path" test, kiểm tra trường hợp hoạt động bình thường.
    """
    # ARRANGE: Chuẩn bị dữ liệu đầu vào.
    account_name = "my_test_account"
    
    # ACT: Gọi hàm mà chúng ta muốn test.
    result_path = utils.get_profile_dir(account_name)
    
    # ASSERT: Kiểm tra kết quả có đúng như mong đợi không.
    # Chúng ta kỳ vọng đường dẫn trả về là <thư mục accounts>/my_test_account
    expected_path = utils.ACCOUNTS_DIR / account_name
    
    # `assert` sẽ kiểm tra xem hai giá trị có bằng nhau không.
    # Nếu không, pytest sẽ báo lỗi và bài test thất bại.
    assert result_path == expected_path

# --- Test Case 2: get_cookies_path ---
def test_get_cookies_path():
    """
    Kiểm tra xem hàm get_cookies_path có trả về đúng đường dẫn file cookies không.
    """
    # Arrange
    account_name = "another_account"
    
    # Act
    result_path = utils.get_cookies_path(account_name)
    
    # Assert
    expected_path = utils.ACCOUNTS_DIR / account_name / 'cookies.json'
    assert result_path == expected_path

# --- Test Case 3 & 4: get_description ---

# Khi một hàm test cần fixture, bạn chỉ cần khai báo nó như một tham số.
# pytest sẽ tự động cung cấp nó cho bạn.
def test_get_description_found(tmp_path, monkeypatch):
    """
    Kiểm tra hàm get_description khi tìm thấy file video.
    Sử dụng tmp_path để tạo thư mục tạm và monkeypatch để thay đổi utils.
    """
    # ARRANGE
    # 1. Tạo một thư mục video giả bên trong thư mục tạm do tmp_path cung cấp.
    fake_video_dir = tmp_path / "fake_videos"
    fake_video_dir.mkdir()

    # 2. Dùng monkeypatch để "bảo" code rằng VIDEO_SOURCES bây giờ là thư mục giả của chúng ta.
    # `setattr` nhận 3 tham số: (object, tên thuộc tính, giá trị mới)
    monkeypatch.setattr(utils, 'VIDEO_SOURCES', {'fake': fake_video_dir})

    # 3. Tạo một file video giả với tên theo đúng định dạng.
    #    Hàm `touch()` chỉ cần tạo ra file trống, chúng ta không cần nội dung.
    video_id = "12345"
    expected_description = "day la mot mo ta"
    fake_file_name = f"{video_id}_{expected_description.replace(' ', '_')}.mp4"
    (fake_video_dir / fake_file_name).touch()

    # ACT
    # Gọi hàm get_description. Nó sẽ tìm trong thư mục giả mà chúng ta đã thiết lập.
    actual_description = utils.get_description(video_id)

    # ASSERT
    # Kiểm tra xem mô tả trích xuất được có đúng không.
    assert actual_description == expected_description

def test_get_description_not_found():
    """
    Kiểm tra hàm get_description khi không tìm thấy file video.
    Trường hợp này đơn giản hơn, không cần tạo file giả.
    """
    # ARRANGE
    video_id = "video_khong_ton_tai"

    # ACT
    description = utils.get_description(video_id)

    # ASSERT
    # Hàm phải trả về một chuỗi rỗng.
    assert description == ""

# --- Test Case 5: get_description với tên file thực tế ---
def test_get_description_with_long_vietnamese_name(tmp_path, monkeypatch):
    """
    Kiểm tra hàm get_description với tên file dài, có ký tự tiếng Việt.
    Đây chính là ví dụ bạn đã hỏi!
    """
    # ARRANGE
    fake_video_dir = tmp_path / "real_world_videos"
    fake_video_dir.mkdir()
    monkeypatch.setattr(utils, 'VIDEO_SOURCES', {'fb': fake_video_dir})

    video_id = "1293437732365385"
    file_name = "1293437732365385_người_vợ_xuất_hiện_tại_lễ_đính_hôn_với_vai_trò_khách_không_mời_cái_kết_tập_1.mp4"
    expected_description = "người vợ xuất hiện tại lễ đính hôn với vai trò khách không mời cái kết tập 1"
    
    (fake_video_dir / file_name).touch()

    # ACT
    actual_description = utils.get_description(video_id)

    # ASSERT
    assert actual_description == expected_description
