# file_schema.py

from sqlalchemy import Column, String

from .base import BaseTable


#
# [A] SQLAlchemyモデル
#
class FileTable(BaseTable):
    """
    MySQL上のテーブル(files)を表すSQLAlchemyモデル。
    基底クラス(BaseTable)から created_at, updated_at, id などを継承。
    """

    __tablename__ = "files"

    blob_name = Column(String(255), nullable=False)
