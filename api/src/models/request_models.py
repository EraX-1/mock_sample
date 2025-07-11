from pydantic import BaseModel, Field

from src.internal.searcher import ChatHistoryItem


class LoginRequest(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., example="Password123")


class SignupRequest(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., example="Password123")


class DeleteChatRoomRequest(BaseModel):
    chat_room_id: str = Field(..., example="UUID")


class CreateChatMessageRequest(BaseModel):
    chat_room_id: str
    message: str
    references: list[str] = []
    assistant_prompt: str = None
    is_active_assistant_prompt: bool = False
    model: str = "GPT-4o-mini"
    index_type: list[str]
    temperature: float = 1.0
    chat_history: list[ChatHistoryItem] = None


class UpdateChatEvaluation(BaseModel):
    message_id: str
    evaluation: str


class GetChatRoomRequest(BaseModel):
    chat_room_id: str


class UpdateChatroomRequest(BaseModel):
    chat_room_id: str
    prompt: str = None
    name: str = None


class UpdateUserRoleRequest(BaseModel):
    user_id: str
    role: str


class UpdateSearchIndexTypeRequest(BaseModel):
    index_type_id: str
    folder_name: str


class ReorderSearchIndexTypesRequest(BaseModel):
    index_type_ids: list[str]
