import logging  # logging をインポート
import os

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)

# コントローラーをインポート
from src.controllers import (
    AdminController,
    AuthController,
    ChatMessageController,
    ChatRoomController,
    CoreController,
)
from src.controllers.blob_storage_controller import router as blob_storage_router
from src.dependencies.auth import requires_role
from src.internal.indexer import (
    index_docx_docs,
    index_excel_docs,
    index_html_docs,
    index_image_docs,
    index_pdf_docs,
    index_pptx_docs,
)
from src.models.request_models import (
    CreateChatMessageRequest,
    DeleteChatRoomRequest,
    GetChatRoomRequest,
    ReorderSearchIndexTypesRequest,
    UpdateChatEvaluation,
    UpdateChatroomRequest,
    UpdateSearchIndexTypeRequest,
    UpdateUserRoleRequest,
)

# utils.logger からヘルパー関数をインポート
from src.utils.logger import get_logger, log_exception

# ロガーを取得
logger = get_logger(__name__)

router = APIRouter()

# Blob Storageルーターを追加
router.include_router(blob_storage_router)

# コントローラーをインスタンス化
# TODO: ルーティング設定の分割
chat_room_controller = ChatRoomController()
chat_message_controller = ChatMessageController()
auth_controller = AuthController()
admin_controller = AdminController()
core_controller = CoreController()


@router.get("/")
def root():
    chatbot_version = "250422_0"
    # extraの指定なしで環境情報を設定できるべき
    logger.info("'/' リクエスト", extra={"environment": "local"})
    return {"message": f"Hello, {chatbot_version}"}


@router.post("/index")
async def index(
    request: Request, file: UploadFile = File(...), index_type: str = Form(...)
):
    # ユーザーIDを取得（ミドルウェアで属性が付与されている想定）
    # span = trace.get_current_span()
    # user_id = span.get_attribute("enduser.id") # 必要であれば取得
    # logger.info(f"インデックス作成リクエスト受信: user_id={user_id}, filename='{file.filename}', index_type='{index_type}'")
    logger.info(
        f"'/index' リクエスト filename='{file.filename}', index_type='{index_type}'"
    )  # user_id はトレース属性で確認

    try:
        contents = await file.read()
        file_extension = os.path.splitext(file.filename)[1].lower()
        logger.debug(
            f"'/index' ファイル読み込み完了: filename='{file.filename}', size={len(contents)}, extension='{file_extension}'"
        )

        result = None
        if file_extension in [".xlsx", ".xls", ".xlsm"]:
            result = await index_excel_docs(contents, file.filename, index_type)
        elif file_extension == ".pdf":
            result = await index_pdf_docs(contents, file.filename, index_type)
        elif file_extension in [".docx", ".doc"]:
            result = await index_docx_docs(contents, file.filename, index_type)
        elif file_extension == ".pptx":
            result = await index_pptx_docs(contents, file.filename, index_type)
        elif file_extension == ".html":
            result = await index_html_docs(contents, file.filename, index_type)
        elif file_extension in [".png", ".jpg", ".jpeg"]:
            result = await index_image_docs(contents, file.filename, index_type)
        else:
            logger.warning(
                f"'/index' サポートされていないファイル形式: filename='{file.filename}', extension='{file_extension}'"
            )
            raise HTTPException(
                status_code=400, detail="サポートされていないファイル形式です"
            )

        logger.info(
            f"'/index' 処理呼び出し完了: filename='{file.filename}', index_type='{index_type}'"
        )
        return result

    except HTTPException as e:
        logger.warning(
            f"'/index' HTTPException: filename='{file.filename}', status_code={e.status_code}, detail='{e.detail}'"
        )
        raise e
    except Exception as e:
        log_exception(
            logger,
            e,
            f"'/index' 予期せぬエラー: filename='{file.filename}', index_type='{index_type}'",
        )
        raise HTTPException(
            status_code=500,
            detail="ファイルのインデックス作成中にエラーが発生しました。",
        )


@router.get("/chat_rooms")
@requires_role("user", "admin")
def get_chat(request: Request):
    logger.debug("'/chat_rooms' (GET) リクエスト")
    try:
        result = chat_room_controller.get_chat_rooms(request)
        logger.info("'/chat_rooms' (GET) 処理完了")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/chat_rooms' (GET) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(logger, e, "'/chat_rooms' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/chat_room")
