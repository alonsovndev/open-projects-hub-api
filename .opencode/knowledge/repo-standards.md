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

### SQLAlchemy Model Column Ordering

**Convention: `id → data → audit`**

Every table must follow this column order. Import `Base` from `src.app.shared.persistence`:

```python
from src.app.shared.persistence import Base
import uuid

class XxxModel(Base):
    __tablename__ = "xxx"

    # 1. Primary key (always first)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 2. Data columns (business fields, foreign keys, enums)
    name = Column(...)
    client_id = Column(UUID(as_uuid=True), ForeignKey(...))
    status = Column(...)

    # 3. Audit columns (always last)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )
```

**Rationale:** `id` first for quick identification. Audit columns last because they are metadata, not business data. SQLAlchemy places parent class columns before child class columns, so `id`, `created_at`, and `updated_at` must be defined **explicitly on each concrete model** — not inherited from a base model.

**Rules:**
- ❌ Do not use an abstract base model with `id`, `created_at`, or `updated_at` — inheritance forces them first in column order
- ✅ Define `id`, `created_at`, and `updated_at` explicitly on each concrete model
- ✅ `id` always first, `created_at`/`updated_at` always last
- ✅ Use `Base = declarative_base()` (without abstract columns) as the shared parent

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

### Mapper Patterns

Two layers of mappers, both in feature-local `mappers/` directories:

**Infrastructure mappers** (`infrastructure/mappers/`): Model ↔ Entity

Standalone `XxxMapper` class with `@staticmethod` methods. Models never carry mapping logic.

```python
# ✅ Good — standalone mapper class
class ClientMapper:
    @staticmethod
    def to_entity(model: ClientModel) -> ClientEntity: ...
    @staticmethod
    def to_model(entity: ClientEntity) -> ClientModel: ...

# ❌ Bad — mapping methods on the model
class ClientModel(Base):
    def to_entity(self) -> ClientEntity: ...    # model shouldn't know about domain
    def from_entity(cls, entity) -> "ClientModel": ...
```

Repository implementations call `XxxMapper.to_entity(model)` and `XxxMapper.to_model(entity)`.

**Application mappers** (`application/mappers/`): Entity ↔ DTO

Standalone functions. Naming: `to_xxx_response(entity, ...)` (match the DTO name). DTOs never carry mapping logic.

```python
# ✅ Good — standalone function
def to_project_response(entity: ProjectEntity, client_name: str, ...) -> ProjectResponse: ...

# ❌ Bad — mapping classmethod on the DTO
class ProjectResponse(BaseModel):
    @classmethod
    def from_entity(cls, entity, ...) -> "ProjectResponse": ...
```

**Rules:**
- ❌ Models must not have `to_entity()` / `from_entity()` methods
- ❌ DTOs must not have `from_entity()` / `to_response()` classmethods
- ❌ Routes must not construct DTOs inline — delegate to application mappers
- ❌ Use cases must not construct DTOs inline — delegate to application mappers
- ✅ Mappers live in the feature they serve (not in `shared/`)
- ✅ Keep mapper files focused — one mapper class/function per concern

### Validation Patterns

**Use shared validators, not wrapper methods:**

```python
# ✅ Good - Direct call to shared validators
class ProjectEntity:
    def update_details(self, name: str):
        ProjectValidators.validate_name(name)
        self._name = name

# ❌ Bad - Unnecessary wrapper methods
class ProjectEntity:
    @staticmethod
    def _validate_name(name: str):
        ProjectValidators.validate_name(name)  # Just passes through

    def update_details(self, name: str):
        self._validate_name(name)  # Extra indirection
```

**Why:** Wrappers add no value, bloat code, and obscure intent. Call validators directly.

**Reference:** See `src/app/features/projects/domain/validators/project_validators.py` for centralized validation.

### Dependency Injection Patterns

**Composition Root:**

All application dependencies are centrally managed in `src/app/composition/`:

```python
# ✅ Good - Import from composition root
from src.app.composition import (
    get_database_session,
    get_create_project_use_case,
    get_project_repository,
)

@router.post("/projects")
async def create_project(
    payload: CreateProjectRequest,
    use_case = Depends(get_create_project_use_case),
):
    return await use_case.execute(request=payload, created_by=user_id)

# ❌ Bad - Direct imports from feature dependencies (old pattern, removed)
from src.app.features.projects.presentation.dependencies import get_create_project_use_case
```

**Composition Structure:**
- `composition/__init__.py` - Public API exports all 38 dependencies
- `composition/infrastructure.py` - Database session, AI service
- `composition/repositories.py` - Shared repository factories (User, Story, Client)
- `composition/features/*.py` - Feature-specific use cases and repositories
- `composition/core.py` - Cross-cutting services (future)
- `composition/config.py` - Configuration dependencies (future)

**Factory Pattern:**
- All factories return interface types, not implementations
- Repositories return `ABC` interfaces (e.g., `ProjectRepository`)
- Use cases return concrete use case classes
- Infrastructure services may use singleton pattern (e.g., AI service)

**FastAPI vs Plain Factories:**
- Use `async def` factories with `Depends(...)` for standard DI in routes and use case wiring
- Use `def` (synchronous) plain factories (e.g., `build_story_repository`) when FastAPI `Depends()` resolution is not available — typically in auth dependency closures or path-parameter-dependent authorization checks
- Both variants live in the same composition module; the plain factory is a thin wrapper that bypasses DI for constrained contexts

**Adding New Dependencies:**
1. Create factory function in appropriate composition module
2. Return interface type from factory (for repositories)
3. Export from `composition/__init__.py`
4. Import from `src.app.composition` in routes

**Reference:** See `src/app/composition/` for complete composition root implementation.

## Import Conventions

**No `__init__.py` files in `src/app/features/`:**

- This project uses implicit namespace packages (Python 3.3+)
- All feature folders under `src/app/features/` have no `__init__.py` files
- Always use explicit file-path imports:

```python
# ✅ Correct - full path to the module file
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.clients.infrastructure.repositories.client_repository_impl import ClientRepositoryImpl

# ❌ Wrong - no __init__.py means no package-level re-exports
from src.app.features.projects.application.use_cases import CreateProjectUseCase  # will fail
```

**Exception:** The `composition/` root and `shared/` root still use `__init__.py` for public API exports.

## Keep It Lean

- Document only what differs from global standards.
- Avoid duplicating global guidance.
