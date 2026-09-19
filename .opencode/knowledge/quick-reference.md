# Quick Reference Guide

Fast lookup for common patterns and commands in this repository.

## 🚀 Common Commands

### Development
```bash
# Start local development
make run                    # API on :8000 with hot reload

# Database
docker compose up postgres -d
alembic upgrade head       # Run migrations
```

### Testing
```bash
make test                  # Unit tests (same as test-unit)
make test-unit             # Fast, no DB
make test-integration      # Requires PostgreSQL
make test-e2e             # End-to-end tests
make coverage             # Coverage report (80% threshold)
```

### Quality
```bash
make lint-fix             # Auto-fix linting issues
make format               # Format code with Ruff
make type-check           # Run MyPy (has known issues)
make security             # Bandit security scan

# Quick check before commit
ruff check . --fix && ruff format . && make test-unit
```

### Docker
```bash
# Build and run
docker compose up -d
docker compose logs -f app

# Database operations
docker compose exec app alembic upgrade head
docker compose exec postgres psql -U open-projects-hub-admin -d open-projects-hub-db
```

---

## 📁 Feature Structure (No `__init__.py`)

**Existing features:** `auth`, `clients`, `dashboard`, `projects`, `refinement`, `stories`, `user`

```
src/app/features/{feature}/
├── application/
│   ├── dtos/              # Request/Response DTOs
│   ├── mappers/           # Entity ↔ DTO conversion (standalone functions)
│   └── use_cases/         # Business orchestration
├── domain/
│   ├── entities/          # Business objects
│   ├── repositories/      # Repository interfaces (ABC)
│   ├── validators/        # Domain validation
│   └── value_objects/     # Immutable domain values
├── infrastructure/
│   ├── mappers/           # Model ↔ Entity conversion (standalone classes)
│   ├── models/            # SQLAlchemy models
│   └── repositories/      # Repository implementations
└── presentation/
    └── {feature}_routes.py # FastAPI routes
```

**Note:** The `refinement` feature router is mounted at `/v1` (no sub-path), while all other feature routers use `/v1/<feature>` prefixes.

**Import convention:** Always use full file paths (no `__init__.py` re-exports)

```python
# ✅ Correct
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase

# ❌ Wrong (will fail)
from src.app.features.projects.application.use_cases import CreateProjectUseCase
```

---

## 🔧 Dependency Injection

### Import from Composition Root

```python
from src.app.composition import (
    get_database_session,
    get_create_project_use_case,
    get_project_repository,
)
```

### Route Pattern

```python
@router.post("/projects")
async def create_project(
    payload: CreateProjectRequest,
    current_user: dict = Depends(verify_jwt_token),
    use_case = Depends(get_create_project_use_case),
):
    user_id = current_user.get("sub")
    return await use_case.execute(request=payload, created_by=user_id)
```

---

## 📝 Use Case Pattern

```python
class CreateProjectUseCase:
    def __init__(
        self,
        project_repository: ProjectRepository,
        client_repository: ClientRepository,
    ):
        self.project_repo = project_repository
        self.client_repo = client_repository

    async def execute(
        self,
        request: CreateProjectRequest,  # DTO
        created_by: str,                # Context
    ) -> ProjectResponse:
        # 1. Validate dependencies
        client = await self.client_repo.find_by_id(request.client_id)
        if not client:
            raise ClientNotFoundError(...)

        # 2. Create entity
        project = ProjectEntity.create(...)

        # 3. Persist
        saved = await self.project_repo.save(project)

        # 4. Return DTO (via application mapper)
        return to_project_response(saved, client_name)
```

**Rules:**
- Max 2-3 parameters: DTO + context
- Use `request` for input DTOs
- Use explicit IDs: `project_id`, not `id`
- Use `created_by` for auth context

---

## 🗂️ File Locations

