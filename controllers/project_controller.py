"""
프로젝트 Controller
View와 Service 계층 연결
"""

from typing import List, Dict, Any
import logging

from models.services.project_service import ProjectService


class ProjectController:
    """프로젝트 컨트롤러 - View와 Service 연결"""
    
    def __init__(self):
        self.project_service = ProjectService()
        self.logger = logging.getLogger(__name__)
    
    # ===== View에서 호출하는 메서드들 =====
    
    def get_all_projects_sorted(self) -> List[Dict[str, Any]]:
        """정렬된 프로젝트 목록 조회 (View용)"""
        try:
            return self.project_service.get_all_projects_sorted()
        except Exception as e:
            self.logger.error(f"프로젝트 목록 조회 실패: {e}")
            return []
    
    def bulk_update_projects(self, changes: List[Dict]) -> int:
        """프로젝트 진행률 일괄 업데이트"""
        try:
            return self.project_service.bulk_update_projects(changes)
        except Exception as e:
            self.logger.error(f"프로젝트 일괄 업데이트 실패: {e}")
            return 0
    
    def sync_with_notion(self) -> Dict[str, int]:
        """노션과 동기화"""
        try:
            return self.project_service.sync_with_notion()
        except Exception as e:
            self.logger.error(f"노션 동기화 실패: {e}")
            return {'created': 0, 'updated': 0, 'deleted': 0}
    
    def get_project_by_id(self, project_id: int) -> Dict[str, Any]:
        """ID로 프로젝트 조회"""
        try:
            project = self.project_service.get_project_by_id(project_id)
            return project if project else {}
        except Exception as e:
            self.logger.error(f"프로젝트 조회 실패 (ID: {project_id}): {e}")
            return {}
