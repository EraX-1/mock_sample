#!/bin/bash

# Azure Database for MySQL ダミーデータ投入スクリプト
# 既存のAzure MySQLサーバーに対してダミーデータを投入します
# 使用方法: ./azure-mysql-seed-data.sh

set -e

# カラー出力の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 必要なツールの確認
check_requirements() {
    log_info "必要なツールを確認しています..."

    if ! command -v az &> /dev/null; then
        log_error "Azure CLI がインストールされていません"
        exit 1
    fi

    if ! command -v mysql &> /dev/null; then
        log_error "MySQL クライアントがインストールされていません"
        log_info "インストール方法:"
        log_info "  macOS: brew install mysql-client"
        log_info "  Ubuntu: sudo apt-get install mysql-client"
        log_info "  CentOS: sudo yum install mysql"
        exit 1
    fi

    log_success "必要なツールが確認できました"
}

# 設定ファイルの読み込み
load_config() {
    if [ -f "scripts/azure-mysql-config.env" ]; then
        log_info "設定ファイルを読み込んでいます..."
        source scripts/azure-mysql-config.env
        log_success "設定ファイルを読み込みました"
    else
        log_error "設定ファイルが見つかりません: scripts/azure-mysql-config.env"
        log_info "scripts/azure-mysql-config.env.example をコピーして設定ファイルを作成してください"
        exit 1
    fi

    # 環境変数の表示
    log_info "=== 設定情報 ==="
    echo "リソースグループ: $RESOURCE_GROUP"
    echo "MySQL サーバー名: $MYSQL_SERVER_NAME"
    echo "管理者ユーザー: $MYSQL_ADMIN_USER"
    echo "データベース名: $MYSQL_DATABASE_NAME"
    echo ""
}

# Azure ログイン確認
check_azure_login() {
    log_info "Azure ログイン状況を確認しています..."

    if ! az account show &> /dev/null; then
        log_error "Azure にログインしていません"
        log_info "az login を実行してください"
        exit 1
    fi

    local account_info=$(az account show --query "{name:name, id:id}" -o tsv)
    log_success "Azure にログイン済み: $account_info"
}

# MySQL サーバーの存在確認
check_mysql_server() {
    log_info "MySQL サーバーの存在を確認しています..."

    if ! az mysql flexible-server show --resource-group "$RESOURCE_GROUP" --name "$MYSQL_SERVER_NAME" &> /dev/null; then
        log_error "MySQL サーバー '$MYSQL_SERVER_NAME' が見つかりません"
        log_info "まず azure-mysql-setup.sh を実行してMySQLサーバーを作成してください"
        exit 1
    fi

    log_success "MySQL サーバーが見つかりました"
}

