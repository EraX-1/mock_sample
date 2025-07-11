from src.models.base import CustomModel


class ChatRoom(CustomModel):
    """
    チャットルームのPydanticモデル。
    バリデーションやシリアライズを担当。
    """

    user_id: str
    name: str
    custom_prompt: str | None = None
    is_active_custom_prompt: bool | None = None
