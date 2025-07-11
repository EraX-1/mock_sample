from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import asc, desc

from src.schemas.chat_room_schema import ChatRoomTable
from src.schemas.message_schema import MessageTable

from .base_repository import BaseRepository


class ChatRoomRepository(BaseRepository):
    """
    SQLAlchemy用リポジトリクラス。
    外部から注入されたSessionを使用してCRUD操作を行う。
    """

    def __init__(self):
        super().__init__(ChatRoomTable)

    def create(self, session: Session, user_id: str, title: str) -> dict:
        obj = ChatRoomTable(user_id=user_id, title=title)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return self.serialize(obj)

    def find_by_id(self, session: Session, chat_room_id: str) -> dict:
        obj = (
            session.query(ChatRoomTable)
            .filter(ChatRoomTable.id == chat_room_id)
            .first()
        )
        return obj

    def find_all_by_user_id(self, session: Session, user_id: str) -> list:
        objs = (
            session.query(ChatRoomTable)
            .filter(ChatRoomTable.user_id == user_id)
            .order_by(desc(ChatRoomTable.updated_at))
            .all()
        )
        return objs

    def find_all_not_deleted_by_user_id(self, session: Session, user_id: str) -> list:
        objs = (
            session.query(ChatRoomTable)
            .filter(
                ChatRoomTable.user_id == user_id, ChatRoomTable.deleted_at.is_(None)
            )
            .order_by(asc(ChatRoomTable.created_at))
            .all()
        )
        return objs

    def logical_delete(self, session: Session, chat_room_id: str) -> None:
        """
        チャットルームと関連するメッセージを論理削除する
        """
        # 関連するメッセージを論理削除
        session.query(MessageTable).filter(
            MessageTable.chat_room_id == chat_room_id, MessageTable.deleted_at.is_(None)
        ).update({"deleted_at": datetime.utcnow()}, synchronize_session=False)

        # チャットルームを論理削除
        obj = (
            session.query(ChatRoomTable)
            .filter(
                ChatRoomTable.id == chat_room_id, ChatRoomTable.deleted_at.is_(None)
            )
            .first()
        )
        if obj:
            obj.deleted_at = datetime.utcnow()
            session.commit()
