# Azure Database for MySQL デプロイメントガイド

このガイドでは、`az` コマンドを使用してAzure Database for MySQLをデプロイし、Yuyama RAG Chatbotと連携させる手順を説明します。

## 前提条件

- Azure CLI がインストールされている
- Azure アカウントにログイン済み
- 適切な権限を持つAzureサブスクリプション
- 既存のリソースグループ

## 環境変数の設定

```bash
# Azure設定
export RESOURCE_GROUP="your-resource-group"
export LOCATION="japaneast"
export SUBSCRIPTION_ID="your-subscription-id"

# MySQL設定
export MYSQL_SERVER_NAME="yuyama-mysql-$(date +%Y%m%d%H%M%S)"
export MYSQL_ADMIN_USER="yuyama_admin"
export MYSQL_ADMIN_PASSWORD="SecurePassword123!"
export MYSQL_DATABASE_NAME="yuyama_production"

# セキュリティ設定
export CLIENT_IP=$(curl -s https://api.ipify.org)
echo "現在のクライアントIP: $CLIENT_IP"
```

## デプロイ手順

### 1. Azure CLI でログイン・サブスクリプション設定

```bash
# ログイン
az login

# サブスクリプションを設定
az account set --subscription $SUBSCRIPTION_ID

# アカウント情報確認
az account show
```

### 2. Azure Database for MySQL サーバーの作成

```bash
# MySQL サーバー作成（フレキシブルサーバー）
az mysql flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $MYSQL_SERVER_NAME \
  --location $LOCATION \
  --admin-user $MYSQL_ADMIN_USER \
  --admin-password $MYSQL_ADMIN_PASSWORD \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 20 \
  --version 8.0 \
  --high-availability Disabled \
  --storage-auto-grow Enabled \
  --backup-retention 7 \
  --geo-redundant-backup Disabled \
  --public-access 0.0.0.0 \
  --yes

echo "MySQL サーバー作成完了: $MYSQL_SERVER_NAME"
```

### 3. ファイアウォール規則の設定

```bash
# Azure サービスからのアクセスを許可
az mysql flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $MYSQL_SERVER_NAME \
  --rule-name "AllowAzureServices" \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# 現在のクライアントIPからのアクセスを許可
az mysql flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $MYSQL_SERVER_NAME \
  --rule-name "AllowClientIP" \
  --start-ip-address $CLIENT_IP \
  --end-ip-address $CLIENT_IP

echo "ファイアウォール規則設定完了"
```

### 4. データベースの作成

```bash
# データベース作成
az mysql flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $MYSQL_SERVER_NAME \
  --database-name $MYSQL_DATABASE_NAME \
  --charset utf8mb4 \
  --collation utf8mb4_unicode_ci

echo "データベース作成完了: $MYSQL_DATABASE_NAME"
```

### 5. SSL設定の調整（開発・テスト用）

```bash
# SSL証明書を必須にしない設定（本番環境では推奨しません）
az mysql flexible-server parameter set \
  --resource-group $RESOURCE_GROUP \
  --server-name $MYSQL_SERVER_NAME \
  --name require_secure_transport \
  --value OFF

echo "SSL設定調整完了"
```

### 6. 接続情報の表示

```bash
# 接続情報を表示
echo "=== MySQL 接続情報 ==="
echo "サーバー名: $MYSQL_SERVER_NAME.mysql.database.azure.com"
echo "管理者ユーザー: $MYSQL_ADMIN_USER"
echo "データベース名: $MYSQL_DATABASE_NAME"
echo "ポート: 3306"
echo ""
echo "=== 接続文字列 ==="
echo "mysql://$MYSQL_ADMIN_USER:$MYSQL_ADMIN_PASSWORD@$MYSQL_SERVER_NAME.mysql.database.azure.com:3306/$MYSQL_DATABASE_NAME"
echo ""
echo "=== Azure App Service 環境変数 ==="
echo "DB_HOST: $MYSQL_SERVER_NAME.mysql.database.azure.com"
echo "DB_USER: $MYSQL_ADMIN_USER"
echo "DB_PASSWORD: $MYSQL_ADMIN_PASSWORD"
echo "DB_NAME: $MYSQL_DATABASE_NAME"
echo "DB_PORT: 3306"
```

## データベースの初期化とダミーデータ投入

### 1. MySQL クライアントでの接続確認

```bash
# MySQL クライアントで接続テスト
mysql -h $MYSQL_SERVER_NAME.mysql.database.azure.com \
      -u $MYSQL_ADMIN_USER \
      -p$MYSQL_ADMIN_PASSWORD \
      -P 3306 \
      -D $MYSQL_DATABASE_NAME \
      -e "SELECT VERSION();"
```

### 2. スキーマとダミーデータの投入

