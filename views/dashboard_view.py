import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any

from controllers.dashboard_controller import DashboardController


class DashboardView:
    def __init__(self):
        from config import get_logger
        self.logger = get_logger(__name__)
        self.controller = DashboardController()

    # ===== 초기 변경값 확인 =====
    def render(self):
        # 페이지 제목 및 설명
        st.title("📈 대시보드")

        # 1: 토스트 메시지 처리
        self._handle_toast_messages()

        # 2: 다른 페이지 변경 감지 및 캐시 무효화
        self._check_auto_refresh()

        # 3: 새로고침 버튼
        self._render_refresh_button()

        # 4: UI 섹션들 렌더링 (캐시 기반)
        self._render_work_log_summary()
        self._render_projects_table()
        self._render_projects_chart()
        self._render_timeline_section()

        # 5: 렌더링 완료 로그
        self.logger.debug("✅ 대시보드 전체 렌더링 완료")

    def _handle_toast_messages(self):
        """렌더링 결과 처리"""
        # 1: 성공 토스트
        if hasattr(st.session_state, 'dashboard_success_toast'):
            st.toast(st.session_state.dashboard_success_toast)
            del st.session_state.dashboard_success_toast

        # 2: 에러 토스트
        if hasattr(st.session_state, 'dashboard_error_toast'):
            st.toast(st.session_state.dashboard_error_toast)
            del st.session_state.dashboard_error_toast

    def _check_auto_refresh(self):
        """
        다른 페이지에서의 변경사항 자동 감지 및 캐시 무효화

        동작 방식:
        1. st.session_state에서 변경 플래그 확인
        2. 플래그가 있으면 관련 캐시 삭제
        3. 플래그 삭제 (중복 처리 방지)
        4. 사용자에게 갱신 알림
        """
        # 1: WorkLog 변경 감지
        if hasattr(st.session_state, 'work_log_updated_dash'):
            self._clear_worklog_affected_cache()
            del st.session_state.work_log_updated_dash

        # 2: Project 변경 감지
        if hasattr(st.session_state, 'project_updated_dash'):
            self._clear_project_affected_cache()
            del st.session_state.project_updated_dash

    def _render_refresh_button(self):
        """전체 새로고침 버튼 렌더링"""
        try:
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 대시보드 최신화", type="primary", use_container_width=True):
                    self._handle_refresh_button()

                self.logger.debug("✅ 대시보드 최신화 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 대시보드 최신화 섹션 렌더링 실패: {str(e)}")
            st.error("대시보드 최신화 섹션을 불러오는데 실패했습니다.")

    # ===== UI 섹션 메서드들 (메서드명만 정의) =====
    def _render_work_log_summary(self):
        """
        작업로그 요약 렌더링
        - 오늘 작업시간 (전날 대비 delta)
        - 이번주 평균 하루 작업시간 (전주 대비 delta)
        - 이번주 총 작업시간
        캐시: dashboard_work_logs_YYYY-MM-DD
        """
        try:
            st.header("작업 요약")

            # 1: 캐시 키 생성
            today = date.today()
            cache_key = f'dashboard_work_logs_{today.strftime("%Y-%m-%d")}'

            # 2: 캐싱된 데이터 로드
            if cache_key not in st.session_state:
                summary = self.controller.get_work_log_summary()
                st.session_state[cache_key] = summary
            else:
                summary = st.session_state[cache_key]

            # 3: UI 렌더링
            if not summary:
                st.warning("요약 데이터가 없습니다.")
                return

            col1, col2, col3 = st.columns(3)

            with col1:
                # 3-1: 금일 작업시간
                today_delta = summary.get('today_delta', 0)
                delta_str = f"{today_delta:+.1f}시간" if today_delta != 0 else None

                st.metric(
                    label="금일 작업시간",
                    value=f"{summary.get('today_hours', 0):.1f}시간",
                    delta=delta_str,
                )

            with col2:
                # 3-2: 이번주 일 평균 작업시간
                week_avg_delta = summary.get('week_avg_delta', 0)
                delta_str = f"{week_avg_delta:+.1f}시간" if week_avg_delta != 0 else None

                st.metric(
                    label="이번주 일 평균 작업시간",
                    value=f"{summary.get('week_avg_hours', 0):.1f}시간",
                    delta=delta_str,
                )

            with col3:
                # 3-3: 이번주 총 작업시간
                st.metric(
                    label="이번주 총 작업시간",
                    value=f"{summary.get('week_total_hours', 0):.1f}시간",
                    help="이번주 누적 총 작업시간"
                )
            self.logger.debug("✅ 작업로그 요약 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 작업로그 요약 섹션 렌더링 실패: {str(e)}")
            st.error("작업로그 요약을 불러오는데 실패했습니다.")

    def _render_projects_table(self):
        """
        프로젝트 현황 테이블 렌더링
        - project_id, 프로젝트명, D-Day, 목표치, 현재값, 진행도, 작업시간, 필요시간, 예상 마감일

        캐시: dashboard_projects_YYYY-MM-DD
        """
        try:
            st.markdown("---")
            st.header("프로젝트 현황")

            # 1: 캐시 키 생성
            today = date.today()
            cache_key = f'dashboard_projects_{today.strftime("%Y-%m-%d")}'

            # 2: 캐싱된 데이터 로드
            if cache_key not in st.session_state:
                projects_data = self.controller.get_projects_summary()
                st.session_state[cache_key] = projects_data
            else:
                projects_data = st.session_state[cache_key]

            # 3: UI 렌더링
            if not projects_data:
                st.info("진행 중인 프로젝트가 없습니다.")
                return

            # 프로젝트 테이블 표시
            df = pd.DataFrame(projects_data)
            st.dataframe(
                df,
                column_config={
                    "project_id": None,
                    "프로젝트명": st.column_config.TextColumn(width="medium"),
                    "D-Day": st.column_config.TextColumn(width="small"),
                    "목표치": st.column_config.TextColumn(width="small"),
                    "현재값": st.column_config.TextColumn(width="small"),
                    "진행도": st.column_config.NumberColumn(min_value=0, max_value=100, step=0.1, format="%.1f%%", width="small"),
                    "작업시간" : None,
                    "필요시간": st.column_config.TextColumn(width="small"),
                    "예상 마감일": st.column_config.DateColumn(format="YYYY-MM-DD", width="large")
                },
                use_container_width=True,
                hide_index=True
            )

            self.logger.debug("✅ 프로젝트 현황 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 프로젝트 현황 섹션 렌더링 실패: {str(e)}")
            st.error("프로젝트 현황을 불러오는데 실패했습니다.")

    def _render_projects_chart(self):
        """
        프로젝트별 사용시간 vs 예상시간 막대차트 렌더링
        - Plotly 막대차트 (누적형)
        - X축: 프로젝트명, Y축: 시간
        - 하단: 사용시간, 상단: 필요시간

        캐시: dashboard_chart_YYYY-MM-DD
        """
        try:
            st.markdown("---")
            st.subheader("프로젝트 현황 시각화")

            # 1: 캐시 키 생성
            today = date.today()
            cache_key = f'dashboard_chart_{today.strftime("%Y-%m-%d")}'

            # 2: 캐싱된 데이터 로드
            if cache_key not in st.session_state:
                chart_data = self.controller.get_chart_data()
                st.session_state[cache_key] = chart_data
            else:
                chart_data = st.session_state[cache_key]


            # 3: UI 렌더링
            if not chart_data:
                st.info("차트 데이터가 없습니다.")
                return

            # 데이터프레임 생성
            df = pd.DataFrame(chart_data)

            # Plotly 누적 막대차트 생성
            fig = px.bar(
                df,
                x='프로젝트명',
                y=['작업시간', '필요시간'],
                title="프로젝트별 작업시간 vs 필요시간",
                labels={
                    'value': '시간 (h)',
                    'variable': '구분',
                    '프로젝트명': '프로젝트'
                },
                color_discrete_map={
                    '작업시간': '#3498db',      # 파란색 (하단)
                    '필요시간': '#e67e22'       # 주황색 (상단)
                }
            )

            # 누적형으로 변경 (하단: 작업시간, 상단: 필요시간)
            fig.update_layout(
                barmode='stack',  # 누적형 막대차트
                xaxis_title="프로젝트",
                yaxis_title="시간 (h)",
                legend_title="구분",
                hovermode='x unified',
                height=500
            )

            # 차트 표시
            st.plotly_chart(fig, use_container_width=True)

            self.logger.debug("✅ 차트 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 차트 섹션 렌더링 실패: {str(e)}")
            st.error("차트 데이터를 불러오는데 실패했습니다.")

    def _render_timeline_section(self):
        """
        기간별 투입시간 추이 섹션 렌더링 (수동 로딩)
        - 기간 선택 (7일/15일/30일/사용자지정)
        - 조회 버튼
        - Plotly 선차트

        캐시: timeline_data
        """
        try:
            st.markdown("---")
            st.subheader("기간별 작업시간 추이")

            col1, col2 = st.columns([3, 1])

            with col1:
                period_options = {
                    "최근 7일": 7,
                    "최근 15일": 15,
                    "최근 30일": 30,
                    "사용자 지정": "custom"
                }
                selected_period = st.selectbox(
                    "📅 기간 선택",
                    options=list(period_options.keys()),
                    index=0,
                    label_visibility="collapsed"  # 라벨 숨김
                )

            # 1: 사용자 지정 날짜 선택
            if selected_period == "사용자 지정":
                col_start, col_end = st.columns(2)
                with col_start:
                    start_date = st.date_input(
                        "시작일",
                        value=date.today() - timedelta(days=date.today().weekday()),  # 이번 주 월요일부터
                        key="timeline_start_date"
                    )
                with col_end:
                    end_date = st.date_input(
                        "종료일",
                        value=date.today(),             # 오늘까지
                        key="timeline_end_date"
                    )
                days = (end_date - start_date).days + 1

            else:
                days = period_options[selected_period]
                end_date = date.today()
                start_date = end_date - timedelta(days=days-1)

            with col2:
                search_button = st.button("🔍 조회", type="primary", use_container_width=True)

            # 2: 타임라인 데이터 가져오기
            if search_button:
                timeline_data = self.controller.get_timeline_data(start_date, end_date)
                st.session_state.timeline_data = timeline_data              # 세션 상태에 저장
            else:
                timeline_data = st.session_state.get('timeline_data')       # 캐시에서 빠른 로드

            # 3: UI 렌더링 (데이터가 있을 때만)
            if timeline_data:
                if not timeline_data:
                    st.info("선택한 기간에 데이터가 없습니다.")
                    return

                # 데이터프레임 생성
                df = pd.DataFrame(timeline_data)

                # Plotly 선 그래프 생성
                fig = px.line(
                    df,
                    x='날짜',
                    y='작업시간',
                    color='프로젝트명',
                    title=f"최근 {days}일간 프로젝트별 일일 작업시간",
                    markers=True,
                    labels={
                        '작업시간': '작업시간 (h)',
                        '날짜': '날짜',
                        '프로젝트명': '프로젝트'
                    }
                )

                # 차트 레이아웃 설정
                fig.update_layout(
                    xaxis_title="날짜",
                    yaxis_title="작업시간 (h)",
                    legend_title="프로젝트",
                    hovermode='x unified',
                    height=500
                )

                # X축 날짜 형식 설정
                fig.update_xaxes(tickformat='%m-%d')

                # 차트 표시
                st.plotly_chart(fig, use_container_width=True)

                # 타임라인 요약 정보
                worked_hours = sum(item['작업시간'] for item in timeline_data)
                avg_hours_per_day = worked_hours / days
                worked_projects = len(set(item['프로젝트명'] for item in timeline_data if item['작업시간'] > 0))

                st.markdown(f"### 📊 최근 {days}일 요약")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("작업한 프로젝트", f"{worked_projects}개")
                with col2:
                    st.metric("평균 일일 작업시간", f"{avg_hours_per_day:.1f}h")
                with col3:
                    st.metric("총 작업시간", f"{worked_hours:.1f}h")

                # 데이터 로드 시간 표시
                st.caption(f"📅 데이터 로드 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            else:
                st.info("기간을 선택하고 '조회' 버튼을 클릭하세요.")

            self.logger.debug("✅ 타임라인 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 타임라인 섹션 렌더링 실패: {str(e)}")
            st.error("타임라인 섹션을 불러오는데 실패했습니다.")

    # ===== 이벤트 핸들러 =====
    def _handle_refresh_button(self):
        """
        전체 새로고침 버튼 클릭시 처리
        - 모든 캐시 삭제
        - 새로고침 완료 메시지 표시
        """
        try:
            # 1: 모든 대시보드 캐시 삭제
            self._clear_all_dashboard_cache()

            # 2: 새로고침 완료 메시지 표시
            st.session_state.dashboard_success_toast = "✅ 대시보드 새로고침 완료"

        except Exception as e:
            st.session_state.dashboard_error_toast = f"❌ 대시보드 새로고침 실패: {str(e)}"

    # ===== 캐시 관리 메서드들 (메서드명만 정의) =====
    def _clear_worklog_affected_cache(self):
        """
        WorkLog 변경시 영향받는 캐시 삭제
        삭제 대상: summary, projects, charts (3개)
        이유: 작업시간 변경 → 모든 통계에 영향
        """
        today = date.today().strftime("%Y-%m-%d")
        keys_to_remove = [
            f'dashboard_work_logs_{today}',
            f'dashboard_projects_{today}',
            f'dashboard_chart_{today}'
        ]

        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]

    def _clear_project_affected_cache(self):
        """
        Project 변경시 영향받는 캐시 삭제
        삭제 대상: projects, charts (2개)
        유지 대상: summary (실제 작업시간은 변하지 않음)
        """
        today = date.today().strftime("%Y-%m-%d")
        keys_to_remove = [
            f'dashboard_projects_{today}',
            f'dashboard_chart_{today}'
        ]

        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]

    def _clear_all_dashboard_cache(self):
        """
        모든 대시보드 캐시 삭제
        삭제 대상: dashboard_로 시작하는 모든 세션 키 + timeline_data
        용도: 전체 새로고침 버튼 클릭시
        """
        keys_to_remove = []

        # dashboard_로 시작하는 모든 키 찾기
        for key in list(st.session_state.keys()):
            if key.startswith('dashboard_'):
                keys_to_remove.append(key)

        # 타임라인 데이터도 삭제
        if 'timeline_data' in st.session_state:
            keys_to_remove.append('timeline_data')

        # 캐시 삭제
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]