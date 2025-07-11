# Yuyama ローカル開発ガイド

**Azure 環境なしで 3 分で起動 - モック環境で完全動作**

## 🎯 モック環境について

ローカル環境では、すべての Azure サービスがモック化されています：

- **🤖 Azure OpenAI** → 事前定義された AI 応答パターン
- **🔍 Azure AI Search** → SQLite ベースの全文検索
- **📁 Azure Blob Storage** → ローカルファイルシステム
- **👤 Azure Active Directory** → テストユーザーでの自動ログイン
- **📄 Document Intelligence** → PyPDF2/python-docx によるローカル処理

**利点**: Azure 課金なし、オフライン動作、高速レスポンス

## ⚡ 高速セットアップ

### **ステップ 1: 基本セットアップ**

```bash
# 1. リポジトリクローン
git clone <repository-url>
cd yuyama

# 2. Web環境変数ファイルを作成（必須）
cat > web/.env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_APP_ENV=development
NEXT_PUBLIC_APP_NAME=Yuyama Local Development
NEXT_PUBLIC_DEBUG=true
NEXT_PUBLIC_LOG_LEVEL=debug
NEXT_PUBLIC_MOCK_MODE=true
EOF

# api側にはtomlファイルを作成 (必須)
cat > api/config.local.toml << 'EOF'
[db]
DB_USER="root"
DB_PASSWORD="password"
DB_HOST="db"
DB_PORT=3306
DB_NAME="yuyama"

[mock]
USE_MOCK_SERVICES=true

[core]
NAME="Yuyama Local Development"
SEARCH_INDEX_NAME_JP_LIST=["mock-index-jp"]
SEARCH_INDEX_NAME_ID_LIST=["mock-index-id"]
SEARCH_INDEX_AZURE_ID_LIST=["mock-azure-id"]
MODEL_LIST=["gpt-4o-mini", "gpt-4o"]
DEFAULT_MODEL="gpt-4o-mini"

[env]
SEARCH_ENDPOINT="http://localhost:8080/mock/search"
SEARCH_API_KEY="mock-search-key"
SEARCH_MODEL_NAME="mock-model"
STORAGE_CONNECTION_STRING="mock-storage-connection"
STORAGE_CONTAINER_NAME="mock-container"
STORAGE_BLOB_SERVICE_ENDPOINT="http://localhost:8080/mock/blob"
EMBEDDING_MODEL_NAME="mock-embedding-model"
AOAI_ENDPOINT="http://localhost:8080/mock/openai"
AOAI_API_KEY="mock-openai-key"
AOAI_API_VERSION="2024-02-01"
SECRET_KEY="local-development-secret-key-change-in-production"
DOCUMENT_INTELLIGENCE_KEY="mock-doc-intel-key"
DOCUMENT_INTELLIGENCE_ENDPOINT="http://localhost:8080/mock/document-intelligence"

[prompt]
SYSTEM_PROMPT="You are Yuyama, a helpful AI assistant running in local development mode."
HYPOTHETICAL_ANSWER_PROMPT="Based on the context provided, generate a hypothetical answer."
EOF

# 3. 自動セットアップ実行
make setup && make up
```

**💡 セットアップの流れ**:

1. `make setup` → API 設定ファイル自動作成、ディレクトリ準備
2. `make up` → Docker コンテナビルド・起動

### **ステップ 2: 起動確認**

正常にセットアップが完了すると、以下の設定ファイルが作成されています：

```bash
# 設定ファイル確認
ls api/config.toml     # ← make setupで自動作成
ls web/.env.local      # ← ステップ1で手動作成
```

**📋 自動で設定される内容**:

- **🔧 API 設定**: モック用 TOML 設定ファイル
- **🌐 Web 環境変数**: フロントエンド開発用設定
- **🗄️ データベース**: MySQL + 初期データ + テストユーザー
- **📁 ストレージ**: ローカルファイルシステム
- **🤖 AI サービス**: 事前定義されたモック応答

## アクセス確認

起動完了後、以下の URL にアクセス：

- **フロントエンド**: http://localhost:3000
- **API**: http://localhost:8080
- **API ドキュメント**: http://localhost:8080/docs