# ファイアウォール規則の確認・更新
ensure_firewall_access() {
    log_info "ファイアウォール規則を確認しています..."

    # 現在のクライアントIPを取得
    local client_ip=$(curl -s https://api.ipify.org 2>/dev/null || echo "unknown")

    if [ "$client_ip" != "unknown" ]; then
        log_info "クライアントIP: $client_ip"

        # クライアントIPのファイアウォール規則を更新
        az mysql flexible-server firewall-rule create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$MYSQL_SERVER_NAME" \
            --rule-name "AllowClientIP" \
            --start-ip-address "$client_ip" \
            --end-ip-address "$client_ip" \
            --yes &>/dev/null || true

        log_success "ファイアウォール規則を更新しました"
    else
        log_warning "クライアントIPを取得できませんでした"
    fi
}

# 接続テスト
test_connection() {
    log_info "データベース接続をテストしています..."

    local mysql_host="$MYSQL_SERVER_NAME.mysql.database.azure.com"
    local max_attempts=5
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "接続試行 $attempt/$max_attempts..."

        if mysql -h "$mysql_host" \
                 -u "$MYSQL_ADMIN_USER" \
                 -p"$MYSQL_ADMIN_PASSWORD" \
                 -P 3306 \
                 -D "$MYSQL_DATABASE_NAME" \
                 -e "SELECT 'Connection successful' as status;" &>/dev/null; then
            log_success "データベースへの接続に成功しました"
            return 0
        fi

        log_warning "接続に失敗しました。15秒後に再試行します..."
        sleep 15
        ((attempt++))
    done

    log_error "データベースへの接続に失敗しました"
    log_info "以下を確認してください:"
    echo "  1. MySQL サーバーが稼働しているか"
    echo "  2. ファイアウォール規則が正しく設定されているか"
    echo "  3. 認証情報が正しいか"
    echo "  4. データベースが存在するか"
    return 1
}

# データベース作成（存在しない場合）
ensure_database_exists() {
    log_info "データベースの存在を確認しています..."

    local mysql_host="$MYSQL_SERVER_NAME.mysql.database.azure.com"

    # データベースの存在確認
    local db_exists=$(mysql -h "$mysql_host" \
                           -u "$MYSQL_ADMIN_USER" \
                           -p"$MYSQL_ADMIN_PASSWORD" \
                           -P 3306 \
                           -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME='$MYSQL_DATABASE_NAME';" \
                           -s -N 2>/dev/null || echo "")

    if [ -z "$db_exists" ]; then
        log_warning "データベースが存在しません。作成します..."

        az mysql flexible-server db create \
            --resource-group "$RESOURCE_GROUP" \
            --server-name "$MYSQL_SERVER_NAME" \
            --database-name "$MYSQL_DATABASE_NAME" \
            --charset utf8mb4 \
            --collation utf8mb4_unicode_ci

        log_success "データベース '$MYSQL_DATABASE_NAME' を作成しました"
    else
        log_info "データベース '$MYSQL_DATABASE_NAME' は既に存在します"
    fi
}

# 既存データの確認
check_existing_data() {
    log_info "既存データを確認しています..."

    local mysql_host="$MYSQL_SERVER_NAME.mysql.database.azure.com"

    # テーブル一覧の取得
    local tables=$(mysql -h "$mysql_host" \
                        -u "$MYSQL_ADMIN_USER" \
                        -p"$MYSQL_ADMIN_PASSWORD" \
                        -P 3306 \
                        -D "$MYSQL_DATABASE_NAME" \
                        -e "SHOW TABLES;" -s -N 2>/dev/null || echo "")

    if [ -n "$tables" ]; then
        log_info "既存のテーブル:"
        echo "$tables" | while read table; do
            echo "  - $table"
        done

        # ユーザー数の確認
        local user_count=$(mysql -h "$mysql_host" \
                                -u "$MYSQL_ADMIN_USER" \
                                -p"$MYSQL_ADMIN_PASSWORD" \
                                -P 3306 \
                                -D "$MYSQL_DATABASE_NAME" \
                                -e "SELECT COUNT(*) FROM users;" -s -N 2>/dev/null || echo "0")

        log_info "現在のユーザー数: $user_count"

        if [ "$user_count" -gt 0 ]; then
            log_warning "既にダミーデータが存在する可能性があります"
            read -p "既存データを削除して新しいダミーデータを投入しますか？ (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "処理を中止します"
                exit 0
            fi

            log_warning "既存データを削除します..."
            # テーブルを削除（外部キー制約を考慮した順序）
            mysql -h "$mysql_host" \
                  -u "$MYSQL_ADMIN_USER" \
                  -p"$MYSQL_ADMIN_PASSWORD" \
                  -P 3306 \
                  -D "$MYSQL_DATABASE_NAME" \
                  -e "SET FOREIGN_KEY_CHECKS = 0;
                      DROP TABLE IF EXISTS indexed_files, search_index_types, chat_messages, chat_rooms, files, users;
                      SET FOREIGN_KEY_CHECKS = 1;" 2>/dev/null || true
        fi
    else
        log_info "既存のテーブルは見つかりませんでした"
    fi
}

# スキーマとダミーデータの投入
setup_database_schema() {
    log_info "データベーススキーマとダミーデータを投入しています..."

    local mysql_host="$MYSQL_SERVER_NAME.mysql.database.azure.com"
    local init_sql_file="scripts/init.sql"

    if [ ! -f "$init_sql_file" ]; then
        log_error "初期化SQLファイルが見つかりません: $init_sql_file"
        return 1
    fi

    # SQLファイルの実行
    log_info "SQLファイルを実行しています..."
    if mysql -h "$mysql_host" \
             -u "$MYSQL_ADMIN_USER" \
             -p"$MYSQL_ADMIN_PASSWORD" \
             -P 3306 \
             -D "$MYSQL_DATABASE_NAME" < "$init_sql_file"; then
        log_success "データベーススキーマとダミーデータの投入が完了しました"
    else
        log_error "データベーススキーマの投入に失敗しました"
        return 1
    fi
}

# データ確認
verify_data() {
    log_info "投入されたデータを確認しています..."

    local mysql_host="$MYSQL_SERVER_NAME.mysql.database.azure.com"

    # テーブル一覧の表示
    log_info "テーブル一覧:"
    mysql -h "$mysql_host" \
          -u "$MYSQL_ADMIN_USER" \
          -p"$MYSQL_ADMIN_PASSWORD" \
          -P 3306 \
          -D "$MYSQL_DATABASE_NAME" \
          -e "SHOW TABLES;"

    echo ""

    # 各テーブルのデータ数確認
    local tables=("users" "chat_rooms" "chat_messages" "files" "indexed_files" "search_index_types")

    for table in "${tables[@]}"; do
        local count=$(mysql -h "$mysql_host" \
                           -u "$MYSQL_ADMIN_USER" \
                           -p"$MYSQL_ADMIN_PASSWORD" \
                           -P 3306 \
                           -D "$MYSQL_DATABASE_NAME" \
                           -e "SELECT COUNT(*) FROM $table;" -s -N 2>/dev/null || echo "0")

        log_info "$table テーブル: $count 件"
    done

    # サンプルユーザーの表示
    log_info "サンプルユーザー:"
    mysql -h "$mysql_host" \
          -u "$MYSQL_ADMIN_USER" \
          -p"$MYSQL_ADMIN_PASSWORD" \
          -P 3306 \
          -D "$MYSQL_DATABASE_NAME" \
          -e "SELECT user_id, display_name, email FROM users LIMIT 3;" 2>/dev/null || true
}

# 接続情報の出力
output_connection_info() {
    log_success "=== ダミーデータ投入完了 ==="
    echo ""
    echo "Azure App Service 環境変数（本番用設定）:"
    echo "  DB_HOST=$MYSQL_SERVER_NAME.mysql.database.azure.com"
    echo "  DB_USER=$MYSQL_ADMIN_USER"
    echo "  DB_PASSWORD=$MYSQL_ADMIN_PASSWORD"
    echo "  DB_NAME=$MYSQL_DATABASE_NAME"
    echo "  DB_PORT=3306"
    echo "  USE_MOCK_SERVICES=false"
    echo ""
    echo "次のステップ:"
    echo "1. Azure App Service の環境変数を上記の値に更新"
    echo "2. アプリケーションを再デプロイまたは再起動"
    echo "3. アプリケーションの動作確認"
    echo ""
    echo "App Service環境変数の更新方法:"
    echo "az webapp config appsettings set \\"
    echo "  --resource-group $RESOURCE_GROUP \\"
    echo "  --name $API_APP_SERVICE_NAME \\"
    echo "  --settings \\"
    echo "    DB_HOST=$MYSQL_SERVER_NAME.mysql.database.azure.com \\"
    echo "    DB_USER=$MYSQL_ADMIN_USER \\"
    echo "    DB_PASSWORD=$MYSQL_ADMIN_PASSWORD \\"
    echo "    DB_NAME=$MYSQL_DATABASE_NAME \\"
    echo "    DB_PORT=3306 \\"
    echo "    USE_MOCK_SERVICES=false"
    echo ""
}

# エラーハンドリング
handle_error() {
    log_error "スクリプト実行中にエラーが発生しました"
    log_info "詳細なログを確認してください"
    exit 1
}

# メイン処理
main() {
    log_info "Azure Database for MySQL ダミーデータ投入を開始します"
    echo ""

    # エラーハンドリングの設定
    trap handle_error ERR

    # 各ステップの実行
    check_requirements
    load_config
    check_azure_login
    check_mysql_server
    ensure_firewall_access

    # 接続確認とデータ投入
    if test_connection; then
        ensure_database_exists
        check_existing_data
        setup_database_schema
        verify_data
        output_connection_info
    else
        log_error "データベースへの接続に失敗したため、処理を中断します"
        exit 1
    fi

    log_success "ダミーデータの投入が完了しました！"
}

# スクリプトが直接実行された場合のみメイン処理を実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
