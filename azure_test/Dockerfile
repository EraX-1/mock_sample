# ベースイメージにPython 3.9を使用
FROM mcr.microsoft.com/azure-functions/python:4-python3.12

# 作業ディレクトリを設定
WORKDIR /home/site/wwwroot

# 依存関係ファイルをコピー
COPY requirements.txt .

# 依存関係をインストール
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Azure Functionsの起動コマンドはベースイメージに含まれているため省略