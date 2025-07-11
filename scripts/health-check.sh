#!/bin/bash

# =============================================================================
# Yuyama Application Health Check Script
#
# 使用方法:
#   ./scripts/health-check.sh [オプション]
#
# オプション:
#   --verbose, -v    詳細出力
#   --json, -j       JSON形式で出力
#   --quiet, -q      エラーのみ出力
#   --help, -h       ヘルプ表示
# =============================================================================

set -e

# カラー出力の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# オプション解析
VERBOSE=false
JSON_OUTPUT=false
QUIET=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -j|--json)
            JSON_OUTPUT=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -h|--help)
            echo "Yuyama Application Health Check Script"
            echo ""
            echo "使用方法: $0 [オプション]"
            echo ""
            echo "オプション:"
            echo "  -v, --verbose    詳細出力"
            echo "  -j, --json       JSON形式で出力"
            echo "  -q, --quiet      エラーのみ出力"
            echo "  -h, --help       このヘルプを表示"
            exit 0
            ;;
        *)
            echo "不明なオプション: $1"
            exit 1
            ;;
    esac
done

# ログ関数
log_info() {
    if [[ "$QUIET" != "true" ]] && [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

log_success() {
    if [[ "$QUIET" != "true" ]] && [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${GREEN}[OK]${NC} $1"
    fi
}

log_warning() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${YELLOW}[WARNING]${NC} $1"
    fi
}

log_error() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${RED}[ERROR]${NC} $1"
    fi
}

# 結果格納用変数
OVERALL_STATUS="healthy"
CHECK_RESULTS=""

# 結果を記録する関数
record_result() {
    local service="$1"
    local status="$2"
    local details="$3"

    if [[ "$status" != "healthy" ]]; then
        OVERALL_STATUS="unhealthy"
    fi

    # JSON出力でダブルクォートをエスケープ
    local escaped_details=$(echo "$details" | sed 's/"/\\"/g')
    CHECK_RESULTS="${CHECK_RESULTS}${service}:${status}:${escaped_details}|"
}

# Docker コンテナチェック
check_containers() {
    log_info "Dockerコンテナの状態をチェック中..."

    local containers=("yuyama-web" "yuyama-api" "yuyama-mysql")

    for container in "${containers[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
            local status=$(docker inspect --format="{{.State.Health.Status}}" "$container" 2>/dev/null || echo "unknown")
            local running=$(docker inspect --format="{{.State.Running}}" "$container" 2>/dev/null)

            if [[ "$running" == "true" ]]; then
                if [[ "$status" == "healthy" ]] || [[ "$status" == "unknown" ]]; then
                    record_result "$container" "healthy" "Running and healthy"
                    log_success "$container: 稼働中 (${status})"
                else
                    record_result "$container" "unhealthy" "Running but unhealthy: $status"
                    log_error "$container: 異常 ($status)"
                fi
            else
                record_result "$container" "stopped" "Container is not running"
                log_error "$container: 停止中"
            fi
        else
            record_result "$container" "missing" "Container not found"
            log_error "$container: コンテナが見つかりません"
        fi
    done
}

# Webサービスチェック
check_web_service() {
    log_info "Webサービスをチェック中..."

    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health 2>/dev/null || echo "000")

    if [[ "$response" == "200" ]]; then
        local health_data=$(curl -s http://localhost:3000/api/health 2>/dev/null || echo "{}")
        record_result "web_service" "healthy" "HTTP 200, $health_data"
        log_success "Webサービス: 正常応答 (HTTP $response)"

        if [[ "$VERBOSE" == "true" ]] && [[ "$JSON_OUTPUT" != "true" ]]; then
            echo "  詳細: $health_data"
        fi
    else
        record_result "web_service" "unhealthy" "HTTP $response"
        log_error "Webサービス: 異常 (HTTP $response)"
    fi
}

# APIサービスチェック
check_api_service() {
    log_info "APIサービスをチェック中..."

    # ヘルスチェックエンドポイント
    local health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null || echo "000")

    if [[ "$health_response" == "200" ]]; then
        local health_data=$(curl -s http://localhost:8080/health 2>/dev/null || echo "{}")
        record_result "api_health" "healthy" "HTTP 200, $health_data"
        log_success "API Health: 正常応答 (HTTP $health_response)"

        if [[ "$VERBOSE" == "true" ]] && [[ "$JSON_OUTPUT" != "true" ]]; then
            echo "  詳細: $health_data"
        fi
    else
        record_result "api_health" "unhealthy" "HTTP $health_response"
        log_error "API Health: 異常 (HTTP $health_response)"
    fi

    # ルートエンドポイント
    local root_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")

    if [[ "$root_response" == "200" ]]; then
        local root_data=$(curl -s http://localhost:8080/ 2>/dev/null || echo "{}")
        record_result "api_root" "healthy" "HTTP 200, $root_data"
        log_success "API Root: 正常応答 (HTTP $root_response)"

        if [[ "$VERBOSE" == "true" ]]; then
            echo "  詳細: $root_data"
        fi
    else
        record_result "api_root" "unhealthy" "HTTP $root_response"
        log_error "API Root: 異常 (HTTP $root_response)"
    fi
}

# データベースチェック
check_database() {
    log_info "データベースをチェック中..."

    if docker exec yuyama-mysql mysql -u root -p'password' -e "SELECT 'MySQL is working' as status;" >/dev/null 2>&1; then
        # テーブル一覧取得
        local tables=$(docker exec yuyama-mysql mysql -u root -p'password' -D yuyama -e "SHOW TABLES;" 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')

        record_result "database" "healthy" "Connected, $tables tables found"
        log_success "データベース: 接続成功 (${tables}テーブル確認)"

        if [[ "$VERBOSE" == "true" ]] && [[ "$JSON_OUTPUT" != "true" ]]; then
            echo "  テーブル一覧:"
            docker exec yuyama-mysql mysql -u root -p'password' -D yuyama -e "SHOW TABLES;" 2>/dev/null | tail -n +2 | sed 's/^/    /'
        fi
    else
        record_result "database" "unhealthy" "Connection failed"
        log_error "データベース: 接続失敗"
    fi
}

# リソース使用量チェック
check_resources() {
    log_info "リソース使用量をチェック中..."

    if command -v docker &> /dev/null; then
        local stats=$(docker stats --no-stream | grep yuyama | awk '{print $2 "\t" $3 "\t" $4}')

        record_result "resources" "healthy" "Docker stats collected"
        log_success "リソース使用量: 取得成功"

        if [[ "$JSON_OUTPUT" != "true" ]] && ([[ "$VERBOSE" == "true" ]] || [[ "$QUIET" != "true" ]]); then
            echo ""
            echo "  リソース使用量:"
            echo "  コンテナ名\t\t\tCPU使用率\tメモリ使用量"
            echo "  ----------------------------------------"
            if [[ -n "$stats" ]]; then
                echo "$stats" | while IFS=$'\t' read -r container cpu mem; do
                    printf "  %-20s\t%-10s\t%s\n" "$container" "$cpu" "$mem"
                done
            else
                echo "  データ取得中..."
            fi
            echo ""
        fi
    else
        record_result "resources" "unknown" "Docker not available"
        log_warning "リソース使用量: Docker利用不可"
    fi
}

# JSON出力
output_json() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")

    echo "{"
    echo "  \"timestamp\": \"$timestamp\","
    echo "  \"overall_status\": \"$OVERALL_STATUS\","
    echo "  \"services\": {"

    local first=true
    IFS='|' read -ra RESULTS <<< "$CHECK_RESULTS"
    for result in "${RESULTS[@]}"; do
        if [[ -n "$result" ]]; then
            IFS=':' read -ra PARTS <<< "$result"
            local service="${PARTS[0]}"
            local status="${PARTS[1]}"
            local details="${PARTS[2]}"

            if [[ "$first" != "true" ]]; then
                echo ","
            fi
            echo -n "    \"$service\": {"
            echo -n "\"status\": \"$status\", \"details\": \"$details\""
            echo -n "}"
            first=false
        fi
    done

    echo ""
    echo "  }"
    echo "}"
}

# メイン実行部分
main() {
    if [[ "$JSON_OUTPUT" != "true" ]] && [[ "$QUIET" != "true" ]]; then
        echo "=============================================="
        echo "  Yuyama Application Health Check"
        echo "  $(date)"
        echo "=============================================="
        echo ""
    fi

    check_containers
    check_web_service
    check_api_service
    check_database
    check_resources

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        output_json
    else
        if [[ "$QUIET" != "true" ]]; then
            echo ""
            echo "=============================================="
        fi
        if [[ "$OVERALL_STATUS" == "healthy" ]]; then
            log_success "総合ステータス: すべてのサービスが正常に動作しています"
            exit 0
        else
            log_error "総合ステータス: 一部のサービスに問題があります"
            exit 1
        fi
    fi
}

# スクリプト実行
main "$@"
