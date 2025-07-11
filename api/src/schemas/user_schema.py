# user_schema.py

from sqlalchemy import Boolean, Column, String

from .base import BaseTable


#
# [A] SQLAlchemyモデル
#
class UserTable(BaseTable):
    """
    MySQL上のテーブル(users)を表すSQLAlchemyモデル。
    基底クラス(BaseTable)から created_at, updated_at, id などを継承。
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False)
    azure_id = Column(String(255), unique=True, nullable=False)  # Azure ADのユーザーID
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)
    is_archive = Column(Boolean, default=False, nullable=False)
