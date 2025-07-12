COMPOSE_PROJECT_NAME := yuyama
COMPOSE_FILE := docker-compose.yml

DOCKER_COMPOSE_VERSION_CHECKER := $(shell docker compose > /dev/null 2>&1 ; echo $$?)
ifeq ($(DOCKER_COMPOSE_VERSION_CHECKER), 0)
	DOCKER_COMPOSE=docker compose
else
	DOCKER_COMPOSE=docker-compose
endif

# ===================== Main Commands =====================

.PHONY: help
help: ## Display help
	@echo "Yuyama - Local Development Environment Management"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick start:"
	@echo "  make setup && make up"
	@echo ""

.PHONY: setup
setup: ## Initial setup (create config files, prepare directories)
	@echo "Starting initial setup..."
	@mkdir -p scripts
	@mkdir -p api/local_storage/blobs/mock-container
	@mkdir -p api/local_storage/search
	@if [ ! -f api/config.toml ]; then \
		echo "Creating API configuration file..."; \
		cp api/config.local.toml api/config.toml; \
	fi
	@echo "Setup completed."
	@echo ""
	@echo "To start services, run:"
	@echo "  make up    # Start all services"

.PHONY: up
up: ## Start all services (DB + API + Web)
	@echo "Starting all services..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) up -d --build
	@echo ""
	@echo "All services started successfully."
	@echo ""
	@echo "Service URLs:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API:      http://localhost:8080"
	@echo "  API Docs: http://localhost:8080/docs"
	@echo ""
	@echo "To view logs:"
	@echo "  make logs"

.PHONY: down
down: ## Stop all services
	@echo "Stopping all services..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) down
	@echo "All services stopped."

.PHONY: restart
restart: down up ## Restart all services

.PHONY: restart-app
restart-app: ## Restart API and Web services with rebuild (keep MySQL running)
	@echo "Stopping API and Web services..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) stop api web
	@echo "Rebuilding and starting API and Web services..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) up -d --build api web
	@echo "API and Web services rebuilt and restarted."

.PHONY: build
build: ## Build all services (no cache)
	@echo "Building all services..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) build --no-cache

.PHONY: rebuild
rebuild: down build up ## Rebuild and start all services

# ===================== Development Commands =====================

.PHONY: up-backend
up-backend: ## Start only DB and API services (for frontend hot reload development)
	@echo "Starting DB and API services only..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) up -d --build db api
	@echo ""
	@echo "Backend services started successfully."
	@echo ""
	@echo "Service URLs:"
	@echo "  API:      http://localhost:8080"
	@echo "  API Docs: http://localhost:8080/docs"
	@echo "  MySQL:    localhost:3306"
	@echo ""
	@echo "To start frontend with hot reload:"
	@echo "  cd web && npm run dev"

.PHONY: dev
dev: ## Start in development mode (with file watching)
	@echo "Starting in development mode..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) up --build

.PHONY: logs
logs: ## Display logs for all services
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) logs
.PHONY: logs-api
logs-api: ## Display logs for API service
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) logs -f api

.PHONY: logs-web
logs-web: ## Display logs for Web service
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) logs -f web

.PHONY: logs-db
logs-db: ## Display logs for DB service
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) logs -f db

# ===================== Individual Service Management =====================

.PHONY: up-db
up-db: ## Start database only
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) up -d db

.PHONY: up-api
up-api: ## Start API server only
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) up -d api

.PHONY: up-web
up-web: ## Start Web server only
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) up -d web

# ===================== Container Operations =====================

.PHONY: exec-api
exec-api: ## Shell access to API container
	docker exec -it yuyama-api bash

.PHONY: exec-web
exec-web: ## Shell access to Web container
	docker exec -it yuyama-web bash

.PHONY: exec-db
exec-db: ## MySQL access to DB container
	docker exec -it yuyama-mysql mysql -u root -ppassword yuyama

# ===================== Testing & Debugging =====================

.PHONY: test-mock
test-mock: ## Test mock service functionality
	@echo "Running mock service tests..."
	docker exec -it yuyama-api python test_mock_services.py

.PHONY: health
health: ## Health check for all services
	@echo "Checking service status..."
	@echo ""
	@echo "Docker container status:"
	@docker ps --filter "name=yuyama-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "API health check:"
	@curl -s http://localhost:8080/ | head -1 || echo "API not responding"
	@echo ""
	@echo "Web health check:"
	@curl -s -o /dev/null -w "%%{http_code}" http://localhost:3000 | grep -q "200" && echo "Web service healthy" || echo "Web service not responding"

.PHONY: test-azure-openai
test-azure-openai: ## Test Azure OpenAI integration
	@echo "Testing Azure OpenAI integration..."
	@echo ""
	@echo "Azure OpenAI Health Check:"
	@curl -s http://localhost:8080/health/azure-openai/status | python3 -m json.tool || echo "Health check failed"
	@echo ""
	@echo "Azure OpenAI Connectivity Test:"
	@curl -s -X POST http://localhost:8080/health/azure-openai/test/connectivity | python3 -m json.tool || echo "Connectivity test failed"
	@echo ""
	@echo "Azure OpenAI Chat Test:"
	@curl -s -X POST http://localhost:8080/test/azure-openai/chat \
		-H "Content-Type: application/json" \
		-d '{"message":"Hello, this is a test from Makefile!"}' | python3 -m json.tool || echo "Chat test failed"

.PHONY: test-azure-openai-embedding
test-azure-openai-embedding: ## Test Azure OpenAI embedding functionality
	@echo "Testing Azure OpenAI embedding functionality..."
	@curl -s -X POST http://localhost:8080/health/azure-openai/test/embedding | python3 -m json.tool || echo "Embedding test failed"

.PHONY: test-azure-openai-full
test-azure-openai-full: test-azure-openai test-azure-openai-embedding ## Run full Azure OpenAI test suite

.PHONY: reset
reset: ## Reset all data (including volumes)
	@echo "WARNING: This will reset all data..."
	@read -p "Are you sure you want to continue? (y/N): " confirm && [ "$$confirm" = "y" ]
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) down -v
	docker volume rm yuyama_mysql_data 2>/dev/null || true
	@echo "Reset completed."

# ===================== Utility Commands =====================

.PHONY: quick-start
quick-start: setup up health ## Quick start (setup -> start -> health check)

.PHONY: quick-test
quick-test: health test-azure-openai ## Quick test (health check + Azure OpenAI test)

.PHONY: status
status: ## Display current status
	@echo "Yuyama Development Environment Status:"
	@echo ""
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) ps

.PHONY: clean
clean: ## Remove stopped containers and images
	@echo "Cleaning up unused resources..."
	docker system prune -f
	@echo "Cleanup completed."

# ===================== Production Environment =====================

.PHONY: setup-prod
setup-prod: ## Setup for production environment
	@echo "Setting up for production environment..."
	@echo "WARNING: Please configure config.toml appropriately for production"
	@echo "WARNING: Set USE_MOCK_SERVICES=false and provide Azure credentials"

# Default target
.DEFAULT_GOAL := help
