#!/bin/bash

# Yuyama RAG Chatbot - リアルタイムログ監視スクリプト
# API・Frontend の Azure App Service ログを並列で監視

set -e

# 設定 (deploy.shと同じ設定を使用)
RESOURCE_GROUP="yuyama"
API_APP_SERVICE="yuyama-rag-chatbot-api"
FRONTEND_APP_SERVICE="yuyama-rag-chatbot-frontend"
API_URL="yuyama-rag-chatbot-api-cmchguh0e8bjdqd6.japaneast-01.azurewebsites.net"
FRONTEND_URL="yuyama-rag-chatbot-frontend-fgf7byd6b9f4fqck.japaneast-01.azurewebsites.net"

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ログプレフィックス用の色
API_COLOR=$CYAN
FRONTEND_COLOR=$MAGENTA

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# App Service の存在確認
check_app_service() {
    local app_name=$1
    local service_type=$2

    log "Checking $service_type App Service: $app_name"

    if az webapp show --resource-group "$RESOURCE_GROUP" --name "$app_name" &>/dev/null; then
        success "$service_type App Service found: $app_name"
        return 0
    else
        error "$service_type App Service not found: $app_name"
        return 1
    fi
}

# リアルタイムログストリーミング (色付き出力)
stream_logs() {
    local app_name=$1
    local service_type=$2
    local color=$3

    log "Starting log stream for $service_type..."

    # ログストリームを開始 (バックグラウンドで実行)
    {
        # unbufferが利用可能かチェック (expectパッケージに含まれる)
        if command -v unbuffer >/dev/null 2>&1; then
            # unbufferを使用してバッファリングを無効化
            unbuffer az webapp log tail \
                --resource-group "$RESOURCE_GROUP" \
                --name "$app_name" \
                --provider application \
                2>&1 | while IFS= read -r line; do
                    # タイムスタンプとサービス名を追加して色付き出力
                    timestamp=$(date '+%H:%M:%S')
                    echo -e "${color}[$timestamp $service_type]${NC} $line"
                done
        else
            # unbufferが利用できない場合は通常の方法
            az webapp log tail \
                --resource-group "$RESOURCE_GROUP" \
                --name "$app_name" \
                --provider application \
                2>&1 | while IFS= read -r line; do
                    # タイムスタンプとサービス名を追加して色付き出力
                    timestamp=$(date '+%H:%M:%S')
                    echo -e "${color}[$timestamp $service_type]${NC} $line"
                    # リアルタイム表示を改善するため、少し待機
                    sleep 0.01
                done
        fi
    } &

    # プロセスIDを保存
    local service_lower=$(echo "$service_type" | tr '[:upper:]' '[:lower:]')
    echo $! > "/tmp/yuyama_${service_lower}_log.pid"
}

# ログストリーミング停止
stop_logs() {
    log "Stopping log streams..."

    # API ログストリーム停止
    if [ -f "/tmp/yuyama_api_log.pid" ]; then
        local api_pid=$(cat "/tmp/yuyama_api_log.pid")
        kill $api_pid 2>/dev/null || true
        rm -f "/tmp/yuyama_api_log.pid"
    fi

    # Frontend ログストリーム停止
    if [ -f "/tmp/yuyama_frontend_log.pid" ]; then
        local frontend_pid=$(cat "/tmp/yuyama_frontend_log.pid")
        kill $frontend_pid 2>/dev/null || true
        rm -f "/tmp/yuyama_frontend_log.pid"
    fi

    # az webapp log tail プロセスを強制終了
    pkill -f "az webapp log tail" 2>/dev/null || true

    success "Log streams stopped"
}

# トラップでクリーンアップ
cleanup() {
    echo ""
    log "Cleaning up..."
    stop_logs
    exit 0
}

# シグナルハンドリング
trap cleanup SIGINT SIGTERM