@requires_role("user", "admin")
def get_by_id(request: Request, data: GetChatRoomRequest = Depends()):
    chat_room_id = data.chat_room_id
    logger.debug(f"'/chat_room' (GET) リクエスト受信: chat_room_id={chat_room_id}")
    try:
        result = chat_room_controller.get_room_by_id(request, data)
        logger.info(f"'/chat_room' (GET) 処理完了: chat_room_id={chat_room_id}")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/chat_room' (GET) HTTPException: chat_room_id={chat_room_id}, status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger, e, f"'/chat_room' (GET) 予期せぬエラー: chat_room_id={chat_room_id}"
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/chat_rooms")
@requires_role("user", "admin")
def create_chat(request: Request):
    logger.debug("'/chat_rooms' (POST) リクエスト受信")
    try:
        result = chat_room_controller.create_chat_room(request)
        logger.info(
            f"'/chat_rooms' (POST) 処理完了: chat_room_id={result.get('id') if isinstance(result, dict) else None}"
        )
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/chat_rooms' (POST) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(logger, e, "'/chat_rooms' (POST) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put("/chat_rooms")
@requires_role("user", "admin")
def update_chat(request: Request, data: UpdateChatroomRequest):
    chat_room_id = data.chat_room_id
    logger.debug(
        f"'/chat_rooms' (PUT) リクエスト受信: chat_room_id={chat_room_id}, data={data.dict(exclude_unset=True)}"
    )
    try:
        result = chat_room_controller.update_chat_room(request, data)
        logger.info(f"'/chat_rooms' (PUT) 処理完了: chat_room_id={chat_room_id}")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/chat_rooms' (PUT) HTTPException: chat_room_id={chat_room_id}, status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger,
            e,
            f"'/chat_rooms' (PUT) 予期せぬエラー: chat_room_id={chat_room_id}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.delete("/chat_rooms")
@requires_role("user", "admin")
def delete_chat(request: Request, data: DeleteChatRoomRequest):
    chat_room_id = data.chat_room_id
    logger.debug(f"'/chat_rooms' (DELETE) リクエスト受信: chat_room_id={chat_room_id}")
    try:
        result = chat_room_controller.delete_chat_room(request, data)
        logger.info(
            f"'/chat_rooms' (DELETE) 処理完了: chat_room_id={chat_room_id}, success={result.get('success')}"
        )
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/chat_rooms' (DELETE) HTTPException: chat_room_id={chat_room_id}, status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger,
            e,
            f"'/chat_rooms' (DELETE) 予期せぬエラー: chat_room_id={chat_room_id}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/chat_messages")
@requires_role("user", "admin")
def get_list(request: Request, chat_room_id: str):
    logger.debug(f"'/chat_messages' (GET) リクエスト受信: chat_room_id={chat_room_id}")
    try:
        result = chat_message_controller.get_chat_messages(request, chat_room_id)
        logger.info(f"'/chat_messages' (GET) 処理完了: chat_room_id={chat_room_id}")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/chat_messages' (GET) HTTPException: chat_room_id={chat_room_id}, status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger,
            e,
            f"'/chat_messages' (GET) 予期せぬエラー: chat_room_id={chat_room_id}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/chat_messages")
@requires_role("user", "admin")
def create(request: Request, data: CreateChatMessageRequest):
    # 必要であれば data.dict(exclude={'message', ...}) のようにようにメッセージ内容を除外する
    logger.debug(
        f"'/chat_messages' (POST) リクエスト受信: chat_room_id={data.chat_room_id}, model={data.model}"
    )
    try:
        response = chat_message_controller.create_chat_message(request, data)
        logger.info(
            f"'/chat_messages' (POST) 処理完了 (StreamingResponse開始): chat_room_id={data.chat_room_id}"
        )
        return response
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/chat_messages' (POST) HTTPException: chat_room_id={data.chat_room_id}, status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger,
            e,
            f"'/chat_messages' (POST) 予期せぬエラー: chat_room_id={data.chat_room_id}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


# メッセージ評価


