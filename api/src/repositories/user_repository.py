from sqlalchemy.orm import Session

from src.models import User
from src.schemas.user_schema import UserTable

from .base_repository import BaseRepository


class UserRepository(BaseRepository):
    """
    SQLAlchemy用リポジトリクラス。
    外部から注入されたSessionを使用してCRUD操作を行う。
    """

    def __init__(self):
        super().__init__(UserTable)

    def get_user_by_email(self, session: Session, email: str) -> User | None:
        """
        emailでユーザーを取得する。
        """
        user = (
            session.query(UserTable)
            .filter(
                UserTable.email == email,
                (UserTable.is_archive == False) | (UserTable.is_archive.is_(None)),
            )
            .first()
        )
        return user

    def get_user_by_azure_id(self, session: Session, azure_id: str) -> User | None:
        return (
            session.query(UserTable)
            .filter(
                UserTable.azure_id == azure_id,
                (UserTable.is_archive == False) | (UserTable.is_archive.is_(None)),
            )
            .first()
        )

    def archive_user(self, session: Session, user_id: str) -> User | None:
        """
        指定したユーザーをアーカイブする (is_archive=True)。
        """
        return self.update_one(
            session=session, record_id=user_id, data={"is_archive": True}
        )

    def get_all_users(self, session: Session) -> User | None:
        """
        全てのユーザーを取得する。
        """
        return session.query(UserTable).filter(UserTable.is_archive == False).all()
