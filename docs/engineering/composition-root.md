# Composition Root Pattern

## Overview

The **Composition Root** is a centralized location where all application dependencies are wired together. It's the single place where concrete implementations are bound to their abstractions.

## Why Composition Root?

### Problems It Solves

❌ **Before (scattered dependencies):**
- 8 separate `dependencies.py` files across features
- Duplicate repository factories
- Inconsistent dependency patterns
- Hard to trace where dependencies come from
- Difficult to maintain

✅ **After (composition root):**
- Single source of truth for all dependencies
- Consistent factory pattern
- Easy to find and understand dependencies
- Simple to add new features
- Clear dependency hierarchy

### Architecture Benefits

1. **Dependency Inversion Principle (SOLID)**
   - Routes depend on abstractions (interfaces), not implementations
   - Business logic is decoupled from infrastructure

2. **Single Responsibility**
   - Composition logic is separate from business logic
   - Each module has one clear purpose

3. **Testability**
   - Easy to mock dependencies at composition level
   - Tests can override specific factories

4. **Maintainability**
   - Adding features follows clear pattern
   - Dependencies are explicitly documented

## Structure

```
src/app/composition/
├── __init__.py              # 🌟 Public API (40+ exports)
├── infrastructure.py        # Database session, AI service
├── repositories.py          # Shared repositories (User, Story, Client)
├── features/
│   ├── auth.py             # Login, Register, Refresh Token
│   ├── clients.py          # Client CRUD use cases
│   ├── dashboard.py        # Dashboard stats
│   ├── projects.py         # Project CRUD + AI generation
│   ├── refinement.py       # Story refinement
│   ├── stories.py          # Story CRUD + lifecycle
│   └── users.py            # User CRUD
├── core.py                 # Cross-cutting services (future)
└── config.py               # Configuration DI (future)
```

## Dependency Hierarchy

The composition root enforces clear dependency levels:

```
Level 1: Infrastructure
  ├── get_database_session()
  └── get_ai_service()

Level 2: Shared Repositories
  ├── get_user_repository()
  ├── get_story_repository()
  └── get_client_repository()

Level 3: Feature Repositories
  ├── get_project_repository()
  └── (feature-specific repos)

Level 4: Use Cases
  ├── get_create_project_use_case()
  ├── get_login_use_case()
  └── (all feature use cases)
```

## Usage Patterns

### 1. In Route Handlers

```python
# ✅ Import from composition root
from src.app.composition import (
    get_database_session,
    get_create_project_use_case,
)

router = APIRouter()

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    payload: CreateProjectRequest,
    current_user: dict = Depends(verify_jwt_token),
    use_case: CreateProjectUseCase = Depends(get_create_project_use_case),
) -> ProjectResponse:
    """Create a new project."""
    user_id = current_user.get("sub")
    return await use_case.execute(request=payload, created_by=user_id)
```

### 2. Direct Repository Access

Sometimes routes need direct database access for authorization checks:

```python
from src.app.composition import get_database_session
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl

async def check_story_ownership(story_id: str, user_id: str):
    """Check if user owns the story."""
    async for session in get_database_session():
        story_repo = StoryRepositoryImpl(session)
        story = await story_repo.find_by_id(story_id)
        return story.created_by.value == user_id
```

## Factory Patterns

### Infrastructure Factories

**Request-scoped dependencies:**
```python
# Database session - new session per request
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (request-scoped)."""
    async with get_db_session_context() as session:
        yield session
```

**Singleton dependencies:**
```python
# AI service - shared across requests
_ai_service_instance: Optional[AIService] = None

def get_ai_service() -> AIService:
    """Get AI service instance (singleton, thread-safe)."""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance
```

### Repository Factories

**Always return interface types:**
```python
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository

def get_project_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ProjectRepository:  # ← Interface type
    """Get project repository instance."""
    # Lazy import to avoid circular dependencies
    from src.app.features.projects.infrastructure.repositories.project_repository_impl import (
        ProjectRepositoryImpl,
    )
    return ProjectRepositoryImpl(session)
```

**Why lazy imports?**
- Avoids circular dependencies
- Reduces startup time (imports only when needed)
- Keeps module-level imports clean

### Use Case Factories

```python
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase

def get_create_project_use_case(
    project_repo: ProjectRepository = Depends(get_project_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    ai_service: AIService = Depends(get_ai_service),
) -> CreateProjectUseCase:
    """Get create project use case with all dependencies."""
    return CreateProjectUseCase(
        project_repository=project_repo,
        client_repository=client_repo,
        ai_service=ai_service,
    )
```

## Adding New Dependencies

### Step 1: Create Factory Function

Choose the appropriate module:
- Infrastructure dependency → `infrastructure.py`
- Shared repository → `repositories.py`
- Feature-specific → `features/<feature_name>.py`

```python
# In composition/features/projects.py

def get_update_project_use_case(
    project_repo: ProjectRepository = Depends(get_project_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
) -> UpdateProjectUseCase:
    """Get update project use case."""
    from src.app.features.projects.application.use_cases.update_project import UpdateProjectUseCase
    return UpdateProjectUseCase(
        project_repository=project_repo,
        client_repository=client_repo,
    )
```

