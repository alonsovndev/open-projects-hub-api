# Repository Agent Instructions

This file contains repository-specific rules and preferences.

## Scope

- Apply only to this repository.
- Do not duplicate global rules from ${HOME}/.config/opencode.

## Domain Boundaries

- Main API bootstrap is `src/app/app.py`; ASGI entrypoint for deployments is `src/main.py` (`app = fastApiApp`).
- Business code is feature-first under `src/app/features/{user,projects,stories,dashboard}` with layered folders (`application/`, `domain/`, `infrastructure/`, `presentation/`).
- Cross-feature concerns live under `src/app/shared/` and follow the same layered split; prefer shared modules only for true cross-feature reuse.
- API routers are centrally wired in `src/app/shared/presentation/router_registry.py` under `/v1/*` prefixes.
- **Dependency injection** is centralized in `src/app/composition/` - all use cases, repositories, and infrastructure dependencies are exported from `composition/__init__.py`.
- **`__init__.py` files:** Feature folders under `src/app/features/` use implicit namespace packages (no `__init__.py`). Always use explicit file-path imports. The `composition/` and `shared/` roots retain `__init__.py` for public API exports.

## Build, Test, and Run Commands

- Install: `make install`
- Run API locally: `make run` (uses `uvicorn src.app.app:fastApiApp --reload --port 8000`)
- Unit/default tests (no DB): `make test` or `make test-unit` (both ignore `src/tests/integration/`)
- DB-backed integration tests: `make test-integration` (requires PostgreSQL)
- Marker-based E2E tests: `make test-e2e` (runs `pytest -m e2e`)
- Coverage: `make coverage` (unit-focused, `--cov-fail-under=80`), `make coverage-all` (includes DB tests), `make coverage-report`

## Quality Verification

**After making any code changes, run these commands to verify quality:**

1. **Linting**: `ruff check .` (check for issues) or `ruff check . --fix` (auto-fix)
2. **Formatting**: `ruff format .` (format code)
3. **Type Checking**: `mypy src/` (note: currently has known type annotation issues)
4. **Unit Tests**: `make test-unit` (must pass before claiming work complete)
5. **Security**: `bandit -r src/app -c pyproject.toml` (check for security issues)

**Verification workflow:**
```bash
# Quick verification (before committing)
ruff check . --fix && ruff format . && make test-unit

# Full verification (before claiming "done")
ruff check . && make test-unit && make coverage
```

**Note**: Pre-commit hooks will automatically run these checks on commit. Do not bypass with `--no-verify` unless explicitly requested by the user.

## Data, Security, and Environment Constraints

- Configuration is environment-driven via `APP_ENV` and `src/app/config/config_<env>.yml`; loaded by `src/app/config/app_config.py`.
- Docker startup runs migrations before serving (`scripts/start-api.sh` executes `alembic upgrade head`).
- Integration tests require PostgreSQL (`compose.yml` service `postgres` or an equivalent local instance).
- In non-local/container environments, API docs are disabled in `src/app/app.py` (`docs_url`, `redoc_url`, `openapi_url` set to `None`).

## Naming Conventions (Quick Reference)

**Use case parameters:**
- `request: CreateProjectRequest` (not `command`)
- `created_by: str` (context from JWT)
- `project_id: str` (explicit IDs, not generic `id`)

**Variable names:**
- ❌ Generic: `command`, `data`, `tmp`, `val`
- ✅ Self-documenting: `request`, `user_count`, `theme_value`

**Comments:**
- Explain WHY, not WHAT
- Only for non-obvious logic

See `.opencode/knowledge/repo-standards.md` for detailed implementation patterns.
