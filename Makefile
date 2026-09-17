# Makefile for Open Projects Hub API
# Common commands for testing, coverage, linting, and running the application

.PHONY: help install install-dev test test-unit test-integration test-e2e coverage coverage-report lint lint-fix format format-check type-check security pre-commit-install run seed-admin clean

# Load environment variables from .env file (if it exists)
-include .env
export

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install            Install production dependencies"
	@echo "  make install-dev        Install dev dependencies + pre-commit hooks"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test               Run all tests (unit + integration)"
	@echo "  make test-unit          Run unit tests only"
	@echo "  make test-integration   Run integration tests only (requires DB)"
	@echo "  make test-e2e           Run end-to-end tests only (requires DB)"
	@echo "  make coverage           Run tests with coverage report"
	@echo "  make coverage-report    Open HTML coverage report"
	@echo ""
	@echo "✨ Code Quality:"
	@echo "  make lint               Run Ruff linter (check only)"
	@echo "  make lint-fix           Run Ruff linter with auto-fix"
	@echo "  make format             Format code with Ruff"
	@echo "  make format-check       Check code formatting (no changes)"
	@echo "  make type-check         Run MyPy type checker"
	@echo "  make security           Run Bandit security scanner"
	@echo "  make pre-commit-install Install pre-commit hooks"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make run                Run development server"
	@echo "  make seed-admin         Create first admin user (uses APP_ENV config, defaults to .env)"
	@echo "  make seed-sample-data   Seed realistic sample clients/projects/stories (requires admin user)"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean              Clean cache and coverage files"

# Install dependencies
install:
	@echo "📦 Installing production dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt

# Install development dependencies and pre-commit hooks
install-dev:
	@echo "📦 Installing development dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install ruff mypy bandit[toml] pre-commit pytest-cov
	@echo ""
	@echo "🪝 Installing pre-commit hooks..."
	pre-commit install --install-hooks
	pre-commit install --hook-type commit-msg
	@echo ""
	@echo "✅ Development environment ready!"
	@echo "   Run 'make lint' to check code quality"
	@echo "   Run 'make format' to format code"
	@echo "   Run 'make test' to run tests"

# Run all tests (excluding integration tests by default)
test:
	pytest --ignore=src/tests/integration/ -m "not integration" -v

# Run unit tests only (exclude integration)
test-unit:
	pytest --ignore=src/tests/integration/ -m "not integration" -v

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

# Linting with Ruff (check only, no fixes)
lint:
	@echo "🔍 Running Ruff linter..."
	ruff check .

# Linting with Ruff (check and auto-fix)
lint-fix:
	@echo "🔧 Running Ruff linter with auto-fix..."
	ruff check --fix .

# Code formatting with Ruff (apply formatting)
format:
	@echo "🎨 Formatting code with Ruff..."
	ruff format .
	@echo "✅ Code formatted successfully"

# Code formatting check (no changes)
format-check:
	@echo "🎨 Checking code formatting..."
	ruff format --check .

# Type checking with MyPy
type-check:
	@echo "🔬 Running MyPy type checker..."
	mypy src/app --config-file=pyproject.toml || true

# Security scanning with Bandit
security:
	@echo "🔒 Running Bandit security scanner..."
	bandit -c pyproject.toml -r src/app

# Install pre-commit hooks
pre-commit-install:
	@echo "🪝 Installing pre-commit hooks..."
	pre-commit install --install-hooks
	pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed"

# Run development server
run:
	uvicorn src.app.app:fastapi_app --reload --host 0.0.0.0 --port 8000

# Seed first admin user (connects using the same config as `make run`, i.e. APP_ENV from .env)
seed-admin:
	@echo "🌱 Creating first admin user..."
	python3 scripts/seed_admin.py

# Seed realistic sample clients/projects/stories (requires an existing admin user)
seed-sample-data:
	@echo "🌱 Seeding sample clients, projects, and stories..."
	python3 scripts/seed_sample_data.py

# Clean cache and coverage files
clean:
	@echo "🧹 Cleaning cache and coverage files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf coverage.json
	rm -rf .coverage.*
	@echo "✅ Cleaned successfully"
