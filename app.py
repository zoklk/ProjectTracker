"""
ProjectTracker - 노션 API와 DB 연동 테스트
Docker 환경에서 실행되는 Streamlit 앱
"""

import streamlit as st
import json
import pandas as pd
from notion_client import Client
from datetime import date, datetime
import config

# DB 모델 import
from models import get_db, Project, WorkLog

st.set_page_config(
    page_title="ProjectTracker - 노션 & DB 연동 테스트",
    page_icon="📊",
    layout="wide"
)

def test_notion_connection():
    """노션 API 연결 테스트"""
    try:
        notion = Client(auth=config.NOTION_API_KEY)
        database_info = notion.databases.retrieve(config.NOTION_DATABASE_ID)
        return True, database_info
    except Exception as e:
        return False, str(e)

def get_notion_projects():
    """노션에서 프로젝트 데이터 조회 및 추출"""
    try:
        notion = Client(auth=config.NOTION_API_KEY)
        
        # 진행중 상태의 프로젝트만 조회
        response = notion.databases.query(
            database_id=config.NOTION_DATABASE_ID,
            filter={
                "property": "상태",
                "status": {
                    "equals": "진행 중"
                }
            }
        )
        
        extracted_projects = []
        
        for page in response.get("results", []):
            project_data = extract_single_project(page)
            if project_data:
                extracted_projects.append(project_data)
        
        return True, extracted_projects
        
    except Exception as e:
        return False, str(e)

def extract_single_project(page):
    """단일 노션 페이지에서 프로젝트 데이터 추출"""
    properties = page.get("properties", {})
    
    # 1. 이름 추출 (title 타입)
    project_name = ""
    if "이름" in properties:
        title_prop = properties["이름"]
        if title_prop.get("type") == "title":
            title_content = title_prop.get("title", [])
            if title_content:
                project_name = title_content[0].get("plain_text", "")
    
    # 2. 상태 추출 (status 타입)
    status = "진행 중"  # 기본값
    if "상태" in properties:
        status_prop = properties["상태"]
        if status_prop.get("type") == "status":
            status_data = status_prop.get("status")
            if status_data:
                status = status_data.get("name", "진행 중")
    
    # 3. 시작일 추출 (date 타입)
    start_date = None
    if "시작일" in properties:
        start_prop = properties["시작일"]
        if start_prop.get("type") == "date":
            date_data = start_prop.get("date")
            if date_data and date_data.get("start"):
                try:
                    start_date = datetime.strptime(date_data.get("start"), "%Y-%m-%d").date()
                except:
                    start_date = date.today()  # 파싱 실패시 오늘 날짜
    
    # 4. 종료일 추출 (date 타입)
    end_date = None
    if "종료일" in properties:
        end_prop = properties["종료일"]
        if end_prop.get("type") == "date":
            date_data = end_prop.get("date")
            if date_data and date_data.get("start"):
                try:
                    end_date = datetime.strptime(date_data.get("start"), "%Y-%m-%d").date()
                except:
                    end_date = date.today()  # 파싱 실패시 오늘 날짜
    
    # 기본값 설정
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today()
    
    # 데이터가 유효한 경우에만 반환
    if project_name:
        return {
            "name": project_name,
            "status": status,
            "start_date": start_date,
            "end_date": end_date,
            "notion_page_id": page.get("id"),
            "notion_url": page.get("url")
        }
    
    return None

def test_db_connection():
    """데이터베이스 연결 테스트"""
    try:
        session = get_db()
        
        # 간단한 쿼리 실행
        project_count = session.query(Project).count()
        worklog_count = session.query(WorkLog).count()
        
        session.close()
        
        return True, {
            "project_count": project_count,
            "worklog_count": worklog_count
        }
        
    except Exception as e:
        return False, str(e)

def get_existing_projects():
    """기존 DB의 프로젝트 목록 조회"""
    try:
        session = get_db()
        projects = session.query(Project).all()
        
        project_list = []
        for project in projects:
            project_list.append({
                "id": project.id,
                "name": project.name,
                "notion_page_id": project.notion_page_id,
                "status": project.status,
                "start_date": project.start_date,
                "end_date": project.end_date,
                "target_value": project.target_value,
                "current_progress": project.current_progress,
                "progress_percentage": project.progress_percentage,
                "d_day_display": project.d_day_display
            })
        
        session.close()
        return True, project_list
        
    except Exception as e:
        return False, str(e)

