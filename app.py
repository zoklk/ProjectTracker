import streamlit as st
from datetime import datetime

@st.cache_resource
def initialize_app():
    """애플리케이션 초기화 - 로깅 설정 + DB 초기화"""

    # 1. 로깅 설정
    from config import setup_logging
    setup_logging()

    # 2. 앱 로거 생성 및 시작 로그
    from config import get_logger
    logger = get_logger(__name__)

    logger.info("🚀 ProjectTracker 애플리케이션 시작")
    logger.info(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 3. DB 매니저 초기화
    from models.database.connection import db_manager

    return {
        "db_manager": db_manager,
        "initialized_at": datetime.now()
    }

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
    try:
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

    except Exception as e:
        st.error(f"❌ 페이지 로딩 중 오류: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()