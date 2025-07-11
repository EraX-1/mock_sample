import os
from functools import wraps

from fastapi import HTTPException, Request
from itsdangerous import URLSafeTimedSerializer

from src.repositories import UserRepository
from src.services.db import get_session

SECRET_KEY = os.environ["SECRET_KEY"]
serializer = URLSafeTimedSerializer(SECRET_KEY)

user_repository = UserRepository()


def create_session_token(data: dict):
    return serializer.dumps(data)


def verify_session_token(token: str, max_age: int = 3600):
    try:
        data = serializer.loads(token, max_age=max_age)
        return data
    except Exception:
        return None


def get_current_user(request: Request):
    # セッションからユーザー情報を取得
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=403, detail="Not authenticated")

    user_data = verify_session_token(token)
    if not user_data:
        raise HTTPException(status_code=403, detail="Invalid or expired session token")
    with get_session() as session:
        is_exist = user_repository.find_one_by_id(session, user_data.get("user_id"))
        if not is_exist:
            raise HTTPException(status_code=403, detail="User not found")

    return user_data


def requires_role(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # `request`を`kwargs`から取得
            request = kwargs.get("request")
            if not request:
                # 位置引数からrequestを探す
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(status_code=400, detail="Request is required")

            # `get_current_user`関数を用いてユーザー情報を取得
            user_data = get_current_user(request)

            # ユーザーのロールが許可されたロールのいずれかに一致するかチェック
            if user_data.get("role") in allowed_roles:
                return func(*args, **kwargs)

            # 必要なロールを持っていない場合
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return wrapper

    return decorator