### Step 2: Export from Public API

Add to `composition/__init__.py`:

```python
# Feature: Projects
from .features.projects import (
    get_project_repository,
    get_create_project_use_case,
    get_update_project_use_case,  # ← Add new export
    # ... other project exports
)

__all__ = [
    # ... existing exports
    "get_update_project_use_case",  # ← Add to __all__
]
```

### Step 3: Use in Routes

```python
from src.app.composition import get_update_project_use_case

@router.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    payload: UpdateProjectRequest,
    use_case = Depends(get_update_project_use_case),
):
    return await use_case.execute(project_id=project_id, request=payload)
```

## Cross-Feature Dependencies

### Intentional Business Rules

Some features have legitimate cross-feature dependencies:

```python
# Projects validates client_id via ClientRepository
def get_create_project_use_case(
    project_repo: ProjectRepository = Depends(get_project_repository),
    client_repo: ClientRepository = Depends(get_client_repository),  # ← Cross-feature
    ai_service: AIService = Depends(get_ai_service),
) -> CreateProjectUseCase:
    """
    Get create project use case.
    
    Cross-feature dependency:
    - ClientRepository: Validates that client exists before creating project
    """
    return CreateProjectUseCase(...)
```

**Document why:**
- Is this a business rule? (e.g., project must belong to valid client)
- Could it be avoided? (e.g., move validation to shared layer)
- What's the tradeoff? (coupling vs. duplication)

## Testing with Composition Root

### Option 1: Mock Use Case Execution

Most tests mock at the use case level:

```python
from unittest.mock import AsyncMock, patch

@patch(
    "src.app.features.projects.application.use_cases.create_project.CreateProjectUseCase.execute",
    new=AsyncMock(return_value=mock_response),
)
async def test_create_project_success():
    response = await client.post("/v1/projects", json=payload)
    assert response.status_code == 201
```

**Benefit:** Tests don't depend on DI wiring.

### Option 2: Override Dependencies

For integration tests:

```python
from fastapi.testclient import TestClient
from src.app.app import fastApiApp
from src.app.composition import get_project_repository

def get_mock_project_repository():
    return MockProjectRepository()

# Override dependency
fastApiApp.dependency_overrides[get_project_repository] = get_mock_project_repository

client = TestClient(fastApiApp)
```

## Repository Usage Matrix

Track which features depend on which repositories:

| Repository       | Used By Features |
|------------------|------------------|
| UserRepository   | auth, user, dashboard |
| StoryRepository  | stories, refinement, dashboard |
| ClientRepository | clients, projects |
| ProjectRepository| projects |

**Use this to:**
- Identify highly coupled repositories (candidates for refactoring)
- Understand blast radius of repository changes
- Document intentional cross-feature dependencies

## Best Practices

### ✅ Do

1. **Return interface types from repository factories**
   ```python
   def get_repo() -> ProjectRepository:  # Interface
       return ProjectRepositoryImpl(...)
   ```

2. **Use lazy imports in factories**
   ```python
   def get_use_case():
       from .use_cases.create import CreateUseCase  # Lazy
       return CreateUseCase(...)
   ```

3. **Document cross-feature dependencies**
   ```python
   # Why: Projects must validate client exists (business rule)
   client_repo: ClientRepository = Depends(get_client_repository)
   ```

4. **Keep composition/__init__.py organized**
   - Group exports by category
   - Maintain alphabetical order within groups
   - Keep `__all__` list up to date

### ❌ Don't

1. **Don't import from feature `dependencies.py` (old pattern)**
   ```python
   # ❌ Bad
   from src.app.features.projects.presentation.dependencies import get_use_case
   
   # ✅ Good
   from src.app.composition import get_use_case
   ```

2. **Don't return concrete types**
   ```python
   # ❌ Bad
   def get_repo() -> ProjectRepositoryImpl:
   
   # ✅ Good
   def get_repo() -> ProjectRepository:
   ```

3. **Don't create circular dependencies**
   - Use lazy imports
   - Review dependency hierarchy
   - Consider extracting shared logic

4. **Don't bypass composition in routes**
   ```python
   # ❌ Bad - direct instantiation
   repo = ProjectRepositoryImpl(session)
   
   # ✅ Good - use factory
   repo = Depends(get_project_repository)
   ```

## Migration Guide

If you're updating old code that used scattered `dependencies.py` files:

### Before (Old Pattern)
```python
from src.app.features.projects.presentation.dependencies import (
    get_create_project_use_case,
    get_project_repository,
)
```

### After (Composition Root)
```python
from src.app.composition import (
    get_create_project_use_case,
    get_project_repository,
)
```

**That's it!** Just change the import. The factory functions themselves are unchanged.

## References

- [Clean Architecture](./clean-architecture.md) - Overall architecture patterns
- [DDD Patterns](./ddd-patterns.md) - Domain-driven design principles
- [Design Principles](./design-principles.md) - SOLID and other principles


## Real-World Example

See the complete implementation in:
- `src/app/composition/` - Full composition root

