# Makefile for cc-benchmark project

.PHONY: help test test-models test-all install install-dev clean lint format

help:  ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync

install-dev:  ## Install dependencies including dev tools
	uv sync
	uv add --dev pytest anthropic

test-models:  ## Test model synchronization with Anthropic SDK
	@echo "🔍 Testing model synchronization..."
	uv run python tests/test_model_sync.py

test:  ## Run model sync tests with pytest
	@echo "🧪 Running tests..."
	uv run python -m pytest tests/test_model_sync.py -v

test-unit:  ## Run only unit tests (fast)
	@echo "⚡ Running unit tests..."
	uv run python -m pytest tests/ -m "unit" -v

test-integration:  ## Run only integration tests (slower)
	@echo "🔗 Running integration tests..."
	uv run python -m pytest tests/ -m "integration" -v

test-all:  ## Run all tests
	@echo "🧪 Running all tests..."
	uv run python -m pytest tests/ -v

lint:  ## Run linting (when linting tools are configured)
	@echo "📝 Linting would run here..."
	@echo "   Add tools like ruff, black, etc."

format:  ## Run code formatting (when formatting tools are configured)
	@echo "🎨 Formatting would run here..."
	@echo "   Add tools like black, ruff format, etc."

clean:  ## Clean up cache files and temporary directories
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Docker integration
docker-test:  ## Run tests in Docker environment  
	@echo "🐳 Running tests in Docker..."
	docker run --rm --env-file .env -v `pwd`:/cc-benchmark -w /cc-benchmark cc-benchmark make test-models