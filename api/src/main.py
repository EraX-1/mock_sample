# main.py
import os

# OpenTelemetry 関連のインポート
from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# カスタムミドルウェアのインポート
from src.middleware.attribute_middleware import AddAttributeMiddleware
from src.routers import router

# OpenTelemetry を Azure Monitor を使用するように設定
# 接続文字列は通常、APPLICATIONINSIGHTS_CONNECTION_STRING 環境変数経由で設定
# この環境変数がデプロイ環境で設定されていることを確認する
connectionString = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if connectionString:
    # リソース属性を設定
    resource = Resource.create({SERVICE_NAME: "yuyama-rag-chatbot"})

    # OpenTelemetryの設定
    configure_azure_monitor(connection_string=connectionString, resource=resource)

    # ロギングの計装を有効化
    LoggingInstrumentor().instrument()

app = FastAPI()

# FastAPI アプリケーションを計装
FastAPIInstrumentor.instrument_app(app)
# requests ライブラリを計装して、アプリケーションによるHTTPリクエストをトレース
RequestsInstrumentor().instrument()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ase-kdk-knowledgedb-dev-cus-001-web-cmauhpdcfrd4dxcx.centralus-01.azurewebsites.net",
        "https://yuyama-rag-chatbot-frontend-fgf7byd6b9f4fqck.japaneast-01.azurewebsites.net",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# カスタムミドルウェアを追加してリクエスト属性（ユーザーIDなど）をトレースに追加
app.add_middleware(AddAttributeMiddleware)


# データベーステーブル初期化
@app.on_event("startup")
async def initialize_database():
    """アプリケーション起動時にデータベーステーブルを作成"""
    try:
        from src.schemas.base import Base
        from src.services.db import ENGINE

        # 全テーブルを作成（既存の場合はスキップ）
        Base.metadata.create_all(bind=ENGINE)
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")


# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """Azure App Serviceのヘルスチェック用エンドポイント"""
    import os

    try:
        from sqlalchemy import text

        from src.config.azure_config import MOCK_CONFIG
        from src.services.db import get_session

        # データベース接続テスト
        db_status = "unknown"
        tables = []
        try:
            with get_session() as session:
                result = session.execute(text("SELECT 1"))
                db_status = "connected"
                tables_result = session.execute(text("SHOW TABLES"))
                tables = [row[0] for row in tables_result.fetchall()]
        except Exception as db_e:
            db_status = f"error: {str(db_e)}"

        return {
            "status": "healthy",
            "service": "yuyama-api",
            "debug": {
                "USE_MOCK_SERVICES": os.getenv("USE_MOCK_SERVICES"),
                "MOCK_CONFIG_use_mock": MOCK_CONFIG.get("use_mock_services"),
                "DB_HOST": os.getenv("DB_HOST", "not_set"),
                "database_status": db_status,
                "tables_found": tables,
            },
        }
    except Exception as e:
        return {"status": "healthy", "service": "yuyama-api", "debug_error": str(e)}


# デバッグエンドポイント（一時的）
@app.get("/debug/env")
async def debug_environment():
    """Azure環境の設定状況を確認（デバッグ用）"""
    import os

    from src.config.azure_config import MOCK_CONFIG, config

    try:
        return {
            "USE_MOCK_SERVICES_env": os.getenv("USE_MOCK_SERVICES"),
            "MOCK_CONFIG_use_mock_services": MOCK_CONFIG.get("use_mock_services"),
            "DB_HOST": os.getenv("DB_HOST", "not_set"),
            "DB_NAME": os.getenv("DB_NAME", "not_set"),
            "config_loaded": bool(config),
            "config_mock": config.get("mock", {}),
            "FRONTEND_URL": os.getenv("FRONTEND_URL", "not_set"),
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/debug/db")
async def debug_database():
    """データベース接続とテーブル状況を確認（デバッグ用）"""
    try:
        from sqlalchemy import text

        from src.services.db import get_session

        with get_session() as session:
            # 接続テスト
            result = session.execute(text("SELECT 1 as test"))
            connection_test = result.fetchone()[0]

            # テーブル存在確認
            tables_result = session.execute(text("SHOW TABLES"))
            tables = [row[0] for row in tables_result.fetchall()]

            # usersテーブルのカウント
            users_count = None
            if "users" in tables:
                count_result = session.execute(text("SELECT COUNT(*) FROM users"))
                users_count = count_result.fetchone()[0]

            return {
                "connection_test": connection_test,
                "existing_tables": tables,
                "users_table_exists": "users" in tables,
                "users_count": users_count,
            }
    except Exception as e:
        return {"db_error": str(e)}


# ヘルスチェックルーター追加
from src.services.azure_openai_health import router as azure_openai_health_router


# Azure OpenAI テスト用エンドポイント
@app.post("/test/azure-openai/chat")
async def test_azure_openai_chat(request_data: dict):
    """
    Azure OpenAI チャット機能のテスト用エンドポイント
    """
    try:
        from src.services.azure_openai import AzureOpenAI

        client = AzureOpenAI()
        message = request_data.get("message", "Hello, this is a test!")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ]

        response = client.create_chat_completion(
            messages=messages, max_tokens=200, temperature=0.7
        )

        response_content = ""
        if hasattr(response, "choices") and response.choices:
            response_content = response.choices[0].message.content

        return {
            "status": "success",
            "user_message": message,
            "ai_response": response_content,
            "model": client.chat_deployment,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "user_message": request_data.get("message", ""),
        }


app.include_router(router)
app.include_router(azure_openai_health_router)
