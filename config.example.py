# config.example.py
import logging
import os
from datetime import datetime

NOTION_API_KEY = "your_notion_api_key_here"
NOTION_DATABASE_ID = "your_database_id_here"

# =============================================================================
# 로깅 설정
# =============================================================================

def setup_logging():
    """종류별 로그 파일 분리 설정"""

    # 1: 로그 디렉토리 생성
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 2: 로그 파일명 (종류별)
    info_log = f"{log_dir}/ProjectTracker_info.log"          # 일반 정보
    error_log = f"{log_dir}/ProjectTracker_error.log"        # 에러만

    # 3: 로그 포맷
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 4. 루트 로거 기본 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 5: 기존 핸들러 제거 (중복 방지)
    root_logger.handlers.clear()

    # 6: 핸들러별 설정
    formatter = logging.Formatter(log_format, date_format)

    # (INFO 이상 → info.log)
    info_handler = logging.FileHandler(info_log, encoding='utf-8')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    root_logger.addHandler(info_handler)

    # (ERROR 이상 → error.log)
    error_handler = logging.FileHandler(error_log, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # (콘솔 출력 (개발 시))
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 7. 외부 라이브러리 노이즈 제거
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("notion_client").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)

# =============================================================================
def get_logger(name: str):
    """모듈별 로거 생성 헬퍼 함수"""
    return logging.getLogger(name)