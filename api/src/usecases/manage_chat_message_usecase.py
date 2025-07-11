from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from src.internal.searcher import semantic_hybrid_search
from src.models import Message
from src.repositories import (
    ChatRoomRepository,
    MessageRepository,
    SearchIndexTypeRepository,
)
from src.services.db import get_session


class ManageChatMessageUsecase:
    def __init__(
        self,
    ):
        self.chat_message_repository = MessageRepository()
        self.chat_room_repository = ChatRoomRepository()
        self.search_index_type_repository = SearchIndexTypeRepository()

    def create_chat_message(
        self,
        user_id,
        chat_room_id,
        message,
        references,
        assistant_prompt,
        is_active_assistant_prompt,
        model,
        index_type,
        chat_history,
    ) -> Message:
        print("\033[31m" + "ユースケース実行" + "\033[0m")
        with get_session() as session:
            chat_room_doc = self.chat_room_repository.find_one_by_id(
                session, chat_room_id
            )
            # チャットルームが存在するか？
            if not chat_room_doc:
                raise HTTPException(status_code=404, detail="Not found ChatRoom.")
            # チャットルーム所有者なら処理
            if chat_room_doc.user_id == user_id:
                # print('\033[31m'+ "index_type: " + index_type + '\033[0m')
                print("index_type: ", index_type)
                message_data_dict = {
                    "chat_room_id": chat_room_id,
                    "role": "user",
                    "message": message,
                    "references": references,
                    "assistant_prompt": assistant_prompt
                    if is_active_assistant_prompt
                    else None,
                    "model": model,
                    "index_types": index_type,
                }
                # ユーザメッセージ保存
                self.chat_message_repository.insert_one(session, message_data_dict)
                self.chat_room_repository.update_one(
                    session,
                    chat_room_doc.id,
                    {
                        "custom_prompt": assistant_prompt,
                        "is_active_custom_prompt": is_active_assistant_prompt,
                    },
                )
                try:
                    (
                        stream_generator,
                        get_full_content,
                        references,
                        get_token_usage,
                    ) = semantic_hybrid_search(
                        query=message,
                        index_type_list=index_type,
                        custom_prompt=assistant_prompt,
                        is_active_custom_prompt=is_active_assistant_prompt,
                        model=model,
                        history=chat_history,
                    )
                except RuntimeError as e:
                    assistant_message_data = {
                        "chat_room_id": chat_room_id,
                        "role": "assistant",
                        "message": str(e),
                        "assistant_prompt": assistant_prompt,
                        "model": model,
                        "references": [],
                        "index_types": index_type,
                    }
                    self.chat_message_repository.insert_one(
                        session, assistant_message_data
                    )
                    raise HTTPException(status_code=500, detail=str(e))

                # 完了したらassistantとしてメッセージ登録
                def wrapped_stream():
                    for item in stream_generator():
                        if "<<TOKEN_INFO>>" not in item:
                            yield item

                    # ストリームが完全に終了した後にコールバックとしてDB登録
                    full_content = get_full_content()
                    token_usage = get_token_usage()

                    assistant_message_data = {
                        "chat_room_id": chat_room_id,
                        "role": "assistant",
                        "message": full_content,
                        "assistant_prompt": assistant_prompt,
                        "model": model,
                        "references": references,
                        "token_usage": token_usage["total_tokens"],
                    }
                    with get_session() as session:
                        self.chat_message_repository.insert_one(
                            session, assistant_message_data
                        )

                return StreamingResponse(wrapped_stream(), media_type="text/plain")

            else:
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: You do not have permission to access this resource.",
                )

    def get_chat_messages(self, chat_room_id):
        with get_session() as session:
            docs = self.chat_message_repository.find_all_by_chat_room_id(
                session, chat_room_id
            )
            return [doc.serialize() for doc in docs]

    def put_message_evaluation(self, user_id, message_id, evaluation):
        with get_session() as session:
            message_doc = self.chat_message_repository.find_one_by_id(
                session, message_id
            )
            chat_room_doc = self.chat_room_repository.find_one_by_id(
                session, message_doc.chat_room_id
            )
            # チャットルームが存在するか？
            if not chat_room_doc:
                raise HTTPException(status_code=404, detail="Not found ChatRoom.")
            # チャットルーム所有者なら処理
            if chat_room_doc.user_id == user_id:
                doc = self.chat_message_repository.update_one(
                    session, message_id, {"evaluation": evaluation}
                )

                return {"message": doc.serialize()}
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: You do not have permission to access this resource.",
                )

    def get_index_type_details(self, index_type_list):
        """index_type_listから詳細情報を取得して返す"""
        index_types = []
        with get_session() as session:
            for index_type_id in index_type_list:
                index_type = self.search_index_type_repository.find_by_id(
                    session, index_type_id
                )
                if index_type:
                    index_types.append(
                        {"id": index_type.id, "folder_name": index_type.folder_name}
                    )
        return index_types
