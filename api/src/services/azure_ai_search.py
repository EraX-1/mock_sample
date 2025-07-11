import logging
import os
from datetime import datetime
from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

from src.config.azure_config import get_search_config

# ロガーの設定
logger = logging.getLogger(__name__)

# Azure AI Search用の簡易設定（モック設定を使用しない）
CONFIG = {
    "env": {},
    "core": {
        "SEARCH_INDEX_NAME_ID_LIST": ["documents"],
        "SEARCH_INDEX_AZURE_ID_LIST": ["yuyama-documents-index"],
    },
}


class AzureAISearch:
    """
    Azure AI Search Python SDK統合クライアント

    主な機能:
    - Search Clientの初期化と設定
    - ドキュメント検索（ベクター検索対応）
    - インデックス管理
    - セキュリティとエラーハンドリング
    """

    def __init__(self, config=CONFIG):
        # 設定の初期化 (モックロジックを無視して常に実際のAzureサービスを使用)
        self.config = config

        # Azure AI Search設定の取得 (常に実際のAzureサービス設定を使用)
        search_config = get_search_config()

        # 常に実際のAzure AI Searchサービスに接続
        self.search_endpoint = search_config.get(
            "endpoint", "https://yuyama-ai-search-std.search.windows.net/"
        )
        self.search_api_key = search_config.get("admin_key")
        self.api_version = search_config.get("api_version", "2023-11-01")

        # デフォルトインデックス名 (実際のAzureサービスのインデックス名)
        self.default_index_name = search_config.get(
            "index_name", "yuyama-documents-index"
        )

        # エンドポイントの正規化 - "/mock/search/"プレフィックス問題の修正
        if self.search_endpoint.endswith("/"):
            self.search_endpoint = self.search_endpoint.rstrip("/")

        # "/mock/search/"プレフィックスが含まれている場合の修正
        if "/mock/search/" in self.search_endpoint:
            self.search_endpoint = self.search_endpoint.replace("/mock/search/", "/")
            logger.warning(f"修正前のエンドポイント: {search_config.get('endpoint')}")
            logger.warning(f"修正後のエンドポイント: {self.search_endpoint}")

        # 環境変数の確認とログ出力
        env_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        if env_endpoint:
            logger.info(f"環境変数AZURE_SEARCH_ENDPOINT: {env_endpoint}")
            if "/mock/search/" in env_endpoint:
                logger.error("環境変数に/mock/search/プレフィックスが含まれています")

        logger.info(
            f"Azure AI Search initialized (PRODUCTION MODE) - Endpoint: {self.search_endpoint}, Index: {self.default_index_name}"
        )
        logger.info(f"API Version: {self.api_version}")

        # エンドポイントの検証
        if not self.search_endpoint.startswith("https://"):
            logger.error(f"無効なエンドポイント形式: {self.search_endpoint}")
            raise ValueError(
                f"Azure Search エンドポイントは https:// で始まる必要があります: {self.search_endpoint}"
            )

        # インデックスタイプとインデックス名のマッピング
        self.index_mappings = {
            "01INDEX01TYPE001001001001": "yuyama-documents-index",
            # 他のインデックスタイプがあれば追加
        }

    def init_search_index_client(self) -> SearchIndexClient:
        """
        検索インデックスクライアントを初期化

        Returns:
            SearchIndexClient: インデックス管理用クライアント
        """
        try:
            search_index_client = SearchIndexClient(
                endpoint=self.search_endpoint,
                credential=AzureKeyCredential(self.search_api_key),
            )
            logger.info("Azure AI Search Index Client initialized successfully")
            return search_index_client
        except Exception as e:
            logger.error(f"Failed to initialize search index client: {str(e)}")
            raise Exception(f"Search index client initialization failed: {str(e)}")

    def init_search_client(self, index_name: str | None = None) -> SearchClient:
        """
        検索クライアントを初期化

        Args:
            index_name (Optional[str]): インデックス名（指定しない場合はデフォルト）

        Returns:
            SearchClient: 検索実行用クライアント
        """
        target_index = index_name or self.default_index_name

        try:
            # デバッグ情報をログ出力
            logger.info("SearchClient初期化開始:")
            logger.info(f"  エンドポイント: {self.search_endpoint}")
            logger.info(f"  インデックス名: {target_index}")
            logger.info(f"  APIキー: {self.search_api_key[:10]}...")

            search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=target_index,
                credential=AzureKeyCredential(self.search_api_key),
            )

            # クライアントの内部エンドポイントを確認
            logger.info(
                f"SearchClient内部エンドポイント: {getattr(search_client, '_endpoint', 'unknown')}"
            )
            logger.info(
                f"Azure AI Search Client initialized successfully for index: {target_index}"
            )
            return search_client
        except Exception as e:
            logger.error(
                f"Failed to initialize search client for index {target_index}: {str(e)}"
            )
            logger.error(f"エンドポイント詳細: {self.search_endpoint}")
            logger.error(f"APIキー詳細: {self.search_api_key[:10]}...")
            raise Exception(f"Search client initialization failed: {str(e)}")

    def search_documents(
        self,
        query: str,
        filters: str | None = None,
        top: int = 10,
        include_total_count: bool = True,
        index_name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        ドキュメント検索を実行

        Args:
            query (str): 検索クエリ
            filters (Optional[str]): フィルター条件
            top (int): 取得件数
            include_total_count (bool): 総件数を含めるか
            index_name (Optional[str]): 検索対象のインデックス名
            **kwargs: その他の検索パラメータ

        Returns:
            Dict[str, Any]: 検索結果
        """
        search_client = self.init_search_client(index_name)

        try:
            # 検索パラメータを設定
            search_params = {
                "search_text": query,
                "top": top,
                "include_total_count": include_total_count,
                **kwargs,
            }

            if filters:
                search_params["filter"] = filters

            # 検索実行
            results = search_client.search(**search_params)

            # 結果をリストに変換
            documents = []
            total_count = 0

            for result in results:
                documents.append(dict(result))

            # 総件数を取得（可能な場合）
            if hasattr(results, "get_count"):
                total_count = results.get_count()

            logger.info(
                f"Search completed: {len(documents)} documents found for query: '{query[:50]}...'"
            )

            return {
                "documents": documents,
                "count": len(documents),
                "total_count": total_count,
                "query": query,
                "index_name": index_name or self.default_index_name,
            }

        except HttpResponseError as e:
            logger.error(f"Azure Search API error: {e.message}")
            raise Exception(f"Search operation failed: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}")
            raise Exception(f"Search operation failed: {str(e)}")

    def upload_documents(
        self, documents: list[dict[str, Any]], index_name: str | None = None
    ) -> dict[str, Any]:
        """
        ドキュメントをインデックスにアップロード

        Args:
            documents (List[Dict[str, Any]]): アップロードするドキュメントリスト
            index_name (Optional[str]): アップロード先のインデックス名

        Returns:
            Dict[str, Any]: アップロード結果
        """
        search_client = self.init_search_client(index_name)

        try:
            # ドキュメントをアップロード
            result = search_client.upload_documents(documents=documents)

            # 結果を集計
            succeeded = sum(1 for r in result if r.succeeded)
            failed = len(result) - succeeded

            logger.info(
                f"Document upload completed: {succeeded} succeeded, {failed} failed"
            )

            return {
                "status": "completed",
                "total": len(documents),
                "succeeded": succeeded,
                "failed": failed,
                "index_name": index_name or self.default_index_name,
            }

        except Exception as e:
            logger.error(f"Error uploading documents: {str(e)}")
            raise Exception(f"Document upload failed: {str(e)}")

    def delete_documents(
        self,
        document_ids: list[str],
        key_field: str = "id",
        index_name: str | None = None,
    ) -> dict[str, Any]:
        """
        ドキュメントを削除

        Args:
            document_ids (List[str]): 削除対象のドキュメントIDリスト
            key_field (str): キーフィールド名
            index_name (Optional[str]): 削除対象のインデックス名

        Returns:
            Dict[str, Any]: 削除結果
        """
        search_client = self.init_search_client(index_name)

        try:
            # 削除用のドキュメント形式に変換
            documents_to_delete = [{key_field: doc_id} for doc_id in document_ids]

            # ドキュメントを削除
            result = search_client.delete_documents(documents=documents_to_delete)

            # 結果を集計
            succeeded = sum(1 for r in result if r.succeeded)
            failed = len(result) - succeeded

            logger.info(
                f"Document deletion completed: {succeeded} succeeded, {failed} failed"
            )

            return {
                "status": "completed",
                "total": len(document_ids),
                "succeeded": succeeded,
                "failed": failed,
                "index_name": index_name or self.default_index_name,
            }

        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise Exception(f"Document deletion failed: {str(e)}")

    def get_document_count(self, index_name: str | None = None) -> int:
        """
        インデックス内のドキュメント総数を取得

        Args:
            index_name (Optional[str]): 対象のインデックス名

        Returns:
            int: ドキュメント数
        """
        search_client = self.init_search_client(index_name)

        try:
            # 空の検索でカウントのみ取得
            results = search_client.search(
                search_text="*", include_total_count=True, top=0
            )

            count = results.get_count() if hasattr(results, "get_count") else 0
            logger.info(
                f"Document count retrieved: {count} documents in index {index_name or self.default_index_name}"
            )

            return count

        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return 0

    def test_connection(self) -> dict[str, Any]:
        """
        Azure AI Searchサービスへの接続をテスト

        Returns:
            Dict[str, Any]: 接続テスト結果
        """
        try:
            # インデックスクライアントでの接続テスト
            search_index_client = self.init_search_index_client()

            # インデックス一覧の取得を試行
            indexes = list(search_index_client.list_indexes())

            logger.info("Azure AI Search connection test successful")

            return {
                "status": "success",
                "message": "Connection to Azure AI Search successful",
                "endpoint": self.search_endpoint,
                "indexes_found": len(indexes),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Azure AI Search connection test failed: {str(e)}")

            return {
                "status": "error",
                "message": f"Connection to Azure AI Search failed: {str(e)}",
                "endpoint": self.search_endpoint,
                "timestamp": datetime.now().isoformat(),
            }

    def get_index_name(self, index_type: str) -> str:
        """
        インデックスタイプからインデックス名を取得

        Args:
            index_type (str): インデックスタイプ

        Returns:
            str: インデックス名
        """
        return self.index_mappings.get(index_type, self.default_index_name)

    def valid_index_types(self):
        """有効なインデックスタイプを取得"""
        return list(self.index_mappings.keys())

    def get_index_info(self, index_name: str | None = None) -> dict[str, Any]:
        """
        インデックス情報を取得

        Args:
            index_name (Optional[str]): 対象のインデックス名

        Returns:
            Dict[str, Any]: インデックス情報
        """
        target_index = index_name or self.default_index_name

        try:
            search_index_client = self.init_search_index_client()

            # インデックス情報を取得
            index_info = search_index_client.get_index(target_index)

            # ドキュメント数も取得
            document_count = self.get_document_count(target_index)

            logger.info(f"Index info retrieved for: {target_index}")

            return {
                "status": "success",
                "index_name": target_index,
                "document_count": document_count,
                "fields_count": len(index_info.fields)
                if hasattr(index_info, "fields")
                else 0,
                "created_date": index_info.e_tag
                if hasattr(index_info, "e_tag")
                else None,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting index info for {target_index}: {str(e)}")

            return {
                "status": "error",
                "index_name": target_index,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
