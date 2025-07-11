from src.schemas.file_schema import FileTable

from .base_repository import BaseRepository


class FileRepository(BaseRepository):
    """
    SQLAlchemy用リポジトリクラス。
    外部から注入されたSessionを使用してCRUD操作を行う。
    """

    def __init__(self):
        super().__init__(FileTable)
