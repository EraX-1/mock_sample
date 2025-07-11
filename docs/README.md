# 📚 Yuyama RAG Chatbot ドキュメント

このディレクトリには、Yuyama RAG Chatbotの各種ドキュメントが整理されています。

## 📖 ドキュメント一覧

### 🚀 クイックスタート
- **[ローカル開発](quickstart/LOCAL.md)** - ローカル環境での3分セットアップ
- **[Azure デプロイ](quickstart/AZURE.md)** - Azure環境への5分デプロイ

### ☁️ デプロイメント
- **[Azure App Service](deployment/AZURE_APP_SERVICE.md)** - FE/BE のコンテナデプロイ
- **[Azure MySQL](deployment/AZURE_MYSQL.md)** - データベースの詳細セットアップ
- **[完全デプロイ](deployment/FULL_DEPLOYMENT.md)** - 統合デプロイガイド

### 🛠️ 開発・運用
- **[API リファレンス](../api/README.md)** - バックエンドAPI詳細
- **[フロントエンド](../web/README.md)** - UI/UX コンポーネント

## 🏗️ アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (MySQL)       │
│   Port: 3000    │    │   Port: 8080    │    │   Port: 3306    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Azure Cloud   │
                    │   Services      │
                    │   (OpenAI, etc) │
                    └─────────────────┘
```

## 🎯 利用シーン別ガイド

### 👨‍💻 **開発者向け**
1. [ローカル開発環境セットアップ](quickstart/LOCAL.md)
2. [API開発ガイド](../api/README.md)
3. [フロントエンド開発](../web/README.md)

### 🚀 **DevOps / インフラ担当者向け**
1. [Azure完全デプロイ](quickstart/AZURE.md)
2. [本番環境構築](deployment/FULL_DEPLOYMENT.md)
3. [監視・メンテナンス](deployment/AZURE_MYSQL.md#監視とメンテナンス)

### 👥 **プロジェクトマネージャー向け**
1. [プロジェクト概要](../README.md)
2. [デプロイ計画](deployment/FULL_DEPLOYMENT.md)
3. [コスト見積もり](quickstart/AZURE.md#コスト最適化)

## 🔧 主要コマンド

```bash
# ローカル開発
make setup && make up        # 初回セットアップ・起動
make dev                     # 開発モード起動
make health                  # ヘルスチェック

# Azure デプロイ
./deploy-azure.sh full       # 完全デプロイ
./scripts/azure-mysql-setup.sh   # MySQL のみ
./scripts/azure-app-service-config.sh  # App Service 設定
```

## 📞 サポート

- **技術的な問題**: [トラブルシューティング](TROUBLESHOOTING.md)
- **API 仕様**: [Swagger UI](http://localhost:8080/docs) (ローカル)
- **プロジェクト課題**: GitHub Issues

---

**🎉 準備完了** 適切なガイドを選択して開発・デプロイを開始してください！
