# Code Quality Guide

This document provides a comprehensive guide to the code quality tools and practices used in this project.

## Quick Start

### One-Command Setup

```bash
make install-dev
```

This installs all dependencies and sets up pre-commit hooks.

### Essential Commands

#### Daily Use

```bash
# Fix linting issues and format code
make lint-fix && make format

# Run tests
make test

# Before committing, run all checks
make lint-fix format test
```

#### Complete Quality Check

```bash
# Run everything (lint, format check, type check, security, test, coverage)
make lint format-check type-check security test coverage
```

### Development Workflow

1.  **Start work**
    ```bash
    git checkout -b feature/my-feature
    ```

2.  **Make changes** (write code + tests)

3.  **Check quality**
    ```bash
    make lint-fix format test
    ```

4.  **Commit** (pre-commit hooks run automatically)
    ```bash
    git add .
    git commit -m "feat(scope): description"
    ```

5.  **Push**
    ```bash
    git push origin feature/my-feature
    ```

6.  **Create PR**
    *   GitHub Actions will run all checks
    *   PR will show quality gate status

---

## Installation

### Quick Setup (Recommended)

Install all development dependencies and pre-commit hooks:

```bash
make install-dev
```

This will:
- Install all production dependencies
- Install all development dependencies (Ruff, MyPy, Bandit, etc.)
- Set up pre-commit hooks
- Configure the development environment

### Manual Setup

If you prefer manual installation:

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg
```

### What You Got (Tools Configured)

1.  **Ruff** - Fast Python linter & formatter (replaces Black, isort, flake8)
2.  **Pytest** - Testing framework with async support
3.  **Coverage** - Test coverage reporting
4.  **MyPy** - Static type checking
5.  **Bandit** - Security vulnerability scanning
6.  **Pre-commit** - Git hooks for automated checks

### Files Created & Updated

#### Configuration
-   `pyproject.toml` - Centralized Python config
-   `.pre-commit-config.yaml` - Pre-commit hooks
-   `.github/workflows/ci-quality.yml` - CI/CD workflow
-   `requirements-dev.txt` - Dev dependencies
-   `.vscode/settings.json` - VS Code settings
-   `.vscode/extensions.json` - Recommended extensions

#### Scripts
-   `scripts/setup-code-quality.sh` - Setup script

#### Updated Files
-   `Makefile` - Enhanced with code quality commands
-   `.gitignore` - Added Ruff cache exclusion

---

## Tools Overview

| Tool         | Purpose                | Configuration          |
| :----------- | :--------------------- | :--------------------- |
| **Ruff**     | Linting & Formatting   | `pyproject.toml`       |
| **Pytest**   | Testing Framework      | `pyproject.toml`       |
| **Coverage** | Test Coverage          | `pyproject.toml`       |
| **MyPy**     | Type Checking          | `pyproject.toml`       |
| **Bandit**   | Security Scanning      | `pyproject.toml`       |
| **Pre-commit** | Git Hooks             | `.pre-commit-config.yaml` |

---

## Ruff - Linting & Formatting

[Ruff](https://github.com/astral-sh/ruff) is an extremely fast Python linter and formatter written in Rust. It replaces Black, isort, flake8, and many other tools.

### Configuration

-   **File**: `pyproject.toml` under `[tool.ruff]`
-   **Line length**: 100 characters
-   **Target Python**: 3.11+

### Enabled Rules

-   **E/W**: pycodestyle (PEP 8 style)
-   **F**: pyflakes (logical errors)
-   **I**: isort (import sorting)
-   **B**: bugbear (bug detection)
-   **UP**: pyupgrade (modern Python syntax)
-   **ARG**: unused arguments detection
-   **SIM**: code simplification
-   **S**: security (Bandit rules)
-   **N**: naming conventions
-   And more...

### Commands

```bash
# Check for issues (no changes)
make lint

# Check and auto-fix issues
make lint-fix

# Format code
make format

# Check formatting without changes
make format-check
```

### Direct Ruff Usage

```bash
# Lint with auto-fix
ruff check --fix .

# Format code
ruff format .

# Check specific file
ruff check src/app/features/users/domain/user_entity.py

# Watch mode (auto-fix on save)
ruff check --watch .
```

### IDE Integration

#### VS Code

Install the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff):

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true,
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

#### PyCharm

1.  Go to **Settings** → **Tools** → **External Tools**
2.  Add Ruff as an external tool
3.  Configure file watchers for automatic formatting

---

## Pytest - Testing

### Configuration

-   **File**: `pyproject.toml` under `[tool.pytest.ini_options]`
-   **Test directory**: `src/tests/`
-   **Async support**: Enabled with `pytest-asyncio`

### Test Markers

Tests are organized using markers:

```python
@pytest.mark.unit          # Unit tests (fast, no external dependencies)
@pytest.mark.integration   # Integration tests (database required)
@pytest.mark.e2e           # End-to-end tests (full system)
@pytest.mark.slow          # Slow running tests
@pytest.mark.auth          # Authentication tests
```

### Commands

```bash
# Run all tests (excluding integration tests)
make test

