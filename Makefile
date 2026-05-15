# Makefile for Open Projects Hub API
# Common commands for testing, coverage, linting, and running the application

.PHONY: help install test test-unit test-integration test-e2e coverage coverage-report lint format run clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install          Install dependencies"
	@echo "  make test             Run all tests (unit + integration)"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only (requires DB)"
	@echo "  make test-e2e         Run end-to-end tests only (requires DB)"
	@echo "  make coverage         Run tests with coverage report"
	@echo "  make coverage-report  Open HTML coverage report"
	@echo "  make lint             Run linting (placeholder)"
	@echo "  make format           Format code (placeholder)"
	@echo "  make run              Run development server"
	@echo "  make clean            Clean cache and coverage files"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# Run all tests (excluding integration tests by default)
test:
	pytest --ignore=src/tests/integration/ -v

# Run unit tests only (exclude integration)
test-unit:
	pytest --ignore=src/tests/integration/ -v

# Run integration tests (require database)
test-integration:
	pytest src/tests/integration/ -v

# Run end-to-end tests (require database)
test-e2e:
	pytest -m e2e -v

# Run tests with coverage (unit tests only, fast)
coverage:
	pytest \
		--ignore=src/tests/integration/ \
		--cov=src/app \
		--cov-report=term-missing:skip-covered \
		--cov-report=html \
		--cov-fail-under=80 \
		-v || true
	@echo "\n📊 Coverage Summary:"
	@coverage report --precision=2 | tail -5

# Run tests with coverage (all tests including integration)
coverage-all:
	pytest \
		--cov=src/app \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-fail-under=80 \
		-v

# Open HTML coverage report in browser
coverage-report:
	@echo "Opening coverage report..."
	@command -v open >/dev/null 2>&1 && open htmlcov/index.html || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open htmlcov/index.html || \
	echo "Please open htmlcov/index.html manually"

# Linting (placeholder - add linting tools as needed)
lint:
	@echo "Linting not yet configured. Add ruff, pylint, or flake8 here."

# Code formatting (placeholder - add formatting tools as needed)
format:
	@echo "Formatting not yet configured. Add black, autopep8, or ruff here."

# Run development server
run:
	uvicorn src.app.app:fastApiApp --reload --host 0.0.0.0 --port 8000

# Clean cache and coverage files
clean:
	@echo "Cleaning cache and coverage files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf coverage.json
	rm -rf .coverage.*
	@echo "✅ Cleaned successfully"
