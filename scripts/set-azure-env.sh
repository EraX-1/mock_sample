#!/bin/bash

# Azure App Service環境変数設定スクリプト

# APIアプリケーションの名前
API_APP_NAME="yuyama-rag-chatbot-api"
RESOURCE_GROUP="yuyama"

echo "Setting environment variables for Azure App Service: $API_APP_NAME"

# モックモードを有効にする
az webapp config appsettings set \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    USE_MOCK_SERVICES=true \
    FRONTEND_URL="https://yuyama-rag-chatbot-frontend-fgf7byd6b9f4fqck.japaneast-01.azurewebsites.net" \
    AZURE_CLIENT_ID="mock-client-id" \
    AZURE_CLIENT_SECRET="mock-client-secret" \
    AZURE_TENANT_ID="mock-tenant-id" \
    REDIRECT_URI="https://yuyama-rag-chatbot-frontend-fgf7byd6b9f4fqck.japaneast-01.azurewebsites.net/auth/callback" \
    AOAI_ENDPOINT="http://localhost:8080/mock/openai" \
    AOAI_API_KEY="mock-openai-key" \
    AOAI_API_VERSION="2024-02-01" \
    AOAI_CHAT_MODEL="gpt-4o" \
    AOAI_EMBED_MODEL="text-embedding-3-small" \
    AOAI_VISION_MODEL="gpt-4o" \
    AOAI_DALLE_MODEL="dall-e-3" \
    SEARCH_API_KEY="mock-search-key" \
    SEARCH_SERVICE_NAME="mock-search" \
    SEARCH_INDEX_NAME="yuyama-index" \
    STORAGE_KEY="mock-storage-key" \
    STORAGE_ACCOUNT_NAME="mockstorageaccount" \
    STORAGE_CONTAINER_NAME="documents" \
    DOCINTEL_KEY="mock-docintel-key" \
    DOCINTEL_ENDPOINT="https://mock-docintel.cognitiveservices.azure.com/"

echo "Environment variables set successfully!"

# APIアプリケーションを再起動
echo "Restarting API application..."
az webapp restart --name $API_APP_NAME --resource-group $RESOURCE_GROUP

echo "API application restarted!"
