# chat_room_schema.py

import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy import func as sql_func

from .base import Base


#
# [A] SQLAlchemyモデル
#
class IndexedFileTable(Base):
    __tablename__ = "indexed_files"
    id = Column(Integer, primary_key=True, index=True)
    original_blob_name = Column(String(512), unique=True, nullable=False, index=True)
    indexed_blob_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    # index_type は SearchIndexType.id を参照する
    index_type = Column(String(36), nullable=False)
    indexed_at = Column(DateTime, default=datetime.datetime.utcnow)


class SearchIndexTypeTable(Base):
    __tablename__ = "search_index_types"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    folder_name = Column(String(255), unique=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime, server_default=sql_func.current_timestamp(), nullable=False
    )