| Concern | Location |
|---------|----------|
| API bootstrap | `src/app/app.py` |
| ASGI entrypoint | `src/main.py` |
| DI factories | `src/app/composition/` |
| Router registry | `src/app/shared/presentation/router_registry.py` |
| Config files | `src/app/config/config_{env}.yml` |
| Models | Feature: `infrastructure/models/`, Shared: `shared/infrastructure/models/` |
| Mappers (infrastructure) | Feature: `infrastructure/mappers/` (classes: `XxxMapper`) |
| Mappers (application) | Feature: `application/mappers/` (functions: `to_xxx_response`) |
| Tests | `src/tests/{unit,application,domain,presentation,infrastructure,integration,e2e}/` |
| Migrations | `alembic/versions/` |
| Scripts | `scripts/` (seed_admin.py, start-api.sh) |
| Health checks | `src/app/shared/presentation/health_checks.py` (`/health`, `/health/live`, `/health/ready`) |
| Logging utils | `src/app/shared/logging/` (structured logging, PII redaction) |
| CORS config | `src/app/config/config_<env>.yml` (per-environment, not hardcoded) |

---

## 🔍 Finding Things

```bash
# Find all routes
find src/app/features -name "*routes*.py"

# Find all repositories
find src/app/features -path "*/repositories/*.py"

# Find use cases
find src/app/features -path "*/use_cases/*.py"

# Find DTOs
find src/app/features -path "*/dtos/*.py"

# Find mappers
find src/app/features -path "*/mappers/*.py"

# Check what's exported from composition
cat src/app/composition/__init__.py | grep "^from"
```

---

## 📦 Adding a New Feature

1. **Create structure:**
   ```bash
   mkdir -p src/app/features/{feature}/{application,domain,infrastructure,presentation}
   mkdir -p src/app/features/{feature}/application/{dtos,mappers,use_cases}
   mkdir -p src/app/features/{feature}/domain/{entities,repositories,validators}
   mkdir -p src/app/features/{feature}/infrastructure/{mappers,models,repositories}
   ```

2. **Create domain (inside out):**
   - Entity: `domain/entities/{entity}_entity.py`
   - Repository interface: `domain/repositories/{entity}_repository.py`
   - Validators: `domain/validators/{entity}_validators.py`

3. **Create application layer:**
   - DTOs: `application/dtos/{entity}_dto.py`
   - Mapper: `application/mappers/{entity}_mapper.py`
   - Use case: `application/use_cases/{action}_{entity}.py`

4. **Create infrastructure:**
    - Mapper: `infrastructure/mappers/{entity}_mapper.py` (standalone class with `to_entity`/`to_model`)
    - Model: `infrastructure/models/{entity}_model.py`
    - Repository impl: `infrastructure/repositories/{entity}_repository_impl.py`

5. **Create presentation:**
   - Routes: `presentation/{feature}_routes.py`

6. **Wire dependencies:**
   - Create `src/app/composition/features/{feature}.py`
   - Export from `src/app/composition/__init__.py`
   - Register router in `src/app/shared/presentation/router_registry.py`

7. **Create migration:**
   ```bash
   alembic revision --autogenerate -m "Add {feature} table"
   alembic upgrade head
   ```

---

## 🧪 Testing Patterns

### Unit Test (Mock Repository)

```python
@pytest.mark.asyncio
async def test_create_project():
    mock_repo = AsyncMock(spec=ProjectRepository)
    mock_repo.save.return_value = mock_entity

    use_case = CreateProjectUseCase(mock_repo)
    result = await use_case.execute(request=request, created_by="user-id")

    assert result.name == "Project"
    mock_repo.save.assert_called_once()
```

### Integration Test (Real DB)

```python
@pytest.mark.integration
async def test_project_repository(db_session):
    repo = ProjectRepositoryImpl(db_session)
    entity = ProjectEntity.create(...)

    saved = await repo.save(entity)

    assert saved.id is not None
    found = await repo.find_by_id(saved.id)
    assert found.name == entity.name
```

### E2E Test

```python
@pytest.mark.e2e
async def test_create_project_e2e(client, admin_token):
    response = await client.post(
        "/v1/projects",
        json={"name": "Test Project", ...},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
```

---

## 🔐 Environment Variables

```bash
# Required
APP_ENV=local                    # local, dev, container, prod, test
SECRET_KEY=<32+ chars>          # JWT secret (CRITICAL)
POSTGRES_PASSWORD=<strong>      # Database password

# Database
POSTGRES_USER=open-projects-hub-admin
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=open-projects-hub-db

# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT_JSON=true            # true for structured JSON logs

# CORS
CORS_ORIGINS=https://app.yourdomain.com
CORS_ALLOW_CREDENTIALS=true
```

