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

### 5. (Optional) Seed Sample Data
```bash
make seed-sample-data
```
Idempotent — populates 3 realistic clients, 6 projects, and ~20 stories with varied statuses.

### 6. Start API
```bash
make run
```

The API will be available at `http://localhost:8000`

### Alternative: Run Everything in Docker

Runs the API and PostgreSQL together with Docker Compose — no local Python install needed.

```bash
cp .env.example .env
# Required in .env: POSTGRES_PASSWORD, SECRET_KEY, API_KEY_ENCRYPTION_KEY
#   (generate the last one with the command shown in .env.example)
# Optional: GEMINI_API_KEY / OPENAI_API_KEY / DEEPSEEK_API_KEY — without the key for
#   `ai.provider` in config_container.yml, refinement falls back to the mock AI service.

docker compose up --build          # add -d to run in the background
```

- API: `http://localhost:8080` — Swagger UI at `/docs`, health check at `/health`.
- Migrations run automatically on container startup (`scripts/start-api.sh`).
- The app always runs with `APP_ENV=container` (`src/app/config/config_container.yml`); `compose.yml` overrides any `APP_ENV` in `.env`.
- Re-run with `--build` after code or dependency changes, otherwise the previous image is reused.

Create the first admin user (one-shot container against the same database):

```bash
docker compose --profile seed run --rm seed-admin
```

Stop the stack with `docker compose down` (add `-v` to also delete the database volume).

📖 **Docker deployment guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
📖 **Full setup guide:** [docs/setup/ADMIN_SETUP.md](docs/setup/ADMIN_SETUP.md)
📖 **Database migrations & rollback runbook:** [docs/DATABASE_MIGRATIONS.md](docs/DATABASE_MIGRATIONS.md)
📖 **Comprehensive project documentation:** [docs/README.md](docs/README.md)

---

## 📖 API Documentation

Swagger UI and ReDoc are generated automatically from route/Pydantic annotations — no hand-written spec to keep in sync. Available in `local`/`container` environments only (disabled elsewhere for security):

- **Swagger UI**: `http://localhost:8000/docs` — browse every endpoint, see request/response schemas, and execute real requests ("Try it out") with a JWT.
- **ReDoc**: `http://localhost:8000/redoc` — read-only alternative layout.
- **Raw schema**: `http://localhost:8000/openapi.json`.

To export a static, committable copy of the current schema (e.g. after adding/changing endpoints):

```bash
make export-openapi   # writes docs/api/openapi.json
```

Full endpoint reference, auth flows, pagination, filtering, and cURL/Python/JS examples: [docs/api/README.md](docs/api/README.md).

---

## 📂 Project Structure

```
src/
├── app/
│   ├── features/          # One package per bounded context (auth, clients, dashboard,
│   │                       # projects, refinement, stories, user)
│   │   └── <feature>/
│   │       ├── domain/           # Entities, value objects, repository interfaces, domain exceptions
│   │       ├── application/      # Use cases, DTOs, mappers
│   │       ├── infrastructure/   # Repository implementations, ORM models, infra mappers
│   │       └── presentation/     # FastAPI routes for this feature
│   ├── shared/             # Cross-feature building blocks (domain/application/infrastructure/
│   │                       # presentation/logging/persistence) reused across features
│   ├── config/             # app_config.py, per-environment config_*.yml, paths.py
│   └── composition/        # Composition root — dependency wiring, one module per feature
└── tests/                  # Mirrors src/app/ (unit, integration, presentation, domain,
                             # application, infrastructure)
```

Every feature follows the same four-layer package structure (domain → application → infrastructure → presentation), enforcing the dependency-inversion rules described in [Clean Architecture](docs/engineering/clean-architecture.md) and [Composition Root](docs/engineering/composition-root.md).

**Import convention**: all internal imports are absolute (`from src.app....`), never relative — enforced by the `known-first-party = ["src"]` isort setting in `pyproject.toml` and checked by `make lint`.

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
