"""
ProjectTracker - 노션 API 연결 테스트
Docker 환경에서 실행되는 Streamlit 앱
"""

import streamlit as st
import json
from notion_client import Client
import config

st.set_page_config(
    page_title="ProjectTracker - 노션 연결 테스트",
    page_icon="📊",
    layout="wide"
)

def test_notion_connection():
    """노션 API 연결 테스트"""
    try:
        # 노션 클라이언트 초기화
        notion = Client(auth=config.NOTION_API_KEY)
        
        # 데이터베이스 정보 조회
        database_info = notion.databases.retrieve(config.NOTION_DATABASE_ID)
        
        return True, database_info
    except Exception as e:
        return False, str(e)

def get_notion_data():
    """노션 데이터베이스에서 데이터 조회"""
    try:
        notion = Client(auth=config.NOTION_API_KEY)
        
        # 데이터베이스의 모든 페이지 조회
        response = notion.databases.query(
            database_id=config.NOTION_DATABASE_ID
        )
        
        return True, response
    except Exception as e:
        return False, str(e)

# 메인 UI
st.title("📊 ProjectTracker - 노션 API 연결 테스트")

# 사이드바에 설정 정보 표시
with st.sidebar:
    st.header("⚙️ 설정 정보")
    st.write(f"**API 키**: {config.NOTION_API_KEY[:10]}...")
    st.write(f"**DB ID**: {config.NOTION_DATABASE_ID[:10]}...")

# 메인 컨텐츠
col1, col2 = st.columns(2)

with col1:
    st.header("🔗 연결 테스트")
    
    if st.button("노션 연결 테스트", type="primary"):
        with st.spinner("노션 연결 테스트 중..."):
            success, result = test_notion_connection()
            
            if success:
                st.success("✅ 노션 연결 성공!")
                
                # 데이터베이스 정보 표시
                st.subheader("📋 데이터베이스 정보")
                database_title = ""
                if result.get('title'):
                    database_title = result['title'][0].get('plain_text', '제목 없음')
                
                st.write(f"**제목**: {database_title}")
                st.write(f"**ID**: {result.get('id', '')}")
                st.write(f"**생성일**: {result.get('created_time', '')}")
                st.write(f"**수정일**: {result.get('last_edited_time', '')}")
                
                # 속성 정보 표시
                st.subheader("🏷️ 데이터베이스 속성")
                properties = result.get('properties', {})
                for prop_name, prop_data in properties.items():
                    prop_type = prop_data.get('type', '')
                    st.write(f"- **{prop_name}**: {prop_type}")
                
            else:
                st.error(f"❌ 노션 연결 실패: {result}")

with col2:
    st.header("📊 데이터 조회")
    
    if st.button("데이터 조회 테스트", type="secondary"):
        with st.spinner("노션 데이터 조회 중..."):
            success, result = get_notion_data()
            
            if success:
                st.success("✅ 데이터 조회 성공!")
                
                # 조회된 페이지 수
                pages = result.get('results', [])
                st.write(f"**조회된 페이지 수**: {len(pages)}")
                
                # 각 페이지의 제목 표시
                if pages:
                    st.subheader("📄 조회된 페이지 목록")
                    for i, page in enumerate(pages[:5], 1):  # 최대 5개만 표시
                        properties = page.get('properties', {})
                        
                        # 제목 찾기
                        title = "제목 없음"
                        for prop_name, prop_data in properties.items():
                            if prop_data.get('type') == 'title':
                                title_content = prop_data.get('title', [])
                                if title_content:
                                    title = title_content[0].get('plain_text', '제목 없음')
                                break
                        
                        st.write(f"{i}. {title}")
                    
                    if len(pages) > 5:
                        st.write(f"... 외 {len(pages) - 5}개 더")
                
            else:
                st.error(f"❌ 데이터 조회 실패: {result}")

# JSON 원본 데이터 표시
st.header("🔍 JSON 원본 데이터")

if st.button("전체 JSON 데이터 보기"):
    with st.spinner("데이터 로딩 중..."):
        success, result = get_notion_data()
        
        if success:
            st.subheader("📋 데이터베이스 스키마")
            schema_success, schema_result = test_notion_connection()
            if schema_success:
                st.json(schema_result)
            
            st.subheader("📊 페이지 데이터")
            st.json(result)
        else:
            st.error(f"데이터 로딩 실패: {result}")

# Docker 환경 정보
st.sidebar.markdown("---")
st.sidebar.subheader("🐳 환경 정보")
st.sidebar.write("**실행 환경**: Docker Container")
st.sidebar.write("**프레임워크**: Streamlit")
