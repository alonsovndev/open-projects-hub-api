# Common Tasks

Step-by-step guides for common development tasks in this repository.

---

## 🆕 Add a New Endpoint

### Scenario: Add `GET /v1/projects/{project_id}/stats` endpoint

**1. Create DTO (if needed):**

```python
# src/app/features/projects/application/dtos/project_dto.py

class ProjectStatsResponse(BaseModel):
    """Response model for project statistics."""
    project_id: str
    total_stories: int
    completed_stories: int
    in_progress_stories: int
    completion_rate: float

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
```

**2. Create Use Case:**

```python
# src/app/features/projects/application/use_cases/get_project_stats.py

from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.repositories.story_repository import StoryRepository

class GetProjectStatsUseCase:
    def __init__(
        self,
        project_repository: ProjectRepository,
        story_repository: StoryRepository,
    ):
        self.project_repo = project_repository
        self.story_repo = story_repository

    async def execute(self, project_id: str) -> ProjectStatsResponse:
        # Verify project exists
        project = await self.project_repo.find_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        # Get story counts
        stories = await self.story_repo.find_by_project(project_id)
        total = len(stories)
        completed = sum(1 for s in stories if s.status == StoryStatus.DONE)
        in_progress = sum(1 for s in stories if s.status == StoryStatus.IN_PROGRESS)

        return ProjectStatsResponse(
            project_id=str(project_id),
            total_stories=total,
            completed_stories=completed,
            in_progress_stories=in_progress,
            completion_rate=completed / total if total > 0 else 0.0,
        )
```

**3. Add to Composition Root:**

```python
# src/app/composition/features/projects.py

from src.app.features.projects.application.use_cases.get_project_stats import GetProjectStatsUseCase

def get_project_stats_use_case(
    project_repo: ProjectRepository = Depends(get_project_repository),
    story_repo: StoryRepository = Depends(get_story_repository),
) -> GetProjectStatsUseCase:
    """Get project stats use case factory."""
    return GetProjectStatsUseCase(
        project_repository=project_repo,
        story_repository=story_repo,
    )
```

**4. Export from Composition:**

```python
# src/app/composition/__init__.py

from .features.projects import (
    # ... existing exports
    get_project_stats_use_case,
)

__all__ = [
    # ... existing exports
    "get_project_stats_use_case",
]
```

**5. Add Route:**

```python
# src/app/features/projects/presentation/project_routes.py

from src.app.composition import get_project_stats_use_case
from src.app.features.projects.application.use_cases.get_project_stats import GetProjectStatsUseCase

@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    project_id: str,
    current_user: dict = Depends(verify_jwt_token),
    use_case: GetProjectStatsUseCase = Depends(get_project_stats_use_case),
) -> ProjectStatsResponse:
    """Get project statistics (story counts, completion rate)."""
    return await use_case.execute(project_id=project_id)
```

**6. Test:**

```bash
# Unit test (mock repositories)
pytest src/tests/unit/application/use_cases/test_get_project_stats.py -v

# E2E test
pytest src/tests/e2e/test_project_stats.py -v
```

---

## 🗃️ Add a New Database Field

### Scenario: Add `description` field to Project

**1. Update Entity:**

```python
# src/app/features/projects/domain/entities/project_entity.py

@dataclass
class ProjectEntity:
    id: EntityId
    name: str
    code: str
    description: Optional[str]  # NEW
    # ... other fields

    @classmethod
    def create(cls, name: str, code: str, description: Optional[str] = None, ...) -> "ProjectEntity":
        return cls(
            id=EntityId.generate(),
            name=name,
            code=code,
            description=description,  # NEW
            # ... other fields
        )

    def update_details(self, name: str, description: Optional[str] = None) -> None:
        ProjectValidators.validate_name(name)
        self._name = name
        self._description = description  # NEW
```

**2. Update Model:**

```python
# src/app/features/projects/infrastructure/models/project_model.py

class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)  # NEW
    # ... other columns

    def to_entity(self) -> ProjectEntity:
        return ProjectEntity(
            id=EntityId(self.id),
            name=self.name,
            code=self.code,
            description=self.description,  # NEW
            # ... other fields
        )

    @classmethod
    def from_entity(cls, entity: ProjectEntity) -> "ProjectModel":
        return cls(
            id=str(entity.id),
            name=entity.name,
            code=entity.code,
            description=entity.description,  # NEW
            # ... other fields
        )
```

