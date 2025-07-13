from typing import List, Dict, Any
import logging
from datetime import date

from models.services.dashboard_service import DashboardService


class DashboardController:
    def __init__(self):
        self.dashboard_service = DashboardService()
        self.logger = logging.getLogger(__name__)

    # ===== View에서 호출하는 메서드들 =====
    def get_work_log_summary(self) -> Dict[str, Any]:
        """상단 3개 메트릭 데이터 조회"""
        try:
            summary = self.dashboard_service.get_work_log_summary()
            self.logger.info("🎮✅ 작업로그 요약 조회 성공")
            return summary

        except Exception as e:
            self.logger.error(f"🎮❌ 작업로그 요약 조회 실패: {str(e)}")
            raise e

    def get_projects_summary(self) -> List[Dict[str, Any]]:
        """프로젝트 현황 테이블 데이터 조회"""
        try:
            projects_data = self.dashboard_service.get_projects_summary()
            self.logger.info(f"🎮✅ 프로젝트 현황 조회 성공: {len(projects_data)}개")
            return projects_data

        except Exception as e:
            self.logger.error(f"🎮❌ 프로젝트 현황 조회 실패: {str(e)}")
            raise e

    def get_chart_data(self) -> List[Dict[str, Any]]:
        """프로젝트별 사용시간 vs 필요시간 차트 데이터 조회"""
        try:
            usage_data = self.dashboard_service.get_chart_data()
            self.logger.info(f"🎮✅ 프로젝트 시각화 차트 데이터 조회 성공: {len(usage_data)}개")
            return usage_data

        except Exception as e:
            self.logger.error(f"🎮❌ 프로젝트 시각화 차트 데이터 조회 실패: {str(e)}")
            raise e

    def get_timeline_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """기간별 프로젝트 작업시간 추이 데이터 조회"""
        try:
            timeline_data = self.dashboard_service.get_timeline_data(start_date, end_date)
            self.logger.info(f"🎮✅ 작업시간 추이 데이터 조회 성공: {len(timeline_data)}개 레코드")
            return timeline_data

        except Exception as e:
            self.logger.error(f"🎮❌ 작업시간 추이 데이터 조회 실패: {str(e)}")
            raise e