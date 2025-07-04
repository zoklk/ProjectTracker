"""
프로젝트 Repository
데이터베이스 직접 액세스 계층
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database.connection import get_db
from ..entities.project import Project


class ProjectRepository:
    """프로젝트 데이터 액세스 객체"""

    def __init__(self):
        pass

    # ===== 기본 CRUD =====

    def save(self, project: Project) -> Project:
        """새 프로젝트 저장"""
        session = get_db()
        try:
            session.add(project)
            session.commit()
            session.refresh(project)
            return project
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def find_by_id(self, project_id: int) -> Optional[Project]:
        """ID로 프로젝트 조회"""
        session = get_db()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                # Lazy loading 속성들을 미리 접근하여 로드
                _ = project.progress_percentage
                _ = project.days_until_deadline
            return project
        finally:
            session.close()

    def find_all(self) -> List[Project]:
        """모든 프로젝트 조회"""
        session = get_db()
        try:
            projects = session.query(Project).all()
            # Entity 데이터를 미리 로드하여 detached 문제 해결
            for project in projects:
                _ = project.progress_percentage
                _ = project.days_until_deadline
            return projects
        finally:
            session.close()

    def update(self, project: Project) -> Project:
        """프로젝트 업데이트"""
        session = get_db()
        try:
            merged_project = session.merge(project)  # 반환된 객체
            session.commit()                         # 병합된 객체를 커밋
            session.refresh(merged_project)          # 병합된 객체 refresh
            return merged_project
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete(self, project_id: int) -> bool:
        """프로젝트 삭제"""
        session = get_db()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                session.delete(project)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ===== 프로젝트 특화 조회 =====

    def find_by_notion_id(self, notion_page_id: str) -> Optional[Project]:
        """노션 페이지 ID로 프로젝트 조회"""
        session = get_db()
        try:
            project = session.query(Project).filter(
                Project.notion_page_id == notion_page_id
            ).first()
            if project:
                # Lazy loading 속성들을 미리 접근하여 로드
                _ = project.progress_percentage
                _ = project.days_until_deadline
            return project
        finally:
            session.close()

    def find_all_sorted_by_status_and_date(self) -> List[Project]:
        """상태 우선순위 + 마감일순으로 정렬된 프로젝트 조회"""
        session = get_db()
        try:
            # 모든 프로젝트를 가져와서 Python에서 정렬
            projects = session.query(Project).all()

            # Entity 데이터를 미리 로드하여 detached 문제 해결
            for project in projects:
                # Lazy loading 속성들을 미리 접근하여 로드
                _ = project.progress_percentage
                _ = project.days_until_deadline
                _ = project.is_overdue
                _ = project.d_day_display

            # 상태 우선순위 매핑
            status_priority = {
                '진행 중': 1,
                '시작 안 함': 2,
                '중단': 3,
                '완료': 4
            }

            # 상태 우선순위, 마감일 오름차순으로 정렬
            sorted_projects = sorted(
                projects,
                key=lambda x: (status_priority.get(x.status, 999), x.end_date)
            )

            return sorted_projects
        finally:
            session.close()

    # ===== 일괄 처리 =====

    def bulk_update_progress(self, updates: List[Dict]) -> int:
        """여러 프로젝트의 진행률 일괄 업데이트

        Args:
            updates: [{'id': 1, 'target_value': 100, 'current_progress': 50}, ...]

        Returns:
            업데이트된 프로젝트 수
        """
        session = get_db()
        try:
            updated_count = 0

            for update_data in updates:
                project_id = update_data['id']
                target_value = update_data['target_value']
                current_progress = update_data['current_progress']

                # 개별 프로젝트 업데이트
                result = session.query(Project).filter(
                    Project.id == project_id
                ).update({
                    'target_value': target_value,
                    'current_progress': current_progress
                })

                updated_count += result

            session.commit()
            return updated_count

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def save_all(self, projects: List[Project]) -> List[Project]:
        """여러 프로젝트 일괄 저장"""
        session = get_db()
        try:
            session.add_all(projects)
            session.commit()

            # 저장된 프로젝트들 refresh
            for project in projects:
                session.refresh(project)

            return projects
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_by_notion_ids(self, notion_ids: List[str]) -> int:
        """노션 페이지 ID 목록으로 프로젝트들 삭제

        Args:
            notion_ids: 삭제할 노션 페이지 ID 목록

        Returns:
            삭제된 프로젝트 수
        """
        if not notion_ids:
            return 0

        session = get_db()
        try:
            deleted_count = session.query(Project).filter(
                Project.notion_page_id.in_(notion_ids)
            ).delete(synchronize_session=False)

            session.commit()
            return deleted_count

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
