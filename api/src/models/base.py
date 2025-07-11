from datetime import datetime

from pydantic import BaseModel, Field


class CustomModel(BaseModel):
    """
    ここでは ULID文字列を id として扱い、
    created_at, updated_at は datetime型を想定。
    """

    id: str | None = Field(None)  # ULIDの文字列
    created_at: datetime
    updated_at: datetime