# ヘルプ表示
show_help() {
    echo "Yuyama RAG Chatbot - リアルタイムログ監視"
    echo ""
    echo "使用方法:"
    echo "  $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  --api-only      APIログのみ表示"
    echo "  --frontend-only Frontendログのみ表示"
    echo "  --health        ヘルスチェック実行"
    echo "  --install-deps  macOS用依存関係インストール"
    echo "  --help          このヘルプを表示"
    echo ""
    echo "操作:"
    echo "  Ctrl+C          ログ監視を停止"
    echo ""
    echo "例:"
    echo "  $0              # 両方のログを並列表示"
    echo "  $0 --api-only   # APIログのみ表示"
    echo "  $0 --health     # ヘルスチェック実行"
    echo ""
    echo "macOS使用時の注意:"
    echo "  リアルタイム性を向上させるには:"
    echo "  brew install expect  # unbufferコマンドをインストール"
    echo "  または $0 --install-deps を実行"
}

# macOS用依存関係インストール
install_deps() {
    log "Installing macOS dependencies for better log streaming..."

    # Homebrewがインストールされているかチェック
    if ! command -v brew >/dev/null 2>&1; then
        error "Homebrew not found. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

    # expectパッケージをインストール (unbufferコマンドが含まれる)
    log "Installing expect package..."
    if brew install expect; then
        success "expect package installed successfully"
        success "unbuffer command is now available for better log streaming"
    else
        error "Failed to install expect package"
        exit 1
    fi
}

# ヘルスチェック
health_check() {
    log "Performing health check..."

    local api_url="https://$API_URL"
    local frontend_url="https://$FRONTEND_URL"

    # 並列ヘルスチェック
    {
        log "Checking API health..."
        local api_status=$(curl -s -o /dev/null -w "%{http_code}" "$api_url/health" || echo "000")
        if [ "$api_status" = "200" ]; then
            success "API is healthy (HTTP $api_status)"
        else
            warn "API health check failed (HTTP $api_status)"
        fi
    } &

    {
        log "Checking Frontend health..."
        local frontend_status=$(curl -s -o /dev/null -w "%{http_code}" "$frontend_url" || echo "000")
        if [ "$frontend_status" = "200" ]; then
            success "Frontend is healthy (HTTP $frontend_status)"
        else
            warn "Frontend health check failed (HTTP $frontend_status)"
        fi
    } &

    wait

    echo ""
    echo "URLs:"
    echo "  🌐 Frontend: $frontend_url"
    echo "  🔧 API: $api_url"
    echo "  📚 API Docs: $api_url/docs"
    echo "  ❤️ API Health: $api_url/health"
}

# メイン処理
main() {
    local api_only=false
    local frontend_only=false
    local health_only=false

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
            --health)
                health_only=true
                shift
                ;;
            --install-deps)
                install_deps
                exit 0
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # ヘルスチェックのみの場合
    if [ "$health_only" = true ]; then
        health_check
        exit 0
    fi

    log "🚀 Starting Yuyama log monitoring..."

    # App Service 存在確認
    local services_available=0

    if [ "$frontend_only" != true ]; then
        if check_app_service "$API_APP_SERVICE" "API"; then
            ((services_available++))
        fi
    fi

    if [ "$api_only" != true ]; then
        if check_app_service "$FRONTEND_APP_SERVICE" "Frontend"; then
            ((services_available++))
        fi
    fi

    if [ $services_available -eq 0 ]; then
        error "No available App Services found"
        exit 1
    fi

    echo ""
    success "📊 Log monitoring started! (Press Ctrl+C to stop)"
    echo ""
    echo -e "${API_COLOR}[API]${NC} = API Service logs"
    echo -e "${FRONTEND_COLOR}[Frontend]${NC} = Frontend Service logs"
    echo ""

    # ログストリーム開始
    if [ "$frontend_only" != true ]; then
        stream_logs "$API_APP_SERVICE" "API" "$API_COLOR"
    fi

    if [ "$api_only" != true ]; then
        stream_logs "$FRONTEND_APP_SERVICE" "Frontend" "$FRONTEND_COLOR"
    fi

    # 無限ループで待機 (Ctrl+Cで終了)
    while true; do
        sleep 1
    done
}

# スクリプトが直接実行された場合のみメイン処理を実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
