import logging
import os
from azure.storage.blob import BlobServiceClient
import azure.functions as func

# 環境変数から接続文字列を取得
AZURE_STORAGE_CONNECTION_STRING = os.environ["STORAGE_CONNECTION_STRING"]
CONTAINER_NAME = os.environ["STORAGE_CONTAINER_NAME"]


def list_blobs(container_name):
    try:
        # Blob クライアントを作成
        blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        )
        container_client = blob_service_client.get_container_client(container_name)

        logging.info(f"Listing blobs in container: {container_name}")

        # BLOB のリストを取得し、ログに出力
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            logging.info(blob.name)  # シンプルにスラッシュ区切りのパスを出力

    except Exception as e:
        logging.error(f"Error accessing Blob Storage: {e}")


def main(mytimer: func.TimerRequest) -> None:
    logging.info("Azure Function Triggered")

    # BLOB のリストを取得してログ出力
    list_blobs(CONTAINER_NAME)
