from src.dependencies.auth import get_current_user
from src.models.request_models import GetChatRoomRequest
from src.usecases.manage_chatroom_usecase import ManageChatroomUsecase


class ChatRoomController:
    def __init__(self):
        self.manage_chatroom_usecase = ManageChatroomUsecase()

    def get_current_user_id(self, request):
        user = get_current_user(request)
        return user["user_id"]

    def create_chat_room(self, request):
        user_id = self.get_current_user_id(request)
        return self.manage_chatroom_usecase.create_chat_room(user_id)

    def get_chat_rooms(self, request):
        user_id = self.get_current_user_id(request)
        return self.manage_chatroom_usecase.get_chat_rooms(user_id)

    def get_room_by_id(self, request, data: GetChatRoomRequest):
        user_id = self.get_current_user_id(request)
        chat_room_id = data.chat_room_id
        return self.manage_chatroom_usecase.get_room_by_id(user_id, chat_room_id)

    def update_chat_room(self, request, data):
        chat_room_id = data.chat_room_id
        name = data.name
        return self.manage_chatroom_usecase.update_chat_room(chat_room_id, name)

    def delete_chat_room(self, request, data):
        chat_room_id = data.chat_room_id
        return self.manage_chatroom_usecase.delete_chat_room(chat_room_id)
