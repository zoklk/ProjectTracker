"""
ProjectTracker - 메인 애플리케이션
사이드바 탭을 통해 각 뷰로 이동
"""

import streamlit as st

# 각 뷰 모듈 import
from views.dashboard_view import DashboardView
from views.project_view import ProjectView
from views.work_log_view import WorkLogView

# Streamlit 페이지 설정
st.set_page_config(
    page_title="ProjectTracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """메인 애플리케이션"""
    
    # 사이드바 네비게이션
    with st.sidebar:
        st.title("📊 ProjectTracker")
        st.markdown("---")
        
        # 페이지 선택 (라디오 버튼으로 변경)
        page = st.radio(
            "📋 페이지 선택",
            options=["대시보드", "프로젝트 관리", "작업 로그"],
            format_func=lambda x: {
                "대시보드": "📈 대시보드",
                "프로젝트 관리": "📋 프로젝트 관리", 
                "작업 로그": "✏️ 작업 로그"
            }[x]
        )
    
    # 선택된 페이지에 따라 뷰 렌더링
    if page == "대시보드":
        dashboard_view = DashboardView()
        dashboard_view.render()
        
    elif page == "프로젝트 관리":
        project_view = ProjectView()
        project_view.render()
        
    elif page == "작업 로그":
        work_log_view = WorkLogView()
        work_log_view.render()

if __name__ == "__main__":
    main()
