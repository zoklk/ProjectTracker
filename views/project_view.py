"""
프로젝트 관리 뷰
노션 동기화 및 프로젝트 관리 기능
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Any

# TODO: 실제 구현에서 import 될 모듈들
# from controllers.project_controller import ProjectController
# from models.entities.project import Project


class ProjectView:
    """프로젝트 관리 페이지 뷰"""
    
    def __init__(self):
        # 실제 컨트롤러 연결
        from controllers.project_controller import ProjectController
        self.controller = ProjectController()
    
    def render(self):
        """프로젝트 관리 페이지 렌더링"""
        st.title("📋 프로젝트 관리")
        st.markdown("노션 프로젝트 동기화 및 진행률 관리")
        
        # 동기화 섹션
        self._render_sync_section()
        
        # 프로젝트 목록
        self._render_project_list()
    
    def _render_sync_section(self):
        """노션 동기화 섹션"""
        st.header("🔄 노션과 동기화")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("📋 노션과 동기화", type="primary", use_container_width=True):
                self._handle_sync_button()
    
    def _render_project_list(self):
        """프로젝트 목록 섹션"""
        st.header("📊 프로젝트 목록")
        
        # 모든 프로젝트 데이터 가져오기
        all_projects = self._get_all_projects_sorted()
        
        if all_projects:
            # 테이블 데이터 준비
            table_data = []
            for project in all_projects:
                days_left = project['days_until_deadline']
                if days_left > 0:
                    d_day_str = f"D-{days_left}"
                elif days_left == 0:
                    d_day_str = "D-Day"
                else:
                    d_day_str = f"D+{abs(days_left)}"
                
                table_data.append({
                    "ID": project["id"],
                    "프로젝트명": project["name"],
                    "상태": project["status"],
                    "시작날짜": str(project["start_date"]),
                    "종료날짜": str(project["end_date"]),
                    "D-day": d_day_str,
                    "목표": project["target_value"],
                    "현재": project["current_progress"]
                })
            
            # 데이터프레임 생성
            import pandas as pd
            df = pd.DataFrame(table_data)
            
            # 편집 가능한 테이블 렌더링
            st.info("📝 **목표**와 **현재** 컬럼만 수정 가능합니다. 수정 후 아래 저장 버튼을 눌러주세요.")
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "ID": st.column_config.NumberColumn(
                        "ID",
                        help="프로젝트 ID",
                        disabled=True
                    ),
                    "프로젝트명": st.column_config.TextColumn(
                        "프로젝트명",
                        help="프로젝트 이름 (노션에서 관리)",
                        disabled=True
                    ),
                    "상태": st.column_config.TextColumn(
                        "상태",
                        help="프로젝트 상태 (노션에서 관리)",
                        disabled=True
                    ),
                    "시작날짜": st.column_config.TextColumn(
                        "시작날짜",
                        help="프로젝트 시작일 (노션에서 관리)",
                        disabled=True
                    ),
                    "종료날짜": st.column_config.TextColumn(
                        "종료날짜",
                        help="프로젝트 마감일 (노션에서 관리)",
                        disabled=True
                    ),
                    "D-day": st.column_config.TextColumn(
                        "D-day",
                        help="마감일까지 남은 일수",
                        disabled=True
                    ),
                    "목표": st.column_config.NumberColumn(
                        "목표",
                        help="프로젝트 목표 수량 (편집 가능)",
                        min_value=1,
                        step=1,
                        disabled=False
                    ),
                    "현재": st.column_config.NumberColumn(
                        "현재",
                        help="현재 진행량 (편집 가능)",
                        min_value=0,
                        step=1,
                        disabled=False
                    )
                },
                use_container_width=True,
                hide_index=True,
                key="project_editor"
            )
            
            # 데이터 변경 감지 및 저장 버튼
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col2:
                # 변경사항 감지
                changes_detected = not df.equals(edited_df)
                if changes_detected:
                    st.warning("📝 변경사항이 감지되었습니다!")
                
            with col3:
                save_button = st.button(
                    "💾 전체 저장",
                    type="primary" if changes_detected else "secondary",
                    disabled=not changes_detected,
                    use_container_width=True
                )
            
            # 저장 버튼 처리
            if save_button and changes_detected:
                self._handle_bulk_project_update(df, edited_df)
                
        else:
            st.info("등록된 프로젝트가 없습니다. 노션에서 프로젝트를 동기화해보세요!")
    
    def _get_all_projects_sorted(self) -> List[Dict[str, Any]]:
        """상태와 마감일 기준으로 정렬된 전체 프로젝트 반환"""
        return self.controller.get_all_projects_sorted()
    
    def _handle_bulk_project_update(self, original_df, edited_df):
        """전체 프로젝트 일괄 업데이트 처리"""
        try:
            # 변경된 행들 찾기
            changes = []
            
            for idx, (orig_row, edit_row) in enumerate(zip(original_df.itertuples(), edited_df.itertuples())):
                project_id = orig_row.ID
                orig_target = orig_row.목표
                orig_current = orig_row.현재
                edit_target = edit_row.목표
                edit_current = edit_row.현재
                
                # 변경사항이 있는 경우
                if orig_target != edit_target or orig_current != edit_current:
                    changes.append({
                        'id': project_id,
                        'name': orig_row.프로젝트명,
                        'target_value': edit_target,
                        'current_progress': edit_current,
                        'old_target': orig_target,
                        'old_current': orig_current
                    })
            
            if changes:
                with st.spinner(f"{len(changes)}개 프로젝트 업데이트 중..."):
                    # 컨트롤러를 통해 일괄 업데이트
                    updated_count = self.controller.bulk_update_projects(changes)
                    
                    if updated_count > 0:
                        # 성공 메시지
                        st.success(f"✅ {updated_count}개 프로젝트 업데이트 완료!")
                        
                        # 변경 내역 표시
                        with st.expander("🔍 변경 내역 보기"):
                            for change in changes:
                                st.write(f"**{change['name']} (ID: {change['id']})**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if change['old_target'] != change['target_value']:
                                        st.write(f"- 목표: {change['old_target']} → **{change['target_value']}**")
                                    else:
                                        st.write(f"- 목표: {change['target_value']} (변경없음)")
                                with col2:
                                    if change['old_current'] != change['current_progress']:
                                        st.write(f"- 현재: {change['old_current']} → **{change['current_progress']}**")
                                    else:
                                        st.write(f"- 현재: {change['current_progress']} (변경없음)")
                                st.divider()
                        
                        # 페이지 새로고침
                        st.rerun()
                    else:
                        st.error("❌ 업데이트에 실패했습니다.")
            else:
                st.info("변경된 내용이 없습니다.")
                
        except Exception as e:
            st.error(f"❌ 업데이트 실패: {str(e)}")
    
    def _handle_sync_button(self):
        """노션 동기화 버튼 처리"""
        with st.spinner("노션에서 프로젝트 정보를 가져오는 중..."):
            # 컨트롤러를 통해 동기화
            sync_result = self.controller.sync_with_notion()
            
            if sync_result:
                created = sync_result.get('created', 0)
                updated = sync_result.get('updated', 0) 
                deleted = sync_result.get('deleted', 0)
                
                st.success(f"✅ 동기화 완료: {created}개 신규 추가, {updated}개 업데이트, {deleted}개 삭제")
                st.rerun()  # 페이지 새로고침
            else:
                st.error("❌ 동기화에 실패했습니다.")
