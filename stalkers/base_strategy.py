# strategies/base.py

from abc import ABC, abstractmethod
from typing import List

class StalkerStrategy(ABC):
    """
    Lớp cơ sở trừu tượng cho tất cả các chiến lược Stalker.
    Mỗi Stalker (Facebook, YouTube, etc.) phải kế thừa từ lớp này.
    """

    @abstractmethod
    def get_targets(self) -> List[str]:
        """Đọc và trả về danh sách các URL mục tiêu từ file cấu hình."""
        pass

    @abstractmethod
    def login(self) -> bool:
        """Thực hiện logic đăng nhập nếu cần. Trả về True nếu thành công."""
        pass

    @abstractmethod
    def execute(self):
        """
        Thực thi logic chính của Stalker, thường là trong một vòng lặp vô tận.
        Đây là entrypoint chính cho một chiến lược được gọi bởi manager.
        """
        pass