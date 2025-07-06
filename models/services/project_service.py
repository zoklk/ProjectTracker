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

    # ===== 1. 프로젝트 목록 조회 및 정렬 =====
    def get_active_projects(self) -> List[Dict[str, Any]]:
        """진행 중 프로젝트 목록 반환"""
        try:
            # 1: Repository에서 진행 중 프로젝트만 조회
            active_projects = self.project_repo.find_by_status("진행 중")

            # 2: 마감일순으로 정렬
            sorted_projects = sorted(
                active_projects,
                key=lambda x: x['days_until_deadline']
            )

            return sorted_projects

        # 3: 예외 처리
        except Exception as e:
            raise e

    def get_archived_projects(self) -> List[Dict[str, Any]]:
        """아카이브 프로젝트 목록 반환 (진행 중이 아닌 모든 프로젝트)"""
        try:
            # 1: Repository에서 모든 프로젝트 조회
            all_projects = self.project_repo.find_all()

            # 2: 진행 중이 아닌 프로젝트만 필터링
            archived_projects = [
                project for project in all_projects
                if project['status'] != '진행 중'
            ]

            # 3: 상태별 우선순위 + 마감일순으로 정렬
            status_priority = {
                '시작 안 함': 1,
                '중단': 2,
                '완료': 3
            }

            sorted_projects = sorted(
                archived_projects,
                key=lambda x: (
                    status_priority.get(x['status'], 99),
                    x['days_until_deadline']
                )
            )

            return sorted_projects

        # 4: 예외 처리
        except Exception as e:
            raise e

    # ===== 2. 노션 전체 프로젝트 동기화 =====
    def sync_with_notion(self) -> Dict[str, int]:
        """노션과 완전 동기화 - 모든 프로젝트 대상"""
        try:
            # 1: 노션에서 모든 프로젝트 가져오기
            notion_projects = self._fetch_all_notion_projects()

            # 2: 벌크 처리로 효율적 동기화
            sync_result = self._perform_bulk_sync(notion_projects)

            return sync_result

        except Exception as e:
            raise e

    def _fetch_all_notion_projects(self) -> List[Dict]:
        """노션에서 모든 프로젝트 가져오기 - 상태 제한 없음"""
        try:
            all_projects = []
            has_more = True
            start_cursor = None

            while has_more:
                # 페이지네이션으로 모든 프로젝트 조회
                response = self.notion_client.databases.query(
                    database_id=config.NOTION_DATABASE_ID,
                    start_cursor=start_cursor,
                    page_size=100  # 한 번에 100개씩
                    # 필터 없음 - 모든 상태의 프로젝트 가져오기
                )

                # 프로젝트 데이터 추출
                for page in response.get("results", []):
                    project_data = self._extract_project_from_notion_page(page)
                    if project_data:
                        all_projects.append(project_data)

                # 다음 페이지 확인
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

            return all_projects

        except Exception as e:
            # 노션 API 에러를 Service 에러로 래핑
            raise Exception(f"⚙️❌ 노션 프로젝트 조회 실패: {str(e)}")

    def _perform_bulk_sync(self, notion_projects: List[Dict]) -> Dict[str, int]:
        """벌크 처리로 효율적 동기화"""
        created_count = 0
        updated_count = 0
        deleted_count = 0

        # 1: 노션 프로젝트 ID 목록
        notion_ids = [p['id'] for p in notion_projects]

        # 2: 기존 프로젝트들 조회 (Dict 형태)
        existing_projects_dict = self.project_repo.find_all()
        existing_notion_ids = {p['notion_page_id']: p for p in existing_projects_dict if p['notion_page_id']}

        # 3: 분류: 신규 vs 수정
        projects_to_create = []
        projects_to_update = []

        for notion_project in notion_projects:
            notion_id = notion_project['id']

            # 3-1: 기존 프로젝트는 entity로 변환 후 수정
            if notion_id in existing_notion_ids:
                existing_project_dict = existing_notion_ids[notion_id]
                if self._needs_update_dict(existing_project_dict, notion_project):
                    existing_entity = self._dict_to_entity(existing_project_dict)
                    self._update_project_fields(existing_entity, notion_project)
                    projects_to_update.append(existing_entity)
            # 3-2: 신규 프로젝트는 새 Entity로 생성
            else:
                new_project = self._create_project_entity(notion_project)
                projects_to_create.append(new_project)

        # 4-1: 벌크 삽입
        if projects_to_create:
            created_count = self.project_repo.bulk_insert(projects_to_create)
        # 4-2: 벌크 업데이트
        if projects_to_update:
                updated_count = self.project_repo.bulk_update(projects_to_update)

        # 5: 삭제 처리
        projects_to_delete = []
        for project_dict in existing_projects_dict:
            if project_dict['notion_page_id'] and project_dict['notion_page_id'] not in notion_ids:
                projects_to_delete.append(project_dict['notion_page_id'])

        if projects_to_delete:
            deleted_count = self.project_repo.delete_by_notion_ids(projects_to_delete)

        return {
            'created': created_count,
            'updated': updated_count,
            'deleted': deleted_count
        }

    def _dict_to_entity(self, project_dict: Dict) -> Project:
        """Dict를 Entity로 변환"""
        return Project(
            id=project_dict['id'],
            notion_page_id=project_dict['notion_page_id'],
            name=project_dict['name'],
            status=project_dict['status'],
            start_date=project_dict['start_date'],
            end_date=project_dict['end_date'],
            target_value=project_dict['target_value'],
            current_progress=project_dict['current_progress']
        )

    def _needs_update_dict(self, existing_project_dict: Dict, notion_data: Dict) -> bool:
        """Dict 기반 업데이트 필요 여부 확인"""
        return (
            existing_project_dict['name'] != notion_data['name'] or
            existing_project_dict['status'] != notion_data['status'] or
            existing_project_dict['start_date'] != notion_data['start_date'] or
            existing_project_dict['end_date'] != notion_data['end_date']
        )

    def _create_project_entity(self, notion_data: Dict) -> Project:
        """노션 데이터로 Project Entity 생성"""
        return Project(
            notion_page_id=notion_data['id'],
            name=notion_data['name'],
            status=notion_data['status'],
            start_date=notion_data['start_date'],
            end_date=notion_data['end_date'],
            target_value=1,  # 기본값
            current_progress=0  # 기본값
        )

    def _update_project_fields(self, existing_project: Project, notion_data: Dict):
        """기존 프로젝트 필드 업데이트 (로컬 진행률 보존)"""
        existing_project.name = notion_data['name']
        existing_project.status = notion_data['status']
        existing_project.start_date = notion_data['start_date']
        existing_project.end_date = notion_data['end_date']

    # ===== 3. 프로젝트 진행률 벌크 수정 =====
    def bulk_update_projects(self, changes: List[Dict]) -> int:
        """여러 프로젝트의 진행률 일괄 업데이트"""
        try:
            # 데이터 검증
            validated_updates = []
            invalid_count = 0

            for change in changes:
                if self._validate_progress_data(change):
                    validated_updates.append({
                        'id': change['id'],
                        'target_value': change['target_value'],
                        'current_progress': change['current_progress']
                    })
                else:
                    invalid_count += 1

            if not validated_updates:
                raise Exception("⚙️❌ 유효한 진행률 데이터가 없습니다")

            if invalid_count > 0:
                raise Exception(f"⚙️❌ 잘못된 진행률 데이터 {invalid_count}개가 발견되었습니다")

            updated_count = self.project_repo.bulk_update_progress(validated_updates)

            return updated_count

        except Exception as e:
            raise e

    # ===== 4. 데이터 무결성 보장 (Service 계층) =====
    def _validate_progress_data(self, data: Dict) -> bool:
        """진행률 데이터 검증 - Service 계층에서 처리"""
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

            # 비즈니스 규칙 체크
            if target_value <= 0 or current_progress < 0:
                return False

            return True

        except Exception:
            return False

    # ===== 5. 노션 API 통합 처리 =====
    def _extract_project_from_notion_page(self, page: Dict) -> Optional[Dict]:
        """노션 페이지에서 프로젝트 데이터 추출"""
        try:
            properties = page.get("properties", {})

            # 1: 이름 추출 (title 타입)
            project_name = ""
            if "이름" in properties:
                title_prop = properties["이름"]
                if title_prop.get("type") == "title":
                    title_content = title_prop.get("title", [])
                    if title_content:
                        project_name = title_content[0].get("plain_text", "")

            # 2: 상태 추출 (status 타입)
            status = "Null"  # 기본값
            if "상태" in properties:
                status_prop = properties["상태"]
                if status_prop.get("type") == "status":
                    status_data = status_prop.get("status")
                    if status_data:
                        status = status_data.get("name", "Null")

            # 3: 시작일 추출 (date 타입)
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

            # 4: 종료일 추출 (date 타입)
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
            raise Exception(f"⚙️❌ 노션 페이지 데이터 추출 실패: {str(e)}")