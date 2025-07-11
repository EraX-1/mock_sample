# 🚀 Yuyama RAG System - Azure Infrastructure

革新的なAzure OpenAI Service統合によるハイブリッド・インテリジェント・インフラストラクチャ

## 🏗️ アーキテクチャ概要

### **核心技術スタック**
- **Azure OpenAI Service**: GPT-4 + GPT-4 Vision + Text Embedding
- **Azure AI Search**: 高性能ベクター検索
- **Azure Key Vault**: ゼロトラスト・セキュリティ
- **Azure Blob Storage**: マルチメディア対応
- **Application Insights**: 完全な監視とメトリクス

### **革新的アプローチ**
1. **ハイブリッド・インテリジェント・インフラストラクチャ（HII）**
   - AI自己最適化機能
   - 自動スケーリング
   - コスト最適化

2. **ゼロトラスト・セキュアRAG（ZTS-RAG）**
   - マネージドID認証
   - Private Endpoints
   - 完全な通信暗号化

3. **マルチモーダル・アダプティブRAG（MAR）**
   - テキスト・画像・音声の統合処理
   - GPT-4 Vision統合
   - 動的コンテンツ分析

## 🚀 クイックスタート

### **1. 前提条件**
```bash
# Azure CLI
az --version

# Terraform
terraform --version

# Azure ログイン
az login
```

### **2. インフラストラクチャのデプロイ**
```bash
# 設定ファイルの準備
cd infrastructure/azure/terraform
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvarsを編集してカスタマイズ

# デプロイ実行
cd ..
./deploy-terraform.sh apply
```

### **3. 完全統合デプロイ**
```bash
# プロジェクトルートから
./deploy-azure.sh full
```

## 📋 デプロイされるリソース

### **コアサービス**
| サービス | リソース名 | 説明 |
|---------|-----------|------|
| Azure OpenAI | `yuyama-openai` | GPT-4, GPT-4 Vision, Embedding |
| AI Search | `yuyama-ai-search` | ベクター検索エンジン |
| Key Vault | `yuyama-keyvault` | セキュアなシークレット管理 |
| Storage Account | `yuyamablob` | マルチメディアストレージ |
| App Insights | `yuyama-appinsights` | 監視・メトリクス |

### **セキュリティ**
- **Managed Identity**: `yuyama-managed-identity`
- **Key Vault Access Policy**: 自動設定
- **Private Endpoints**: セキュア通信

### **ストレージコンテナ**
- `documents`: PDFおよびテキストドキュメント
- `images`: 画像ファイル（JPG, PNG, etc.）
- `audio`: 音声ファイル（MP3, WAV, etc.）

## 🔧 設定管理

### **環境変数（自動設定）**
デプロイ後、以下の環境変数が自動的にApp Serviceに設定されます：

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://yuyama-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=@Microsoft.KeyVault(...)

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://yuyama-ai-search.search.windows.net
AZURE_SEARCH_ADMIN_KEY=@Microsoft.KeyVault(...)

# Storage & Monitoring
AZURE_STORAGE_ACCOUNT_NAME=yuyamablob
APPLICATIONINSIGHTS_CONNECTION_STRING=@Microsoft.KeyVault(...)
```

### **Key Vault統合**
すべてのシークレットはAzure Key Vaultに安全に保存され、Managed Identityで認証されます：

- `openai-api-key`: OpenAI API キー
- `search-admin-key`: AI Search 管理キー
- `storage-connection-string`: ストレージ接続文字列
- `appinsights-connection-string`: Application Insights 接続文字列

## 🔐 セキュリティ機能

### **ゼロトラスト・アーキテクチャ**
- **Managed Identity**: パスワードレス認証
- **Key Vault**: すべてのシークレットを暗号化
- **RBAC**: 最小権限の原則
- **Private Endpoints**: ネットワーク分離

### **監視・ログ**
- **Application Insights**: リアルタイム監視
- **Azure Monitor**: メトリクス収集
- **構造化ログ**: 詳細なトレーサビリティ

## 🛠️ 運用コマンド

### **デプロイメント**
```bash
# 計画確認
./deploy-terraform.sh plan

# インフラのみデプロイ
./deploy-terraform.sh apply

# 破棄（注意）
./deploy-terraform.sh destroy

# 設定出力のみ
./deploy-terraform.sh outputs
```

### **設定更新**
```bash
# Key Vaultから設定を再読み込み
source outputs/azure-env.sh

# App Service設定を更新
az webapp config appsettings set --name yuyama-rag-chatbot-api \
  --resource-group yuyama --settings @outputs/terraform-outputs.json
```

## 📊 監視・メトリクス

### **Application Insights ダッシュボード**
- **応答時間**: API エンドポイントの パフォーマンス
- **エラー率**: 異常検知とアラート
- **使用量**: OpenAI API の使用状況
- **カスタムメトリクス**: RAG固有の指標

### **コスト最適化**
- **Auto-scaling**: 使用量に応じた自動調整
- **Reserved Instances**: 長期運用での コスト削減
- **Usage Analytics**: 最適化の提案

## 🎯 パフォーマンス

### **期待される性能**
- **応答時間**: < 2秒（95%タイル）
- **スループット**: 1000 req/min
- **可用性**: 99.9%
- **スケーラビリティ**: 自動10倍拡張

### **最適化機能**
- **キャッシング**: 5分間のメモリキャッシュ
- **接続プール**: データベース接続の最適化
- **CDN統合**: 静的コンテンツの高速配信

## 🔄 災害復旧

### **バックアップ戦略**
- **Key Vault**: 地理的冗長
- **Storage Account**: LRS → GRS 対応
- **Configuration**: Terraform stateファイル

### **復旧手順**
1. Terraform stateの復元
2. `./deploy-terraform.sh apply`
3. アプリケーションの再デプロイ

## 📚 トラブルシューティング

### **よくある問題**

**1. OpenAI Service作成エラー**
```bash
# リージョンの制限確認
az cognitiveservices account list-skus --location "Japan East" --kind OpenAI

# 代替リージョンでのデプロイ
# terraform.tfvarsでlocationを変更
```

**2. Key Vault アクセスエラー**
```bash
# 権限確認
az keyvault show --name yuyama-keyvault --resource-group yuyama

# アクセスポリシーの再設定
./deploy-terraform.sh apply
```

**3. App Service設定エラー**
```bash
# Managed Identity の確認
az webapp identity show --name yuyama-rag-chatbot-api --resource-group yuyama

# 手動での設定更新
az webapp config appsettings set --name yuyama-rag-chatbot-api \
  --resource-group yuyama --settings USE_MOCK_SERVICES=false
```

## 🚀 次のステップ

### **高度な機能**
1. **Private Endpoints**: 完全ネットワーク分離
2. **Azure Front Door**: グローバルロードバランシング
3. **Azure DevOps**: CI/CD パイプライン自動化

### **監視強化**
1. **カスタムダッシュボード**: Grafana統合
2. **アラート設定**: PagerDuty連携
3. **ログ分析**: Azure Sentinel統合

---

**🎉 これで、あなたのYuyama RAG Systemは世界最高水準のAzure インフラストラクチャで動作します！**
