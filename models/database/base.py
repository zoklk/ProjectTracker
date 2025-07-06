from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from typing import Any


class Base(DeclarativeBase):
    # 테이블 네이밍 컨벤션 설정
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )

    def to_dict(self) -> dict[str, Any]:
        """
        ORM 객체를 딕셔너리로 변환
        JSON 시리얼라이제이션에 유용
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """
        객체의 문자열 표현
        디버깅과 로깅에 유용
        """
        class_name = self.__class__.__name__
        attrs = []

        # Primary key나 name 컬럼을 우선적으로 표시
        for column in self.__table__.columns:
            if column.primary_key or column.name == 'name':
                value = getattr(self, column.name)
                attrs.append(f"{column.name}={value!r}")

        return f"{class_name}({', '.join(attrs)})"
