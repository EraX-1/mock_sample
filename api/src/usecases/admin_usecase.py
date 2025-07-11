from datetime import datetime, timedelta

from src.repositories import (
    MessageRepository,
    SearchIndexTypeRepository,
    UserRepository,
)
from src.services.db import get_session


class AdminUsecase:
    def __init__(self):
        self.user_repository = UserRepository()
        self.search_index_type_repository = SearchIndexTypeRepository()
        self.message_repository = MessageRepository()

    def get_admin_dashboard(self):
        with get_session() as session:
            today = datetime.utcnow().date()
            last_7days = [str(today - timedelta(days=i)) for i in range(6, -1, -1)]

            # チャット数の推移を取得
            chat_count_transition = (
                self.message_repository.get_latest_n_days_chat_count_transition(
                    session, 7
                )
            )
            last_7days_chat_transition = {
                str(elm[0]): elm[1] for elm in chat_count_transition
            }

            # トークン使用量の推移を取得
            token_usage_transition = (
                self.message_repository.get_latest_n_days_token_usage_transition(
                    session, 7
                )
            )
            last_7days_token_usage = {
                str(elm[0]): elm[1] for elm in token_usage_transition
            }

            # 日付ごとのデータを結合
            filled_last_7days_transition = [
                {
                    "date": date,
                    "chat_count": last_7days_chat_transition.get(date, 0),
                    "token_usage": last_7days_token_usage.get(date, 0),
                }
                for date in last_7days
            ]

            user_list = self.user_repository.get_all_users(session)

            res = {
                "last_24h_chat_count": self.message_repository.get_latest_n_days_chat_count(
                    session, 1
                ),
                "last_7days_transition": filled_last_7days_transition,
                "latest_chat_list": [
                    obj.serialize()
                    for obj in self.message_repository.get_latest_n_chat(session, 20)
                ],
                "user_list": [
                    {
                        "id": obj.id,
                        "email": obj.email,
                        "created_at": obj.created_at,
                        "role": obj.role,
                    }
                    for obj in user_list
                ],
            }
            return res

    def get_search_index_types(self):
        with get_session() as session:
            index_types = self.search_index_type_repository.find_all_ordered(session)
            return [
                {
                    "id": index_type.id,
                    "folder_name": index_type.folder_name,
                    "display_order": index_type.display_order,
                    "created_at": index_type.created_at,
                }
                for index_type in index_types
            ]

    def update_search_index_type(self, index_type_id: str, folder_name: str):
        with get_session() as session:
            # find_by_id の代わりに find_one_by_id を使用
            index_type = self.search_index_type_repository.find_one_by_id(
                session, index_type_id
            )
            if not index_type:
                return {
                    "success": False,
                    "message": "指定されたインデックスが見つかりません",
                }

            index_type.folder_name = folder_name
            session.commit()

            # 設定ファイルを更新するスクリプトを実行
            try:
                import subprocess

                subprocess.run(["node", "/app/scripts/updateCoreConfig.js"], check=True)
                return {"success": True, "message": "インデックス名を更新しました"}
            except Exception as e:
                return {
                    "success": True,
                    "message": f"インデックス名を更新しましたが、設定の反映に失敗しました: {str(e)}",
                }

    def reorder_search_index_types(self, index_type_ids: list):
        with get_session() as session:
            # 各IDに対して新しい順序を設定
            for i, index_type_id in enumerate(index_type_ids):
                # find_by_id の代わりに find_one_by_id を使用
                index_type = self.search_index_type_repository.find_one_by_id(
                    session, index_type_id
                )
                if index_type:
                    index_type.display_order = i

            session.commit()

            # 設定ファイルを更新するスクリプトを実行
            try:
                import subprocess

                subprocess.run(["node", "/app/scripts/updateCoreConfig.js"], check=True)
                return {"success": True, "message": "インデックスの順序を更新しました"}
            except Exception as e:
                return {
                    "success": True,
                    "message": f"インデックスの順序を更新しましたが、設定の反映に失敗しました: {str(e)}",
                }
