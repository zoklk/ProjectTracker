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
        default="Null",
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

    initial_progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="초기 진행도 (BUG/#8)"
    )

    # ===== 관계 설정 =====
    work_logs: Mapped[List["WorkLog"]] = relationship(
        "WorkLog",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    # ===== 제약조건 =====
    __table_args__ = (
        CheckConstraint(
            "status IN ('진행 중', '완료', '시작 안 함', '중단')",
            name="valid_status"
        ),
        CheckConstraint(
            "initial_progress >= 0",
            name="valid_initial_progress"
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

    # ===== 속성값 계산 =====
    @property
    def current_progress(self) -> int:
        """현재 진행도 = 초기값 + 작업로그 누적 (자동 계산)"""
        work_logs_sum = sum(log.progress_added for log in self.work_logs)
        return self.initial_progress + work_logs_sum

    @property
    def days_until_deadline(self) -> int:
        """마감일까지 남은 일수 (매번 계산)"""
        today = date.today()
        delta = self.end_date - today
        return delta.days

    @property
    def is_overdue(self) -> bool:
        """마감일 초과 여부 (매번 계산)"""
        return self.days_until_deadline < 0

    @property
    def d_day_display(self) -> str:
        """D-Day 표시용 문자열 (매번 계산)"""
        days = self.days_until_deadline
        if days > 0:
            return f"D-{days}"
        elif days == 0:
            return "D-Day"
        else:
            return f"D+{abs(days)}"

    # ===== Base.to_dict() 오버라이드 =====
    def to_dict(self) -> dict:
        """Base의 to_dict()를 오버라이드"""
        # 1: 기본 컬럼들은 Base의 방식 사용
        base_dict = super().to_dict()

        # 2: property 추가
        base_dict.update({
            'current_progress': self.current_progress,  # 계산된 현재 진행도
            'days_until_deadline': self.days_until_deadline,
            'is_overdue': self.is_overdue,
            'd_day_display': self.d_day_display
        })

        return base_dict