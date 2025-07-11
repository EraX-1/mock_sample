from pydantic import EmailStr

from .base import CustomModel


class User(CustomModel):
    """
    バリデーションやシリアライズを担当。
    """

    email: EmailStr
    azure_id: str
    name: str
    role: str = "user"
