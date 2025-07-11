import json
from typing import Literal

from pydantic import field_serializer, field_validator

from .base import CustomModel


class Message(CustomModel):
    """
    MongoDB版のMessageに相当するPydanticモデル。
    バリデーションやシリアライズを担当。
    """

    chat_room_id: str
    role: Literal["user", "assistant"]
    message: str
    references: list[str]
    evaluation: Literal["none", "good", "bad"] = "none"
    assistant_prompt: str | None = None
    model: str = "gpt-4o-mini"
    index_types: list[dict[str, str]] | None = None

    @field_serializer("references")
    def serialize_references(self, references: list[str]) -> str:
        return json.dumps(references)

    @field_validator("references", mode="before")
    def deserialize_references(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value

    @field_serializer("index_types")
    def serialize_index_types(
        self, index_types: list[dict[str, str]] | None
    ) -> str | None:
        if index_types is None:
            return None
        return json.dumps(index_types)

    @field_validator("index_types", mode="before")
    def deserialize_index_types(
        cls, value: str | list[dict[str, str]] | None
    ) -> list[dict[str, str]] | None:
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value