@router.put("/chat_message/evaluation")
@requires_role("user", "admin")
def create(request: Request, data: UpdateChatEvaluation):
    message_id = data.message_id
    evaluation = data.evaluation
    logger.debug(
        f"'/chat_message/evaluation' (PUT) リクエスト受信: message_id={message_id}, evaluation={evaluation}"
    )
    try:
        result = chat_message_controller.put_message_evaluation(request, data)
        logger.info(
            f"'/chat_message/evaluation' (PUT) 処理完了: message_id={message_id}, evaluation={evaluation}"
        )
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/chat_message/evaluation' (PUT) HTTPException: message_id={message_id}, status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger,
            e,
            f"'/chat_message/evaluation' (PUT) 予期せぬエラー: message_id={message_id}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =================================================
# 認証関係
# =================================================


@router.get("/auth/url")
def auth_url():
    logger.debug("'/auth/url' (GET) リクエスト受信")
    try:
        from src.config.azure_config import MOCK_CONFIG, USE_MOCK_SERVICES

        logger.info(
            f"モック設定: USE_MOCK_SERVICES={USE_MOCK_SERVICES}, MOCK_CONFIG_use_mock={MOCK_CONFIG.get('use_mock_services')}"
        )

        result = auth_controller.get_auth_url()
        logger.info("'/auth/url' (GET) 処理完了")
        return result
    except HTTPException as e:
        logger.error(f"'/auth/url' (GET) HTTPException: {e.detail}")
        raise e
    except Exception as e:
        log_exception(logger, e, "'/auth/url' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/auth/admin/url")
def admin_auth_url():
    logger.debug("'/auth/admin/url' (GET) リクエスト受信")
    try:
        from src.config.azure_config import MOCK_CONFIG, USE_MOCK_SERVICES

        logger.info(
            f"管理者認証モック設定: USE_MOCK_SERVICES={USE_MOCK_SERVICES}, MOCK_CONFIG_use_mock={MOCK_CONFIG.get('use_mock_services')}"
        )

        result = auth_controller.get_auth_url(admin_mode=True)
        logger.info("'/auth/admin/url' (GET) 処理完了")
        return result
    except HTTPException as e:
        logger.error(f"'/auth/admin/url' (GET) HTTPException: {e.detail}")
        raise e
    except Exception as e:
        log_exception(logger, e, "'/auth/admin/url' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/auth/callback")
async def auth_callback(code: str):
    logger.debug("'/auth/callback' (GET) リクエスト受信")
    try:
        result = await auth_controller.handle_auth_callback(code)
        logger.info("'/auth/callback' (GET) 処理完了")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/auth/callback' (GET) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(logger, e, "'/auth/callback' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/logout")
def logout_endpoint():
    logger.debug("'/logout' (POST) リクエスト受信")
    try:
        result = auth_controller.logout()
        logger.info("'/logout' (POST) 処理完了")
        return result
    except Exception as e:
        log_exception(logger, e, "'/logout' (POST) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/dropout")
@requires_role("user", "admin")
def dropout_endpoint(request: Request):
    logger.debug("'/dropout' (POST) リクエスト受信")
    try:
        result = auth_controller.dropout(request)
        logger.info("'/dropout' (POST) 処理完了")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/dropout' (POST) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(logger, e, "'/dropout' (POST) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =================================================
# コア取得関係
# =================================================


@router.get("/core_config")
def get_core_config_endpoint():
    logger.debug("'/core_config' (GET) リクエスト受信")
    try:
        result = core_controller.get_core_config()
        logger.info("'/core_config' (GET) 処理完了")
        return result
    except Exception as e:
        log_exception(logger, e, "'/core_config' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/core_name")
