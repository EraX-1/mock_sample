# 🚀 Yuyama RAG Chatbot 完全デプロイガイド

このガイドでは、Azure環境にYuyama RAG Chatbotを完全にデプロイする手順を説明します。

## 📋 デプロイメント概要

### 🎯 構成要素
- **Frontend**: Next.js (Azure App Service)
- **Backend**: FastAPI (Azure App Service)
- **Database**: MySQL (Azure Database for MySQL)
- **Storage**: Azure Blob Storage
- **AI Services**: Azure OpenAI, Azure AI Search

### ⏱️ 所要時間
- **自動デプロイ**: 約15-20分
- **手動設定含む**: 約30-45分

## 🛠️ 前提条件

### 必須ツール
```bash
# Azure CLI の確認
az --version

# Docker の確認
docker --version

# MySQL Client の確認
mysql --version
```

### Azure リソース
- Azure サブスクリプション
- リソースグループ
- Azure Container Registry (ACR)

## 🚀 デプロイ手順

### 1️⃣ **設定ファイルの準備**

```bash
# リポジトリをクローン
git clone <repository-url>
cd yuyama

# 設定ファイルをコピー
cp scripts/azure-mysql-config.env.example scripts/azure-mysql-config.env
```

**重要**: `scripts/azure-mysql-config.env` を編集：

```bash
# Azure 基本設定
RESOURCE_GROUP="yuyama-rg"              # 既存のリソースグループ
SUBSCRIPTION_ID="your-subscription-id"  # サブスクリプションID
LOCATION="eastus"                       # 推奨リージョン

# MySQL設定
MYSQL_ADMIN_PASSWORD="SecurePassword123!"  # 強力なパスワードに変更

# App Service名（既存の名前に変更）
API_APP_SERVICE_NAME="your-api-app-service"
FRONTEND_APP_SERVICE_NAME="your-frontend-app-service"
```

### 2️⃣ **Azureにログイン**

```bash
# Azure CLI でログイン
az login

# サブスクリプションを設定
az account set --subscription "your-subscription-id"

# アカウント確認
az account show
```

### 3️⃣ **完全デプロイの実行**

```bash
# 統合デプロイスクリプトを実行
./deploy-azure.sh full
```

このスクリプトは以下を自動実行します：
1. Frontend & Backend のビルド・デプロイ
2. MySQL データベースの作成・初期化
3. App Service の環境変数設定
4. ヘルスチェック・動作確認

## 🔧 個別デプロイ手順

自動デプロイに問題がある場合の個別実行手順：

### Step 1: Frontend & Backend デプロイ

```bash
# 既存の App Service デプロイスクリプト
./deploy-azure.sh app-only
```

詳細は [Azure App Service デプロイガイド](AZURE_APP_SERVICE.md) を参照。

### Step 2: MySQL データベース作成

```bash
# MySQL 自動セットアップ
./scripts/azure-mysql-setup.sh
```

手動作成が必要な場合：
```bash
# 手動作成ガイドを表示
./scripts/azure-mysql-manual.sh
```

詳細は [Azure MySQL デプロイガイド](AZURE_MYSQL.md) を参照。

### Step 3: App Service 環境変数設定

```bash
# App Service とMySQLの連携設定
./scripts/azure-app-service-config.sh
```

## ✅ デプロイ後の確認

### 🔍 **ヘルスチェック**

```bash
# API サービス確認
curl https://your-api-app.azurewebsites.net/health

# データベース接続確認
curl https://your-api-app.azurewebsites.net/health/db

# Frontend 確認
curl https://your-frontend-app.azurewebsites.net
```

### 🌐 **アクセスURL**

- **Frontend**: `https://your-frontend-app.azurewebsites.net`
- **API**: `https://your-api-app.azurewebsites.net`
- **API Docs**: `https://your-api-app.azurewebsites.net/docs`

### 👤 **テストログイン**

| ユーザー種別 | メールアドレス | パスワード | 説明 |
|------------|-------------|---------|------|
| 一般ユーザー | `test.user@example.com` | (設定済み) | 基本機能テスト |
| 管理者 | `admin@example.com` | (設定済み) | 管理機能テスト |
| デモユーザー | `demo@kandenko.co.jp` | (設定済み) | デモ用 |

## 🛠️ トラブルシューティング

### ❌ **よくあるエラーと解決策**

#### 1. "No available SKUs in this location"
```bash
# より安定したリージョンを使用
LOCATION="eastus"  # または "westeurope"
```

#### 2. App Service が起動しない
```bash
# ログを確認
az webapp log tail --resource-group <RG> --name <APP_NAME>

# コンテナを再起動
az webapp restart --resource-group <RG> --name <APP_NAME>
```

#### 3. データベース接続エラー
```bash
# ファイアウォール規則を確認
az mysql flexible-server firewall-rule list \
  --resource-group <RG> \
  --name <MYSQL_SERVER>

# SSL設定を確認（開発環境では無効）
az mysql flexible-server parameter show \
  --resource-group <RG> \
  --server-name <MYSQL_SERVER> \
  --name require_secure_transport
```

