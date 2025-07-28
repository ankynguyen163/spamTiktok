import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / 'logs'
LOG_FILE = LOG_DIR / 'stalkers.log'

def setup_stalker_logger():
    """
    Cấu hình logger chính để ghi ra cả file và console.
    Có thể gọi nhiều lần mà không bị đúp log.
    """
    LOG_DIR.mkdir(exist_ok=True)
    root_logger = logging.getLogger()

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(logging.INFO)

    # Định dạng log rõ ràng, thân thiện hơn
    formatter = logging.Formatter(
        "\n🕵️  %(asctime)s"
        #"\n🔧  Level   : %(levelname)s"
        #"\n⚙️   PID     : %(process)d"
        #"\n📦  Logger  : %(name)s"
        "\n💬  Message : %(message)s\n",
        datefmt='%H:%M:%S'
    )

    # Ghi file
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Ghi console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
