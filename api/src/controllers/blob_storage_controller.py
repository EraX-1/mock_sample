"""
Azure Blob Storage コントローラー (INFRA-003)
ファイルアップロード、SAS URL生成、削除機能のAPIエンドポイント
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.services.azure_blob_storage import AzureBlobStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/blob-storage", tags=["Blob Storage"])


# AzureBlobStorageの初期化
def get_blob_storage():
    """Blob Storageサービスを取得"""
    try:
        return AzureBlobStorage()
    except Exception as e:
        logger.error(f"Failed to initialize AzureBlobStorage: {str(e)}")
        raise HTTPException(status_code=500, detail="Blob Storage service unavailable")


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), generate_sas: bool = Form(default=True)
) -> JSONResponse:
    """
    ファイルをAzure Blob Storageにアップロード

    Args:
        file: アップロードするファイル
        generate_sas: SAS URLを生成するかどうか

    Returns:
        JSONResponse: アップロード結果
    """
    try:
        blob_storage = get_blob_storage()

        # ファイルデータを読み取り
        file_data = await file.read()

        # ファイルをアップロード
        upload_result = await blob_storage.upload_document(
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
        )

        response_data = {
            "status": "success",
            "message": "File uploaded successfully",
            "upload_info": upload_result,
        }

        # SAS URLを生成する場合
        if generate_sas:
            sas_url = await blob_storage.generate_sas_url(upload_result["blob_name"])
            response_data["sas_url"] = sas_url

        logger.info(f"File uploaded: {file.filename} -> {upload_result['blob_name']}")

        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        logger.error(f"Error uploading file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/list")
async def list_documents(prefix: str = "") -> JSONResponse:
    """
    ドキュメント一覧を取得

    Args:
        prefix: フィルタ用プレフィックス

    Returns:
        JSONResponse: ドキュメント一覧
    """
    try:
        blob_storage = get_blob_storage()

        documents_result = await blob_storage.list_documents(prefix=prefix)

        logger.info(f"Listed {documents_result['count']} documents")

        return JSONResponse(content=documents_result, status_code=200)

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/sas-url/{blob_name}")
async def generate_sas_url(blob_name: str, expiry_hours: int = 24) -> JSONResponse:
    """
    SAS URLを生成

    Args:
        blob_name: Blob名（URLエンコードされている場合は自動でデコード）
        expiry_hours: 有効期限（時間）

    Returns:
        JSONResponse: SAS URL
    """
    try:
        # URLエンコードされたblob_nameをデコード
        from urllib.parse import unquote

        decoded_blob_name = unquote(blob_name)

        # 完全URLが渡された場合はファイル名部分のみを抽出
        if (
            "blob.core.windows.net" in decoded_blob_name
            or decoded_blob_name.startswith("http")
        ):
            decoded_blob_name = decoded_blob_name.split("/")[-1]
            logger.info(
                f"Extracted filename from URL: {blob_name} -> {decoded_blob_name}"
            )

        # blob_nameの妥当性チェック
        if not decoded_blob_name or decoded_blob_name.strip() == "":
            raise HTTPException(
                status_code=400, detail="Invalid blob_name: empty or whitespace-only"
            )

        logger.info(f"Attempting to find blob for: {decoded_blob_name}")

        blob_storage = get_blob_storage()

        # まず完全一致で試みる
        actual_blob_name = decoded_blob_name
        try:
            # Blob情報を取得して存在確認
            info = await blob_storage.get_document_info(decoded_blob_name)
            if info is None:
                raise Exception("Blob not found")
        except:
            # 完全一致が見つからない場合は、部分一致で検索
            logger.info(
                f"Exact match not found, searching for partial match: {decoded_blob_name}"
            )

            # ドキュメント一覧を取得
            documents_result = await blob_storage.list_documents()
            found_blob = None

            # タイムスタンプ付きのファイル名を検索
            for doc in documents_result["documents"]:
                doc_name = doc["name"]
                # ファイル名の最後の部分が一致するかチェック
                if doc_name.endswith(decoded_blob_name):
                    found_blob = doc_name
                    logger.info(f"Found matching blob: {found_blob}")
                    break

            if not found_blob:
                # より柔軟な検索: ファイル名に含まれているかチェック
                for doc in documents_result["documents"]:
                    doc_name = doc["name"]
                    if decoded_blob_name in doc_name:
                        found_blob = doc_name
                        logger.info(f"Found blob containing filename: {found_blob}")
                        break

            if found_blob:
                actual_blob_name = found_blob
            else:
                logger.error(f"No matching blob found for: {decoded_blob_name}")
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found in Blob Storage: {decoded_blob_name}",
                )

        # SAS URLを生成
        sas_url = await blob_storage.generate_sas_url(
            blob_name=actual_blob_name, expiry_hours=expiry_hours
        )

        response_data = {
            "status": "success",
            "blob_name": actual_blob_name,
            "original_blob_name": blob_name,
            "requested_filename": decoded_blob_name,
            "sas_url": sas_url,
            "expiry_hours": expiry_hours,
        }

        logger.info(f"SAS URL generated successfully for: {actual_blob_name}")

        return JSONResponse(content=response_data, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Failed to generate SAS URL for '{blob_name}': {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=error_message)


@router.get("/info/{blob_name}")
async def get_document_info(blob_name: str) -> JSONResponse:
    """
    ドキュメント情報を取得

    Args:
        blob_name: Blob名

    Returns:
        JSONResponse: ドキュメント情報
    """
    try:
        blob_storage = get_blob_storage()

        document_info = await blob_storage.get_document_info(blob_name)

        if document_info is None:
            raise HTTPException(
                status_code=404, detail=f"Document {blob_name} not found"
            )

        response_data = {"status": "success", "document_info": document_info}

        logger.info(f"Document info retrieved for: {blob_name}")

        return JSONResponse(content=response_data, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info for {blob_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get document info: {str(e)}"
        )


@router.delete("/delete/{blob_name}")
async def delete_document(blob_name: str) -> JSONResponse:
    """
    ドキュメントを削除

    Args:
        blob_name: 削除するBlob名

    Returns:
        JSONResponse: 削除結果
    """
    try:
        blob_storage = get_blob_storage()

        delete_result = await blob_storage.delete_document(blob_name)

        response_data = {
            "status": "success",
            "message": "Document deleted successfully",
            "delete_info": delete_result,
        }

        logger.info(f"Document deleted: {blob_name}")

        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        logger.error(f"Error deleting document {blob_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    Blob Storageヘルスチェック

    Returns:
        JSONResponse: ヘルス状態
    """
    try:
        blob_storage = get_blob_storage()

        # 簡単な接続テスト（コンテナの存在確認）
        test_result = await blob_storage.list_documents(prefix="__health_check__")

        response_data = {
            "status": "healthy",
            "service": "Azure Blob Storage",
            "account_name": blob_storage.account_name,
            "container_name": blob_storage.container_name,
            "timestamp": "2025-06-22T04:13:34.880321+00:00",
        }

        logger.info("Blob Storage health check successful")

        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        logger.error(f"Blob Storage health check failed: {str(e)}")

        response_data = {
            "status": "unhealthy",
            "service": "Azure Blob Storage",
            "error": str(e),
            "timestamp": "2025-06-22T04:13:34.880321+00:00",
        }

        return JSONResponse(content=response_data, status_code=503)


