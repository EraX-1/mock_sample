import msal
from fastapi import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse

from src.config.azure_config import AZURE_CONFIG, MOCK_CONFIG
from src.dependencies.auth import create_session_token
from src.repositories import UserRepository
from src.services.azure_ad import get_user_info
from src.services.db import get_session


class UserAuthenticationUsecase:
    def __init__(self):
        self.user_repository = UserRepository()

    def get_msal_app(self):
        # モックモードの場合はNoneを返す（実際には使用されない）
        if MOCK_CONFIG["use_mock_services"]:
            return None

        # Azure AD設定の検証
        required_config = {
            "client_id": AZURE_CONFIG.get("client_id"),
            "client_secret": AZURE_CONFIG.get("client_secret"),
            "authority": AZURE_CONFIG.get("authority"),
            "redirect_uri": AZURE_CONFIG.get("redirect_uri"),
        }

        missing_configs = [key for key, value in required_config.items() if not value]
        if missing_configs:
            raise HTTPException(
                status_code=500,
                detail=f"Azure AD configuration missing: {', '.join(missing_configs)}. Please set the required environment variables.",
            )

        try:
            return msal.ConfidentialClientApplication(
                AZURE_CONFIG["client_id"],
                authority=AZURE_CONFIG["authority"],
                client_credential=AZURE_CONFIG["client_secret"],
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize Azure AD client: {str(e)}",
            )

    def get_auth_url(self, admin_mode=False):
        # デバッグ用ログ
        print(f"DEBUG: get_auth_url called with admin_mode={admin_mode}")
        print(f"DEBUG: MOCK_CONFIG={MOCK_CONFIG}")
        print(f"DEBUG: USE_MOCK_SERVICES={MOCK_CONFIG.get('use_mock_services')}")

        # モックモードの場合、ダミーの認証URLを返す
        if MOCK_CONFIG["use_mock_services"]:
            print("DEBUG: Using mock mode")
            import os

            from src.config.azure_config import config

            frontend_url = config.get("env", {}).get(
                "FRONTEND_URL", os.getenv("FRONTEND_URL", "http://localhost:3000")
            )
            print(f"DEBUG: frontend_url={frontend_url}")
            if admin_mode:
                return {
                    "auth_url": f"{frontend_url}/auth/callback?code=mock-admin-code"
                }
            else:
                return {"auth_url": f"{frontend_url}/auth/callback?code=mock-auth-code"}

        msal_app = self.get_msal_app()
        auth_url = msal_app.get_authorization_request_url(
            scopes=AZURE_CONFIG["scope"], redirect_uri=AZURE_CONFIG["redirect_uri"]
        )
        return {"auth_url": auth_url}

    async def handle_auth_callback(self, code: str):
        # モックモードの場合、モックユーザー情報を使用
        if MOCK_CONFIG["use_mock_services"]:
            if code == "mock-auth-code":
                user_info = MOCK_CONFIG["mock_user"]
            elif code == "mock-admin-code":
                user_info = MOCK_CONFIG["mock_admin_user"]
            else:
                # デフォルトでモックユーザーを返す
                user_info = MOCK_CONFIG["mock_user"]
        else:
            # 本番モード
            msal_app = self.get_msal_app()
            result = msal_app.acquire_token_by_authorization_code(
                code,
                scopes=AZURE_CONFIG["scope"],
                redirect_uri=AZURE_CONFIG["redirect_uri"],
            )

            if "error" in result:
                raise HTTPException(
                    status_code=400, detail=result.get("error_description")
                )

            # Microsoftグラフ APIからユーザー情報を取得
            access_token = result["access_token"]
            user_info = get_user_info(access_token)

        with get_session() as session:
            # まずazure_idで既存ユーザーを検索
            user = self.user_repository.get_user_by_azure_id(session, user_info["id"])

            # azure_idで見つからない場合、emailで検索
            if not user:
                user = self.user_repository.get_user_by_email(
                    session, user_info["mail"]
                )

                # emailでも見つからない場合のみ新規ユーザー登録
                if not user:
                    # モック管理者ユーザーの場合は admin ロール、それ以外は user ロール
                    role = (
                        "admin"
                        if user_info["id"] == MOCK_CONFIG["mock_admin_user"]["id"]
                        else "user"
                    )
                    user_data = {
                        "email": user_info["mail"],
                        "azure_id": user_info["id"],
                        "name": user_info["displayName"],
                        "role": role,
                    }
                    user = self.user_repository.insert_one(session, user_data)
                    session.refresh(user)  # セッションを最新の状態に更新
                else:
                    # emailで見つかった場合、azure_idを更新
                    user = self.user_repository.update_one(
                        session=session,
                        record_id=user.id,
                        data={"azure_id": user_info["id"]},
                    )

            # セッション内でトークンを生成
            token = create_session_token(
                {
                    "user_id": str(user.id),
                    "email": user.email,
                    "role": user.role,
                    "azure_id": user.azure_id,
                }
            )

            frontend_url = AZURE_CONFIG.get("frontend_url")
            response = RedirectResponse(url=f"{frontend_url}/chat")
            response.set_cookie(
                key="session_token",
                value=token,
                secure=True,
                max_age=259200,
                samesite="None",
                httponly=True,
            )
            return response

    def logout(self):
        response = JSONResponse({"message": "Logout successful"})
        response.delete_cookie(
            key="session_token", secure=True, samesite="None", httponly=True
        )
        return response

    def dropout(self, user_id: str):
        with get_session() as session:
            self.user_repository.archive_user(session, user_id)
            return self.logout()

    def update_user_role(self, admin_user, user_id, role):
        if admin_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="管理者権限が必要です")

        with get_session() as session:
            user = self.user_repository.find_one_by_id(session, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

            updated_user = self.user_repository.update_one(
                session=session, record_id=user_id, data={"role": role}
            )
            return {
                "message": "ユーザー権限を更新しました",
                "user": updated_user.serialize(),
            }
