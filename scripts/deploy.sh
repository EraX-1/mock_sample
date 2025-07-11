#!/bin/bash

# Yuyama RAG Chatbot - シンプルデプロイスクリプト
# DockerイメージをビルドしてACRにプッシュ → App Service再起動

set -e

# 設定
ACR_NAME="yuyamaregistry"
RESOURCE_GROUP="yuyama"
API_APP_SERVICE="yuyama-rag-chatbot-api"
FRONTEND_APP_SERVICE="yuyama-rag-chatbot-frontend"
API_URL="yuyama-rag-chatbot-api-cmchguh0e8bjdqd6.japaneast-01.azurewebsites.net"
FRONTEND_URL="yuyama-rag-chatbot-frontend-fgf7byd6b9f4fqck.japaneast-01.azurewebsites.net"

# ユニークなタグ生成 (タイムスタンプ + Git commit hash)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
GIT_COMMIT=$(git rev-parse --short HEAD)
UNIQUE_TAG="${TIMESTAMP}-${GIT_COMMIT}"

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 並列実行対応の関数
build_and_push() {
    local service=$1
    local dir=$2
    local image_name="yuyama-rag-chatbot-$service"

    log "Building $service image with tag: $UNIQUE_TAG..."
    cd $dir

    # 並列実行可能なようにバックグラウンドで実行
    {
        docker build --platform linux/amd64 -t $image_name:$UNIQUE_TAG .
        docker tag $image_name:$UNIQUE_TAG $ACR_NAME.azurecr.io/$image_name:$UNIQUE_TAG
        docker push $ACR_NAME.azurecr.io/$image_name:$UNIQUE_TAG
        success "$service image pushed successfully with tag: $UNIQUE_TAG"
    } &

    cd - > /dev/null
}

update_app_service_image() {
    local app_name=$1
    local service=$2
    local image_name="yuyama-rag-chatbot-$service"
    local full_image_url="$ACR_NAME.azurecr.io/$image_name:$UNIQUE_TAG"

    log "Updating $app_name to use image: $full_image_url"

    # App Serviceのコンテナ設定を更新
    az webapp config container set \
        --resource-group $RESOURCE_GROUP \
        --name $app_name \
        --container-image-name $full_image_url

    # 再起動
    log "Restarting $app_name..."
    az webapp restart --resource-group $RESOURCE_GROUP --name $app_name
}

main() {
    log "🚀 Starting Yuyama deployment with unique tag: $UNIQUE_TAG"

    # ACRログイン
    log "Logging into Azure Container Registry..."
    az acr login --name $ACR_NAME

    # 並列ビルド・プッシュ
    log "Building and pushing images in parallel..."
    build_and_push "api" "api"

    # フロントエンド用の環境変数を設定してビルド
    log "Building frontend with Azure development API URL..."
    cd web
    docker build --platform linux/amd64 \
        --build-arg NEXT_PUBLIC_API_URL=https://$API_URL \
        --build-arg NEXT_PUBLIC_APP_ENV=development \
        -t yuyama-rag-chatbot-frontend:$UNIQUE_TAG .
    docker tag yuyama-rag-chatbot-frontend:$UNIQUE_TAG $ACR_NAME.azurecr.io/yuyama-rag-chatbot-frontend:$UNIQUE_TAG
    docker push $ACR_NAME.azurecr.io/yuyama-rag-chatbot-frontend:$UNIQUE_TAG &
    cd - > /dev/null

    # ビルド完了を待機
    wait
    success "All images built and pushed with tag: $UNIQUE_TAG!"

    # App Service設定を新しいイメージに更新
    log "Updating App Services to use new images..."
    update_app_service_image $API_APP_SERVICE "api" &
    update_app_service_image $FRONTEND_APP_SERVICE "frontend" &

    # 更新完了を待機
    wait
    success "All App Services updated and restarted!"

    success "🎉 Deployment completed with tag: $UNIQUE_TAG!"
    echo ""
    echo "URLs:"
    echo "  Frontend: https://$FRONTEND_URL"
    echo "  API: https://$API_URL"
    echo ""
    echo "Deployed images:"
    echo "  API: $ACR_NAME.azurecr.io/yuyama-rag-chatbot-api:$UNIQUE_TAG"
    echo "  Frontend: $ACR_NAME.azurecr.io/yuyama-rag-chatbot-frontend:$UNIQUE_TAG"
}

main "$@"
