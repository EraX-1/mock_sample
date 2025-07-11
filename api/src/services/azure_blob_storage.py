import os
from datetime import datetime, timedelta

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
)

from src.utils.logger import get_logger

logger = get_logger(__name__)


class AzureBlobStorage:
    """
    Azure Blob Storage サービス (INFRA-003)
    ファイルのアップロード、ダウンロード、削除、SAS URL生成機能を提供
    """

    def __init__(self):
        """Azure Blob Storage クライアントを初期化"""
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "documents")

        if not self.account_name or not self.account_key:
            raise ValueError("Azure Storage credentials not configured")

        # BlobServiceClientを初期化
        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{self.account_name}.blob.core.windows.net",
            credential=self.account_key,
        )

        logger.info(
            f"Azure Blob Storage initialized - Account: {self.account_name}, Container: {self.container_name}"
        )

    def get_blob_url(self, blob_name: str) -> str:
        """
        Blob URLを取得

        Args:
            blob_name (str): Blob名

        Returns:
            str: Blob URL
        """
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"

    async def upload_document(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> dict[str, str]:
        """
        ファイルをAzure Blob Storageにアップロード

        Args:
            file_data (bytes): ファイルデータ
            filename (str): ファイル名
            content_type (str): コンテンツタイプ

        Returns:
            Dict[str, str]: アップロード結果
        """
        try:
            # コンテナクライアントを取得
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            # タイムスタンプ付きのファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"{timestamp}_{filename}"

            # ファイルをアップロード
            blob_client = container_client.upload_blob(
                name=blob_name,
                data=file_data,
                content_settings=ContentSettings(content_type=content_type),
                overwrite=True,
            )

            blob_url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"

            logger.info(f"File uploaded successfully: {blob_name}")

            return {
                "status": "success",
                "blob_name": blob_name,
                "blob_url": blob_url,
                "size": len(file_data),
                "content_type": content_type,
                "uploaded_at": datetime.now().isoformat(),
            }

        except ResourceExistsError:
            logger.warning(f"Blob already exists: {filename}")
            raise Exception(f"File {filename} already exists")
        except Exception as e:
            logger.error(f"Error uploading file {filename}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to upload file: {str(e)}")

    async def generate_sas_url(self, blob_name: str, expiry_hours: int = 24) -> str:
        """
        SAS URLを生成して安全なファイルアクセスを提供

        Args:
            blob_name (str): Blob名
            expiry_hours (int): 有効期限（時間）

        Returns:
            str: SAS URL
        """
        try:
            # SAS権限を設定
            sas_permissions = BlobSasPermissions(read=True)

            # 有効期限を設定
            expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)

            # SAS URLを生成
            sas_url = generate_blob_sas(
                account_name=self.account_name,
                account_key=self.account_key,
                container_name=self.container_name,
                blob_name=blob_name,
                permission=sas_permissions,
                expiry=expiry_time,
            )

            # 完全なURLを構築
            full_sas_url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_url}"

            logger.info(f"SAS URL generated for: {blob_name}")

            return full_sas_url

        except Exception as e:
            logger.error(f"Error generating SAS URL for {blob_name}: {str(e)}")
            raise Exception(f"Failed to generate SAS URL: {str(e)}")

    async def delete_document(self, blob_name: str) -> dict[str, str]:
        """
        ドキュメントを削除

        Args:
            blob_name (str): 削除するBlob名

        Returns:
            Dict[str, str]: 削除結果
        """
        try:
            # Blobクライアントを取得して削除
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_name
            )

            blob_client.delete_blob()

            logger.info(f"Document deleted successfully: {blob_name}")

            return {
                "status": "success",
                "blob_name": blob_name,
                "deleted_at": datetime.now().isoformat(),
            }

        except ResourceNotFoundError:
            logger.warning(f"Blob not found for deletion: {blob_name}")
            raise Exception(f"File {blob_name} not found")
        except Exception as e:
            logger.error(f"Error deleting document {blob_name}: {str(e)}")
            raise Exception(f"Failed to delete document: {str(e)}")

    async def list_documents(self, prefix: str = "") -> dict[str, list]:
        """
        ドキュメント一覧を取得

        Args:
            prefix (str): フィルタ用プレフィックス

        Returns:
            Dict[str, list]: ドキュメント一覧
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            blobs = []
            for blob in container_client.list_blobs(name_starts_with=prefix):
                blobs.append(
                    {
                        "name": blob.name,
                        "size": blob.size,
                        "last_modified": blob.last_modified.isoformat()
                        if blob.last_modified
                        else None,
                        "content_type": blob.content_settings.content_type
                        if blob.content_settings
                        else None,
                    }
                )

            logger.info(f"Listed {len(blobs)} documents with prefix: '{prefix}'")

            return {
                "status": "success",
                "documents": blobs,
                "count": len(blobs),
                "prefix": prefix,
            }

        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise Exception(f"Failed to list documents: {str(e)}")

    async def get_document_info(self, blob_name: str) -> dict[str, str] | None:
        """
        ドキュメント情報を取得

        Args:
            blob_name (str): Blob名

        Returns:
            Optional[Dict[str, str]]: ドキュメント情報
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_name
            )

            # Blobプロパティを取得
            properties = blob_client.get_blob_properties()

            document_info = {
                "name": blob_name,
                "size": properties.size,
                "content_type": properties.content_settings.content_type
                if properties.content_settings
                else None,
                "last_modified": properties.last_modified.isoformat()
                if properties.last_modified
                else None,
                "etag": properties.etag,
                "creation_time": properties.creation_time.isoformat()
                if properties.creation_time
                else None,
            }

            logger.info(f"Document info retrieved for: {blob_name}")

            return document_info

        except ResourceNotFoundError:
            logger.warning(f"Document not found: {blob_name}")
            return None
        except Exception as e:
            logger.error(f"Error getting document info for {blob_name}: {str(e)}")
            raise Exception(f"Failed to get document info: {str(e)}")

    async def download_document(self, blob_name: str) -> bytes:
        """
        ドキュメントをダウンロード

        Args:
            blob_name (str): Blob名

        Returns:
            bytes: ファイルデータ
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_name
            )

            # ファイルをダウンロード
            download_stream = blob_client.download_blob()
            file_data = download_stream.readall()

            logger.info(f"Document downloaded: {blob_name}")

            return file_data

        except ResourceNotFoundError:
            logger.warning(f"Document not found for download: {blob_name}")
            raise Exception(f"File {blob_name} not found")
        except Exception as e:
            logger.error(f"Error downloading document {blob_name}: {str(e)}")
            raise Exception(f"Failed to download document: {str(e)}")
