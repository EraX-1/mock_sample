import logging

from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# 依存関係からユーザー取得関数をインポート
# 循環インポートを避けるため、try-exceptで囲むか、
# または get_current_user を別の場所に移動することを検討する必要があるかも
try:
    from src.dependencies.auth import get_current_user
except ImportError:
    # 依存関係の問題が発生した場合のフォールバック
    # ログ出力などで警告し、get_current_user を None に設定
    logging.warning(
        "Could not import get_current_user from dependencies.auth. User ID logging might be affected."
    )
    get_current_user = None


class AddAttributeMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        リクエストからユーザーIDを取得し、現在のトレーススパンに属性として追加するミドルウェア。
        """
        span = trace.get_current_span()

        # スパンが有効（記録対象）の場合のみ属性を追加
        if span and span.is_recording():
            user_id = None
            # 認証が必要なエンドポイントの場合、ユーザー情報を取得試行
            # get_current_user がインポートできていれば実行
            if get_current_user:
                try:
                    # get_current_user は Request オブジェクトを必要とする
                    user_info = get_current_user(request)
                    if user_info and "user_id" in user_info:
                        user_id = user_info["user_id"]
                except Exception:
                    # get_current_user は認証されていない場合に例外を発生させる可能性がある
                    # または、認証不要のエンドポイントではユーザー情報は取得できない
                    # そのため、例外が発生してもここでは処理を続行する
                    pass

            if user_id:
                # OpenTelemetry のセマンティック規約に従い 'enduser.id' を使用
                span.set_attribute("enduser.id", str(user_id))

        # 次のミドルウェアまたはルートハンドラを呼び出す
        response = await call_next(request)

        return response
