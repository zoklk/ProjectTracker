"""
작업 로그 뷰 (Placeholder)
일일 작업 기록 및 관리
"""

import streamlit as st
from datetime import date, timedelta


class WorkLogView:
    """작업 로그 페이지 뷰"""
    
    def __init__(self):
        # TODO: 실제 컨트롤러 연결
        pass
    
    def render(self):
        """작업 로그 페이지 렌더링"""
        st.title("✏️ 작업 로그")
        st.markdown("일일 작업 기록 및 진행 상황 업데이트")
        
        # 탭 구성
        tab1, tab2 = st.tabs(["📝 오늘 작업 기록", "📊 작업 기록 조회"])
        
        with tab1:
            self._render_today_log_form()
            
        with tab2:
            self._render_work_log_history()
    
    def _render_today_log_form(self):
        """오늘 작업 기록 입력 폼"""
        st.header(f"📝 오늘 작업 기록 ({date.today().strftime('%Y-%m-%d')})")
        
        # 프로젝트 선택
        projects = ["블로그 포스팅 프로젝트", "Python 강의 수강", "영어 공부"]  # 임시 데이터
        
        with st.form("today_work_log"):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_project = st.selectbox(
                    "📋 프로젝트 선택",
                    options=projects,
                    help="작업한 프로젝트를 선택하세요"
                )
                
                progress_added = st.number_input(
                    "➕ 오늘 진행량",
                    min_value=0,
                    value=1,
                    help="오늘 추가로 진행한 양"
                )
            
            with col2:
                hours_spent = st.number_input(
                    "⏰ 작업 시간 (시간)",
                    min_value=0.0,
                    max_value=24.0,
                    value=1.0,
                    step=0.5,
                    help="실제 작업에 투입한 시간"
                )
                
                memo = st.text_area(
                    "📝 메모",
                    placeholder="오늘 작업한 내용을 간단히 기록하세요...",
                    max_chars=100,
                    help="작업 내용이나 특이사항을 기록"
                )
            
            submitted = st.form_submit_button("💾 작업 기록 저장", type="primary", use_container_width=True)
            
            if submitted:
                self._handle_work_log_submit(selected_project, progress_added, hours_spent, memo)
        
        # 오늘의 요약
        st.markdown("---")
        st.subheader("📊 오늘의 작업 요약")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("작업한 프로젝트", "2개")
        
        with col2:
            st.metric("총 작업 시간", "4.5시간")
        
        with col3:
            st.metric("총 진행량", "8")
    
    def _render_work_log_history(self):
        """작업 기록 히스토리"""
        st.header("📊 작업 기록 조회")
        
        # 기간 선택
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            start_date = st.date_input(
                "시작일",
                value=date.today() - timedelta(days=7)
            )
        
        with col2:
            end_date = st.date_input(
                "종료일", 
                value=date.today()
            )
        
        with col3:
            if st.button("🔍 조회", use_container_width=True):
                st.rerun()
        
        # 작업 로그 테이블
        st.subheader("📋 작업 기록 목록")
        
        # 임시 데이터
        import pandas as pd
        
        sample_logs = [
            {
                "날짜": "2025-06-30",
                "프로젝트": "블로그 포스팅 프로젝트",
                "진행량": 3,
                "시간": 2.5,
                "효율성": 1.2,
                "메모": "SEO 최적화 관련 포스팅 작성"
            },
            {
                "날짜": "2025-06-29", 
                "프로젝트": "Python 강의 수강",
                "진행량": 2,
                "시간": 3.0,
                "효율성": 0.67,
                "메모": "클래스와 객체 챕터 수강"
            },
            {
                "날짜": "2025-06-28",
                "프로젝트": "블로그 포스팅 프로젝트", 
                "진행량": 5,
                "시간": 4.0,
                "효율성": 1.25,
                "메모": "기술 블로그 3편 작성 완료"
            }
        ]
        
        df = pd.DataFrame(sample_logs)
        st.dataframe(df, use_container_width=True)
        
        # 통계 요약
        st.subheader("📈 기간별 통계")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 작업 일수", "7일")
        
        with col2:
            st.metric("총 작업 시간", "23.5시간")
        
        with col3:
            st.metric("총 진행량", "45")
        
        with col4:
            st.metric("평균 효율성", "1.1")
    
    def _handle_work_log_submit(self, project: str, progress: int, hours: float, memo: str):
        """작업 로그 저장 처리"""
        try:
            # TODO: 실제 저장 로직
            # success = self.controller.create_work_log(project, progress, hours, memo)
            
            # 임시 성공 처리
            st.success(f"✅ 작업 기록 저장 완료!")
            st.info(f"프로젝트: {project} | 진행량: {progress} | 시간: {hours}시간")
            
            if memo:
                st.info(f"메모: {memo}")
                
        except Exception as e:
            st.error(f"❌ 저장 실패: {str(e)}")
