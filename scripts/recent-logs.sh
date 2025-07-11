#!/bin/bash

# Yuyama RAG Chatbot - 最近のログ取得スクリプト
# 過去のログを確認

set -e

# 設定
RESOURCE_GROUP="yuyama"
API_APP_SERVICE="yuyama-rag-chatbot-api"
FRONTEND_APP_SERVICE="yuyama-rag-chatbot-frontend"

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 最近のログを取得
get_recent_logs() {
    local app_name=$1
    local service_type=$2
    local color=$3
    local hours=${4:-1}  # デフォルトは過去1時間

    log "Getting logs for $service_type (past $hours hour(s))..."

    # 過去のログを取得（最大1000行）
    echo -e "\n${color}=== $service_type Logs ===${NC}"

    az webapp log download \
        --resource-group "$RESOURCE_GROUP" \
        --name "$app_name" \
        --log-file "/tmp/${app_name}_logs.zip" 2>/dev/null || {
        error "Failed to download logs for $service_type"
        return 1
    }

    # ZIPファイルを解凍して最新のログを表示
    if [ -f "/tmp/${app_name}_logs.zip" ]; then
        unzip -q -o "/tmp/${app_name}_logs.zip" -d "/tmp/${app_name}_logs/"

        # 最新のアプリケーションログを検索
        local log_files=$(find "/tmp/${app_name}_logs/" -name "*.txt" -o -name "*.log" 2>/dev/null | sort -r)

        if [ -n "$log_files" ]; then
            echo "$log_files" | head -5 | while read -r log_file; do
                if [ -f "$log_file" ]; then
                    echo -e "${color}--- $(basename "$log_file") ---${NC}"
                    tail -50 "$log_file" | while IFS= read -r line; do
                        echo -e "${color}$line${NC}"
                    done
                    echo ""
                fi
            done
        else
            warn "No log files found for $service_type"
        fi

        # クリーンアップ
        rm -rf "/tmp/${app_name}_logs/" "/tmp/${app_name}_logs.zip"
    fi
}

# エラーログのみ取得
get_error_logs() {
    local app_name=$1
    local service_type=$2

    log "Checking for errors in $service_type..."

    # Kuduサイトから診断ログを取得
    local kudu_url="https://${app_name}.scm.azurewebsites.net/api/logs/docker"

    echo -e "\n${RED}=== $service_type Error Analysis ===${NC}"

    # 最近のDocker/コンテナログを確認
    az webapp log show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$app_name" \
        --query "properties" 2>/dev/null || {
        error "Failed to get container logs for $service_type"
    }
}

# メイン処理
main() {
    local api_only=false
    local frontend_only=false
    local errors_only=false
    local hours=1

    # 引数解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-only)
                api_only=true
                shift
                ;;
            --frontend-only)
                frontend_only=true
                shift
                ;;
            --errors)
                errors_only=true
                shift
                ;;
            --hours)
                hours=$2
                shift 2
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --api-only      Show API logs only"
                echo "  --frontend-only Show Frontend logs only"
                echo "  --errors        Show errors only"
                echo "  --hours N       Show logs from past N hours (default: 1)"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    log "🔍 Fetching recent logs..."

    if [ "$errors_only" = true ]; then
        # エラーログのみ
        if [ "$frontend_only" != true ]; then
            get_error_logs "$API_APP_SERVICE" "API"
        fi

        if [ "$api_only" != true ]; then
            get_error_logs "$FRONTEND_APP_SERVICE" "Frontend"
        fi
    else
        # 通常ログ
        if [ "$frontend_only" != true ]; then
            get_recent_logs "$API_APP_SERVICE" "API" "$CYAN" "$hours"
        fi

        if [ "$api_only" != true ]; then
            get_recent_logs "$FRONTEND_APP_SERVICE" "Frontend" "$MAGENTA" "$hours"
        fi
    fi

    success "✅ Log retrieval completed!"
}

main "$@"
