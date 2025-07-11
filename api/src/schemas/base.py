from datetime import datetime

import ulid
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.ext.declarative import declarative_base

# BaseTableをBaseとしても使えるようにする
Base = BaseTable = declarative_base()


class BaseTable(Base):
    """
    全テーブル共通の抽象クラス。
    主キーに ULID (26文字の文字列) を使用し、先頭に定義しています。
    次いで created_at, updated_at の順番。
    """

    __abstract__ = True

    id = Column(
        String(26), primary_key=True, default=lambda: str(ulid.new()), nullable=False
    )

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def serialize(self):
        data = {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
