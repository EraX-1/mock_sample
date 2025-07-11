from fastapi import HTTPException

from src.models import ChatRoom
from src.repositories import ChatRoomRepository
from src.services.db import get_session


class ManageChatroomUsecase:
    def __init__(self):
        self.chat_room_repository = ChatRoomRepository()

    def create_chat_room(self, user_id) -> ChatRoom:
        with get_session() as session:
            result = self.chat_room_repository.insert_one(
                session,
                {
                    "user_id": user_id,
                    "name": "チャットルーム",
                },
            )
            name = "新しいチャット"
            doc = self.chat_room_repository.update_one(
                session, result.id, {"name": name}
            )
            return doc.serialize()

    def get_chat_rooms(self, user_id) -> list[ChatRoom]:
        with get_session() as session:
            docs = self.chat_room_repository.find_all_not_deleted_by_user_id(
                session, user_id
            )
            return [doc.serialize() for doc in docs]

    def get_room_by_id(self, user_id, chat_room_id) -> ChatRoom:
        with get_session() as session:
            doc = self.chat_room_repository.find_one_by_id(session, chat_room_id)

            # チャットルームが存在しない、または論理削除されている場合は404
            if doc is None or doc.deleted_at is not None:
                raise HTTPException(status_code=404, detail="Chat room not found")

            # チャットルームの所有者がユーザーでない場合は403
            if doc.user_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: You do not have permission to access this resource.",
                )

            return doc.serialize()

    def update_chat_room(self, chat_room_id, name) -> ChatRoom:
        new_data_dict = {}
        if name:
            new_data_dict["name"] = name
        with get_session() as session:
            doc = self.chat_room_repository.update_one(
                session, chat_room_id, new_data_dict
            )
            return doc.serialize()

    def delete_chat_room(self, chat_room_id) -> dict:
        try:
            with get_session() as session:
                self.chat_room_repository.logical_delete(session, chat_room_id)
        except Exception:
            return {"success": "false"}
        return {"success": "true"}
