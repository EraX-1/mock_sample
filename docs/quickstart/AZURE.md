# Yuyama Azure デプロイガイド

**⚠️ 注意**: このガイドは開発中です。現在はセットアップ手順として参考にしてください。

**Azure環境への完全デプロイ手順**

## 🚀 超高速デプロイメント

```bash
# 1. リポジトリクローン
git clone <repository-url>
cd yuyama

# 2. 設定ファイル作成
cp scripts/azure-mysql-config.env.example scripts/azure-mysql-config.env

# 3. 設定ファイル編集（重要！）
# RESOURCE_GROUP, SUBSCRIPTION_ID, パスワード等を設定
vim scripts/azure-mysql-config.env

# 4. Azure ログイン
az login

# 5. 完全デプロイ実行（Frontend + Backend + MySQL）
./deploy-azure.sh full
```

## ⚡ 個別デプロイメント（段階的実行）

### 1. Frontend & Backend のみ

```bash
# 既存のモック環境デプロイ
./azure-deploy.sh
```

### 2. MySQL データベース作成

```bash
# MySQL セットアップ
./scripts/azure-mysql-setup.sh
```

### 3. App Service 環境変数設定

```bash
# サービス連携設定
./scripts/azure-app-service-config.sh
```

## 📋 デプロイ前の設定

### 必須設定項目

`scripts/azure-mysql-config.env` を編集：

```bash
# Azure 基本設定
RESOURCE_GROUP="your-resource-group"
SUBSCRIPTION_ID="your-subscription-id"

# MySQL設定
MYSQL_ADMIN_PASSWORD="SecurePassword123!"

# 既存のApp Service名（AZURE_DEPLOYMENT.mdの環境に合わせる）
API_APP_SERVICE_NAME="yuyama-rag-chatbot-api-cmchguh0e8bjdqd6"
FRONTEND_APP_SERVICE_NAME="yuyama-rag-chatbot-frontend-fgf7byd6b9f4fqck"
```

## 🔗 アクセス確認

デプロイ完了後、以下のURLにアクセス：

- **Frontend**: https://your-frontend-app.azurewebsites.net
- **API**: https://your-api-app.azurewebsites.net
- **API Docs**: https://your-api-app.azurewebsites.net/docs

## 🧪 動作テスト

### 1. ヘルスチェック

```bash
# API サービス確認
curl https://your-api-app.azurewebsites.net/health

# データベース接続確認
curl https://your-api-app.azurewebsites.net/health/db
```

### 2. ログイン テスト

| ユーザー種別 | メールアドレス | 説明 |
|------------|-------------|------|
| 一般ユーザー | `test.user@example.com` | 基本機能テスト用 |
| 管理者 | `admin@example.com` | 管理機能テスト用 |
| デモユーザー | `demo@kandenko.co.jp` | デモンストレーション用 |

### 3. 機能確認

- ✅ チャット機能（実際のMySQLベース）
- ✅ 文書アップロード（Azure Blob Storage）
- ✅ 検索機能（MySQLベースの全文検索）
- ✅ 管理機能（ユーザー・権限管理）

## 🛠️ トラブルシューティング

### 接続エラー

```bash
# サービス再起動
az webapp restart --resource-group <RG> --name <APP_NAME>

# ログ確認
az webapp log tail --resource-group <RG> --name <APP_NAME>
```

### データベース接続問題

```bash
# MySQL接続テスト
mysql -h your-mysql-server.mysql.database.azure.com \
      -u your-admin-user -p \
      -D your-database
```

### 設定リセット

```bash
# 設定ファイル再作成
cp scripts/azure-mysql-config.env.example scripts/azure-mysql-config.env

# 環境変数再設定
./scripts/azure-app-service-config.sh
```

## 📊 監視とメンテナンス

### Azure Portal でのモニタリング

1. **App Service メトリクス**
   - CPU使用率
   - メモリ使用量
   - HTTP応答時間

2. **MySQL メトリクス**
   - 接続数
   - クエリパフォーマンス
   - ストレージ使用量

3. **ログストリーム**
   - リアルタイムログ監視
   - エラー追跡

### 自動スケーリング

```bash
# App Service のスケールアウト設定
az monitor autoscale create \
  --resource-group <RG> \
  --resource <APP_SERVICE> \
  --min-count 1 \
  --max-count 5 \
  --count 2
```

## 🔐 セキュリティ設定

### 本番環境向け強化

```bash
# SSL証明書の強制
az mysql flexible-server parameter set \
  --resource-group <RG> \
  --server-name <MYSQL_SERVER> \
  --name require_secure_transport \
  --value ON

# IP制限の設定
az webapp config access-restriction add \
  --resource-group <RG> \
  --name <APP_NAME> \
  --rule-name "AllowCorporateNetwork" \
  --action Allow \
  --ip-address 203.0.113.0/24
```

### シークレット管理

```bash
# Azure Key Vault 作成
az keyvault create \
  --name yuyama-keyvault \
  --resource-group <RG> \
  --location japaneast

# シークレット保存
az keyvault secret set \
  --vault-name yuyama-keyvault \
  --name "mysql-password" \
  --value "your-secure-password"
```

## 💰 コスト最適化

### 開発環境コスト削減

```bash
# 夜間・週末の自動停止設定
az webapp config appsettings set \
  --resource-group <RG> \
  --name <APP_NAME> \
  --settings WEBSITE_TIME_ZONE="Tokyo Standard Time"

# MySQL の低コストプラン
# SKU: Standard_B1ms (バースト可能)
# ストレージ: 20GB（自動拡張有効）
```

## 🔄 CI/CD パイプライン

### GitHub Actions 設定例

```yaml
name: Deploy to Azure
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to Azure
        run: |
          az login --service-principal \
            -u ${{ secrets.AZURE_CLIENT_ID }} \
            -p ${{ secrets.AZURE_CLIENT_SECRET }} \
            --tenant ${{ secrets.AZURE_TENANT_ID }}

          ./deploy-azure.sh full
```

## 📚 参考資料

- [Azure App Service ドキュメント](https://docs.microsoft.com/azure/app-service/)
- [Azure Database for MySQL](https://docs.microsoft.com/azure/mysql/)
- [Azure CLI リファレンス](https://docs.microsoft.com/cli/azure/)

## 🆘 サポート

問題が発生した場合：

1. **ログ確認**: Azure Portal → App Service → ログストリーム
2. **設定確認**: 環境変数とネットワーク設定
3. **リソース状態**: CPU・メモリ使用量
4. **データベース**: 接続数と性能メトリクス

---

**準備完了** Azure 上で完全なプロダクション環境が利用可能です！
