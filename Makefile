# Use bash for better scripting
SHELL := /bin/bash

# Define compose files to avoid repetition
DEV_COMPOSE_FILE := -f docker-compose.dev.yml
PROD_COMPOSE_FILE := -f docker-compose.prod.yml

# Default command to run when 'make' is called without arguments
.DEFAULT_GOAL := help

# Phony targets prevent conflicts with files of the same name
.PHONY: prune dev dev-up dev-build dev-down dev-stop dev-restart dev-logs dev-logs-backend dev-logs-frontend dev-shell-backend dev-shell-frontend dev-shell-db prod prod-up prod-build prod-down prod-stop prod-restart prod-logs prod-logs-backend prod-logs-frontend prod-shell-backend prod-shell-frontend prod-shell-db

# --- General Utility Commands ---

help:
	@echo "Usage: make [command]"
	@echo ""
	@echo "Available Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

prune: dev-down prod-down ## Clean up the system by removing all stopped containers, unused networks, and dangling images.
	@echo "Pruning Docker system..."
	@docker system prune -af

# --- Development Environment Commands ---

dev: dev-up ## Start the development environment with hot-reloading (alias for 'dev-up').

dev-up: ## Start the development environment with hot-reloading.
	@echo "Starting development containers in detached mode (with hot-reloading)..."
	@docker-compose $(DEV_COMPOSE_FILE) up --build -d

dev-build: ## Force a rebuild of all development images without starting containers.
	@echo "Building development images..."
	@docker-compose $(DEV_COMPOSE_FILE) build

dev-down: ## Stop and remove all development containers, networks, and volumes.
	@echo "Stopping all containers..."
	@docker-compose $(DEV_COMPOSE_FILE) down -v --remove-orphans

dev-stop: ## Stop running development containers without removing them.
	@echo "Stopping development containers..."
	@docker-compose $(DEV_COMPOSE_FILE) stop

dev-restart: ## Restart all development services.
	@echo "Restarting development containers..."
	@make dev-stop && make dev-up

dev-logs: ## View and follow logs for all running development services.
	@echo "Following logs for all development services..."
	@docker-compose $(DEV_COMPOSE_FILE) logs -f

dev-logs-backend: ## View and follow logs for the development backend service only.
	@echo "Following backend logs..."
	@docker-compose $(DEV_COMPOSE_FILE) logs -f backend

dev-logs-frontend: ## View and follow logs for the development frontend service only.
	@echo "Following frontend logs..."
	@docker-compose $(DEV_COMPOSE_FILE) logs -f frontend

dev-shell-backend: ## Open a bash shell inside the running development backend container.
	@echo "Opening bash shell in backend container..."
	@docker-compose $(DEV_COMPOSE_FILE) exec backend /bin/bash

dev-shell-frontend: ## Open a bash shell inside the running development frontend container.
	@echo "Opening bash shell in frontend container..."
	@docker-compose $(DEV_COMPOSE_FILE) exec frontend /bin/bash

dev-shell-db: ## Open a psql shell to interact with the development PostgreSQL database.
	@echo "Opening psql shell in db container..."
	@docker-compose $(DEV_COMPOSE_FILE) exec db psql -U $$(grep POSTGRES_USER .env.dev | cut -d '=' -f2) -d $$(grep POSTGRES_DB .env.dev | cut -d '=' -f2)


# --- Production Environment Commands ---

prod: prod-up ## Start the production environment (alias for 'prod-up').

prod-up: ## Build and start the production environment in detached mode.
	@echo "Starting production containers in detached mode..."
	@docker-compose $(PROD_COMPOSE_FILE) up --build -d

prod-build: ## Build production images without starting containers.
	@echo "Building production images..."
	@docker-compose $(PROD_COMPOSE_FILE) build

prod-down: ## Stop and remove production containers, networks, and volumes.
	@echo "Stopping production containers..."
	@docker-compose $(PROD_COMPOSE_FILE) down -v --remove-orphans

prod-stop: ## Stop running production containers without removing them.
	@echo "Stopping production containers..."
	@docker-compose $(PROD_COMPOSE_FILE) stop

prod-restart: ## Restart all production services.
	@echo "Restarting production containers..."
	@make prod-stop && make prod-up

prod-logs: ## View and follow logs for all running production services.
	@echo "Following logs for all production services..."
	@docker-compose $(PROD_COMPOSE_FILE) logs -f

prod-logs-backend: ## View and follow logs for the production backend service only.
	@echo "Following production backend logs..."
	@docker-compose $(PROD_COMPOSE_FILE) logs -f backend

prod-logs-frontend: ## View and follow logs for the production frontend service only.
	@echo "Following production frontend logs..."
	@docker-compose $(PROD_COMPOSE_FILE) logs -f frontend

prod-shell-backend: ## Open a bash shell inside the running production backend container.
	@echo "Opening bash shell in production backend container..."
	@docker-compose $(PROD_COMPOSE_FILE) exec backend /bin/bash

prod-shell-frontend: ## Open a bash shell inside the running production frontend container.
	@echo "Opening bash shell in production frontend container..."
	@docker-compose $(PROD_COMPOSE_FILE) exec frontend /bin/bash

prod-shell-db: ## Open a psql shell to interact with the production PostgreSQL database.
	@echo "Opening psql shell in production db container..."
	@docker-compose $(PROD_COMPOSE_FILE) exec db psql -U $$(grep POSTGRES_USER .env.prod | cut -d '=' -f2) -d $$(grep POSTGRES_DB .env.prod | cut -d '=' -f2)