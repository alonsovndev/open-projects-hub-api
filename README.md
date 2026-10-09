# Open Projects Hub API

> FastAPI backend for [Open Projects Hub](https://github.com/alonsovndev/open-projects-hub): Clean Architecture/DDD, JWT authentication, role-based access control, and LLM-assisted requirements refinement.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Part of [alonsovndev](https://github.com/alonsovndev), the open-source engineering lab by [Alonso Villanueva](https://alonsovndev.com).

## 🚀 Quick Start

Requires Python 3.12 and Docker (for PostgreSQL).

### 1. Configure and Install
```bash
cp .env.example .env   # then set SECRET_KEY, POSTGRES_PASSWORD, API_KEY_ENCRYPTION_KEY
make install-dev        # runtime + test + quality tooling
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

**Troubleshooting — verification/reset emails never arrive (macOS):** if the API log shows
`email.send_failed` with `SSL: CERTIFICATE_VERIFY_FAILED ... unable to get local issuer certificate`,
the python.org Python has no CA bundle installed. Run it once, then restart the API:

```bash
/Applications/Python\ 3.12/Install\ Certificates.command
```

### Alternative: Run Everything in Docker

Runs the API and PostgreSQL together with Docker Compose — no local Python install needed.

```bash
cp .env.example .env
# Required in .env: POSTGRES_PASSWORD, SECRET_KEY, API_KEY_ENCRYPTION_KEY
#   (generate the last one with the command shown in .env.example)
# Optional: GEMINI_API_KEY — without it, refinement falls back to the mock AI service.

docker compose up --build          # add -d to run in the background
```

- API: `http://localhost:8080` — Swagger UI at `/docs`, health check at `/health`.
- Migrations run automatically on container startup (`scripts/start-api.sh`).
- The app always runs with `APP_ENV=container` (`src/app/config/config_container.yml`); `compose.yml` overrides any `APP_ENV` in `.env`.
- Re-run with `--build` after code or dependency changes, otherwise the previous image is reused.

Create the first admin user (one-shot container against the same database). `ADMIN_PASSWORD` is required and must contain a letter and a digit:

```bash
ADMIN_EMAIL="admin@example.com" ADMIN_PASSWORD="<strong-password>" \
  docker compose --profile seed run --rm -e ADMIN_EMAIL -e ADMIN_PASSWORD seed-admin
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
│   ├── features/          # One package per bounded context (ai_config, auth, backlog,
│   │                       # client_review, clients, dashboard, projects, refinement,
│   │                       # stories, user, workspaces)
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
- **[MyPy](https://mypy.readthedocs.io/)** - Static type checking
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
make coverage          # Run tests with coverage
```

### CI/CD

Pre-commit hooks run automatically on `git commit`. GitHub Actions (`.github/workflows/ci.yml`) runs on pushes and pull requests to `main` and `dev`: lint, format check, unit tests, coverage, OpenAPI export, and a Docker build. Type checking and the database integration suite run in CI but are informational for now (see Known Limitations).

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

---

## ⚠️ Known Limitations

- **Type checking:** `mypy` reports about 190 errors, mostly from SQLAlchemy 1.x-style `Column` declarations and the `= Depends(...)` default pattern. Migrating models to `Mapped[...]` and routes to `Annotated[..., Depends()]` would clear most of them.
- **Integration tests** (`make test-integration`) are out of date with the current domain model and run as informational in CI. They also reset the database they connect to, so never point them at a database you care about.
- **Rate limiting** keeps counters in process memory per worker and keys on the socket IP. Behind a proxy or with several workers, limits are looser than configured; a shared store (Redis) and proxy headers are needed for production.
- **Platform AI:** without `GEMINI_API_KEY`, platform-credit refinement uses the mock AI service. Set the key in any real deployment.
- **Client Review access codes** are 8 characters, stored in plain text, and don't expire. Regenerating a code revokes the old one.
- **No production deployment pipeline** yet: the Terraform/App Runner path in the docs is the target design.
