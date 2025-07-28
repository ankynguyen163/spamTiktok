import re
import random

def clean_caption(text):
    """
    Làm sạch caption bằng cách loại bỏ các phần không cần thiết một cách linh hoạt.
    Hàm sẽ cắt chuỗi tại vị trí xuất hiện đầu tiên của bất kỳ
    ký tự hoặc từ khóa phân cách nào (ví dụ: hashtag, credit, separator).
    Điều này giúp lấy được phần mô tả chính của video.
    """
    if not isinstance(text, str) or not text:
        return ""

    # Các mẫu phân cách. `re.IGNORECASE` sẽ xử lý các biến thể hoa/thường.
    # Thứ tự trong group quan trọng, ví dụ 'credit to' phải đứng trước 'credit'.
    # `\\n` là để xử lý chuỗi literal '\n' có thể có từ API/JSON.
    delimiters_pattern = r'\\n|#|\||©️|//|\b(credit to|credit|creds|via|source)\b'

    # Tách chuỗi tại lần xuất hiện đầu tiên của một trong các delimiter
    parts = re.split(delimiters_pattern, text, maxsplit=1, flags=re.IGNORECASE)

    # Lấy phần đầu tiên và loại bỏ khoảng trắng ở hai đầu
    cleaned_text = parts[0].strip()

    # Xử lý thêm trường hợp các ký tự rác cuối câu
    cleaned_text = re.sub(r'[\s:.,-]+$', '', cleaned_text)

    return cleaned_text

def generate_hashtags():
    """Tạo một chuỗi hashtags ngẫu nhiên và đa dạng."""
    core_hashtags = [
        '#CollectedVideo', '#FoundVideo', '#NotOriginal', '#CreditToCreator',
        '#VideoCollection', '#CuratedContent', '#SharedVideo', '#NotMyVideo',
        '#JustSharing', '#Sututam'  # Sưu tầm
    ]
    trending_hashtags = [
        '#ForYou', '#FYP', '#Viral', '#Trending', '#Entertainment',
        '#xuhuong', '#thinhhanh', '#LearnOnTikTok'
    ]

    # Chọn ngẫu nhiên một số lượng hashtags từ mỗi nhóm
    num_core_to_select = random.randint(2, 4)
    num_trending_to_select = random.randint(2, 3)

    selected_core = random.sample(core_hashtags, num_core_to_select)
    selected_trending = random.sample(trending_hashtags, num_trending_to_select)

    all_hashtags = selected_core + selected_trending
    random.shuffle(all_hashtags)

    return ' '.join(all_hashtags)