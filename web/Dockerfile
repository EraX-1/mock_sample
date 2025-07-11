# マルチステージビルド: ビルドステージ
# linux/amd64プラットフォームを明示的に指定（Azure App Service用）
FROM --platform=linux/amd64 node:20-alpine AS builder

# 作業ディレクトリを設定
WORKDIR /app

# package.jsonとpackage-lock.jsonを先にコピー（キャッシュ効率化）
COPY package*.json ./

# 全ての依存関係をインストール（ビルド用）
RUN npm ci && npm cache clean --force

# アプリケーションのソースコードをコピー
COPY . .

# ビルド時に環境変数を設定（docker-compose.ymlやビルド時に注入される）
ARG NEXT_PUBLIC_API_URL=http://localhost:8080
ARG NEXT_PUBLIC_APP_ENV=development

# 環境変数をエクスポート
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_APP_ENV=${NEXT_PUBLIC_APP_ENV}

# Next.jsのビルドを実行
RUN npm run build

# 依存関係のクリーンアップステージ
FROM --platform=linux/amd64 node:20-alpine AS deps

WORKDIR /app
COPY package*.json ./

# 本番用依存関係のみインストール
RUN npm ci --only=production && npm cache clean --force

# プロダクションステージ
FROM --platform=linux/amd64 node:20-alpine AS production

# セキュリティ: 非rootユーザーを作成
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# 作業ディレクトリを設定
WORKDIR /app

# Next.js設定
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# 必要なファイルのみをコピー
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 本番用依存関係のみコピー
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json

# 非rootユーザーに切り替え
USER nextjs

# ポート3000を公開（Azure App Serviceのデフォルト）
EXPOSE 3000

# ヘルスチェックの設定
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1); })" || exit 1

# Next.jsアプリケーションを起動（standalone モード）
CMD ["node", "server.js"]
