from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database.connection import db_manager
from ..entities.project import Project

class ProjectRepository:
    """프로젝트 데이터 액세스 객체 - 딕셔너리 반환"""
    def __init__(self):
        pass

    # ===== 조회 메서드들 (Dict 반환) =====
    def find_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """ID로 프로젝트 조회 - Dict 반환"""
        with db_manager.get_session_context() as session:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                return project.to_dict()
            return None

    def find_all(self) -> List[Dict[str, Any]]:
        """모든 프로젝트 조회 - Dict 리스트 반환"""
        with db_manager.get_session_context() as session:
            projects = session.query(Project).all()

            result = []
            for project in projects:
                project_dict = project.to_dict()
                result.append(project_dict)

            return result

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """상태별 프로젝트 조회 - Dict 리스트 반환"""
        with db_manager.get_session_context() as session:
            projects = session.query(Project).filter(Project.status == status).all()

            result = []
            for project in projects:
                project_dict = project.to_dict()
                result.append(project_dict)

            return result

    def find_by_notion_id(self, notion_page_id: str) -> Optional[Dict[str, Any]]:
        """노션 페이지 ID로 프로젝트 조회 - Dict 반환"""
        with db_manager.get_session_context() as session:
            project = session.query(Project).filter(
                Project.notion_page_id == notion_page_id
            ).first()
            if project:
                return project.to_dict()
            return None


    # ===== 생성 메서드들 (Entity 반환) =====
    def insert(self, project: Project) -> None:
        """새 프로젝트 생성 - 성공 여부 반환"""
        with db_manager.get_session_context() as session:
            session.add(project)

    def bulk_insert(self, projects: List[Project]) -> int:
        """여러 프로젝트 일괄 생성 - All or Nothing"""
        if not projects:
            return 0

        with db_manager.get_session_context() as session:
            for project in projects:
                session.add(project)

        return len(projects)

    # ===== 수정 메서드들 (Entity 반환) =====
    def update(self, project: Project) -> None:
        """프로젝트 수정 - 성공 여부 반환"""
        with db_manager.get_session_context() as session:
            session.merge(project)

    def bulk_update(self, projects: List[Project]) -> int:
        """여러 프로젝트 전체 필드 일괄 수정 (노션 동기화용)"""
        if not projects:
            return 0

        with db_manager.get_session_context() as session:
            updated_count = 0
            for project in projects:
                session.merge(project)
                updated_count += 1

        return updated_count

    def bulk_update_progress(self, updates: List[Dict]) -> int:
        """여러 프로젝트의 진행률 일괄 수정"""
        if not updates:
            return 0

        with db_manager.get_session_context() as session:
            updated_count = 0

            for update_data in updates:
                project_id = update_data['id']
                target_value = update_data['target_value']
                current_progress = update_data['current_progress']

                result = session.query(Project).filter(
                    Project.id == project_id
                ).update({
                    'target_value': target_value,
                    'current_progress': current_progress
                })
                updated_count += result

        return updated_count

    # ===== 삭제 메서드들 =====
    def delete(self, project_id: int) -> bool:
        """프로젝트 삭제"""
        with db_manager.get_session_context() as session:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                session.delete(project)
                return True
            return False

    def bulk_delete(self, project_ids: List[int]) -> int:
        """여러 프로젝트 일괄 삭제"""
        if not project_ids:
            return 0

        with db_manager.get_session_context() as session:
            deleted_count = session.query(Project).filter(
                Project.id.in_(project_ids)
            ).delete(synchronize_session=False)
            return deleted_count

    def delete_by_notion_ids(self, notion_ids: List[str]) -> int:
        """노션 페이지 ID 목록으로 프로젝트들 삭제 (노션 동기화용)"""
        if not notion_ids:
            return 0

        with db_manager.get_session_context() as session:
            deleted_count = session.query(Project).filter(
                Project.notion_page_id.in_(notion_ids)
            ).delete(synchronize_session=False)
            return deleted_count