@router.post("/test-connectivity")
async def test_connectivity() -> JSONResponse:
    """
    Blob Storage接続テスト

    Returns:
        JSONResponse: 接続テスト結果
    """
    try:
        blob_storage = get_blob_storage()

        # テストファイルのアップロード
        test_content = b"Azure Blob Storage connectivity test"
        test_filename = "connectivity_test.txt"

        upload_result = await blob_storage.upload_document(
            file_data=test_content, filename=test_filename, content_type="text/plain"
        )

        # SAS URL生成テスト
        sas_url = await blob_storage.generate_sas_url(
            upload_result["blob_name"], expiry_hours=1
        )

        # ファイル情報取得テスト
        file_info = await blob_storage.get_document_info(upload_result["blob_name"])

        # テストファイルを削除
        await blob_storage.delete_document(upload_result["blob_name"])

        response_data = {
            "status": "success",
            "message": "All Blob Storage operations tested successfully",
            "test_results": {
                "upload": "success",
                "sas_url_generation": "success",
                "file_info_retrieval": "success",
                "file_deletion": "success",
            },
            "test_file_info": {
                "blob_name": upload_result["blob_name"],
                "size": len(test_content),
                "sas_url_generated": bool(sas_url),
            },
        }

        logger.info("Blob Storage connectivity test completed successfully")

        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        logger.error(f"Blob Storage connectivity test failed: {str(e)}")

        response_data = {
            "status": "error",
            "message": "Blob Storage connectivity test failed",
            "error": str(e),
            "timestamp": "2025-06-22T04:13:34.880321+00:00",
        }

        return JSONResponse(content=response_data, status_code=500)
