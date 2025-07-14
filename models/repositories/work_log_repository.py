from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, Float

from ..database.connection import db_manager
from ..entities.work_log import WorkLog
from ..entities.project import Project


class WorkLogRepository:
    """작업 로그 데이터 접근 객체"""

    def __init__(self):
        pass

    # ===== 조회 메서드들 (Dict 반환) =====
    def find_by_date(self, work_date: date) -> List[Dict[str, Any]]:
        """특정 날짜의 작업 로그 조회 (JOIN 없음)"""
        with db_manager.get_session_context() as session:
            work_logs = session.query(WorkLog).filter(
                WorkLog.work_date == work_date
            ).all()
            return [log.to_dict() for log in work_logs]

    def find_by_date_range(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """기간별 작업 로그 + 프로젝트 정보 JOIN 조회"""
        with db_manager.get_session_context() as session:
            # 1: WorkLog + Project JOIN 쿼리
            query_result = session.query(WorkLog, Project)\
                .join(Project, WorkLog.project_id == Project.id)\
                .filter(WorkLog.work_date.between(start_date, end_date))\
                .all()

            # 2: Entity의 to_dict() 활용 + JOIN 데이터 추가
            result = []
            for work_log, project in query_result:
                log_dict = work_log.to_dict()
                log_dict['project_name'] = project.name  # JOIN으로 가져온 프로젝트명 추가
                result.append(log_dict)

            return result

    # ===== 생성 메서드들 (성공 여부 반환) =====
    def bulk_insert(self, work_logs: List[WorkLog]) -> int:
        """여러 WorkLog 엔티티 일괄 삽입"""
        if not work_logs:
            return 0

        with db_manager.get_session_context() as session:
            session.add_all(work_logs)
            return len(work_logs)

    # ===== 수정 메서드들 (성공 여부 반환) =====
    def bulk_update(self, updates: List[Dict]) -> int:
        """여러 WorkLog 일괄 업데이트"""
        if not updates:
            return 0

        with db_manager.get_session_context() as session:
            updated_count = 0

            for update_data in updates:
                result = session.query(WorkLog).filter(
                    and_(
                        WorkLog.project_id == update_data['project_id'],
                        WorkLog.work_date == update_data['work_date']
                    )
                ).update({
                    'progress_added': update_data['progress_added'],
                    'hours_spent': update_data['hours_spent'],
                    'memo': update_data['memo']
                })
                updated_count += result

            return updated_count


    # ===== 효율성 통계 메서드들 (dashboard 용) =====
    def get_efficiency_stats_by_projects(self, project_ids: List[int]) -> Dict[int, Dict]:
        """
        Returns:
            Dict[project_id, {
                'avg_efficiency': float,                    # 평균 효율성 (진행량/시간)
                'worked_hours': float,                       # 총 작업시간
                'avg_hours_per_day': float                  # 현실적 일평균 작업시간 (작업 못한 날 포함)
            }]
        """
        if not project_ids:
            return {}

        with db_manager.get_session_context() as session:
            result = session.query(
                WorkLog.project_id,
                func.avg(
                    func.cast(WorkLog.progress_added, Float) /
                    func.nullif(WorkLog.hours_spent, 0)
                ).label('avg_efficiency'),
                func.sum(WorkLog.hours_spent).label('worked_hours'),
                func.min(WorkLog.work_date).label('first_work_date'),
                func.max(WorkLog.work_date).label('last_work_date')
            ).filter(
                WorkLog.project_id.in_(project_ids)
            ).group_by(WorkLog.project_id).all()

            # 결과를 딕셔너리로 변환
            stats_dict = {}
            for row in result:
                project_id = row.project_id
                avg_efficiency = row.avg_efficiency or 0
                worked_hours = row.worked_hours or 0
                first_work_date = row.first_work_date
                last_work_date = row.last_work_date

                # 현실적 일 평균 작업시간 계산 (전체 기간 기준)
                if first_work_date and last_work_date:
                    total_period_days = (last_work_date - first_work_date).days + 1
                    avg_hours_per_day = worked_hours / total_period_days
                else:
                    avg_hours_per_day = 0

                stats_dict[project_id] = {
                    'avg_efficiency': float(avg_efficiency),
                    'worked_hours': float(worked_hours),
                    'avg_hours_per_day': float(avg_hours_per_day)
                }

            return stats_dict