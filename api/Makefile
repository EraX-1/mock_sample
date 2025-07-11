COMPOSE_PROJECT_NAME := erax-chatbot-template
API_CONTAINER := erax-chatbot-template-api

# ローカル開発用の設定
LOCAL_COMPOSE_PROJECT_NAME := yuyama-local
LOCAL_API_CONTAINER := yuyama-api-local

DOCKER_COMPOSE_VERSION_CHECKER := $(shell docker compose > /dev/null 2>&1 ; echo $$?)
ifeq ($(DOCKER_COMPOSE_VERSION_CHECKER), 0)
	DOCKER_COMPOSE=docker compose
else
	DOCKER_COMPOSE=docker-compose
endif

# デフォルトターゲット（本番環境）
.PHONY: init
init: up-d run

# ローカル開発環境用のターゲット
.PHONY: init-local
init-local: up-d-local run-local

.PHONY: build
build:
	$(DOCKER_COMPOSE) -p $(COMPOSE_PROJECT_NAME) build --no-cache

.PHONY: up-d
up-d:
	$(DOCKER_COMPOSE) -p $(COMPOSE_PROJECT_NAME) up -d

.PHONY: down
down:
	$(DOCKER_COMPOSE) -p $(COMPOSE_PROJECT_NAME) down

.PHONY: exec
exec:
	docker exec -it $(API_CONTAINER) bash

.PHONY: run
run:
	docker exec -it $(API_CONTAINER) bash -c "uvicorn src.main:app --reload --host 0.0.0.0 --port 8080"

.PHONY: reload-config
reload-config:
	docker cp config.toml $(API_CONTAINER):/app/config.toml

.PHONY: install-requirements
install-requirements:
	docker cp requirements.txt $(API_CONTAINER):/app/requirements.txt
	docker exec -it $(API_CONTAINER) bash -c "pip install -r requirements.txt"

.PHONY: install-requirements-local
install-requirements-local:
	pip3 install -r requirements.txt --break-system-packages

.PHONY: logs
logs:
	docker logs -f $(API_CONTAINER)

.PHONY: logs-tail
logs-tail:
	docker logs -f --tail 100 $(API_CONTAINER)

# =================== ローカル開発環境用コマンド ===================

.PHONY: build-local
build-local:
	$(DOCKER_COMPOSE) -f docker-compose.local.yml -p $(LOCAL_COMPOSE_PROJECT_NAME) build --no-cache

.PHONY: up-d-local
up-d-local:
	$(DOCKER_COMPOSE) -f docker-compose.local.yml -p $(LOCAL_COMPOSE_PROJECT_NAME) up -d

.PHONY: down-local
down-local:
	$(DOCKER_COMPOSE) -f docker-compose.local.yml -p $(LOCAL_COMPOSE_PROJECT_NAME) down

.PHONY: exec-local
exec-local:
	docker exec -it $(LOCAL_API_CONTAINER) bash

.PHONY: run-local
run-local:
	docker exec -it $(LOCAL_API_CONTAINER) bash -c "uvicorn src.main:app --reload --host 0.0.0.0 --port 8080"

.PHONY: logs-local
logs-local:
	docker logs -f $(LOCAL_API_CONTAINER)

.PHONY: logs-tail-local
logs-tail-local:
	docker logs -f --tail 100 $(LOCAL_API_CONTAINER)

# ローカル開発用：ホストで直接実行
.PHONY: dev
dev:
	cp config.local.toml config.toml
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# ローカル開発用：データベースのみ起動
.PHONY: db-only-local
db-only-local:
	$(DOCKER_COMPOSE) -f docker-compose.local.yml -p $(LOCAL_COMPOSE_PROJECT_NAME) up -d db

# 設定とディレクトリの初期化
.PHONY: setup-local
setup-local:
	@echo "ローカル開発環境をセットアップしています..."
	cp config.local.toml config.toml
	mkdir -p local_storage/blobs/mock-container
	mkdir -p local_storage/search
	@echo "✅ ローカル開発環境のセットアップが完了しました！"
	@echo ""
	@echo "🚀 次のコマンドでアプリケーションを起動できます："
	@echo "   make dev           # ホストで直接実行"
	@echo "   make init-local    # Dockerで実行"