---

## 🎯 Common Patterns

### DTO with Validation

```python
class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=2, max_length=20)
    client_id: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if not value.isalnum():
            raise ValueError("Code must be alphanumeric")
        return value.upper()
```

### Entity with Domain Logic

```python
@dataclass
class ProjectEntity:
    id: EntityId
    name: str
    code: str
    status: ProjectStatus
    created_at: datetime

    @classmethod
    def create(cls, name: str, code: str, client_id: str) -> "ProjectEntity":
        ProjectValidators.validate_name(name)
        ProjectValidators.validate_code(code)
        return cls(
            id=EntityId.generate(),
            name=name,
            code=code,
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )

    def archive(self) -> None:
        self.status = ProjectStatus.ARCHIVED
```

### Repository Interface

```python
class ProjectRepository(ABC):
    @abstractmethod
    async def save(self, project: ProjectEntity) -> ProjectEntity:
        pass

    @abstractmethod
    async def find_by_id(self, project_id: str) -> Optional[ProjectEntity]:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> Optional[ProjectEntity]:
        pass
```

### Repository Implementation

```python
class ProjectRepositoryImpl(ProjectRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, project: ProjectEntity) -> ProjectEntity:
        model = ProjectMapper.to_model(project)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return ProjectMapper.to_entity(model)

    async def find_by_id(self, project_id: str) -> Optional[ProjectEntity]:
        result = await self.session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        model = result.scalar_one_or_none()
        return ProjectMapper.to_entity(model) if model else None
```

### Infrastructure Mapper (Model ↔ Entity)

```python
class ProjectMapper:
    """Maps between ProjectEntity and ProjectModel."""

    @staticmethod
    def to_entity(model: ProjectModel) -> ProjectEntity:
        return ProjectEntity(
            id=EntityId(model.id),
            name=model.name,
            code=model.code,
            # ...
        )

    @staticmethod
    def to_model(entity: ProjectEntity) -> ProjectModel:
        return ProjectModel(
            id=entity.id.value,
            name=entity.name,
            code=entity.code,
            # ...
        )
```

### Application Mapper (Entity → DTO)

```python
def to_project_response(
    entity: ProjectEntity,
    client_name: str,
) -> ProjectResponse:
    return ProjectResponse(
        id=str(entity.id),
        name=entity.name,
        code=entity.code,
        clientName=client_name,
        # ...
    )
```

---

## 📋 Code Review Checklist

- [ ] Uses DTOs for use case parameters (not many individual params)
- [ ] Imports from `src.app.composition` (not feature dependencies)
- [ ] Uses explicit file-path imports (no `__init__.py` re-exports)
- [ ] Repository returns interface type, not implementation
- [ ] Routes pass DTOs directly to use cases
- [ ] Routes never construct DTOs inline — delegate to application mappers
- [ ] Use cases never construct DTOs inline — delegate to application mappers
- [ ] Models do NOT have `to_entity()` / `from_entity()` — use infrastructure mapper class
- [ ] DTOs do NOT have `from_entity()` classmethods — use application mapper function
- [ ] Infrastructure mappers are `XxxMapper` class with `@staticmethod` methods
- [ ] Application mappers are standalone `to_xxx_response()` functions
- [ ] Tests run and pass (`make test-unit`)
- [ ] Code formatted (`make format`)
- [ ] No linting errors (`make lint-fix`)
- [ ] Migration created if model changed

---

## 🐛 Troubleshooting

### Import Errors

```python
# If you see: ModuleNotFoundError: No module named 'src.app.features.projects.application.use_cases'
# Check: Are you using package-level imports? (not allowed in features/)
# Fix: Use full file-path imports

# ✅ Correct
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
```

### Database Connection

```bash
# Check database is running
docker compose ps postgres

# Check connection
docker compose exec postgres psql -U open-projects-hub-admin -d open-projects-hub-db -c "SELECT 1;"

# View logs
docker compose logs postgres
```

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

### Test Failures

```bash
# Run single test
pytest src/tests/unit/path/to/test_file.py::test_function_name -v

# Run with debugging
pytest src/tests/unit/path/to/test_file.py::test_function_name -v -s

# Clear cache and rerun
make clean && make test-unit
```

---

**Last Updated:** June 18, 2026
