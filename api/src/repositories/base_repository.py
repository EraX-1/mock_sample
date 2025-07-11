from datetime import UTC, datetime
from typing import Any

import ulid
from sqlalchemy.orm import Session


#
# [C] SQLAlchemyリポジトリの基底クラス
#
class BaseRepository:
    """
    MongoDB版の機能をSQLAlchemy(MySQL)用に書き換えたベースクラス。
    """

    def __init__(self, model):
        self.model = model

    def insert_one(self, session: Session, data: dict):
        """
        1件のレコードを挿入する
        """
        record = self.model(**data)
        record.id = str(ulid.new())  # UUID4からULIDに変更
        record.created_at = datetime.now(UTC)
        record.updated_at = datetime.now(UTC)
        session.add(record)
        session.commit()
        session.refresh(record)  # レコードを最新の状態に更新
        return record

    def update_one(self, session: Session, record_id: str, data: dict[str, Any]):
        # updated_atを更新
        now = datetime.now(UTC)
        data["updated_at"] = now

        instance = session.get(self.model, record_id)
        if not instance:
            return None

        for k, v in data.items():
            setattr(instance, k, v)

        session.commit()
        session.refresh(instance)
        return instance

    def find_one_by_id(self, session: Session, record_id: str):
        return session.get(self.model, record_id)

    def delete_one(self, session: Session, record_id: str):
        instance = session.get(self.model, record_id)
        if instance:
            session.delete(instance)
            session.commit()
        return instance

    def find_all(self, session: Session):
        return session.query(self.model).all()
