"""
WorkLog 엔티티 - 일일 작업 기록을 관리하는 ORM 모델
프로젝트별 작업 시간과 진행량을 추적
"""

from datetime import datetime, date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Integer, String, DateTime, Date, Text, Float,
    ForeignKey, CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .project import Project

from ..database.base import Base


class WorkLog(Base):
    """
    일일 작업 기록을 저장하는 테이블
    프로젝트별로 하루에 한 번만 기록 가능
    """

    __tablename__ = "work_logs"

    # ===== Primary Key =====
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ===== Foreign Key =====
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="프로젝트 FK"
    )

    # ===== 작업 기록 필드 =====
    work_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        comment="작업일"
    )

    progress_added: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="오늘 추가된 진행량"
    )

    hours_spent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="작업시간 (시간 단위)"
    )

    memo: Mapped[Optional[str]] = mapped_column(
    String(100),
    nullable=True,
    comment="작업 메모 (100자 제한)"
    )

    # ===== 관계 설정 =====
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="work_logs"
    )

    # ===== 제약조건 =====
    __table_args__ = (
        # 데이터 유효성 검증
        CheckConstraint(
            "progress_added >= 0",
            name="valid_progress_added"
        ),
        CheckConstraint(
            "hours_spent >= 0",
            name="valid_hours"
        ),
        # 하루에 한 번만 기록 가능
        UniqueConstraint(
            "project_id", "work_date",
            name="unique_project_date"
        ),
        # 성능을 위한 인덱스
        Index("ix_work_logs_work_date", "work_date"),
        Index("ix_work_logs_project_date", "project_id", "work_date"),
    )

    # ===== 계산된 속성 =====
    @property
    def efficiency(self) -> float:
        """
        작업 효율성 계산 (진행량/시간)
        시간당 완성한 작업량
        """
        if self.hours_spent <= 0:
            return 0.0
        return self.progress_added / self.hours_spent

    # ===== Base.to_dict() 오버라이드 =====
    def to_dict(self) -> dict:
        """Base의 to_dict()를 오버라이드"""
        # 1: 기본 컬럼들은 Base의 방식 사용
        base_dict = super().to_dict()

        # 2: property 추가
        base_dict.update({
            'efficiency': self.efficiency,
        })

        return base_dict