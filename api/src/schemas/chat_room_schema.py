# chat_room_schema.py

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from .base import BaseTable


#
# [A] SQLAlchemyモデル
#
class ChatRoomTable(BaseTable):
    """
    MySQL上のテーブル(chat_rooms)を表すSQLAlchemyモデル。
    基底クラス(BaseTable)から created_at, updated_at, id などを継承。
    """

    __tablename__ = "chat_rooms"

    user_id = Column(String(26), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    custom_prompt = Column(Text, nullable=True)
    is_active_custom_prompt = Column(Boolean, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
