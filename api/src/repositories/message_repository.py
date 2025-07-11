from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import Message
from src.schemas.message_schema import MessageTable

from .base_repository import BaseRepository


class MessageRepository(BaseRepository):
    """
    SQLAlchemy用リポジトリクラス。
    外部から注入されたSessionを使用してCRUD操作を行う。
    """

    def __init__(self):
        super().__init__(MessageTable)

    def find_all_by_chat_room_id(
        self, session: Session, chat_room_id: str
    ) -> list[Message]:
        """
        chat_room_idで絞り込んだレコードを取得する。
        """
        objs = (
            session.query(MessageTable)
            .filter(
                MessageTable.chat_room_id == chat_room_id,
                MessageTable.deleted_at.is_(None),
            )
            .order_by(MessageTable.created_at.asc())
            .all()
        )
        # BaseRepositoryのserialize()を使ってPydanticモデル(Message)に変換し、リスト化
        return objs

    def get_latest_n_days_chat_count(self, session: Session, days: int):
        last_n_days = datetime.utcnow() - timedelta(days=days)
        count = (
            session.query(MessageTable)
            .filter(MessageTable.created_at >= last_n_days)
            .count()
        )
        return count

    def get_latest_n_days_chat_count_transition(self, session: Session, days: int):
        last_n_days = datetime.utcnow() - timedelta(days=days)
        count_transition = (
            session.query(
                func.date(MessageTable.created_at).label("date"),
                func.count().label("count"),
            )
            .filter(MessageTable.created_at >= last_n_days)
            .group_by(func.date(MessageTable.created_at))
            .order_by(func.date(MessageTable.created_at))
            .all()
        )
        return count_transition

    def get_latest_n_chat(self, session: Session, count: int):
        objs = (
            session.query(MessageTable)
            .filter(MessageTable.role == "user")
            .order_by(MessageTable.created_at.desc())
            .limit(count)
            .all()
        )
        return objs

    def get_latest_n_days_token_usage_transition(self, session: Session, days: int):
        """
        過去n日間のトークン使用量の推移を取得する
        """
        last_n_days = datetime.utcnow() - timedelta(days=days)
        token_usage_transition = (
            session.query(
                func.date(MessageTable.created_at).label("date"),
                func.sum(MessageTable.token_usage).label("token_usage"),
            )
            .filter(MessageTable.created_at >= last_n_days)
            .filter(MessageTable.token_usage.isnot(None))  # token_usageがNULLでないレコードのみ
            .group_by(func.date(MessageTable.created_at))
            .order_by(func.date(MessageTable.created_at))
            .all()
        )
        return token_usage_transition
