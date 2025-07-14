"""
DashboardService - 완전 구현
Controller에서 호출하는 4개 메서드 구현
"""

from typing import List, Dict, Any
from datetime import date, datetime, timedelta
import logging

from ..services.project_service import ProjectService
from ..services.work_log_service import WorkLogService


class DashboardService:
    """대시보드 서비스 - 비즈니스 로직 및 데이터 처리"""

    def __init__(self):
        self.project_service = ProjectService()
        self.work_log_service = WorkLogService()
        self.logger = logging.getLogger(__name__)

    def get_work_log_summary(self) -> Dict[str, Any]:
        """
        작업로그 요약 데이터 생성
        - 오늘 작업시간 및 전날 대비 증감
        - 이번주 평균 하루 작업시간 및 전주 대비 증감
        - 이번주 총 작업시간

        Returns:
            Dict: {
                'today_hours': float,           # 오늘 작업시간
                'today_delta': float,           # 전날 대비 증감
                'week_avg_hours': float,        # 이번주 평균 하루 작업시간
                'week_avg_delta': float,        # 전주 대비 증감
                'week_total_hours': float       # 이번주 총 작업시간
            }
        """
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)

            # 1: today_hours 계산
            today_logs = self.work_log_service.get_today_work_data()
            today_hours = sum(log['작업시간'] for log in today_logs)

            # 2: today_delta 계산
            yesterday_logs = self.work_log_service.get_past_work_data(yesterday, yesterday)
            yesterday_hours = sum(log['작업시간'] for log in yesterday_logs)
            today_delta = today_hours - yesterday_hours

            # 3: week_avg_hours 계산
            days_since_monday = today.weekday()
            this_week_start = today - timedelta(days=days_since_monday)
            this_week_end = today

            this_week_logs = self.work_log_service.get_past_work_data(this_week_start, this_week_end)
            week_total_hours = sum(log['작업시간'] for log in this_week_logs)

            week_avg_hours = week_total_hours / (days_since_monday + 1)

            # 4: week_avg_delta 계산
            last_week_start = this_week_start - timedelta(days=7)
            last_week_end = this_week_start - timedelta(days=1)

            last_week_logs = self.work_log_service.get_past_work_data(last_week_start, last_week_end)
            last_week_total_hours = sum(log['작업시간'] for log in last_week_logs)

            last_week_avg_hours = last_week_total_hours / ((last_week_end - last_week_start).days + 1)
            week_avg_delta = week_avg_hours - last_week_avg_hours

            return {
                'today_hours': today_hours,
                'today_delta': today_delta,
                'week_avg_hours': week_avg_hours,
                'week_avg_delta': week_avg_delta,
                'week_total_hours': week_total_hours
            }

        except Exception as e:
            raise Exception(f"⚙️❌ 작업로그 요약 데이터 생성 실패: {str(e)}")

    def get_projects_summary(self) -> List[Dict[str, Any]]:
        """
        프로젝트 현황 테이블 데이터 생성

        Returns:
            List[Dict]: [
                {
                    'project_id': int,
                    '프로젝트명': str,
                    'D-Day': str,
                    '목표치': int,
                    '현재값': int,
                    '진행률': str,          # "75.0%"
                    '작업시간': float,   # "10.0"
                    '필요시간': str,        # "40.0h" 또는 "None"
                    '예상 마감일': date     # 예상 완료 날짜 또는 None
                }
            ]
        """
        try:
            # 1: 활성 프로젝트 조회 (Project Service 매서드)
            active_projects = self.project_service.get_active_projects()

            if not active_projects:
                return []

            # 2: 모든 프로젝트의 효율성 통계를 한 번에 조회 (Work Log Service 메서드)
            project_ids = [p['id'] for p in active_projects]
            efficiency_stats = self.work_log_service.get_efficiency_stats_for_projects(project_ids)

            # 3: 프로젝트별 예측 계산
            today = date.today()
            result = []

            for project in active_projects:
                # 3-1: 기본 프로젝트 정보
                project_id = project['id']
                project_name = project['name']
                project_d_day = project['d_day_display']
                target_value = project['target_value']
                current_progress = project['current_progress']

                # 3-2: 진행률 계산
                remaining_work = max(0, target_value - current_progress)
                progress_rate = (current_progress / target_value * 100) if target_value > 0 else 0
                progress_percentage = f"{progress_rate:.1f}%"  # 진행률 포맷팅

                # 3-3: 효율성 통계 가져오기
                stats = efficiency_stats.get(project_id, {})
                avg_efficiency = stats.get('avg_efficiency', 0)
                worked_hours = stats.get('worked_hours', 0)
                avg_hours_per_day = stats.get('avg_hours_per_day', 0)

                # 3-4: 예상 필요시간 계산 (남은 작업량 / 평균 효율성)
                if avg_efficiency > 0 and remaining_work > 0:
                    estimated_hours = remaining_work / avg_efficiency
                    required_hours = f"{estimated_hours:.1f}h"

                    # 3-5: 예상 마감일 계산 (남은 작업량 / 평균 하루 작업시간)
                    if avg_hours_per_day > 0:
                        estimated_days = estimated_hours / avg_hours_per_day
                        estimated_completion_date = today + timedelta(days=int(estimated_days))
                    else:
                        estimated_completion_date = None

                # 이미 완료된 경우
                elif remaining_work == 0:
                    required_hours = "0h"
                    estimated_completion_date = today
                # 효율성 데이터가 없는 경우
                else:
                    required_hours = None
                    estimated_completion_date = None

                # 4: 결과 딕셔너리 생성
                project_summary = {
                    'project_id': project_id,
                    '프로젝트명': project_name,
                    'D-Day': project_d_day,
                    '목표치': target_value,
                    '현재값': current_progress,
                    '진행률': progress_percentage,
                    '작업시간' : worked_hours,
                    '필요시간': required_hours,
                    '예상 마감일': estimated_completion_date
                }

                result.append(project_summary)

            return result

        except Exception as e:
            raise Exception(f"⚙️❌ 프로젝트 현황 조회 실패: {str(e)}")

    def get_chart_data(self) -> List[Dict[str, Any]]:
        """
        프로젝트별 사용시간 vs 필요시간 비교 데이터

        Returns:
            List[Dict]: [
                {
                    '프로젝트명': str,
                    '작업시간': float,         # 현재까지 투입한 총 시간
                    '필요시간': float          # 앞으로 필요한 시간
                }
            ]
        """
        try:
            # 1: 프로젝트 현황 데이터 재사용
            projects_summary = self.get_projects_summary()

            if not projects_summary:
                return []

            result = []
            for project in projects_summary:
                # 2: 필요시간에서 숫자만 추출
                required_hours_str = project['필요시간']
                if required_hours_str == None:
                    required_hours = 0
                else:
                    required_hours = float(required_hours_str.replace('h', ''))

                # 3: 결과 딕셔너리 생성
                result.append({
                    '프로젝트명': project['프로젝트명'],
                    '작업시간': project['작업시간'],
                    '필요시간': float(required_hours)
                })

            return result

        except Exception as e:
            raise Exception(f"⚙️❌ 프로젝트 시각화 차트 데이터 조회 실패: {str(e)}")

    def get_timeline_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        기간별 프로젝트 투입시간 추이 데이터

        Returns:
            List[Dict]: [
                {
                    '날짜': date,              # 작업 날짜
                    '프로젝트명': str,         # 프로젝트 이름
                    '작업시간': float          # 해당일 투입 시간
                }
            ]
        """
        try:
            # 1. 날짜 유효성 검증
            if start_date > end_date:
                raise ValueError("⚙️❌ 시작일이 종료일보다 늦을 수 없습니다")
            if end_date > date.today():
                raise ValueError("⚙️❌ 미래 날짜는 조회할 수 없습니다")

            # 2. Work Log Service를 통한 기간별 작업 로그 조회
            work_logs = self.work_log_service.get_past_work_data(start_date, end_date)

            # 3. 차트용 데이터 구조로 변환
            result = []
            for log in work_logs:
                timeline_entry = {
                    '날짜': log['work_date'],
                    '프로젝트명': log['프로젝트명'],    # get_past_work_data에서 이미 변환됨
                    '작업시간': log['작업시간']        # get_past_work_data에서 이미 변환됨
                }
                result.append(timeline_entry)

            # 4. 날짜순 정렬 (오래된 날짜부터)
            result.sort(key=lambda x: x['날짜'])

            return result

        except ValueError as e:
            # 날짜 유효성 에러는 그대로 전파
            raise e
        except Exception as e:
            raise Exception(f"⚙️❌ 타임라인 데이터 조회 실패: {str(e)}")