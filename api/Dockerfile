# Python 3.11 の公式イメージを使用
# linux/amd64プラットフォームを明示的に指定（Azure App Service用）
FROM --platform=linux/amd64 python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージの更新と必要なパッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Pythonの依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# アプリケーションファイルをコピー
COPY --chown=appuser:appuser ./config.toml /app/
COPY --chown=appuser:appuser ./src /app/src/

# ローカルストレージディレクトリを作成
RUN mkdir -p /app/local_storage && \
    chown -R appuser:appuser /app/local_storage

# 環境変数の設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 非rootユーザーに切り替え
USER appuser

# ポート8080を公開（Azure App Serviceで使用）
EXPOSE 8080

# ヘルスチェックの設定
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# プロダクション用の起動コマンド（gunicornを使用）
CMD ["gunicorn", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
