# message_schema.py

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Text

from .base import BaseTable


#
# [A] SQLAlchemyモデル
#
class MessageTable(BaseTable):
    """
    MySQL上のテーブル(chat_messages)を表すSQLAlchemyモデル。
    基底クラス(BaseTable)から created_at, updated_at, id などを継承。
    """

    __tablename__ = "chat_messages"

    chat_room_id = Column(String(26), ForeignKey("chat_rooms.id"), nullable=False)
    role = Column(Enum("user", "assistant", name="role_enum"), nullable=False)
    message = Column(Text, nullable=False)
    references = Column(JSON, nullable=False)  # JSON型として保存
    evaluation = Column(
        Enum("none", "good", "bad", name="evaluation_enum"),
        default="none",
        nullable=False,
    )
    assistant_prompt = Column(Text, nullable=True)
    model = Column(String(50), default="gpt-4o-mini", nullable=False)
    token_usage = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    index_types = Column(JSON, nullable=True)  # JSON型として保存
