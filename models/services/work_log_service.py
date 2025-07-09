from typing import List, Dict, Any, Optional
from datetime import date, datetime
import logging

from ..repositories.work_log_repository import WorkLogRepository
from ..entities.work_log import WorkLog
from ..services.project_service import ProjectService


class WorkLogService:
    def __init__(self):
        self.work_log_repo = WorkLogRepository()
        self.project_service = ProjectService()  # Project 정보 활용
        self.logger = logging.getLogger(__name__)

    def get_today_work_data(self) -> List[Dict[str, Any]]:
        """오늘 작업 현황 - 모든 진행 중 프로젝트 + 오늘 작업 로그 동적 조합"""
        try:
            today = date.today()

            # 1: 진행 중 프로젝트 목록 조회 (ProjectService 활용)
            active_projects = self.project_service.get_active_projects()

            # 2: 오늘 log 자동 생성
            self._ensure_today_logs_exist(active_projects, today)

            # 3. DB에서 오늘 작업 로그 조회
            today_logs = self.work_log_repo.find_by_date(today)

            # 4: 프로젝트별 로그 매핑 (빠른 조회용 딕셔너리)
            log_by_project = {log['project_id']: log for log in today_logs}

            # 5: 동적 조합 (LEFT JOIN 효과)
            result = []
            for project in active_projects:
                project_id = project['id']
                existing_log = log_by_project.get(project_id)

                # 6: fd에서 인식 가능하도록 파싱
                row = {
                    'project_id': project_id,
                    'work_date': today,
                    '프로젝트명': project['name'],
                    'D-Day': project['d_day_display'],
                    '목표치': project['target_value'],
                    '현재값': project['current_progress'],
                    # 기존 로그가 있으면 실제 값, 없으면 기본값 0
                    '진행량': existing_log['progress_added'] if existing_log else 0,
                    '작업시간': existing_log['hours_spent'] if existing_log else 0.0,
                    '메모': existing_log['memo'] if existing_log else ""
                }
                result.append(row)

            return result

        except Exception as e:
            raise e

    def _ensure_today_logs_exist(self, active_projects: List[Dict], today: date):
        """오늘 날짜 로그가 없는 진행 중 프로젝트들의 로그 자동 생성"""
        # 1: 기존 오늘 로그 조회
        existing_logs = self.work_log_repo.find_by_date(today)
        existing_project_ids = {log['project_id'] for log in existing_logs}

        # 2: 로그가 없는 프로젝트들 찾기
        missing_projects = [
            project for project in active_projects
            if project['id'] not in existing_project_ids
        ]

        # 3: 없는 프로젝트들에 대해 기본값 로그 생성
        if missing_projects:
            new_logs = []
            for project in missing_projects:
                new_log = WorkLog(
                    project_id=project['id'],
                    work_date=today,
                    progress_added=0,    # 기본값
                    hours_spent=0.0,     # 기본값
                    memo=""              # 기본값
                )
                new_logs.append(new_log)

            # 4: 벌크 삽입
            if new_logs:
                self.work_log_repo.bulk_insert(new_logs)

    def get_past_work_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """과거 작업 로그 조회 - 실제 기록된 데이터만 반환"""
        try:
            # +: 날짜 유효성 검사
            if start_date > end_date:
                raise ValueError("⚙️❌ 시작일이 종료일보다 늦을 수 없습니다")
            if start_date > date.today() or end_date > date.today():
                raise ValueError("⚙️❌ 미래 날짜는 조회할 수 없습니다")

            # 1: 기간별 작업 로그 + 프로젝트 정보 조회
            work_logs = self.work_log_repo.find_by_date_range(start_date, end_date)

            # 2: View 친화적 구조로 변환
            result = []
            for log in work_logs:
                # 요일 계산
                weekdays = ['월', '화', '수', '목', '금', '토', '일']
                weekday = weekdays[log['work_date'].weekday()]

                row = {
                    'project_id': log['project_id'],
                    'work_date': log['work_date'],
                    '날짜': f"{log['work_date'].strftime('%Y-%m-%d')} ({weekday})",
                    '프로젝트명': log['project_name'],  # Repository에서 JOIN으로 가져온 프로젝트명
                    '진행량': log['progress_added'],
                    '작업시간': log['hours_spent'],
                    '메모': log['memo']
                }
                result.append(row)

            # 3: 날짜순 정렬 (최신순)
            result.sort(key=lambda x: x['work_date'], reverse=True)

            return result

        except Exception as e:
            raise e

    def update_work_logs(self, changes: List[Dict[str, Any]]) -> int:
        """작업 로그 업데이트 (INSERT는 get_today_work_data에서 이미 처리됨)"""
        try:
            # 1: 빈 변경사항 체크
            if not changes:
                return 0

            # 2: 데이터 검증
            validated_changes = []
            invalid_count = 0

            for change in changes:
                if self._validate_work_log_data(change):
                    validated_changes.append(change)
                else:
                    invalid_count += 1

            # 3: 검증 실패 처리
            if not validated_changes:
                raise ValueError("⚙️❌ 유효한 작업 로그 데이터가 없습니다")

            if invalid_count > 0:
                raise ValueError(f"⚙️❌ 잘못된 작업 로그 데이터 {invalid_count}개가 발견되었습니다")

            # 4: 단순 업데이트만 수행 (로그는 이미 존재함이 보장됨)
            updated_count = self.work_log_repo.bulk_update(validated_changes)

            return updated_count

        except Exception as e:
            raise e

    # ===== Private 헬퍼 메서드 =====
    def _validate_work_log_data(self, data: Dict) -> bool:
        """작업 로그 데이터 검증"""
        try:
            # 1: 필수 필드 체크
            required_fields = ['project_id', 'work_date', 'progress_added', 'hours_spent', 'memo']
            if not all(field in data for field in required_fields):
                return False

            # 2: 타입 체크
            if not isinstance(data['project_id'], int):
                return False
            if not isinstance(data['work_date'], date):
                return False
            if not isinstance(data['progress_added'], (int, float)):
                return False
            if not isinstance(data['hours_spent'], (int, float)):
                return False
            if not isinstance(data['memo'], str):
                return False

            # 3: 비즈니스 규칙 체크
            if data['project_id'] <= 0:
                return False
            if data['progress_added'] < 0:
                return False
            if data['hours_spent'] < 0:
                return False
            if data['work_date'] > date.today():
                return False

            return True

        except Exception:
            return False