#### 4. リソース作成エラー
```bash
# クォータ制限を確認
az vm list-usage --location eastus --output table

# サブスクリプションの制限を確認
az account show --query "subscriptionPolicies"
```

### 🔄 **リセット・再デプロイ**

```bash
# MySQL サーバーの削除（データも削除される）
az mysql flexible-server delete \
  --resource-group <RG> \
  --name <MYSQL_SERVER> \
  --yes

# App Service の設定リセット
az webapp config appsettings delete \
  --resource-group <RG> \
  --name <APP_NAME> \
  --setting-names DB_HOST DB_USER DB_PASSWORD

# 完全再デプロイ
./deploy-azure.sh full
```

## 📊 監視・運用

### 📈 **パフォーマンス監視**

Azure Portal で以下を監視：

1. **App Service メトリクス**
   - CPU 使用率
   - メモリ使用量
   - HTTP 応答時間
   - エラー率

2. **MySQL メトリクス**
   - 接続数
   - クエリパフォーマンス
   - ストレージ使用量
   - レプリケーション遅延

3. **リソース使用量**
   - ネットワーク帯域幅
   - ストレージ I/O
   - CPU とメモリの傾向

### 🚨 **アラート設定**

```bash
# CPU 使用率アラート
az monitor metrics alert create \
  --name "High CPU Usage" \
  --resource-group <RG> \
  --scopes <APP_SERVICE_ID> \
  --condition "avg CpuPercentage > 80" \
  --window-size 5m \
  --evaluation-frequency 1m

# データベース接続数アラート
az monitor metrics alert create \
  --name "High DB Connections" \
  --resource-group <RG> \
  --scopes <MYSQL_SERVER_ID> \
  --condition "avg active_connections > 80" \
  --window-size 5m
```

### 🔄 **自動スケーリング**

```bash
# App Service の自動スケーリング設定
az monitor autoscale create \
  --resource-group <RG> \
  --resource <APP_SERVICE_ID> \
  --min-count 1 \
  --max-count 5 \
  --count 2

# スケールアウト条件
az monitor autoscale rule create \
  --resource-group <RG> \
  --autoscale-name <AUTOSCALE_NAME> \
  --condition "CpuPercentage > 70 avg 5m" \
  --scale out 1
```

## 💰 コスト最適化

### 💡 **開発環境コスト削減**

```bash
# 夜間の自動停止（Dev/Test環境）
az webapp config appsettings set \
  --resource-group <RG> \
  --name <APP_NAME> \
  --settings WEBSITE_TIME_ZONE="Tokyo Standard Time"

# 低コストMySQLプラン
SKU_NAME="Standard_B1s"  # 最小構成
STORAGE_SIZE="20"        # 最小ストレージ
```

### 📊 **コスト監視**

```bash
# 月間コスト確認
az consumption usage list \
  --billing-period-name "202401" \
  --query "[?contains(instanceName, 'yuyama')]"

# 予算アラート設定
az consumption budget create \
  --budget-name "yuyama-monthly-budget" \
  --amount 100 \
  --time-grain Monthly \
  --start-date "2024-01-01" \
  --end-date "2024-12-31"
```

## 🔐 セキュリティ強化

### 🛡️ **本番環境向け設定**

```bash
# SSL 証明書の強制
az mysql flexible-server parameter set \
  --resource-group <RG> \
  --server-name <MYSQL_SERVER> \
  --name require_secure_transport \
  --value ON

# App Service のHTTPS強制
az webapp update \
  --resource-group <RG> \
  --name <APP_NAME> \
  --https-only true

# IP制限の設定
az webapp config access-restriction add \
  --resource-group <RG> \
  --name <APP_NAME> \
  --rule-name "AllowCorporateNetwork" \
  --action Allow \
  --ip-address 203.0.113.0/24 \
  --priority 100
```

### 🔑 **シークレット管理**

```bash
# Azure Key Vault 作成
az keyvault create \
  --name "yuyama-keyvault" \
  --resource-group <RG> \
  --location <LOCATION>

# シークレットの保存
az keyvault secret set \
  --vault-name "yuyama-keyvault" \
  --name "mysql-password" \
  --value <SECURE_PASSWORD>

# App Service でKey Vault参照
az webapp config appsettings set \
  --resource-group <RG> \
  --name <APP_NAME> \
  --settings DB_PASSWORD="@Microsoft.KeyVault(VaultName=yuyama-keyvault;SecretName=mysql-password)"
```

## 🔄 CI/CD パイプライン

### 📋 **GitHub Actions設定例**

`.github/workflows/deploy-azure.yml`:

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

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to Azure
        run: |
          chmod +x ./deploy-azure.sh full
          ./deploy-azure.sh full
        env:
          RESOURCE_GROUP: ${{ secrets.RESOURCE_GROUP }}
          MYSQL_ADMIN_PASSWORD: ${{ secrets.MYSQL_PASSWORD }}
```

## 📚 関連ドキュメント

- [Azure App Service デプロイ](AZURE_APP_SERVICE.md)
- [Azure MySQL セットアップ](AZURE_MYSQL.md)
- [ローカル開発環境](../quickstart/LOCAL.md)

---

**🎉 デプロイ完了** 本格的なプロダクション環境が利用可能になりました！
