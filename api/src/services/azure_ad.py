import requests
from fastapi import HTTPException

from src.config.azure_config import MOCK_CONFIG


class MockAzureADService:
    """ローカル開発用のAzure ADモックサービス"""

    def __init__(self):
        self.mock_tokens = {
            "mock-token-user": MOCK_CONFIG["mock_user"],
            "mock-token-admin": MOCK_CONFIG["mock_admin_user"],
        }

    def get_user_info(self, access_token: str) -> dict:
        """モックユーザー情報を返す"""
        # トークンに基づいてユーザー情報を返す
        if access_token in self.mock_tokens:
            return self.mock_tokens[access_token]

        # デフォルトユーザーを返す
        return MOCK_CONFIG["mock_user"]


# モックサービスのインスタンス
mock_service = MockAzureADService() if MOCK_CONFIG["use_mock_services"] else None


def get_user_info(access_token: str) -> dict:
    """
    Microsoft Graph APIを使用してユーザー情報を取得する
    モックモードの場合はモックサービスを使用
    """
    # モックモードの場合
    if MOCK_CONFIG["use_mock_services"] and mock_service:
        return mock_service.get_user_info(access_token)

    # 本番モード
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Microsoft Graph APIのエンドポイント
    graph_url = "https://graph.microsoft.com/v1.0/me"

    try:
        response = requests.get(graph_url, headers=headers)
        response.raise_for_status()
        user_info = response.json()

        # 必要な情報を抽出
        return {
            "id": user_info.get("id"),
            "mail": user_info.get("mail") or user_info.get("userPrincipalName"),
            "displayName": user_info.get("displayName"),
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get user info from Microsoft Graph API: {str(e)}",
        )
