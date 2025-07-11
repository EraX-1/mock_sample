from typing import Any

from src.repositories.index_repository import (
    IndexedFileRepository,
    SearchIndexTypeRepository,
)
from src.services.db import get_session


class IndexUsecase:
    def __init__(self, indexed_file_repository: IndexedFileRepository):
        self.indexed_file_repository = indexed_file_repository
        self.search_index_type_repository = SearchIndexTypeRepository()

    def get_all_indexed_files(self) -> list[dict[str, Any]]:
        """インデックス済みファイル一覧を取得"""
        with get_session() as session:
            indexed_files = session.query(self.indexed_file_repository.model).all()
            search_index_types = self.search_index_type_repository.find_all_ordered(
                session
            )

            # インデックスタイプの辞書を作成
            index_type_map = {st.id: st.folder_name for st in search_index_types}

            result = []
            for file in indexed_files:
                result.append(
                    {
                        "id": file.id,
                        "original_blob_name": file.original_blob_name,
                        "indexed_blob_name": file.indexed_blob_name,
                        "file_type": file.file_type,
                        "index_type": file.index_type,
                        "index_type_name": index_type_map.get(file.index_type, "不明"),
                        "indexed_at": file.indexed_at.isoformat()
                        if file.indexed_at
                        else None,
                    }
                )

            return result
