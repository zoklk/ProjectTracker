from typing import List, Dict, Any
import logging

from models.services.project_service import ProjectService


class ProjectController:
    def __init__(self):
        self.project_service = ProjectService()
        self.logger = logging.getLogger(__name__)

    # ===== View에서 호출하는 메서드들 =====
    def get_active_projects(self) -> List[Dict[str, Any]]:
        """진행 중 프로젝트 목록 조회"""
        try:
            projects = self.project_service.get_active_projects()
            self.logger.info(f"🎮✅ 진행 중 프로젝트 목록 조회 성공: {len(projects)}개")
            return projects
        except Exception as e:
            self.logger.error(f"🎮❌ 진행 중 프로젝트 목록 조회 실패: {str(e)}")
            raise e

    def get_archived_projects(self) -> List[Dict[str, Any]]:
        """아카이브 프로젝트 목록 조회"""
        try:
            projects = self.project_service.get_archived_projects()
            self.logger.info(f"🎮✅ 아카이브 프로젝트 목록 조회 성공: {len(projects)}개")
            return projects
        except Exception as e:
            self.logger.error(f"🎮❌ 아카이브 프로젝트 목록 조회 실패: {str(e)}")
            raise e

    def bulk_update_projects(self, changes: List[Dict]) -> int:
        """프로젝트 진행률 일괄 업데이트"""
        try:
            updated_count = self.project_service.bulk_update_projects(changes)
            self.logger.info(f"🎮✅ 프로젝트 진행률 일괄 업데이트 완료: {updated_count}개")
            return updated_count
        except Exception as e:
            self.logger.error(f"🎮❌ 프로젝트 진행률 일괄 업데이트 실패: {str(e)}")
            raise e

    def sync_with_notion(self) -> Dict[str, int]:
        """노션과 동기화 - 모든 프로젝트 대상"""
        try:
            sync_result = self.project_service.sync_with_notion()
            created = sync_result.get('created', 0)
            updated = sync_result.get('updated', 0)
            deleted = sync_result.get('deleted', 0)
            self.logger.info(f"🎮✅ 노션 동기화 완료: 신규 {created}개, 수정 {updated}개, 삭제 {deleted}개")
            return sync_result
        except Exception as e:
            self.logger.error(f"🎮❌ 노션 동기화 실패: {str(e)}")
            raise e