# Run only unit tests
make test-unit

# Run integration tests (requires database)
make test-integration

# Run E2E tests
make test-e2e

# Run with coverage
make coverage

# Run with coverage (all tests)
make coverage-all

# Open coverage report in browser
make coverage-report
```

### Direct Pytest Usage

```bash
# Run specific test file
pytest src/tests/domain/users/test_user_entity.py

# Run specific test function
pytest src/tests/domain/users/test_user_entity.py::test_create_user

# Run tests matching pattern
pytest -k "user" -v

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src/app --cov-report=term-missing
```

### Writing Tests

#### Unit Test Example

```python
import pytest
from src.app.features.users.domain.entities.user_entity import UserEntity

@pytest.mark.unit
def test_create_user_entity():
    """Test creating a user entity with valid data."""
    user = UserEntity(
        id=1,
        username="testuser",
        email="test@example.com",
    )

    assert user.username == "testuser"
    assert user.email == "test@example.com"
```

#### FastAPI Integration Test Example

```python
import pytest
from httpx import AsyncClient
from src.app.app import fastapi_app


@pytest.mark.integration
async def test_get_user_endpoint():
    """Test GET /api/v1/users/{user_id} endpoint."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        response = await client.get("/api/v1/users/1")

    assert response.status_code == 200
    data = response.json()
    assert "username" in data
```

---

## Coverage - Test Coverage

### Configuration

-   **File**: `pyproject.toml` under `[tool.coverage]`
-   **Target**: `>=80%` coverage
-   **Output**: Terminal, HTML, XML, JSON

### Commands

```bash
# Run tests with coverage
make coverage

# Generate and open HTML report
make coverage-report
```

### Coverage Reports

After running coverage:

-   **Terminal**: Immediate summary in console
-   **HTML**: Open `htmlcov/index.html` in browser
-   **XML**: `coverage.xml` (for CI/CD tools like Codecov)
-   **JSON**: `coverage.json` (programmatic access)

### Target: ≥80% coverage

---

## MyPy - Type Checking

[MyPy](http://mypy-lang.org/) performs static type checking to catch type-related bugs before runtime.

### Configuration

-   **File**: `pyproject.toml` under `[tool.mypy]`
-   **Strict mode**: Disabled (gradual typing)
-   **Python version**: 3.11

### Commands

```bash
# Run type checking
make type-check
```

### Direct MyPy Usage

```bash
# Check entire project
mypy src/app

# Check specific file
mypy src/app/features/users/domain/user_entity.py

# Generate type coverage report
mypy --html-report mypy-report src/app
```

### Type Hints Example

```python
from typing import Optional

def get_user_by_id(user_id: int) -> Optional[UserEntity]:
    """Get user by ID.

    Args:
        user_id: The user ID to search for

    Returns:
        UserEntity if found, None otherwise
    """
    # Implementation
    pass
```

---

## Bandit - Security Scanning

[Bandit](https://bandit.readthedocs.io/) is a security linter that finds common security issues in Python code.

### Configuration

-   **File**: `pyproject.toml` under `[tool.bandit]`
-   **Target**: `src/app/`
-   **Excludes**: Test files

### Commands

```bash
# Run security scan
make security
```

### Direct Bandit Usage

```bash
# Scan entire project
bandit -c pyproject.toml -r src/app

# Generate JSON report
bandit -c pyproject.toml -r src/app -f json -o bandit-report.json

# Check specific file
bandit src/app/features/auth/application/jwt_service.py
```

### Common Security Issues

Bandit checks for:
-   Hardcoded passwords and secrets
-   SQL injection vulnerabilities
-   Use of insecure functions (e.g., `eval`, `exec`)
-   Weak cryptographic practices
-   Command injection risks

---

## Pre-commit - Git Hooks

[Pre-commit](https://pre-commit.com/) runs code quality checks before each commit, **ensuring that only high-quality, compliant code enters the repository.** It prevents common issues like linting errors, formatting inconsistencies, and invalid commit messages.

### Configuration

-   **File**: `.pre-commit-config.yaml`

### Hooks Configured

1.  Ruff - Linting and formatting
2.  Trailing whitespace - Remove trailing spaces
3.  End of file fixer - Ensure files end with newline
4.  YAML/JSON/TOML validation - Syntax checking
5.  Bandit - Security scanning
6.  MyPy - Type checking
7.  Conventional commits - Commit message validation

### Commands

```bash
# Install hooks
make pre-commit-install

# Run hooks manually on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Update hook versions
pre-commit autoupdate
```

### Commit Message Format

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
```
feat(auth): add JWT token refresh endpoint
fix(users): resolve email validation bug
docs(api): update API documentation
test(projects): add integration tests for project creation
```

---

## CI/CD - GitHub Actions

### Workflow: Code Quality & Testing

**File**: `.github/workflows/ci-quality.yml`

This workflow runs automatically on:
-   Push to `main`, `develop`, or `feature/**` branches
-   Pull requests to `main` or `develop`

### Jobs

1.  **Lint** - Ruff linting and format checking
2.  **Type Check** - MyPy static type analysis
3.  **Security** - Bandit security scanning
4.  **Test** - Unit and integration tests with coverage
5.  **E2E Tests** - End-to-end tests with database
6.  **Quality Gate** - Fail build if any check fails

### Required Environment Variables (CI)

```yaml
DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5432/test_db
APP_ENV: test
SECRET_KEY: test-secret-key-for-ci-only
JWT_SECRET_KEY: test-jwt-secret-key-for-ci-only
```

---

## Project Structure

```
open-projects-hub-api/
├── .github/
│   └── workflows/
│       ├── ci-quality.yml          # CI/CD quality workflow
│       ├── test-coverage.yml       # Existing coverage workflow
│       └── security.yml            # Existing security workflow
├── src/
│   ├── app/                        # Application code
│   │   ├── features/               # Feature modules
│   │   ├── shared/                 # Shared utilities
│   │   └── config/                 # Configuration
│   └── tests/                      # Test suite
│       ├── unit/                   # Unit tests
│       ├── integration/            # Integration tests
│       ├── e2e/                    # E2E tests
│       └── conftest.py             # Pytest fixtures
├── pyproject.toml                  # Python project config (Ruff, Pytest, MyPy, Bandit, Coverage)
├── .pre-commit-config.yaml         # Pre-commit hooks config
├── requirements.txt                # Production dependencies
├── requirements-dev.txt            # Development dependencies
├── pytest.ini                      # Legacy pytest config (migrate to pyproject.toml)
├── .coveragerc                     # Legacy coverage config (migrate to pyproject.toml)
└── Makefile                        # Common commands
```

---

## Migration from Legacy Config

This project previously used separate config files. The new setup centralizes configuration in `pyproject.toml`.

### What Changed

| Old          | New                                  | Status      |
| :----------- | :----------------------------------- | :---------- |
| `pytest.ini`   | `[tool.pytest]` in `pyproject.toml`  | ✅ Migrated |
| `.coveragerc`  | `[tool.coverage]` in `pyproject.toml` | ✅ Migrated |
| Black        | Ruff format                          | ✅ Replaced |
| isort        | Ruff (I rules)                       | ✅ Replaced |
| flake8       | Ruff                                 | ✅ Replaced |

### Cleanup (Optional)

After verifying everything works:

```bash
# Remove legacy config files
rm pytest.ini .coveragerc

# Keep for now as reference, delete later
```

---

## Troubleshooting

### "Command not found: ruff"

```bash
make install-dev
```

### Pre-commit Hook Fails

```bash
# Fix issues
make lint-fix format

# Try commit again
git commit
```

### Tests Fail

```bash
# See failures
make test

# Fix code/tests, then run again
make test
```

### Type Checking Errors

```bash
# MyPy is non-blocking, but fix issues for better code quality
make type-check

# Add type: ignore comment for unavoidable issues
result = some_function()  # type: ignore[type-of-issue]
```

### Skip Hooks Temporarily (Not Recommended)

```bash
git commit --no-verify
```

---

## Verification

### Verification Checklist

Run these to verify everything works:

```bash
# Check installations
ruff --version          # Should show ≥0.8.4
mypy --version          # Should show ≥1.14.0
bandit --version        # Should show ≥1.8.0
pre-commit --version    # Should show ≥4.0.0
pytest --version        # Should show 8.3.4

# Test commands
make lint               # Should check linting
make format-check       # Should check formatting
make test               # Should run tests
make coverage           # Should run coverage

# Test pre-commit
pre-commit run --all-files  # Should run all hooks
```

### Success Criteria

After migration, you should have:

-   ✅ Zero linting violations
-   ✅ Consistent code formatting
-   ✅ ≥80% test coverage
-   ✅ No security vulnerabilities
-   ✅ Pre-commit hooks active
-   ✅ CI/CD passing
-   ✅ Clean commit history

---

## Additional Resources

-   [Ruff Docs](https://docs.astral.sh/ruff/)
-   [Pytest Docs](https://docs.pytest.org/)
-   [MyPy Docs](https://mypy.readthedocs.io/)
-   [Pre-commit Docs](https://pre-commit.com/)
-   [Conventional Commits](https://www.conventionalcommits.org/)
-   [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

## Contributing

All contributors must:
1.  Run `make install-dev` to set up the environment
2.  Ensure `make lint` and `make test` pass before committing
3.  Follow conventional commit message format
4.  Maintain test coverage ≥80%

---

## License

This project follows the license specified in the root LICENSE file.