def sync_projects_from_notion():
    """노션에서 프로젝트를 동기화하여 DB에 추가"""
    try:
        # 1. 노션에서 프로젝트 가져오기
        notion_success, notion_projects = get_notion_projects()
        if not notion_success:
            return False, f"노션 데이터 조회 실패: {notion_projects}"
        
        # 2. 기존 DB 프로젝트 확인
        session = get_db()
        existing_notion_ids = set()
        existing_projects = session.query(Project).all()
        
        for project in existing_projects:
            if project.notion_page_id:
                existing_notion_ids.add(project.notion_page_id)
        
        # 3. 새로운 프로젝트 찾기 및 추가
        new_projects = []
        added_count = 0
        
        for notion_project in notion_projects:
            notion_id = notion_project["notion_page_id"]
            
            # 이미 존재하는 프로젝트는 건너뛰기
            if notion_id in existing_notion_ids:
                continue
            
            # 새 프로젝트 생성
            new_project = Project(
                notion_page_id=notion_id,
                name=notion_project["name"],
                status=notion_project["status"],
                start_date=notion_project["start_date"],
                end_date=notion_project["end_date"],
                target_value=100,  # 기본값
                target_unit="units",  # 기본값
                current_progress=0  # 기본값
            )
            
            session.add(new_project)
            new_projects.append(notion_project["name"])
            added_count += 1
        
        # 4. 변경사항 커밋
        session.commit()
        session.close()
        
        return True, {
            "added_count": added_count,
            "new_projects": new_projects,
            "total_notion_projects": len(notion_projects)
        }
        
    except Exception as e:
        session.rollback()
        session.close()
        return False, str(e)

# ===== 메인 UI =====
st.title("📊 ProjectTracker - 노션 & DB 연동 테스트")

# 사이드바에 설정 정보 표시
with st.sidebar:
    st.header("⚙️ 설정 정보")
    st.write(f"**API 키**: {config.NOTION_API_KEY[:10]}...")
    st.write(f"**DB ID**: {config.NOTION_DATABASE_ID[:10]}...")
    
    st.markdown("---")
    st.subheader("🧪 테스트 메뉴")
    
    # 연결 테스트 버튼들
    if st.button("🔗 노션 연결 테스트", use_container_width=True):
        with st.spinner("노션 연결 테스트 중..."):
            success, result = test_notion_connection()
            if success:
                st.success("✅ 노션 연결 성공!")
            else:
                st.error(f"❌ 노션 연결 실패: {result}")
    
    if st.button("🗄️ DB 연결 테스트", use_container_width=True):
        with st.spinner("DB 연결 테스트 중..."):
            success, result = test_db_connection()
            if success:
                st.success("✅ DB 연결 성공!")
                st.write(f"프로젝트: {result['project_count']}개")
                st.write(f"작업로그: {result['worklog_count']}개")
            else:
                st.error(f"❌ DB 연결 실패: {result}")

# 메인 컨텐츠
tab1, tab2, tab3 = st.tabs(["📥 노션 데이터", "🔄 프로젝트 동기화", "📊 DB 프로젝트 목록"])

