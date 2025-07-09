from typing import List, Dict, Any
from datetime import date, datetime
import logging

from models.services.work_log_service import WorkLogService
from models.services.project_service import ProjectService


class WorkLogController:
    def __init__(self):
        self.work_log_service = WorkLogService()
        self.logger = logging.getLogger(__name__)

    # ===== View에서 호출하는 메서드들 =====
    def get_today_work_data(self) -> List[Dict[str, Any]]:
        """오늘 작업 로그 조회"""
        try:
            today_work_data = self.work_log_service.get_today_work_data()
            self.logger.info(f"🎮✅ 오늘 작업 로그 조회 성공: {len(today_work_data)}개")
            return today_work_data
        except Exception as e:
            self.logger.error(f"🎮❌ 오늘 작업 로그 조회 실패: {str(e)}")
            raise e

    def get_past_work_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """과거 작업 로그 조회"""
        try:
            past_work_data = self.work_log_service.get_past_work_data(start_date, end_date)
            self.logger.info(f"🎮✅ 과거 작업 로그 조회 성공: {len(past_work_data)}개")
            return past_work_data
        except Exception as e:
            self.logger.error(f"🎮❌ 과거 작업 로그 조회 실패: {str(e)}")
            raise e

    def update_work_logs(self, changes: List[Dict[str, Any]]) -> int:
        """작업 로그 업데이트"""
        try:
            updated_count = self.work_log_service.update_work_logs(changes)
            self.logger.info(f"🎮✅ 작업 로그 업데이트 성공: {updated_count}개")
            return updated_count
        except Exception as e:
            self.logger.error(f"🎮❌ 작업 로그 업데이트 실패: {str(e)}")
            raise e