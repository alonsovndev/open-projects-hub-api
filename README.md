# Open Projects Hub API

A FastAPI-based project management API with Clean Architecture, JWT authentication, and role-based access control.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
make install
```

### 2. Run Database
```bash
docker compose up postgres -d
```

### 3. Run Migrations
```bash
alembic upgrade head
```

### 4. Create First Admin User
```bash
ADMIN_EMAIL="admin@example.com" \
ADMIN_PASSWORD="Admin123!" \
make seed-admin
```

### 5. Start API
```bash
make run
```

The API will be available at `http://localhost:8000`

📖 **Full setup guide:** [docs/setup/ADMIN_SETUP.md](docs/setup/ADMIN_SETUP.md)
📖 **Comprehensive project documentation:** [docs/README.md](docs/README.md)

---

## 🎨 Code Quality

This project uses modern Python code quality tools to ensure clean, consistent, and secure code.

### Tools

- **[Ruff](https://docs.astral.sh/ruff/)** - Fast Python linter and formatter (replaces Black, isort, flake8)
- **[Pytest](https://docs.pytest.org/)** - Testing framework with async support
- **[MyPy](https://mypypy.readthedocs.io/)** - Static type checking
- **[Bandit](https://bandit.readthedocs.io/)** - Security vulnerability scanning
- **[Pre-commit](https://pre-commit.com/)** - Git hooks for automated quality checks

### Quick Start

```bash
# Install development environment
make install-dev

# Run code quality checks
make lint-fix format test

# Commit (pre-commit hooks run automatically)
git commit -m "feat(scope): description"
```

### Documentation

- **[Complete Guide](docs/CODE_QUALITY.md)** - Comprehensive documentation
- **[Setup Summary](docs/SETUP_SUMMARY.md)** - Installation overview

### Available Commands

```bash
# Code quality
make lint              # Check linting
make lint-fix          # Fix linting issues
make format            # Format code
make format-check      # Check formatting
make type-check        # Run type checker
make security          # Run security scan

# Testing
make test              # Run unit tests (excludes integration tests)
make test-unit         # Run unit tests only
make test-integration  # Run integration tests (requires PostgreSQL)
make test-e2e          # Run E2E tests
make coverage          # Run tests with coverage
```

### CI/CD

Pre-commit hooks run automatically on `git commit` to enforce code quality standards locally. CI/CD workflow configuration has not yet been added to this repository.

### Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, test, chore
```

**Examples:**
- `feat(auth): add JWT token refresh`
- `fix(users): resolve email validation`
- `test(projects): add integration tests`
