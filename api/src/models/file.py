from pydantic import Field

from .base import CustomModel


class File(CustomModel):
    """
    MongoDB版のFileに相当するPydanticモデル。
    バリデーションやシリアライズを担当。
    """

    blob_name: str = Field(description="Azure Storage AccountのBlobの名前")