## テストログイン

以下の認証情報でログイン可能：

| ユーザー種別 | メールアドレス          | 説明                   |
| ------------ | ----------------------- | ---------------------- |
| 一般ユーザー | `test.user@example.com` | 基本機能テスト用       |
| 管理者       | `admin@example.com`     | 管理機能テスト用       |
| デモユーザー | `demo@kandenko.co.jp`   | デモンストレーション用 |

## ✅ 動作確認とモック環境テスト

### **1. サービス起動確認**

```bash
# ヘルスチェック（全サービス確認）
make health

# 個別確認
curl http://localhost:8080/health      # API ヘルスチェック
curl http://localhost:8080/health/db   # データベース接続確認
```

### **2. モック環境動作確認**

**チャット機能**:

- ログイン後、チャット画面で質問を入力
- **期待結果**: モック応答が即座に返される（Azure OpenAI 課金なし）

**文書アップロード**:

- 管理画面で PDF/Word ファイルをアップロード
- **期待結果**: `api/local_storage/blobs/mock-container/` に保存

**検索機能**:

- アップロードした文書で検索テスト
- **期待結果**: SQLite ベースの検索結果が表示

### **3. 設定ファイル動作確認**

```bash
# モックサービステスト実行
make test-mock

# API設定確認
curl http://localhost:8080/docs   # Swagger UI でAPI仕様確認

# 環境変数確認
make exec-api
python -c "import toml; print(toml.load('/app/config.toml')['mock'])"
```

## 便利なコマンド

```bash
# ログ確認
make logs

# ヘルスチェック
make health

# モックサービステスト
make test-mock

# 停止
make down

# 完全リセット
make reset
```

## トラブルシューティング

### 最も一般的なエラー

**エラー**: `cp: api/config.local.toml: No such file or directory`

```bash
# 解決方法: config.local.tomlファイルを作成
cat > api/config.local.toml << 'EOF'
[db]
DB_USER="root"
DB_PASSWORD="password"
DB_HOST="db"
DB_PORT=3306
DB_NAME="yuyama"

[mock]
USE_MOCK_SERVICES=true

[core]
NAME="Yuyama Local Development"
SEARCH_INDEX_NAME_JP_LIST=["mock-index-jp"]
SEARCH_INDEX_NAME_ID_LIST=["mock-index-id"]
SEARCH_INDEX_AZURE_ID_LIST=["mock-azure-id"]
MODEL_LIST=["gpt-4o-mini", "gpt-4o"]
DEFAULT_MODEL="gpt-4o-mini"

[env]
SEARCH_ENDPOINT="http://localhost:8080/mock/search"
SEARCH_API_KEY="mock-search-key"
SEARCH_MODEL_NAME="mock-model"
STORAGE_CONNECTION_STRING="mock-storage-connection"
STORAGE_CONTAINER_NAME="mock-container"
STORAGE_BLOB_SERVICE_ENDPOINT="http://localhost:8080/mock/blob"
EMBEDDING_MODEL_NAME="mock-embedding-model"
AOAI_ENDPOINT="http://localhost:8080/mock/openai"
AOAI_API_KEY="mock-openai-key"
AOAI_API_VERSION="2024-02-01"
SECRET_KEY="local-development-secret-key-change-in-production"
DOCUMENT_INTELLIGENCE_KEY="mock-doc-intel-key"
DOCUMENT_INTELLIGENCE_ENDPOINT="http://localhost:8080/mock/document-intelligence"

[prompt]
SYSTEM_PROMPT="You are Yuyama, a helpful AI assistant running in local development mode."
HYPOTHETICAL_ANSWER_PROMPT="Based on the context provided, generate a hypothetical answer."
EOF

# その後、再実行
make setup && make up
```

### その他のエラー

**ポートエラー**

```bash
make down && make up
```

**完全リセット**

```bash
make reset
```

**ヘルプ表示**

```bash
make help
```

## 次のステップ

1. **コード確認**: `api/src/` と `web/app/` でソースコード確認
2. **カスタマイズ**: `api/config.local.toml` で設定変更
3. **開発開始**: `make dev` でファイル監視モード起動

---

**準備完了** 開発を開始できます。