**3. Update DTOs:**

```python
# src/app/features/projects/application/dtos/project_dto.py

class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=2, max_length=20)
    description: Optional[str] = Field(None, max_length=1000)  # NEW
    client_id: str

class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)  # NEW

class ProjectResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]  # NEW
    # ... other fields

    @classmethod
    def from_entity(cls, entity: ProjectEntity, client_name: str) -> "ProjectResponse":
        return cls(
            id=str(entity.id),
            name=entity.name,
            code=entity.code,
            description=entity.description,  # NEW
            # ... other fields
        )
```

**4. Create Migration:**

```bash
alembic revision --autogenerate -m "Add description field to projects"
```

**5. Review Migration:**

```python
# alembic/versions/xxxx_add_description_field_to_projects.py

def upgrade() -> None:
    op.add_column('projects', sa.Column('description', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('projects', 'description')
```

**6. Apply Migration:**

```bash
alembic upgrade head
```

**7. Update Tests:**

```python
# Update fixtures, assertions to include description
```

**8. Verify:**

```bash
make test-unit
make test-integration
```

---

## 🔄 Add a New Repository Method

### Scenario: Add `find_active_by_client` to ProjectRepository

**1. Add to Interface:**

```python
# src/app/features/projects/domain/repositories/project_repository.py

class ProjectRepository(ABC):
    # ... existing methods

    @abstractmethod
    async def find_active_by_client(self, client_id: str) -> List[ProjectEntity]:
        """Find all active projects for a client."""
        pass
```

**2. Implement:**

```python
# src/app/features/projects/infrastructure/repositories/project_repository_impl.py

async def find_active_by_client(self, client_id: str) -> List[ProjectEntity]:
    """Find all active projects for a client."""
    result = await self.session.execute(
        select(ProjectModel)
        .where(ProjectModel.client_id == client_id)
        .where(ProjectModel.status == ProjectStatus.ACTIVE.value)
        .order_by(ProjectModel.created_at.desc())
    )
    models = result.scalars().all()
    return [model.to_entity() for model in models]
```

**3. Test:**

```python
# src/tests/integration/infrastructure/repositories/test_project_repository.py

@pytest.mark.integration
async def test_find_active_by_client(db_session):
    repo = ProjectRepositoryImpl(db_session)

    # Create test data
    client_id = "client-123"
    active = ProjectEntity.create(name="Active", code="ACT", client_id=client_id)
    archived = ProjectEntity.create(name="Archived", code="ARC", client_id=client_id)
    archived.archive()

    await repo.save(active)
    await repo.save(archived)

    # Test
    results = await repo.find_active_by_client(client_id)

    assert len(results) == 1
    assert results[0].code == "ACT"
```

---

## 🧪 Add Tests for Existing Code

### Unit Test (Use Case)

```python
# src/tests/unit/application/use_cases/test_create_project.py

import pytest
from unittest.mock import AsyncMock

from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.application.dtos.project_dto import CreateProjectRequest

@pytest.mark.asyncio
async def test_create_project_success():
    # Arrange
    mock_project_repo = AsyncMock()
    mock_client_repo = AsyncMock()
    mock_ai_service = AsyncMock()

    mock_client_repo.find_by_id.return_value = mock_client_entity
    mock_project_repo.save.return_value = mock_project_entity

    use_case = CreateProjectUseCase(
        project_repository=mock_project_repo,
        client_repository=mock_client_repo,
        ai_service=mock_ai_service,
    )

    request = CreateProjectRequest(
        name="Test Project",
        code="TEST",
        client_id="client-123",
    )

    # Act
    result = await use_case.execute(request=request, created_by="user-456")

    # Assert
    assert result.name == "Test Project"
    mock_client_repo.find_by_id.assert_called_once_with("client-123")
    mock_project_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_create_project_client_not_found():
    # Arrange
    mock_project_repo = AsyncMock()
    mock_client_repo = AsyncMock()
    mock_ai_service = AsyncMock()

    mock_client_repo.find_by_id.return_value = None  # Client doesn't exist

    use_case = CreateProjectUseCase(...)
    request = CreateProjectRequest(...)

    # Act & Assert
    with pytest.raises(ClientNotFoundError):
        await use_case.execute(request=request, created_by="user-456")
```

