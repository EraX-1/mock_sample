from sqlalchemy.orm import Session

from src.schemas.index_schema import IndexedFileTable, SearchIndexTypeTable

from .base_repository import BaseRepository


class IndexedFileRepository(BaseRepository):
    def __init__(self):
        super().__init__(IndexedFileTable)


class SearchIndexTypeRepository(BaseRepository):
    def __init__(self):
        super().__init__(SearchIndexTypeTable)

    def find_all_ordered(self, session: Session):
        """表示順序でソートされた全てのインデックスタイプを取得"""
        return session.query(self.model).order_by(self.model.display_order).all()

    def find_by_id(self, session: Session, id: str):
        """IDによるインデックスタイプの検索"""
        return session.query(self.model).filter(self.model.id == id).first()