def get_core_name_endpoint():
    logger.debug("'/core_name' (GET) リクエスト受信")
    try:
        result = core_controller.get_core_name()
        logger.info("'/core_name' (GET) 処理完了")
        return result
    except Exception as e:
        log_exception(logger, e, "'/core_name' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =================================================
# 管理者ダッシュボード
# =================================================
@router.get("/admin")
@requires_role("user", "admin")
def get_admin_dashboard_emdpoint(request: Request):
    logger.debug("'/admin' (GET) リクエスト受信")
    try:
        result = admin_controller.get_admin_dashboard(request)
        logger.info("'/admin' (GET) 処理完了")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/admin' (GET) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(logger, e, "'/admin' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =================================================
# ユーザ情報取得（自分）
# =================================================
@router.get("/user")
@requires_role("user", "admin")
def get_user_data_endpoint(request: Request):
    logger.debug("'/user' (GET) リクエスト受信")
    try:
        result = auth_controller.get_user_data(request)
        logger.info(
            f"'/user' (GET) 処理完了: user_id={result.get('user_id') if isinstance(result, dict) else None}"
        )
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/user' (GET) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(logger, e, "'/user' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =================================================
# ユーザー権限更新
# =================================================
@router.put("/user/role")
@requires_role("admin")
def update_user_role_endpoint(request: Request, data: UpdateUserRoleRequest):
    target_user_id = data.user_id
    new_role = data.role
    logger.debug(
        f"'/user/role' (PUT) リクエスト受信: target_user_id={target_user_id}, new_role={new_role}"
    )
    try:
        result = auth_controller.update_user_role(request, data)
        logger.info(
            f"'/user/role' (PUT) 処理完了: target_user_id={target_user_id}, new_role={new_role}"
        )
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/user/role' (PUT) HTTPException: target_user_id={target_user_id}, status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger,
            e,
            f"'/user/role' (PUT) 予期せぬエラー: target_user_id={target_user_id}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =================================================
# 検索インデックス関係
# =================================================
@router.get("/admin/search_index_types")
@requires_role("admin")
def get_search_index_types_endpoint(request: Request):
    logger.debug("'/admin/search_index_types' (GET) リクエスト受信")
    try:
        result = admin_controller.get_search_index_types()
        logger.info("'/admin/search_index_types' (GET) 処理完了")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/admin/search_index_types' (GET) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(logger, e, "'/admin/search_index_types' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put("/admin/search_index_type")
@requires_role("admin")
def update_search_index_type_endpoint(
    request: Request, data: UpdateSearchIndexTypeRequest
):
    index_type_id = data.index_type_id
    folder_name = data.folder_name
    logger.debug(
        f"'/admin/search_index_type' (PUT) リクエスト受信: index_type_id={index_type_id}, folder_name='{folder_name}'"
    )
    try:
        result = admin_controller.update_search_index_type(index_type_id, folder_name)
        logger.info(
            f"'/admin/search_index_type' (PUT) 処理完了: index_type_id={index_type_id}, success={result.get('success')}"
        )
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/admin/search_index_type' (PUT) HTTPException: index_type_id={index_type_id}, status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger,
            e,
            f"'/admin/search_index_type' (PUT) 予期せぬエラー: index_type_id={index_type_id}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put("/admin/search_index_types/reorder")
@requires_role("admin")
def reorder_search_index_types_endpoint(
    request: Request, data: ReorderSearchIndexTypesRequest
):
    index_type_ids = data.index_type_ids
    logger.debug(
        f"'/admin/search_index_types/reorder' (PUT) リクエスト受信: index_type_ids={index_type_ids}"
    )
    try:
        result = admin_controller.reorder_search_index_types(index_type_ids)
        logger.info(
            f"'/admin/search_index_types/reorder' (PUT) 処理完了: success={result.get('success')}"
        )
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/admin/search_index_types/reorder' (PUT) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger, e, "'/admin/search_index_types/reorder' (PUT) 予期せぬエラー"
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 一般ユーザー向けの検索インデックス取得エンドポイント
@router.get("/search_index_types")
@requires_role("user", "admin")
def get_search_index_types_for_user_endpoint(request: Request):
    logger.debug("'/search_index_types' (GET) リクエスト受信")
    try:
        result = admin_controller.get_search_index_types()
        logger.info("'/search_index_types' (GET) 処理完了")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/search_index_types' (GET) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(logger, e, "'/search_index_types' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =================================================
# インデックス済みファイル一覧取得エンドポイント
# =================================================
@router.get("/indexed_files")
@requires_role("admin")
def get_indexed_files_endpoint(request: Request):
    logger.debug("'/indexed_files' (GET) リクエスト受信")
    try:
        from src.repositories.index_repository import IndexedFileRepository
        from src.usecases.index_usecase import IndexUsecase

        indexed_file_repository = IndexedFileRepository()
        index_usecase = IndexUsecase(indexed_file_repository)

        result = index_usecase.get_all_indexed_files()
        logger.info(f"'/indexed_files' (GET) 処理完了: {len(result)}件取得")
        return result
    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/indexed_files' (GET) HTTPException: status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(logger, e, "'/indexed_files' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =================================================
# メンテナンス状態エンドポイント
# =================================================
@router.get("/maintenance_status")
def maintenance_status_endpoint():
    """メンテナンス状態を返すエンドポイント"""
    logger.debug("'/maintenance_status' (GET) リクエスト受信")
    try:
        # デフォルトではメンテナンス中ではない
        response_data = {"maintenance": False, "message": "", "status": "operational"}
        logger.info("'/maintenance_status' (GET) 処理完了")
        return response_data
    except Exception as e:
        log_exception(logger, e, "'/maintenance_status' (GET) 予期せぬエラー")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =================================================
# 検索エンドポイント
# =================================================
@router.get("/search")
# @requires_role("user", "admin")  # テスト用に一時的に無効化
def search_documents_endpoint(
    request: Request,
    query: str = Query(...),
    index_types: str = Query(None),
    top: int = Query(10),
):
    logger.debug(
        f"'/search' (GET) リクエスト受信: query='{query[:50]}...', index_types={index_types}, top={top}"
    )
    try:
        from src.services.azure_ai_search import AzureAISearch

        # Azure AI Searchサービスを初期化
        search_service = AzureAISearch()

        # インデックス名を決定（index_typesが指定された場合の処理は今後実装）
        index_name = None  # デフォルトインデックスを使用

        # 検索実行
        search_results = search_service.search_documents(
            query=query, top=top, index_name=index_name
        )

        logger.info(
            f"'/search' (GET) 処理完了: query='{query[:50]}...', count={search_results['count']}"
        )

        return {
            "status": "success",
            "query": query,
            "results": search_results["documents"],
            "count": search_results["count"],
            "total_count": search_results.get("total_count", 0),
            "index_name": search_results["index_name"],
        }

    except HTTPException as e:
        logger.log(
            logging.WARNING if e.status_code < 500 else logging.ERROR,
            f"'/search' (GET) HTTPException: query='{query[:50]}...', status_code={e.status_code}, detail='{e.detail}'",
        )
        raise e
    except Exception as e:
        log_exception(
            logger, e, f"'/search' (GET) 予期せぬエラー: query='{query[:50]}...'"
        )
        # デバッグ用に詳細なエラー情報を含める
        error_detail = f"検索処理中にエラーが発生しました。詳細: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/test/document-intelligence")
