"""
대시보드 뷰 (Placeholder)
전체 프로젝트 진행 상황을 보여주는 대시보드
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import date, timedelta


class DashboardView:
    """대시보드 페이지 뷰"""

    def __init__(self):
        # 1: 로깅 설정
        from config import get_logger
        self.logger = get_logger(__name__)
        # TODO: 실제 컨트롤러 연결
        pass

    def render(self):
        """대시보드 페이지 렌더링"""
        st.title("📈 대시보드")
        st.markdown("전체 프로젝트 진행 상황과 분석")

        # 요약 메트릭
        self._render_summary_metrics()

        # 차트 섹션
        col1, col2 = st.columns(2)

        with col1:
            self._render_progress_chart()

        with col2:
            self._render_timeline_chart()

        # 최근 활동
        self._render_recent_activity()

    def _render_summary_metrics(self):
        """요약 메트릭 표시"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("총 프로젝트", "5개", delta="1개 신규")

        with col2:
            st.metric("진행 중", "2개", delta="활발함")

        with col3:
            st.metric("평균 진행률", "47.6%", delta="5.2%")

        with col4:
            st.metric("이번 주 작업", "15시간", delta="3시간")

    def _render_progress_chart(self):
        """진행률 차트"""
        st.subheader("📊 프로젝트별 진행률")

        # 임시 데이터
        data = {
            'Project': ['블로그 포스팅', 'Python 강의', '영어 공부', '운동 루틴', '독서 챌린지'],
            'Progress': [46, 67, 0, 25, 100]
        }

        df = pd.DataFrame(data)
        fig = px.bar(df, x='Project', y='Progress',
                     title="프로젝트별 진행률",
                     color='Progress',
                     color_continuous_scale='Viridis')

        st.plotly_chart(fig, use_container_width=True)

    def _render_timeline_chart(self):
        """타임라인 차트"""
        st.subheader("📅 프로젝트 타임라인")

        # 임시 간트 차트 데이터
        data = {
            'Project': ['블로그 포스팅', 'Python 강의', '영어 공부'],
            'Start': [date(2025, 6, 1), date(2025, 6, 10), date(2025, 7, 1)],
            'End': [date(2025, 7, 15), date(2025, 7, 5), date(2025, 8, 30)],
            'Status': ['진행 중', '진행 중', '시작 안 함']
        }

        df = pd.DataFrame(data)
        fig = px.timeline(df, x_start='Start', x_end='End', y='Project',
                         color='Status', title="프로젝트 타임라인")

        st.plotly_chart(fig, use_container_width=True)

    def _render_recent_activity(self):
        """최근 활동"""
        st.subheader("🕒 최근 활동")

        # 임시 활동 데이터
        activities = [
            {"time": "2시간 전", "action": "블로그 포스팅", "detail": "3페이지 작성"},
            {"time": "어제", "action": "Python 강의", "detail": "2강 수강 완료"},
            {"time": "3일 전", "action": "독서 챌린지", "detail": "프로젝트 완료!"},
        ]

        for activity in activities:
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.caption(activity["time"])
                with col2:
                    st.write(f"**{activity['action']}** - {activity['detail']}")
                st.divider()
