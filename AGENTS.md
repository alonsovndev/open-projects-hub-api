# AGENTS.md

## Purpose

- This file gives repository-specific guidance to coding agents working in `open-projects-hub-api`.
- Follow repository evidence first and update this file when commands, tooling, or structure change.

## Current Repository State

- The project is now a Python FastAPI API.
- Package root: `src/app/`.
- Tests live in `src/tests/`.
- Base dependencies currently live in `requirements.txt`.
- No `pyproject.toml` exists right now.
- No `.cursor/rules/` directory exists.
- No `.cursorrules` file exists.
- No `.github/copilot-instructions.md` file exists.

## Technology Stack

- Framework: FastAPI.
- Runtime: Python 3.10+.
- Test framework: pytest.
- HTTP test client: FastAPI `TestClient`.
- No lint tool is configured in the repository yet.
- Dependency management is not locked to a specific installer yet; use `pip` unless the repo later adopts `uv`, Poetry, or another tool.

## Verified Commands

### Install

- Base dependencies: `python3 -m pip install -r requirements.txt`
- Dev dependencies: not separately configured yet.

### Run The API

- Local dev server: `python3 -m uvicorn src.app.main:app --reload`

### Lint

- No lint command is configured today.

### Test

- Full test suite: `python3 -m pytest`
- Quiet test suite: `python3 -m pytest -q`
- Single test file: `python3 -m pytest src/tests/presentation/api/test_auth_login.py -q`
- Single test function: `python3 -m pytest src/tests/presentation/api/test_auth_login.py::test_login_success_returns_frontend_shape -q`

### Build

- No dedicated build command is required today.
- If packaging verification is needed later, add the exact command here when the workflow exists.

## Application Structure

- `src/app/main.py`: FastAPI app bootstrap and router registration.
- `src/app/domain/`: domain entities, domain contracts, and domain errors.
- `src/app/application/`: use cases and application DTOs.
- `src/app/infrastructure/`: adapters such as in-memory repositories.
- `src/app/presentation/`: FastAPI routers, request models, response models, and dependency wiring.
- `src/tests/`: automated tests mirroring the package structure when practical.
- `docs/`: repository notes and supporting documentation when needed.

## Clean Architecture / DDD Rules

- Keep FastAPI and other frameworks inside `src/app/presentation/`.
- Keep business rules in `src/app/application/` and `src/app/domain/`.
- Domain code must not depend on FastAPI, Pydantic, or infrastructure concerns.
- Infrastructure implements domain/application contracts; it should not own business rules.
- Presentation code translates HTTP input/output to application DTOs.
- Prefer constructor injection for use cases and adapters.
- Keep dependencies pointing inward: presentation -> application -> domain.

## Auth Module Conventions

- Current auth flow is intentionally simple and in-memory.
- Primary endpoint: `POST /auth/login`.
- Request body fields: `email`, `password`.
- Success response fields must match frontend expectations exactly:
  - `token`
  - `email`
  - `displayName`
  - `loggedInAt`
- Invalid credentials should return `401` with a generic message such as `Invalid credentials`.
- Use mock values only where the current feature explicitly calls for them.
- CORS currently allows the local frontend origin `http://localhost:5173`.
- If JWT, hashing, refresh tokens, or persistent storage are introduced later, update this file.

## Code Style Baseline

- Use 4 spaces for indentation.
- Use UTF-8 text files and Unix newlines.
- Keep lines readable; target roughly 88-100 characters.
- Favor explicit, boring code over clever abstractions.
- Match existing naming and module boundaries before introducing new patterns.

## Imports

- Group imports into standard library, third-party, and local imports.
- Separate import groups with one blank line.
- Prefer absolute imports.
- Avoid wildcard imports.
- Import only what is used.

## Formatting

- Prefer one statement per line.
- Use trailing commas in multiline literals when they improve diffs.
- Avoid vertically aligned formatting.
- Keep top-level definitions separated by two blank lines.

## Types

- Add type hints for public functions, methods, and module-level constants.
- Prefer explicit return types for non-trivial functions.
- Use built-in generics like `list[str]` and `dict[str, str]`.
- Avoid `Any` unless a boundary is genuinely dynamic.
- Use `dataclass` for simple internal DTOs and entities unless another pattern is justified.

## Naming

- Use `snake_case` for modules, variables, and functions.
- Use `PascalCase` for classes.
- Use `UPPER_SNAKE_CASE` for constants.
- Use descriptive names over abbreviations.
- Name exception classes with the `Error` suffix.

## Functions And Classes

- Keep functions focused on one responsibility.
- Prefer small use cases with explicit inputs and outputs.
- Avoid deep nesting when guard clauses are clearer.
- Keep classes narrow in responsibility.
- Prefer composition over inheritance.

## Error Handling

- Raise specific exceptions for domain and application failures.
- Do not swallow exceptions silently.
- Translate domain/application errors to HTTP responses in the presentation layer.
- Keep error messages safe and generic at public API boundaries.

## Validation And Schemas

- Validate HTTP request shape in Pydantic models.
- Normalize data once near the boundary when possible.
- Keep transport schemas separate from domain entities.
- Do not pass Pydantic models directly into domain logic when a DTO is clearer.

## Testing Guidance

- Add tests for each new use case and endpoint.
- Prefer fast, deterministic tests with no network access.
- Keep one assertion theme per test.
- When fixing a bug, add or update a test that would have caught it.
- For API tests, verify both status codes and response payload shape.

## Documentation Maintenance

- Update this file when commands, architecture, or conventions change.
- Keep examples aligned with the actual codebase.
- Do not claim support for tools or workflows that are not configured.

## Cursor / Copilot Rules

- Cursor rules present: no.
- Copilot instructions present: no.
- No external editor-agent instruction files were available to merge.