```bash
# 初期化スクリプトの実行
mysql -h $MYSQL_SERVER_NAME.mysql.database.azure.com \
      -u $MYSQL_ADMIN_USER \
      -p$MYSQL_ADMIN_PASSWORD \
      -P 3306 \
      -D $MYSQL_DATABASE_NAME \
      < scripts/init.sql

echo "データベース初期化完了"
```

## Azure App Service との連携

### 1. API App Service の環境変数更新

```bash
# API App Service名を設定
export API_APP_SERVICE_NAME="yuyama-rag-chatbot-api-cmchguh0e8bjdqd6"

# 環境変数の設定
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_SERVICE_NAME \
  --settings \
    DB_HOST="$MYSQL_SERVER_NAME.mysql.database.azure.com" \
    DB_USER="$MYSQL_ADMIN_USER" \
    DB_PASSWORD="$MYSQL_ADMIN_PASSWORD" \
    DB_NAME="$MYSQL_DATABASE_NAME" \
    DB_PORT="3306" \
    USE_MOCK_SERVICES="false"

echo "API App Service 環境変数更新完了"
```

### 2. App Service の再起動

```bash
# API サービスの再起動
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_SERVICE_NAME

echo "API App Service 再起動完了"
```

## 接続テストとヘルスチェック

### 1. データベース接続テスト

```bash
# API ヘルスチェック
curl -X GET "https://$API_APP_SERVICE_NAME.azurewebsites.net/health"

# データベース接続確認
curl -X GET "https://$API_APP_SERVICE_NAME.azurewebsites.net/health/db"
```

### 2. ユーザー情報確認

```bash
# テストユーザーの存在確認
curl -X GET "https://$API_APP_SERVICE_NAME.azurewebsites.net/api/users/test" \
     -H "Content-Type: application/json"
```

## セキュリティ設定（本番環境用）

### 1. SSL証明書の有効化

```bash
# SSL証明書を必須にする（本番環境用）
az mysql flexible-server parameter set \
  --resource-group $RESOURCE_GROUP \
  --server-name $MYSQL_SERVER_NAME \
  --name require_secure_transport \
  --value ON
```

### 2. より厳密なファイアウォール規則

```bash
# 特定のIPレンジのみ許可（例：会社のIPレンジ）
az mysql flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $MYSQL_SERVER_NAME \
  --rule-name "AllowCorporateNetwork" \
  --start-ip-address "203.0.113.0" \
  --end-ip-address "203.0.113.255"

# 不要な汎用ルールを削除
az mysql flexible-server firewall-rule delete \
  --resource-group $RESOURCE_GROUP \
  --name $MYSQL_SERVER_NAME \
  --rule-name "AllowAzureServices" \
  --yes
```

## 監視とメンテナンス

### 1. ログの確認

```bash
# MySQL サーバーログの表示
az mysql flexible-server logs list \
  --resource-group $RESOURCE_GROUP \
  --server-name $MYSQL_SERVER_NAME

# 特定のログファイルを表示
az mysql flexible-server logs download \
  --resource-group $RESOURCE_GROUP \
  --server-name $MYSQL_SERVER_NAME \
  --name "mysql-slow.log"
```

### 2. メトリクスの確認

```bash
# CPU使用率の確認
az monitor metrics list \
  --resource "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DBforMySQL/flexibleServers/$MYSQL_SERVER_NAME" \
  --metric "cpu_percent" \
  --interval PT1M
```

## バックアップとリストア

### 1. ポイントインタイムリカバリ

```bash
# 特定の時点へのリストア
az mysql flexible-server restore \
  --resource-group $RESOURCE_GROUP \
  --name "$MYSQL_SERVER_NAME-restored" \
  --source-server $MYSQL_SERVER_NAME \
  --restore-time "2024-01-01T12:00:00Z"
```

## トラブルシューティング

### よくある問題と解決方法

1. **接続できない場合**
   - ファイアウォール規則を確認
   - クライアントIPが変更されていないか確認
   - SSL設定を確認

2. **認証エラーの場合**
   - ユーザー名とパスワードを確認
   - MySQL のユーザー権限を確認

3. **パフォーマンスが悪い場合**
   - SKUを上位プランに変更
   - インデックスの最適化
   - クエリのパフォーマンス分析

## クリーンアップ

```bash
# MySQL サーバーの削除（注意：データも削除されます）
az mysql flexible-server delete \
  --resource-group $RESOURCE_GROUP \
  --name $MYSQL_SERVER_NAME \
  --yes
```

## 参考リンク

- [Azure Database for MySQL ドキュメント](https://docs.microsoft.com/azure/mysql/)
- [Azure CLI MySQL コマンド](https://docs.microsoft.com/cli/azure/mysql/)
- [MySQL 8.0 リファレンス](https://dev.mysql.com/doc/refman/8.0/en/)

---

**注意**: パスワードや機密情報は適切に管理し、本番環境では Azure Key Vault などのシークレット管理サービスを使用してください。