# @requires_role("user", "admin")  # テスト用に一時的に無効化
def test_document_intelligence_endpoint(file: UploadFile = File(...)):
    logger.debug(
        f"'/test/document-intelligence' (POST) リクエスト受信: filename='{file.filename}'"
    )
    try:
        from src.utils.extract_markdown_text_from_file import (
            extract_markdown_text_from_image,
            extract_markdown_text_from_pdf,
        )

        # ファイル内容を読み取り
        contents = file.file.read()
        file.file.seek(0)  # ファイルポインタをリセット

        # ファイル拡張子を確認
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension == ".pdf":
            # PDFファイルの処理
            docs = extract_markdown_text_from_pdf(contents)
            logger.info(
                f"'/test/document-intelligence' (POST) PDF処理完了: filename='{file.filename}', pages={len(docs)}"
            )

            return {
                "status": "success",
                "file_type": "PDF",
                "filename": file.filename,
                "pages_processed": len(docs),
                "sample_content": docs[0]["page_content"][:500] + "..." if docs else "",
                "metadata": docs[0].get("metadata", {}) if docs else {},
            }

        elif file_extension in [".png", ".jpg", ".jpeg"]:
            # 画像ファイルの処理
            docs = extract_markdown_text_from_image(contents)
            logger.info(
                f"'/test/document-intelligence' (POST) 画像処理完了: filename='{file.filename}', pages={len(docs)}"
            )

            return {
                "status": "success",
                "file_type": "IMAGE",
                "filename": file.filename,
                "pages_processed": len(docs),
                "sample_content": docs[0]["page_content"][:500] + "..." if docs else "",
                "metadata": docs[0].get("metadata", {}) if docs else {},
            }

        else:
            return {
                "status": "error",
                "message": f"サポートされていないファイル形式: {file_extension}",
                "supported_formats": [".pdf", ".png", ".jpg", ".jpeg"],
            }

    except Exception as e:
        error_detail = str(e)
        log_exception(
            logger,
            e,
            f"'/test/document-intelligence' (POST) 予期せぬエラー: filename='{file.filename}', error={error_detail}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Document Intelligence処理中にエラーが発生しました: {error_detail}",
        )
