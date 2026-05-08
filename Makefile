# Makefile for Docker operations
# Usage: make [target]

.PHONY: help build build-gpu up down logs clean test

# Default target
help:
	@echo "Facial Recognition Attendance System - Docker Commands"
	@echo ""
	@echo "Development (CPU - SQLite):"
	@echo "  make build          - Build CPU image"
	@echo "  make up             - Start development stack"
	@echo "  make down           - Stop development stack"
	@echo "  make logs           - View live logs"
	@echo "  make clean          - Stop and remove everything"
	@echo ""
	@echo "Production (GPU - PostgreSQL):"
	@echo "  make build-gpu      - Build GPU image"
	@echo "  make up-prod        - Start production stack"
	@echo "  make down-prod      - Stop production stack"
	@echo "  make logs-prod      - View production logs"
	@echo ""
	@echo "Other:"
	@echo "  make health         - Check container health"
	@echo "  make shell          - Open bash in backend container"
	@echo "  make test           - Run tests"
	@echo "  make rebuild        - Rebuild and restart"

# Development targets (CPU + SQLite)
build:
	@echo "Building CPU image..."
	docker-compose build

up: build
	@echo "Starting development stack..."
	docker-compose up -d
	@echo "✓ Application ready at http://localhost:8000"
	@echo "✓ API Docs at http://localhost:8000/docs"

down:
	@echo "Stopping development stack..."
	docker-compose down

logs:
	docker-compose logs -f backend

health:
	@echo "Checking health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ Service unavailable"

shell:
	docker-compose exec backend bash

test:
	docker-compose exec backend pytest -v

# Production targets (GPU + PostgreSQL)
build-gpu:
	@echo "Building GPU image..."
	docker-compose -f docker-compose.prod.yml build

up-prod: build-gpu
	@echo "Starting production stack with GPU support..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✓ Backend ready at http://localhost:8000"
	@echo "✓ API Docs at http://localhost:8000/docs"
	@echo "✓ pgAdmin available at http://localhost:5050"
	@sleep 10 && $(MAKE) health

down-prod:
	@echo "Stopping production stack..."
	docker-compose -f docker-compose.prod.yml down

logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f backend

# Combined targets
clean:
	@echo "Cleaning up everything..."
	docker-compose down -v
	docker-compose -f docker-compose.prod.yml down -v
	@echo "✓ Cleanup complete"

rebuild:
	@echo "Rebuilding and restarting..."
	$(MAKE) down
	$(MAKE) build
	$(MAKE) up
	@sleep 5 && $(MAKE) health

# Docker image management
push-docker:
	@read -p "Enter Docker registry URL: " registry; \
	docker tag face-attendance:cpu $$registry/face-attendance:cpu; \
	docker push $$registry/face-attendance:cpu

prune:
	@echo "Removing unused Docker resources..."
	docker system prune -f
	@echo "✓ Cleanup complete"

# Status
ps:
	docker-compose ps

ps-prod:
	docker-compose -f docker-compose.prod.yml ps

# Development helpers
install-nvidia-docker:
	@echo "Installing NVIDIA Docker runtime..."
	@echo "Visit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"

check-gpu:
	@echo "Checking GPU availability..."
	docker run --rm --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi

# All targets
.DEFAULT_GOAL := help
