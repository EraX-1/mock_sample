from src.dependencies.auth import get_current_user
from src.usecases.manage_chat_message_usecase import ManageChatMessageUsecase


class ChatMessageController:
    def __init__(self):
        self.manage_chat_message_usecase = ManageChatMessageUsecase()

    def get_current_user_id(self, request):
        user = get_current_user(request)
        return user["user_id"]

    def create_chat_message(self, request, data):
        print("\033[31m" + "コントローラ実行" + "\033[0m")
        user_id = self.get_current_user_id(request)
        return self.manage_chat_message_usecase.create_chat_message(
            user_id,
            data.chat_room_id,
            data.message,
            data.references,
            data.assistant_prompt,
            data.is_active_assistant_prompt,
            data.model,
            data.index_type,
            data.chat_history,
        )

    def get_chat_messages(self, request, chat_room_id):
        return self.manage_chat_message_usecase.get_chat_messages(chat_room_id)

    def put_message_evaluation(self, request, data):
        user_id = self.get_current_user_id(request)
        return self.manage_chat_message_usecase.put_message_evaluation(
            user_id, data.message_id, data.evaluation
        )
