"""
데이터베이스 연결 및 세션 관리
SQLite 기반의 로컬 데이터베이스 설정
"""

import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .base import Base


class DatabaseManager:
    """
    데이터베이스 연결과 세션을 관리하는 싱글톤 클래스
    """

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is None:
            self._initialize_database()

    def _initialize_database(self) -> None:
        """
        데이터베이스 엔진 및 세션 팩토리 초기화
        """
        database_url = self._get_database_url()
        self._create_engine(database_url)
        self._create_session_factory()
        self.create_tables()
        self._configure_sqlite()

    def _get_database_url(self) -> str:
        """
        데이터베이스 URL 생성 및 디렉토리 확인
        """
        # 1: 현재 파일 기준 상대 경로 계산
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..', '..')
        data_dir = os.path.join(project_root, 'data')

        # 2: 디렉토리 존재 확인 및 생성
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, mode=0o755)
            print(f"🗂️ 데이터 디렉토리 생성: {data_dir}")

        # 3: DB 파일 경로 생성
        db_path = os.path.join(data_dir, 'project_tracker.db')

        # 4: DB 파일 존재 여부 확인
        if not os.path.exists(db_path):
            print(f"🔧 새로운 데이터베이스 생성: {db_path}")
        else:
            print(f"🔗 기존 데이터베이스 사용: {db_path}")

        return f"sqlite:///{db_path}"

    def _create_engine(self, database_url: str) -> None:
        """
        SQLAlchemy 엔진 생성
        """
        self._engine = create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    def _create_session_factory(self) -> None:
        """
        세션 팩토리 생성
        """
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )

    def create_tables(self) -> None:
        """
        모든 테이블 생성
        """
        # 모든 엔티티를 import해서 메타데이터에 등록
        from ..entities.project import Project
        from ..entities.work_log import WorkLog

        # 테이블 생성
        Base.metadata.create_all(bind=self._engine)

    def _configure_sqlite(self) -> None:
        """
        SQLite 성능 최적화 설정
        """
        with self._engine.connect() as conn:
            # 외래키 제약조건 활성화
            conn.execute(text("PRAGMA foreign_keys=ON"))
            # WAL 모드로 설정 (동시성 향상)
            conn.execute(text("PRAGMA journal_mode=WAL"))
            # 동기화 설정 (성능과 안정성 균형)
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            # 캐시 크기 설정 (메모리 사용량 최적화)
            conn.execute(text("PRAGMA cache_size=1000"))
            conn.commit()

    def get_session(self) -> Session:
        """
        특수용도: 세션 수동 관리
        """
        return self._session_factory()

    def get_session_context(self) -> Generator[Session, None, None]:
        """
        대체로: 컨텍스트 매니저를 사용한 자동 세션 관리
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def engine(self):
        """엔진 인스턴스 반환"""
        return self._engine


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()


def get_db_session() -> Generator[Session, None, None]:
    """
    의존성 주입을 위한 세션 제공 함수
    FastAPI나 다른 프레임워크와의 통합에 유용
    """
    yield from db_manager.get_session_context()


def get_db() -> Session:
    """
    단순한 세션 반환 함수
    Streamlit과 같은 환경에서 사용
    """
    return db_manager.get_session()