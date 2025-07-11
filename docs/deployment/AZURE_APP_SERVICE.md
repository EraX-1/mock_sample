# Azure App Service デプロイメントガイド

このガイドでは、Yuyama RAG Chatbot をモックモードで Azure App Service にデプロイする手順を説明します。

## 前提条件

- Azure CLI がインストールされている
- Docker がインストールされている
- Azure Container Registry (ACR) が作成されている
- Azure App Service が作成されている
- 必要な権限を持つ Azure アカウント

## デプロイ手順

### 1. Azure CLI でログイン

```bash
az login
```

### 2. 環境変数の設定

```bash
# Azure Container Registry名を設定
export ACR_NAME=your-acr-name

# オプション: APIエンドポイントをカスタマイズ
export NEXT_PUBLIC_API_URL=https://yuyama-rag-chatbot-api-cmchguh0e8bjdqd6.japaneast-01.azurewebsites.net
export NEXT_PUBLIC_APP_ENV=development
export NEXT_PUBLIC_MOCK_MODE=true
```

### 3. デプロイスクリプトの実行

```bash
# プロジェクトルートディレクトリで実行
./azure-deploy.sh
```

このスクリプトは以下を実行します：

- フロントエンドと API の Docker イメージをビルド
- Azure Container Registry にイメージをプッシュ
- latest タグと タイムスタンプ付きタグの両方を作成

### 4. Azure App Service の設定

#### 4.1 フロントエンド App Service

1. Azure Portal で フロントエンド App Service を開く
2. 「デプロイセンター」 → 「設定」で以下を設定：

   - レジストリ: Azure Container Registry
   - イメージ: `yuyama-rag-chatbot-frontend`
   - タグ: `latest`

3. 「構成」 → 「アプリケーション設定」で環境変数を追加：
   ```
   NEXT_PUBLIC_API_URL=https://yuyama-rag-chatbot-api-cmchguh0e8bjdqd6.japaneast-01.azurewebsites.net
   NEXT_PUBLIC_APP_ENV=development
   NEXT_PUBLIC_APP_NAME=yuyama-rag-chatbot-frontend
   NEXT_PUBLIC_DEBUG=true
   NEXT_PUBLIC_LOG_LEVEL=debug
   NEXT_PUBLIC_MOCK_MODE=true
   WEBSITES_PORT=3000
   ```

#### 4.2 API App Service

1. Azure Portal で API App Service を開く
2. 「デプロイセンター」 → 「設定」で以下を設定：

   - レジストリ: Azure Container Registry
   - イメージ: `yuyama-rag-chatbot-api`
   - タグ: `latest`

3. 「構成」 → 「アプリケーション設定」で環境変数を追加（`.env.azure.example`を参考）：

   ```
   # データベース設定（モック環境では任意）
   DB_USER=azureuser
   DB_PASSWORD=your-secure-password
   DB_HOST=your-mysql-server.mysql.database.azure.com
   DB_PORT=3306
   DB_NAME=yuyama_production

   # モックサービス有効化
   USE_MOCK_SERVICES=true

   # その他の設定（.env.azure.exampleを参照）
   WEBSITES_PORT=8080
   ```

### 5. ヘルスチェックの確認

デプロイ後、以下の URL でヘルスチェックを確認：

- フロントエンド: `https://yuyama-rag-chatbot-frontend-fgf7byd6b9f4fqck.japaneast-01.azurewebsites.net/api/health`
- API: `https://yuyama-rag-chatbot-api-cmchguh0e8bjdqd6.japaneast-01.azurewebsites.net/health`

## トラブルシューティング

### コンテナが起動しない場合

1. App Service のログストリームを確認
2. コンテナの診断ログを有効化
3. 環境変数が正しく設定されているか確認

### API に接続できない場合

1. CORS 設定を確認（API の main.py で設定済み）
2. フロントエンドの`NEXT_PUBLIC_API_URL`が正しいか確認
3. API のヘルスチェックエンドポイントが応答するか確認

### デプロイが失敗する場合

1. ACR へのプッシュ権限があるか確認
2. App Service が ACR からプルする権限があるか確認
3. Docker イメージのビルドログを確認

## セキュリティに関する注意事項

1. **本番環境での使用について**

   - 現在の設定はモック環境用です
   - 実際の Azure サービスを使用する場合は、適切な認証情報に更新してください

2. **シークレット管理**

   - パスワードや API キーは Azure Key Vault で管理することを推奨
   - 環境変数に直接機密情報を設定する場合は、App Service の設定で管理

3. **ネットワークセキュリティ**
   - 必要に応じて Virtual Network 統合を検討
   - App Service のアクセス制限を設定

## 更新とロールバック

### イメージの更新

```bash
# 新しいバージョンをデプロイ
./azure-deploy.sh

# App Service で最新イメージを取得
# Azure Portal → App Service → デプロイセンター → 「同期」をクリック
```

### ロールバック

タイムスタンプ付きタグを使用してロールバック：

```bash
# Azure Portal → App Service → デプロイセンター
# タグを特定のバージョン（例: 20240618120000-abc1234）に変更
```

## 監視とログ

1. **Application Insights**（オプション）

   - 接続文字列を環境変数`APPLICATIONINSIGHTS_CONNECTION_STRING`に設定

2. **ログストリーム**

   - Azure Portal → App Service → 「ログストリーム」で確認

3. **メトリクス**
   - CPU 使用率、メモリ使用率、応答時間などを監視

## 参考リンク

- [Azure App Service ドキュメント](https://docs.microsoft.com/azure/app-service/)
- [Azure Container Registry ドキュメント](https://docs.microsoft.com/azure/container-registry/)
- [Docker ドキュメント](https://docs.docker.com/)
