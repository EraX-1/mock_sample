# このリポジトリ

2025/07/11_mock環境
* web検索ボタン
* GPTsUI


# Yuyama RAG Chatbot

エンタープライズ向けRAG（Retrieval-Augmented Generation）チャットボットシステム

## 概要

本システムは、社内文書を活用したAI質問応答機能を提供する企業向けソリューションです。Azure OpenAI ServiceとAzure AI Searchを基盤として、高精度な情報検索と自然言語での対話を実現します。

## システム要件

- Docker Desktop 20.10以上
- Docker Compose v2.0以上
- Git
- Azure サブスクリプション（本番環境用）

## クイックスタート

### ローカル環境

```bash
# リポジトリのクローン
git clone <repository-url>
cd yuyama

# セットアップと起動
make setup && make up
```

アプリケーション: http://localhost:3000

### 本番環境デプロイ

```bash
# Azure環境へのデプロイ
./deploy-azure.sh full
```

詳細は[デプロイメントガイド](docs/deployment/FULL_DEPLOYMENT.md)を参照してください。

## アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (MySQL)       │
│   Port: 3000    │    │   Port: 8080    │    │   Port: 3306    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │
                    ┌────────────────────────┐
                    │   Azure Services       │
                    │ • OpenAI Service       │
                    │ • AI Search            │
                    │ • Blob Storage         │
                    │ • Active Directory     │
                    └────────────────────────┘
```

## 主要機能

- **文書管理**: PDF、Office文書、画像ファイルのアップロードと自動インデックス化
- **AI検索**: セマンティック検索による高精度な関連文書の取得
- **チャット機能**: GPTモデルを活用した自然言語での質問応答
- **認証・認可**: Azure Active Directory統合によるセキュアなアクセス制御
- **管理機能**: ユーザー管理、インデックス管理、システム設定

## 技術スタック

### フロントエンド
- Next.js 15 (TypeScript)
- Tailwind CSS
- Material UI
- TanStack Query

### バックエンド
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0
- LangChain
- Azure SDK

### インフラストラクチャ
- Docker & Docker Compose
- Azure App Service
- Azure Database for MySQL
- Azure Monitor

## 開発

```bash
# 開発環境の起動
make dev

# ログの確認
make logs

# テストの実行
make test-mock

# 環境のリセット
make reset
```

## ドキュメント

- [ローカル開発ガイド](docs/quickstart/LOCAL.md)
- [Azure デプロイガイド](docs/quickstart/AZURE.md)
- [API リファレンス](api/README.md)
- [フロントエンド仕様](web/README.md)

## ライセンス

本プロジェクトは[MIT License](LICENSE)の下で公開されています。

## サポート

技術的な問題や質問については、[GitHub Issues](../../issues)をご利用ください。
