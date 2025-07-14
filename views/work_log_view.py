import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any

from controllers.work_log_controller import WorkLogController


class WorkLogView:
    def __init__(self):
        from config import get_logger
        self.logger = get_logger(__name__)

        # TODO: 실제 컨트롤러 연결 필요
        self.controller = WorkLogController()

    def render(self):
        """작업 로그 페이지 메인 렌더링"""
        st.title("✏️ 작업 로그")
        st.markdown("---")

        # 1: 토스트 메시지 관리
        if hasattr(st.session_state, 'work_save_toast'):
            st.toast(st.session_state.work_save_toast)
            del st.session_state.work_save_toast

        if hasattr(st.session_state, 'work_error_toast'):
            st.toast(st.session_state.work_error_toast)
            del st.session_state.work_error_toast

        # +: 다른 페이지 변경 감지 및 캐시 무효화
        self._check_auto_refresh()

        # 2: 컴포넌트 렌더링
        self._render_today_work_section()
        self._render_past_work_section()

    def _check_auto_refresh(self):
        """
        다른 페이지에서의 변경사항 자동 감지 및 캐시 무효화

        동작 방식:
        1. st.session_state에서 변경 플래그 확인
        2. 플래그가 있으면 관련 캐시 삭제
        3. 플래그 삭제 (중복 처리 방지)
        4. 사용자에게 갱신 알림
        """
        # +: Project 변경 감지
        if hasattr(st.session_state, 'project_updated_work_log'):
            self._clear_all_work_log_cash()
            del st.session_state.project_updated_work_log
            st.session_state.dashboard_success_toast = "✅ Project 변경으로 작업로그가 갱신되었습니다!"

    def _render_today_work_section(self):
        """상단: 작업 기록 섹션"""
        try:
            st.header("금일 작업 로그")

            # 1: 오늘 날짜 표시
            today = date.today()
            weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][today.weekday()]
            st.markdown(f"📅 : {today.strftime('%Y-%m-%d')} ({weekday_kr})")

            # 2: 캐싱된 오늘 데이터 로드
            cache_key = f'today_work_data_{today.strftime("%Y-%m-%d")}'
            if cache_key not in st.session_state:
                today_work_data = self.controller.get_today_work_data()
                st.session_state[cache_key] = today_work_data
            else:
                today_work_data = st.session_state[cache_key]

            if today_work_data:
                # 3: 데이터프레임 생성
                df = pd.DataFrame(today_work_data)
                edited_df = st.data_editor(
                    df,
                    disabled=["project_id", "work_date", "프로젝트명", "D-Day", "목표치", "현재값"],
                    column_config={
                        "project_id": None,
                        "work_date": None,
                        "프로젝트명": st.column_config.TextColumn(width="medium"),
                        "D-Day": st.column_config.TextColumn(width="small"),
                        "목표치": st.column_config.NumberColumn(width="small"),
                        "현재값": st.column_config.NumberColumn(width="small"),
                        "진행량": st.column_config.NumberColumn(min_value=0, step=1, width="small"),
                        "작업시간": st.column_config.NumberColumn(min_value=0.0, step=0.5, format="%.1f", width="small"),
                        "메모": st.column_config.TextColumn(max_chars=100, width="large")
                    },
                    use_container_width=True,
                    hide_index=True,
                    key="today_work_editor"
                )

                # 4: 데이터 변경 감지 및 저장 버튼
                self._render_save_section(df, edited_df, "today")

            else:
                st.info("작업 기록이 없습니다. 진행 중인 프로젝트가 있는지 확인해주세요.")

            self.logger.debug("✅ 작업 기록 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 작업 기록 섹션 렌더링 실패: {str(e)}")
            st.error("작업 기록를 불러오는데 실패했습니다.")

    def _render_past_work_section(self):
        """하단: 지난 작업로그 섹션"""
        try:
            st.markdown("---")
            st.header("지난 작업 로그")

            col1, col2 = st.columns([3, 1])

            with col1:
                period_options = {
                    "최근 7일": 7,
                    "최근 14일": 14,
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
                        value=date.today() - timedelta(days=7),
                        key="past_start_date"
                    )
                with col_end:
                    end_date = st.date_input(
                        "종료일",
                        value=date.today() - timedelta(days=1),  # 어제까지
                        key="past_end_date"
                    )
            else:
                days = period_options[selected_period]
                end_date = date.today() - timedelta(days=1)  # 어제까지
                start_date = end_date - timedelta(days=days-1)

            with col2:
                search_button = st.button("🔍 조회", type="secondary", use_container_width=True)

            # 2: 과거 작업 데이터 가져오기
            if search_button or 'past_work_data' not in st.session_state:
                past_work_data = self.controller.get_past_work_data(start_date, end_date)
                st.session_state.past_work_data = past_work_data    # 세션 상태에 저장
            else:
                past_work_data = st.session_state.past_work_data    # 캐시에서 빠른 로드

            if past_work_data:
                # 3: 데이터프레임 생성
                past_df = pd.DataFrame(past_work_data)
                edited_past_df = st.data_editor(
                    past_df,
                    disabled=["project_id","work_date", "날짜", "프로젝트명"],
                    column_config={
                        "project_id": None,
                        "work_date": None,
                        "날짜": st.column_config.TextColumn(width="small"),
                        "프로젝트명": st.column_config.TextColumn(width="medium"),
                        "진행량": st.column_config.NumberColumn(min_value=0, step=1, width="small"),
                        "작업시간": st.column_config.NumberColumn(min_value=0.0, step=0.5, format="%.1f", width="small"),
                        "메모": st.column_config.TextColumn(max_chars=100, width="large")
                    },
                    use_container_width=True,
                    hide_index=True,
                    key="past_work_editor"
                )

                # 4: 데이터 변경 감지 및 저장 버튼
                self._render_save_section(past_df, edited_past_df, "past")

                # 5: 기간 요약
                self._render_period_summary(past_work_data)

            else:
                st.info(f"📝 선택한 기간에 작업 기록이 없습니다.")

            self.logger.debug("✅ 지난 작업로그 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 지난 작업로그 섹션 렌더링 실패: {str(e)}")
            st.error("지난 작업로그를 불러오는데 실패했습니다.")

    def _render_period_summary(self, past_work_data: List[Dict]):
        """선택 기간 요약 표시"""
        st.markdown("### 📈 요약")

        # 1: 요약 계산
        total_days = len(set(item['날짜'] for item in past_work_data))
        total_hours = sum(item['작업시간'] for item in past_work_data)
        total_projects = len(set(item['프로젝트명'] for item in past_work_data))

        # 2: 메트릭 표시
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("총 작업일수", f"{total_days}일")

        with col2:
            st.metric("총 작업시간", f"{total_hours:.1f}시간")

        with col3:
            st.metric("작업한 프로젝트", f"{total_projects}개")

    def _render_save_section(self, original_df: pd.DataFrame, edited_df: pd.DataFrame, update_type: str):
        """통합된 저장 섹션 렌더링"""
        # 1: 변경 감지 및 저장 버튼
        col1, col2, col3 = st.columns([2, 1, 1])

        with col2:
            changes_detected = not original_df.equals(edited_df)
            if changes_detected:
                st.warning("변경사항이 감지되었습니다!")

        with col3:
            save_button = st.button(
                "💾 변경사항 저장",
                type="primary" if changes_detected else "secondary",
                disabled=not changes_detected,
                use_container_width=True,
                key=f"save_{update_type}_work"
            )

        # 2: 저장 처리
        if save_button and changes_detected:
            self._handle_work_log_update(original_df, edited_df, update_type)

    # ===== 이벤트 핸들러들 =====
    def _handle_work_log_update(self, original_df: pd.DataFrame, edited_df: pd.DataFrame, update_type: str):
        """통합된 작업 로그 업데이트 핸들러"""
        try:
            # 1: 변경된 행들 찾기
            changes = []
            for idx, (orig_row, edit_row) in enumerate(zip(original_df.itertuples(), edited_df.itertuples())):
                # 편집 가능한 3개 열 비교
                if (orig_row.진행량 != edit_row.진행량 or
                    orig_row.작업시간 != edit_row.작업시간 or
                    orig_row.메모 != edit_row.메모):

                    # work_date가 이미 테이블에 포함됨
                    changes.append({
                        'project_id': edit_row.project_id,
                        'work_date': edit_row.work_date,
                        'progress_added': edit_row.진행량,
                        'hours_spent': edit_row.작업시간,
                        'memo': edit_row.메모
                    })

            # 2: 컨트롤러 호출
            if changes:
                with st.spinner(f"{len(changes)}개 작업 로그 저장 중..."):
                    updated_count = self.controller.update_work_logs(changes)  # 통합 메서드

                # 3: 캐시 무효화
                if update_type == "today":
                    self._clear_today_work_log_cash()
                else:
                    self._clear_past_work_log_cash()

                # +: dashboard에 영향
                st.session_state.work_log_updated = True

                # 4: 성공 메시지
                st.session_state.work_save_toast = f"✅ {updated_count}개 작업 로그가 저장되었습니다!"
                st.rerun()
            else:
                st.info("변경된 내용이 없습니다.")

        except Exception as e:
            st.session_state.work_error_toast = f"❌ 작업 로그 저장 실패: {str(e)}"
            st.rerun()

    def _clear_today_work_log_cash(self):
        """오늘 작업 로그 캐시 무효화"""
        today_key = f'today_work_data_{date.today().strftime("%Y-%m-%d")}'
        if today_key in st.session_state:
            del st.session_state[today_key]

    def _clear_past_work_log_cash(self):
        """과거 작업 로그 캐시 무효화"""
        if 'past_work_data' in st.session_state:
            del st.session_state['past_work_data']

    def _clear_all_work_log_cash(self):
        """모든 작업 로그 캐시 무효화"""
        self._clear_today_work_log_cash()
        self._clear_past_work_log_cash()