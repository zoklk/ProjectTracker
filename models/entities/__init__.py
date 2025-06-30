"""
Entities 패키지 초기화
ORM 모델들을 제공
"""

from .project import Project
from .work_log import WorkLog

__all__ = [
    "Project",
    "WorkLog"
]