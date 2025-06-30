"""
Project 엔티티 - 프로젝트 정보를 관리하는 ORM 모델
노션 동기화와 로컬 관리 기능을 포함
"""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Integer, String, DateTime, Date, Text, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .work_log import WorkLog

from ..database.base import Base


class Project(Base):
    """
    프로젝트 정보를 저장하는 메인 테이블
    노션과 동기화되며 로컬에서 진행상황을 관리
    """

    __tablename__ = "projects"

    # ===== Primary Key =====
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ===== 노션 동기화 관련 필드 =====
    notion_page_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="노션 페이지 ID (동기화 키)"
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="프로젝트명 (노션에서 가져옴)"
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="진행 중",
        comment="상태 (노션에서 가져옴)"
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="시작일 (노션에서 가져옴)"
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="목표 종료일 (노션에서 가져옴)"
    )

    # ===== 로컬 관리 필드 =====
    target_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="목표치 (로컬에서 설정)"
    )

    current_progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="현재 진행도 (초기값 + 작업로그 누적)"
    )

    # ===== 관계 설정 =====
    work_logs: Mapped[List["WorkLog"]] = relationship(
        "WorkLog",
        back_populates="project",
        cascade="all, delete-orphan"
        # order_by 제거 - 필요시 쿼리에서 직접 정렬
    )

    # ===== 제약조건 =====
    __table_args__ = (
        CheckConstraint(
            "status IN ('진행 중', '완료', '시작 안 함', '중단')",
            name="valid_status"
        ),
        CheckConstraint(
            "current_progress >= 0",
            name="valid_progress"
        ),
        CheckConstraint(
            "target_value > 0",
            name="valid_target"
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="valid_date_range"
        ),
        # 성능을 위한 인덱스
        Index("ix_projects_status", "status"),
        Index("ix_projects_end_date", "end_date"),
        Index("ix_projects_notion_page_id", "notion_page_id"),
    )

    # ===== 계산된 속성 =====
    @property
    def progress_percentage(self) -> float:
        """진행률을 퍼센트로 반환 (0.0 ~ 100.0)"""
        if self.target_value <= 0:
            return 0.0
        return min((self.current_progress / self.target_value) * 100, 100.0)

    @property
    def days_until_deadline(self) -> int:
        """마감일까지 남은 일수 (음수면 지연)"""
        today = date.today()
        delta = self.end_date - today
        return delta.days

    @property
    def is_overdue(self) -> bool:
        """마감일 초과 여부"""
        return self.days_until_deadline < 0

    @property
    def d_day_display(self) -> str:
        """D-Day 표시용 문자열"""
        days = self.days_until_deadline
        if days > 0:
            return f"D-{days}"
        elif days == 0:
            return "D-Day"
        else:
            return f"D+{abs(days)}"