# ===== Tab 1: 노션 데이터 조회 =====
with tab1:
    st.header("📥 노션에서 프로젝트 데이터 조회")
    
    if st.button("노션 프로젝트 조회", type="primary"):
        with st.spinner("노션에서 진행중 프로젝트 조회 중..."):
            success, projects = get_notion_projects()
            
            if success:
                st.success(f"✅ {len(projects)}개 프로젝트 조회 성공!")
                
                if projects:
                    # 데이터프레임으로 표시
                    df_data = []
                    for project in projects:
                        df_data.append({
                            "프로젝트명": project["name"],
                            "상태": project["status"],
                            "시작일": project["start_date"],
                            "종료일": project["end_date"],
                            "노션 ID": project["notion_page_id"][:8] + "..."
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # 상세 정보
                    with st.expander("📋 상세 정보"):
                        for i, project in enumerate(projects, 1):
                            st.write(f"**{i}. {project['name']}**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"- 상태: {project['status']}")
                                st.write(f"- 시작일: {project['start_date']}")
                            with col2:
                                st.write(f"- 종료일: {project['end_date']}")
                                st.write(f"- 노션 ID: {project['notion_page_id']}")
                            
                            if project.get('notion_url'):
                                st.link_button("노션 페이지 보기", project['notion_url'])
                            st.markdown("---")
                else:
                    st.warning("진행중인 프로젝트가 없습니다.")
                    
            else:
                st.error(f"❌ 노션 데이터 조회 실패: {projects}")

# ===== Tab 2: 프로젝트 동기화 =====
with tab2:
    st.header("🔄 노션 → DB 프로젝트 동기화")
    
    st.info("""
    **동기화 과정:**
    1. 노션에서 '진행 중' 상태의 프로젝트 조회
    2. 기존 DB와 비교하여 새로운 프로젝트 확인
    3. 존재하지 않는 프로젝트를 DB에 추가
    """)
    
    if st.button("프로젝트 동기화 실행", type="primary"):
        with st.spinner("프로젝트 동기화 중..."):
            success, result = sync_projects_from_notion()
            
            if success:
                st.success("✅ 프로젝트 동기화 완료!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("노션 프로젝트 수", result["total_notion_projects"])
                
                with col2:
                    st.metric("새로 추가된 프로젝트", result["added_count"])
                
                with col3:
                    if result["added_count"] > 0:
                        st.metric("동기화 상태", "신규 추가", delta="NEW")
                    else:
                        st.metric("동기화 상태", "최신 상태", delta="UP TO DATE")
                
                # 새로 추가된 프로젝트 목록
                if result["new_projects"]:
                    st.subheader("📝 새로 추가된 프로젝트")
                    for i, project_name in enumerate(result["new_projects"], 1):
                        st.write(f"{i}. {project_name}")
                else:
                    st.info("새로 추가된 프로젝트가 없습니다. (모든 프로젝트가 이미 동기화됨)")
                    
            else:
                st.error(f"❌ 프로젝트 동기화 실패: {result}")

# ===== Tab 3: DB 프로젝트 목록 =====
with tab3:
    st.header("📊 데이터베이스 프로젝트 목록")
    
    if st.button("DB 프로젝트 조회", type="secondary"):
        with st.spinner("DB에서 프로젝트 조회 중..."):
            success, projects = get_existing_projects()
            
            if success:
                st.success(f"✅ {len(projects)}개 프로젝트 조회 성공!")
                
                if projects:
                    # 요약 메트릭
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_projects = len(projects)
                        st.metric("총 프로젝트", total_projects)
                    
                    with col2:
                        synced_projects = len([p for p in projects if p["notion_page_id"]])
                        st.metric("노션 연동", synced_projects)
                    
                    with col3:
                        active_projects = len([p for p in projects if p["status"] == "진행 중"])
                        st.metric("진행중", active_projects)
                    
                    with col4:
                        avg_progress = sum(p["progress_percentage"] for p in projects) / len(projects)
                        st.metric("평균 진행률", f"{avg_progress:.1f}%")
                    
                    # 프로젝트 테이블
                    st.subheader("📋 프로젝트 상세 목록")
                    
                    table_data = []
                    for project in projects:
                        table_data.append({
                            "ID": project["id"],
                            "프로젝트명": project["name"],
                            "상태": project["status"],
                            "진행률": f"{project['progress_percentage']:.1f}%",
                            "D-Day": project["d_day_display"],
                            "목표": project["target_value"],
                            "현재": project["current_progress"],
                            "노션연동": "✅" if project["notion_page_id"] else "❌"
                        })
                    
                    df = pd.DataFrame(table_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # 프로젝트별 상세 정보
                    with st.expander("🔍 프로젝트 상세 정보"):
                        for project in projects:
                            st.write(f"**🎯 {project['name']} (ID: {project['id']})**")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**기본 정보**")
                                st.write(f"- 상태: {project['status']}")
                                st.write(f"- 시작일: {project['start_date']}")
                                st.write(f"- 종료일: {project['end_date']}")
                            
                            with col2:
                                st.write(f"**진행 상황**")
                                st.write(f"- 목표: {project['target_value']}")
                                st.write(f"- 현재: {project['current_progress']}")
                                st.write(f"- 진행률: {project['progress_percentage']:.1f}%")
                            
                            with col3:
                                st.write(f"**기타 정보**")
                                st.write(f"- D-Day: {project['d_day_display']}")
                                notion_status = "연동됨" if project['notion_page_id'] else "로컬 전용"
                                st.write(f"- 노션: {notion_status}")
                                if project['notion_page_id']:
                                    st.write(f"- 노션 ID: {project['notion_page_id'][:8]}...")
                            
                            st.markdown("---")
                
                else:
                    st.warning("데이터베이스에 프로젝트가 없습니다.")
                    st.info("노션에서 프로젝트를 동기화해보세요!")
                    
            else:
                st.error(f"❌ DB 프로젝트 조회 실패: {projects}")

# 하단 정보
st.markdown("---")
st.subheader("🔧 시스템 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("**노션 API 상태**\n연결 테스트로 확인")

with col2:
    st.info("**데이터베이스 상태**\nSQLite 로컬 DB")

with col3:
    st.info("**동기화 방식**\n노션 → DB 단방향")
