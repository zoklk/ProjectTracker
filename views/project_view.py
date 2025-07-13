import streamlit as st
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Any

from controllers.project_controller import ProjectController
from models.entities.project import Project


class ProjectView:
    def __init__(self):
        """프로젝트 관리 페이지 초기화"""
        from config import get_logger
        self.logger = get_logger(__name__)
        self.controller = ProjectController()

    def render(self):
        """프로젝트 관리 페이지 렌더링"""
        st.title("📋 프로젝트 관리")

        # 1: 토스트 메세지 관리
        # (동기화 성공)
        if hasattr(st.session_state, 'sync_toast'):
            st.toast(st.session_state.sync_toast)
            del st.session_state.sync_toast

        # (에러)
        if hasattr(st.session_state, 'error_toast'):
            st.toast(st.session_state.error_toast)
            del st.session_state.error_toast

        # (업데이트 성공)
        if hasattr(st.session_state, 'update_toast'):
            st.toast(st.session_state.update_toast)
            del st.session_state.update_toast

        # 2: 컴포넌트 랜더링
        self._render_sync_section()
        self._render_active_projects()
        self._render_archived_projects()

    # ===== UI 컴포넌트 렌더링 메서드들 =====
    def _render_sync_section(self):
        """노션 동기화 섹션 - UI 렌더링만 담당"""
        try:
            col1, col2 = st.columns([3, 1])

            with col2:
                if st.button("🔄 노션과 동기화", type="primary", use_container_width=True):
                    self._handle_sync_button()

            self.logger.debug("✅ 동기화 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 동기화 섹션 렌더링 실패: {str(e)}")
            st.error("동기화 섹션을 불러오는데 실패했습니다.")

    def _render_active_projects(self):
        """진행 중 프로젝트 목록 섹션"""
        try:
            st.markdown("---")
            st.header("진행 중 프로젝트")

            # 1: 진행 중 프로젝트 데이터 캐싱
            cache_key = 'active_projects'
            if cache_key not in st.session_state:
                active_projects = self.controller.get_active_projects()
                st.session_state[cache_key] = active_projects
            else:
                active_projects = st.session_state[cache_key]

            if active_projects:
                # 2: 테이블 데이터 준비
                table_data = []
                for project in active_projects:
                    table_data.append({
                        "ID": project["id"],
                        "프로젝트명": project["name"],
                        "시작날짜": str(project["start_date"]),
                        "종료날짜": str(project["end_date"]),
                        "D-day": project["d_day_display"],
                        "초기값": project["initial_progress"],    # 편집 가능
                        "현재값": project["current_progress"],    # 읽기 전용 (계산값)
                        "목표치": project["target_value"]         # 편집 가능
                    })

                # 3: 데이터프레임 생성
                df = pd.DataFrame(table_data)
                edited_df = st.data_editor(
                    df,
                    disabled=["ID", "프로젝트명", "시작날짜", "종료날짜", "D-day", "현재값"],
                    column_config={
                        "초기값": st.column_config.NumberColumn(min_value=0, step=1),
                        "목표치": st.column_config.NumberColumn(min_value=1, step=1)
                    },
                    use_container_width=True,
                    hide_index=True,
                    key="active_projects_editor"
                )

                # 4: 데이터 변경 감지 및 저장 버튼
                col1, col2, col3 = st.columns([2, 1, 1])
                with col2:
                    changes_detected = not df.equals(edited_df)
                    if changes_detected:
                        st.warning("변경사항이 감지되었습니다!")

                with col3:
                    save_button = st.button(
                        "💾 변경사항 저장",
                        type="primary" if changes_detected else "secondary",
                        disabled=not changes_detected,
                        use_container_width=True,
                        key="save_active_projects"
                    )

                # 5: 저장 버튼 처리
                if save_button and changes_detected:
                    self._handle_bulk_project_update(df, edited_df)

            else:
                st.info("진행 중인 프로젝트가 없습니다.")

            self.logger.debug("✅ 진행 중 프로젝트 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 진행 중 프로젝트 섹션 렌더링 실패: {str(e)}")
            st.error("진행 중 프로젝트를 불러오는데 실패했습니다.")

    def _render_archived_projects(self):
        """아카이브 프로젝트 목록 섹션"""
        try:
            st.markdown("---")
            st.header("아카이브")

            # 1: 아카이브 프로젝트 데이터 캐싱
            cache_key = 'archived_projects'
            if cache_key not in st.session_state:
                archived_projects = self.controller.get_archived_projects()
                st.session_state[cache_key] = archived_projects
            else:
                archived_projects = st.session_state[cache_key]

            if archived_projects:
                # 2: 테이블 데이터 준비
                table_data = []
                for project in archived_projects:
                    table_data.append({
                        "ID": project["id"],
                        "프로젝트명": project["name"],
                        "시작날짜": str(project["start_date"]),
                        "종료날짜": str(project["end_date"]),
                        "D-day": project["d_day_display"],
                        "초기값": project["initial_progress"],
                        "현재값": project["current_progress"],    # 계산값
                        "목표치": project["target_value"]
                    })

                # 3: 데이터프레임 생성 (읽기 전용)
                df = pd.DataFrame(table_data)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:
                st.info("아카이브된 프로젝트가 없습니다.")

            self.logger.debug("✅ 아카이브 섹션 렌더링 성공")

        except Exception as e:
            self.logger.error(f"❌ 아카이브 섹션 렌더링 실패: {str(e)}")
            st.error("아카이브를 불러오는데 실패했습니다.")

    # ===== 이벤트 핸들러 메서드들 =====
    def _handle_sync_button(self):
        """노션 동기화 버튼 처리"""
        try:
            with st.spinner("노션에서 프로젝트 정보를 가져오는 중..."):
                sync_result = self.controller.sync_with_notion()

                created = sync_result.get('created', 0)
                updated = sync_result.get('updated', 0)
                deleted = sync_result.get('deleted', 0)

                # 1: 캐시 생명주기 관리 호출
                self._manage_cache_lifecycle("sync", sync_result)

                st.session_state.sync_toast = f"✅ 동기화 완료: 신규 {created}, 수정 {updated}, 삭제 {deleted}"
                st.rerun()

        except Exception as e:
            st.session_state.error_toast = f"❌ 동기화 실패: {str(e)}"
            st.rerun()

    def _handle_bulk_project_update(self, original_df, edited_df):
        """프로젝트 일괄 업데이트 처리"""
        try:
            # 1: 변경된 값 추적
            changes = []
            for idx, (orig_row, edit_row) in enumerate(zip(original_df.itertuples(), edited_df.itertuples())):
                project_id = orig_row.ID
                orig_target = orig_row.목표치
                orig_initial = orig_row.초기값
                edit_target = edit_row.목표치
                edit_initial = edit_row.초기값

                if orig_target != edit_target or orig_initial != edit_initial:
                    changes.append({
                        'id': project_id,
                        'target_value': edit_target,
                        'initial_progress': edit_initial,
                    })

            # 2: 변경사항 업데이트
            with st.spinner(f"{len(changes)}개 프로젝트 진행률 업데이트 중..."):
                updated_count = self.controller.bulk_update_projects(changes)

                # 캐시 생명주기 관리 호출 (진행 중 프로젝트만 편집 가능)
                update_result = {
                    'updated_count': updated_count
                }
                self._manage_cache_lifecycle("update", update_result)

                st.session_state.update_toast = f"✅ {updated_count}개 프로젝트 진행률 업데이트 완료!"
                st.rerun()

        # 4: 예외 처리
        except Exception as e:
            st.session_state.error_toast = f"❌ 프로젝트 진행률 업데이트 실패: {str(e)}"
            st.rerun()

    # ===== 캐시 관리 메서드들 =====
    def _manage_cache_lifecycle(self, operation_type: str, operation_result: Dict):
        """캐시 생명주기 관리 통합 메서드

        Args:
            operation_type (str): 작업 유형 ('sync', 'update')
            operation_result (Dict): 작업 결과 정보
        """

        # 1: 노션 동기화 결과에 따른 캐시 관리
        if operation_type == "sync":
            created = operation_result.get('created', 0)
            updated = operation_result.get('updated', 0)
            deleted = operation_result.get('deleted', 0)

            if created > 0 or updated > 0 or deleted > 0:
                self._clear_all_project_cache()

                # +: dashboard에 영향
                st.session_state.project_updated= True

        # 2: 프로젝트 업데이트 결과에 따른 캐시 관리
        elif operation_type == "update":
            updated_count = operation_result.get('updated_count', 0)
            if updated_count > 0:
                self._clear_active_projects_cache()

                # +: dashboard에 영향
                st.session_state.project_updated= True

    def _clear_active_projects_cache(self):
        """진행 중 프로젝트 캐시만 무효화"""
        if 'active_projects' in st.session_state:
            del st.session_state['active_projects']

    def _clear_archived_projects_cache(self):
        """아카이브 프로젝트 캐시만 무효화"""
        if 'archived_projects' in st.session_state:
            del st.session_state['archived_projects']

    def _clear_all_project_cache(self):
        """모든 프로젝트 캐시 무효화"""
        self._clear_active_projects_cache()
        self._clear_archived_projects_cache()