"""
프로젝트 Service
비즈니스 로직 처리 계층
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
import logging

from ..repositories.project_repository import ProjectRepository
from ..entities.project import Project

# 노션 API 클라이언트 import
from notion_client import Client
import config


class ProjectService:
    """프로젝트 비즈니스 로직 서비스"""

    def __init__(self):
        self.project_repo = ProjectRepository()
        # 노션 클라이언트 초기화
        self.notion_client = Client(auth=config.NOTION_API_KEY)
        self.logger = logging.getLogger(__name__)

    # ===== 프로젝트 조회 및 관리 =====

    def get_all_projects_sorted(self) -> List[Dict[str, Any]]:
        """상태 우선순위 + 마감일순으로 정렬된 프로젝트 목록 반환 (View용 Dict 형태)"""
        try:
            # Repository에서 정렬된 프로젝트 조회
            projects = self.project_repo.find_all_sorted_by_status_and_date()

            # View에서 사용할 Dict 형태로 변환
            project_dicts = []
            for project in projects:
                # D-day 계산
                days_left = project.days_until_deadline
                if days_left > 0:
                    d_day_str = f"D-{days_left}"
                elif days_left == 0:
                    d_day_str = "D-Day"
                else:
                    d_day_str = f"D+{abs(days_left)}"

                # View 테이블에 맞는 구조로 생성
                project_dict = {
                    'id': project.id,
                    'name': project.name,
                    'status': project.status,
                    'start_date': project.start_date,
                    'end_date': project.end_date,
                    'target_value': project.target_value,
                    'current_progress': project.current_progress,
                    'days_until_deadline': days_left  # 계산된 값 저장
                }
                project_dicts.append(project_dict)

            return project_dicts

        except Exception as e:
            self.logger.error(f"프로젝트 목록 조회 실패: {e}")
            raise e

    def bulk_update_projects(self, changes: List[Dict]) -> int:
        """여러 프로젝트의 진행률 일괄 업데이트

        Args:
            changes: [{'id': 1, 'target_value': 100, 'current_progress': 50}, ...]

        Returns:
            업데이트된 프로젝트 수
        """
        try:
            # 입력 데이터 검증
            validated_updates = []
            for change in changes:
                if self._validate_progress_data(change):
                    validated_updates.append({
                        'id': change['id'],
                        'target_value': change['target_value'],
                        'current_progress': change['current_progress']
                    })
                else:
                    self.logger.warning(f"잘못된 진행률 데이터: {change}")

            if not validated_updates:
                return 0

            # Repository를 통해 일괄 업데이트
            updated_count = self.project_repo.bulk_update_progress(validated_updates)

            self.logger.info(f"{updated_count}개 프로젝트 진행률 업데이트 완료")
            return updated_count

        except Exception as e:
            self.logger.error(f"프로젝트 일괄 업데이트 실패: {e}")
            raise e

    # ===== 노션 동기화 =====

    def sync_with_notion(self) -> Dict[str, int]:
        """노션과 완전 동기화 (신규/수정/삭제)

        Returns:
            {'created': 2, 'updated': 1, 'deleted': 0}
        """
        try:
            # 1: 노션에서 "진행 중" 프로젝트 가져오기
            notion_projects = self._fetch_notion_projects()

            # 2: 기존 프로젝트와 비교하여 동기화
            sync_result = self._perform_sync(notion_projects)

            self.logger.info(f"노션 동기화 완료: {sync_result}")
            return sync_result

        except Exception as e:
            self.logger.error(f"노션 동기화 실패: {e}")
            raise e

    def _fetch_notion_projects(self) -> List[Dict]:
        """노션에서 진행 중인 프로젝트 가져오기"""
        try:
            # 1: 노션 API를 통해 '진행 중' 상태의 프로젝트 조회
            response = self.notion_client.databases.query(
                database_id=config.NOTION_DATABASE_ID,
                filter={
                    "property": "상태",
                    "status": {
                        "equals": "진행 중"
                    }
                }
            )

            notion_projects = []

            # 2: 각 노션 페이지에서 프로젝트 데이터 추출
            for page in response.get("results", []):
                project_data = self._extract_project_from_notion_page(page)
                if project_data:
                    notion_projects.append(project_data)

            self.logger.info(f"노션에서 {len(notion_projects)}개 프로젝트 조회 완료")
            return notion_projects

        except Exception as e:
            self.logger.error(f"노션 프로젝트 조회 실패: {e}")
            return []

    def _extract_project_from_notion_page(self, page: Dict) -> Optional[Dict]:
        """노션 페이지에서 프로젝트 데이터 추출"""
        try:
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
                        except ValueError:
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
                        except ValueError:
                            end_date = date.today()  # 파싱 실패시 오늘 날짜

            # 기본값 설정
            if not start_date:
                start_date = date.today()
            if not end_date:
                end_date = date.today()

            # 데이터가 유효한 경우에만 반환
            if project_name:
                return {
                    "id": page.get("id"),
                    "name": project_name,
                    "status": status,
                    "start_date": start_date,
                    "end_date": end_date
                }

            return None

        except Exception as e:
            self.logger.error(f"노션 페이지 데이터 추출 실패: {e}")
            return None

    def _perform_sync(self, notion_projects: List[Dict]) -> Dict[str, int]:
        """실제 동기화 수행"""
        created_count = 0
        updated_count = 0
        deleted_count = 0

        # 노션 프로젝트 ID 목록
        notion_ids = [p['id'] for p in notion_projects]

        # 기존 프로젝트들 조회
        existing_projects = self.project_repo.find_all()
        existing_notion_ids = {p.notion_page_id: p for p in existing_projects if p.notion_page_id}

        # 1. 신규 생성 및 업데이트
        for notion_project in notion_projects:
            notion_id = notion_project['id']

            if notion_id in existing_notion_ids:
                # 기존 프로젝트 업데이트 (노션 정보만, 로컬 진행률 보존)
                existing_project = existing_notion_ids[notion_id]
                if self._update_project_from_notion(existing_project, notion_project):
                    updated_count += 1
            else:
                # 신규 프로젝트 생성
                if self._create_project_from_notion(notion_project):
                    created_count += 1

        # 2. 노션에 없는 프로젝트 삭제
        projects_to_delete = []
        for project in existing_projects:
            if project.notion_page_id and project.notion_page_id not in notion_ids:
                projects_to_delete.append(project.notion_page_id)

        if projects_to_delete:
            deleted_count = self.project_repo.delete_by_notion_ids(projects_to_delete)

        return {
            'created': created_count,
            'updated': updated_count,
            'deleted': deleted_count
        }

    def _create_project_from_notion(self, notion_data: Dict) -> bool:
        """노션 데이터로 새 프로젝트 생성"""
        try:
            new_project = Project(
                notion_page_id=notion_data['id'],
                name=notion_data['name'],
                status=notion_data['status'],
                start_date=notion_data['start_date'],
                end_date=notion_data['end_date'],
                target_value=1,  # 기본값
                current_progress=0  # 기본값
            )

            self.project_repo.save(new_project)
            return True

        except Exception as e:
            self.logger.error(f"노션 프로젝트 생성 실패: {e}")
            return False

    # 여기 보던중===================================================================
    # 여기 보던중===================================================================
    # 여기 보던중===================================================================
    def _update_project_from_notion(self, existing_project: Project, notion_data: Dict) -> bool:
        """기존 프로젝트를 노션 데이터로 업데이트 (로컬 진행률 보존)"""
        try:
            # 변경사항 있는지 확인
            has_changes = (
                existing_project.name != notion_data['name'] or
                existing_project.status != notion_data['status'] or
                existing_project.start_date != notion_data['start_date'] or
                existing_project.end_date != notion_data['end_date']
            )

            if not has_changes:
                return False  # 변경사항 없으면 False 반환

            # 실제 변경사항이 있을 때만 업데이트
            existing_project.name = notion_data['name']
            existing_project.status = notion_data['status']
            existing_project.start_date = notion_data['start_date']
            existing_project.end_date = notion_data['end_date']

            self.project_repo.update(existing_project)
            return True

        except Exception as e:
            self.logger.error(f"노션 프로젝트 업데이트 실패: {e}")
            return False

    # ===== 유틸리티 메서드 =====

    def _validate_progress_data(self, data: Dict) -> bool:
        """진행률 데이터 검증"""
        try:
            project_id = data.get('id')
            target_value = data.get('target_value')
            current_progress = data.get('current_progress')

            # 필수 필드 체크
            if not all([project_id, target_value is not None, current_progress is not None]):
                return False

            # 숫자 타입 체크
            if not isinstance(target_value, (int, float)) or not isinstance(current_progress, (int, float)):
                return False

            # 값 범위 체크
            if target_value <= 0 or current_progress < 0:
                return False

            return True

        except Exception:
            return False

    def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """ID로 프로젝트 조회 (Dict 형태)"""
        try:
            project = self.project_repo.find_by_id(project_id)
            if project:
                # D-day 계산
                days_left = project.days_until_deadline
                if days_left > 0:
                    d_day_str = f"D-{days_left}"
                elif days_left == 0:
                    d_day_str = "D-Day"
                else:
                    d_day_str = f"D+{abs(days_left)}"

                return {
                    'id': project.id,
                    'name': project.name,
                    'status': project.status,
                    'start_date': project.start_date,
                    'end_date': project.end_date,
                    'target_value': project.target_value,
                    'current_progress': project.current_progress,
                    'days_until_deadline': days_left
                }
            return None

        except Exception as e:
            self.logger.error(f"프로젝트 조회 실패 (ID: {project_id}): {e}")
            raise e