### Integration Test (Repository)

```python
# src/tests/integration/infrastructure/repositories/test_project_repository.py

import pytest
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.features.projects.domain.entities.project_entity import ProjectEntity

@pytest.mark.integration
async def test_save_and_find_project(db_session):
    # Arrange
    repo = ProjectRepositoryImpl(db_session)
    entity = ProjectEntity.create(
        name="Integration Test Project",
        code="INTEG",
        client_id="client-123",
    )

    # Act - Save
    saved = await repo.save(entity)
    await db_session.commit()

    # Act - Find
    found = await repo.find_by_id(str(saved.id))

    # Assert
    assert found is not None
    assert found.name == "Integration Test Project"
    assert found.code == "INTEG"
```

### E2E Test (API)

```python
# src/tests/e2e/test_projects.py

import pytest

@pytest.mark.e2e
async def test_create_project_e2e(async_client, admin_token):
    # Act
    response = await async_client.post(
        "/v1/projects",
        json={
            "name": "E2E Test Project",
            "code": "E2E",
            "clientId": "test-client-id",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "E2E Test Project"
    assert data["code"] == "E2E"
    assert "id" in data
```

---

## 🔐 Add Authorization Check

### Scenario: Only project owner or admin can delete project

**1. Create Authorization Function:**

```python
# src/app/features/projects/presentation/auth_checks.py

from fastapi import HTTPException, status
from src.app.composition import get_project_repository, get_database_session

async def verify_project_ownership(
    project_id: str,
    current_user: dict,
) -> None:
    """Verify user owns project or is admin."""
    user_id = current_user.get("sub")
    user_role = current_user.get("role")

    # Admin can access any project
    if user_role == "admin":
        return

    # Check ownership
    async for session in get_database_session():
        from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
        repo = ProjectRepositoryImpl(session)
        project = await repo.find_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if str(project.created_by) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this project"
            )
```

**2. Use in Route:**

```python
# src/app/features/projects/presentation/project_routes.py

from src.app.features.projects.presentation.auth_checks import verify_project_ownership

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(verify_jwt_token),
    use_case = Depends(get_delete_project_use_case),
) -> None:
    """Delete a project (owner or admin only)."""
    await verify_project_ownership(project_id, current_user)
    await use_case.execute(project_id=project_id)
```

---

## 📊 Update API Documentation

**After adding/modifying endpoints:**

1. **Update API Contract:**

```markdown
<!-- docs/api/api-contract.md -->

| Method | Path | Authentication | Description |
|---|---|---|---|
| `GET` | `/v1/projects/{project_id}/stats` | Authenticated | Get project statistics |
```

2. **Update README if needed:**

```markdown
<!-- docs/api/README.md -->

### New Endpoints

#### Get Project Statistics

`GET /v1/projects/{project_id}/stats`

Returns story counts and completion rate for a project.

**Response:**
\`\`\`json
{
  "projectId": "123",
  "totalStories": 20,
  "completedStories": 15,
  "inProgressStories": 3,
  "completionRate": 0.75
}
\`\`\`
```

---

## 🐛 Debug Common Issues

### Issue: Import Error

```
ModuleNotFoundError: No module named 'src.app.features.projects.application.use_cases'
```

**Cause:** Trying to import from package (no `__init__.py` in features/)

**Fix:** Use full file-path imports

```python
# ❌ Wrong
from src.app.features.projects.application.use_cases import CreateProjectUseCase

# ✅ Correct
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
```

### Issue: Circular Import

```
ImportError: cannot import name 'X' from partially initialized module
```

**Cause:** Two modules importing each other at module level

**Fix:** Use lazy imports in composition root

```python
# In factory function
def get_use_case():
    from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
    return CreateProjectUseCase(...)
```

### Issue: Test Database Not Found

```
sqlalchemy.exc.OperationalError: database "test_db" does not exist
```

**Fix:** Ensure PostgreSQL is running and test database exists

```bash
docker compose up postgres -d
docker compose exec postgres createdb -U open-projects-hub-admin open-projects-hub-test-db
```

---

**Last Updated:** June 11, 2026
