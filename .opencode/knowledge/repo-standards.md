# Repository Standards

Repository-specific standards for making safe, minimal changes in this codebase.

## Architecture Boundaries

- Keep feature logic inside its feature package in `src/app/features/*`; avoid leaking feature-specific code into `src/app/shared/*`.
- Presentation layer (routes/DTOs/dependencies) stays in `presentation/`; use cases stay in `application/`; persistence/adapters stay in `infrastructure/`.
- Preserve central router registration in `src/app/shared/presentation/router_registry.py` instead of mounting routers ad hoc.

## Clean Code Practices

### Use Case Design

**Follow Command Pattern with DTOs:**
- Use case methods should accept DTOs (e.g., `CreateProjectRequest`) rather than many individual parameters
- Keep context parameters separate (e.g., `created_by: str` from JWT token)
- Maximum 2-3 parameters per use case method (typically: DTO + context)

**Parameter naming:**
- Use `request` for input DTOs (matches `XxxRequest` type name)
- Use explicit ID names: `project_id`, `user_id`, `story_id` (not generic `id`)
- Use `created_by` for actor context from authentication

**Example:**
```python
# ✅ Good
async def execute(self, request: CreateProjectRequest, created_by: str) -> ProjectResponse:
    pass

# ❌ Bad (too many params)
async def execute(self, name: str, code: str, client_id: str, desc: str, ...) -> ProjectResponse:
    pass
```

### Route Handler Patterns

**Pass DTOs directly to use cases:**
```python
# ✅ Good - pass DTO directly
use_case.execute(request=payload, created_by=user_id)

# ❌ Bad - manual unpacking
use_case.execute(
    name=payload.name,
    code=payload.code,
    client_id=payload.client_id,
    # ... many lines
)
```

### Variable Naming

- Use self-documenting names that match their type or purpose
- Avoid generic names: `command`, `data`, `tmp`, `val`
- Match DTO type names: `CreateProjectRequest` → `request`
- Be explicit with IDs and context variables

## API Contract Rules

- Keep endpoint versioning under `/v1` as defined by router prefixes in `src/app/shared/presentation/router_registry.py`.
- Align route updates with docs in `docs/api/README.md` when paths or auth requirements change.
- DTOs use `camelCase` for JSON (Pydantic `alias_generator=to_camel`) but Python code uses `snake_case`.

## Data and Migration Constraints

- For model/schema changes, update SQLAlchemy models and create Alembic migrations (`alembic revision --autogenerate -m "..."`, then `alembic upgrade head`).
- Maintain startup compatibility with container flow that expects migrations to succeed before Gunicorn starts (`scripts/start-api.sh`).

## Testing Strategy for This Repo

- Test suites are split by scope under `src/tests/` (`unit/`, `application/`, `domain/`, `presentation/`, `infrastructure/`, `integration/`, `e2e/`).
- Use markers from `pytest.ini` (`unit`, `integration`, `e2e`, `slow`, `auth`) and keep marker semantics intact when adding tests.
- Keep coverage threshold expectations at `>=80%` in local/CI commands.

## Deployment Notes

- Docker service exposes API on `:8080` (`compose.yml`) while local `make run` serves on `:8000`; verify the correct base URL in tests/docs.
- Container runtime entrypoint is `src.main:app` via Gunicorn (`scripts/start-api.sh`), not direct `uvicorn` module execution.

## Refactoring Guidelines

### When Refactoring Use Cases

1. **Check parameter count** - If > 4 parameters, refactor to use DTO
2. **Use existing DTOs** - Most features have `CreateXxxRequest` and `UpdateXxxRequest` DTOs
3. **Keep context separate** - Authentication/authorization context stays as separate params
4. **Update routes** - Change route handlers to pass DTOs directly (no unpacking)
5. **Update tests** - Modify test fixtures to create DTOs instead of passing individual params
6. **Verify** - Run `make test-unit` to ensure no regressions

### Repository Pattern Consistency

- All repositories use plain `ABC` with explicit methods (no `BaseRepository`)
- Return types should match domain needs (e.g., `Tuple[ProjectEntity, str]` for project + client name)
- Repository methods use domain entities, not DTOs or models directly

### Mapper Location

- Mappers live in feature's `application/mappers/` directory (not `shared/`)
- Mappers convert between domain entities and application DTOs
- Keep mappers close to the DTOs they work with

## Keep It Lean

- Document only what differs from global standards.
- Avoid duplicating global guidance.
