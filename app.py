"""
ProjectTracker - 메인 애플리케이션
사이드바 탭을 통해 각 뷰로 이동
"""

# app.py
import streamlit as st

@st.cache_resource
def initialize_app():
    print("🚀 ProjectTracker 시작!", flush=True)
    from models.database.connection import db_manager
    print(f"✅ DB 매니저 초기화 완료: {db_manager}", flush=True)
    return db_manager

# 페이지 설정
st.set_page_config(
    page_title="ProjectTracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 초기화 실행
app_state = initialize_app()

def main():
    """메인 애플리케이션"""

    # 사이드바 네비게이션
    with st.sidebar:
        st.title("📊 ProjectTracker")
        st.markdown("---")

        page = st.radio(
            "📋 페이지 선택",
            options=["대시보드", "작업 로그", "프로젝트 관리"],
            format_func=lambda x: {
                "대시보드": "📈 대시보드",
                "작업 로그": "✏️ 작업 로그",
                "프로젝트 관리": "📋 프로젝트 관리"
            }[x]
        )

    # 페이지별로 지연 import
    if page == "대시보드":
        from views.dashboard_view import DashboardView
        dashboard_view = DashboardView()
        dashboard_view.render()

    elif page == "작업 로그":
        from views.work_log_view import WorkLogView
        work_log_view = WorkLogView()
        work_log_view.render()

    elif page == "프로젝트 관리":
        from views.project_view import ProjectView
        project_view = ProjectView()
        project_view.render()

if __name__ == "__main__":
    main()