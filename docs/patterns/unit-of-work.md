# Unit of Work Pattern Guide

## Overview

The Unit of Work (UoW) pattern provides transaction management across multiple repositories, ensuring atomicity for operations that span multiple aggregates. This implementation follows Martin Fowler's pattern definition and integrates seamlessly with our Clean Architecture design.

## Why Unit of Work?

### Problem It Solves

Without UoW, coordinating writes across multiple repositories is difficult:

```python
# ❌ Without UoW - No transaction boundary
async def delete_project(project_id: UUID):
    # Delete stories
    story_repo = StoryRepositoryImpl(session1)
    await story_repo.delete_by_project(project_id)
    
    # Delete project (what if this fails?)
    project_repo = ProjectRepositoryImpl(session2)
    await project_repo.delete(project_id)
    
    # Stories deleted but project still exists = inconsistent state!
```

With UoW, all operations succeed or fail together:

```python
# ✅ With UoW - Atomic transaction
async def delete_project(project_id: UUID, uow: UnitOfWork):
    async with uow:
        # Delete stories
        await uow.stories.delete_by_project(project_id)
        
        # Delete project
        await uow.projects.delete(project_id)
        
        # Commit together - atomic!
        await uow.commit()
```

### Benefits

1. **Atomicity**: All changes succeed or fail together
2. **Consistency**: No partial updates across aggregates
3. **Simplified error handling**: Automatic rollback on exceptions
4. **Clear transaction boundaries**: Explicit commit points
5. **Repository coordination**: Single session shared across repositories

## Architecture

### Layer Placement

```
src/app/shared/
├── domain/
│   └── unit_of_work.py              # Abstract UoW interface
└── infrastructure/
    └── unit_of_work_impl.py         # SQLAlchemy implementation

src/app/shared/presentation/
└── dependencies.py                   # FastAPI dependency provider
```

### Design Principles

- **Interface in Domain**: `UnitOfWork` is a domain abstraction
- **Implementation in Infrastructure**: `SqlAlchemyUnitOfWork` is infrastructure concern
- **Dependency Injection**: Provided via FastAPI dependencies
- **Repository Access**: Lazy-loaded repositories share transaction

## Usage Patterns

### 1. Basic Usage in Use Cases

```python
from src.app.shared.domain.unit_of_work import UnitOfWork

class CreateProjectWithStoriesUseCase:
    """Create project and initial stories atomically."""
    
    async def execute(
        self,
        project_name: str,
        story_titles: list[str],
        owner_id: UUID,
        uow: UnitOfWork,
    ) -> ProjectResponse:
        async with uow:
            # Create project
            project = ProjectEntity.create(
                name=project_name,
                owner_id=EntityId(owner_id),
                status=ProjectStatus.ACTIVE,
            )
            saved_project = await uow.projects.save(project)
            
            # Create stories
            for title in story_titles:
                story = StoryEntity.create(
                    title=title,
                    project_id=saved_project.id,
                    created_by=EntityId(owner_id),
                )
                await uow.stories.save(story)
            
            # Commit all changes atomically
            await uow.commit()
            
            return to_project_response(saved_project)
```

### 2. Using in FastAPI Routes

```python
from fastapi import Depends
from src.app.shared.presentation.dependencies import get_unit_of_work

@router.post("/projects/{project_id}/complete")
async def complete_project_with_stories(
    project_id: str,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Complete project and mark all stories as done."""
    async with uow:
        # Update project
        project = await uow.projects.find_by_id(UUID(project_id))
        if not project:
            raise HTTPException(404, "Project not found")
        
        project.complete()
        await uow.projects.save(project)
        
        # Update all stories
        stories = await uow.stories.find_all(
            project_id=UUID(project_id),
            limit=1000,
            offset=0,
        )
        for story in stories:
            story.mark_done()
            await uow.stories.save(story)
        
        # Atomic commit
        await uow.commit()
    
    return {"status": "completed"}
```

### 3. Error Handling and Rollback

```python
async def update_project_and_stories(
    project_id: UUID,
    updates: dict,
    uow: UnitOfWork,
):
    try:
        async with uow:
            # Update project
            project = await uow.projects.find_by_id(project_id)
            project.update(**updates)
            await uow.projects.save(project)
            
            # Update stories
            stories = await uow.stories.find_all(project_id=project_id)
            for story in stories:
                story.update_from_project(project)
                await uow.stories.save(story)
            
            # Validate business rules
            if not project.is_valid():
                raise ValidationError("Invalid project state")
            
            # Commit if validation passed
            await uow.commit()
            
    except ValidationError:
        # Automatic rollback on exception
        logger.warning("Validation failed, transaction rolled back")
        raise
    except Exception as e:
        # Any exception triggers rollback
        logger.error(f"Transaction failed: {e}")
        raise
```

### 4. Explicit Rollback

```python
async def conditional_update(
    project_id: UUID,
    user_id: UUID,
    uow: UnitOfWork,
):
    async with uow:
        project = await uow.projects.find_by_id(project_id)
        
        # Check permissions
        if project.owner_id != EntityId(user_id):
            # Explicit rollback before raising
            await uow.rollback()
            raise UnauthorizedError("Not project owner")
        
        # Continue with update
        project.update(...)
        await uow.projects.save(project)
        await uow.commit()
```

### 5. Complex Multi-Repository Operations

```python
async def reassign_all_stories(
    from_user_id: UUID,
    to_user_id: UUID,
    uow: UnitOfWork,
):
    """Reassign all stories from one user to another."""
    async with uow:
        # Verify both users exist
        from_user = await uow.users.find_by_id(from_user_id)
        to_user = await uow.users.find_by_id(to_user_id)
        
        if not from_user or not to_user:
            raise ValueError("User not found")
        
        # Find all stories assigned to from_user
        stories = await uow.stories.find_all(
            assigned_to=from_user_id,
            limit=1000,
            offset=0,
        )
        
        # Reassign each story
        for story in stories:
            story.assign_to(EntityId(to_user_id))
            await uow.stories.save(story)
        
        # Update user statistics (if tracked)
        from_user.assigned_count -= len(stories)
        to_user.assigned_count += len(stories)
        
        await uow.users.save(from_user)
        await uow.users.save(to_user)
        
        # Commit all changes atomically
        await uow.commit()
        
        return len(stories)
```

## Repository Access

UoW provides lazy-loaded repositories:

```python
async with uow:
    # Access repositories as properties
    project = await uow.projects.find_by_id(project_id)
    story = await uow.stories.find_by_id(story_id)
    user = await uow.users.find_by_email(email)
    prefs = await uow.user_preferences.find_by_user(user_id)
    
    # All repositories share the same session
    # Changes are visible across repositories within transaction
```

### Available Repositories

- `uow.projects` → `ProjectRepository`
- `uow.stories` → `StoryRepository`
- `uow.users` → `UserRepository`
- `uow.user_preferences` → `UserPreferencesRepository`

## Transaction Lifecycle

### 1. Start Transaction

```python
async with uow:
    # Transaction begins implicitly
```

### 2. Perform Operations

```python
    # All operations use shared session
    entity = await uow.projects.find_by_id(id)
    entity.update(...)
    await uow.projects.save(entity)
```

### 3. Commit or Rollback

```python
    # Explicit commit
    await uow.commit()  # Changes persisted
    
    # OR explicit rollback
    await uow.rollback()  # Changes discarded
    
    # OR automatic rollback on exception
    raise Exception()  # Triggers automatic rollback
```

### 4. Exit Context

```python
# Context manager ensures cleanup
```

## Best Practices

### ✅ Do

1. **Always use context manager**
   ```python
   async with uow:
       # Your code here
       await uow.commit()
   ```

2. **Explicit commit**
   ```python
   # Always call commit() explicitly
   await uow.commit()
   ```

3. **Single UoW per request**
   ```python
   # One UoW instance per HTTP request or use case
   uow = Depends(get_unit_of_work)
   ```

4. **Handle exceptions**
   ```python
   try:
       async with uow:
           # operations
           await uow.commit()
   except Exception as e:
       logger.error(f"Transaction failed: {e}")
       raise
   ```

5. **Keep transactions short**
   ```python
   # Minimize time between start and commit
   async with uow:
       # Quick operations only
       await uow.commit()
   ```

### ❌ Don't

1. **Don't forget to commit**
   ```python
   # ❌ Missing commit - will rollback!
   async with uow:
       await uow.projects.save(project)
       # Forgot await uow.commit()
   ```

2. **Don't nest UoW instances**
   ```python
   # ❌ Nested UoW not supported
   async with uow1:
       async with uow2:  # Don't do this!
           pass
   ```

3. **Don't mix UoW and direct repositories**
   ```python
   # ❌ Don't mix approaches
   async with uow:
       await uow.projects.save(project)
       
       # Don't use separate repo instance
       separate_repo = StoryRepositoryImpl(different_session)
       await separate_repo.save(story)  # Different transaction!
   ```

4. **Don't reuse UoW after commit**
   ```python
   # ❌ Don't reuse after commit
   async with uow:
       await uow.commit()
       # UoW is done, don't use again
       await uow.projects.save(project)  # Error!
   ```

5. **Don't hold transactions open too long**
   ```python
   # ❌ Don't do expensive operations in transaction
   async with uow:
       await uow.projects.save(project)
       
       # Don't call external APIs, send emails, etc.
       await send_email(...)  # Do this AFTER commit
       
       await uow.commit()
   ```

## Testing

### Unit Tests with Mock Session

```python
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

async def test_use_case_with_uow():
    # Create mock session
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    
    # Create UoW with mock
    uow = SqlAlchemyUnitOfWork(mock_session)
    
    # Test use case
    async with uow:
        # ... test operations
        await uow.commit()
    
    # Verify
    mock_session.commit.assert_called_once()
```

### Integration Tests with Real Database

```python
@pytest.mark.e2e
async def test_atomic_transaction(db_session: AsyncSession):
    uow = SqlAlchemyUnitOfWork(db_session)
    
    async with uow:
        # Create entities
        project = await uow.projects.save(project_entity)
        story = await uow.stories.save(story_entity)
        
        # Commit
        await uow.commit()
    
    # Verify persistence
    async with uow:
        found_project = await uow.projects.find_by_id(project.id)
        assert found_project is not None
```

## Migration Guide

### Migrating Existing Use Cases

**Before (without UoW):**
```python
class UpdateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo
    
    async def execute(self, project_id: UUID, name: str):
        project = await self._project_repo.find_by_id(project_id)
        project.name = name
        return await self._project_repo.save(project)
```

**After (with UoW):**
```python
class UpdateProjectUseCase:
    async def execute(
        self,
        project_id: UUID,
        name: str,
        uow: UnitOfWork,
    ):
        async with uow:
            project = await uow.projects.find_by_id(project_id)
            project.name = name
            saved = await uow.projects.save(project)
            await uow.commit()
            return saved
```

### When to Use UoW vs Direct Repository

**Use UoW when:**
- ✅ Operations span multiple aggregates/repositories
- ✅ Need atomicity across multiple writes
- ✅ Complex business transactions
- ✅ Coordinated updates required

**Use direct repository when:**
- ✅ Single repository operations
- ✅ Read-only queries
- ✅ Simple CRUD operations
- ✅ No need for transaction coordination

## Performance Considerations

### Connection Pool Usage

UoW uses the existing connection pool:
- One connection per request
- Session lifecycle managed by context manager
- Automatic cleanup on exit

### Transaction Duration

Keep transactions short:
```python
# ✅ Good - short transaction
async with uow:
    project = await uow.projects.find_by_id(id)
    project.complete()
    await uow.projects.save(project)
    await uow.commit()

# Expensive operations AFTER commit
await send_email(project.owner)
await notify_users(project.id)
```

### Lazy Loading Optimization

Repositories are lazy-loaded:
```python
async with uow:
    # Only creates repository when accessed
    project = await uow.projects.find_by_id(id)
    
    # Stories repo only created if needed
    if project.needs_story_update:
        stories = await uow.stories.find_all(project_id=id)
```

## Troubleshooting

### Common Issues

#### 1. "Transaction already committed"

**Cause**: Attempting to commit twice

**Solution**: Call commit() only once per context
```python
async with uow:
    # operations
    await uow.commit()  # ✅ Once
    # await uow.commit()  # ❌ Don't call again
```

#### 2. "Changes not persisted"

**Cause**: Forgot to call commit()

**Solution**: Always explicitly commit
```python
async with uow:
    await uow.projects.save(project)
    await uow.commit()  # ✅ Don't forget!
```

#### 3. "Foreign key constraint violation"

**Cause**: Saving entities in wrong order

**Solution**: Save referenced entities first
```python
async with uow:
    # Save project first
    project = await uow.projects.save(project)
    
    # Then save story (references project)
    story.project_id = project.id
    await uow.stories.save(story)
    
    await uow.commit()
```

## Future Enhancements

### Planned Improvements

1. **Distributed Transactions**: Support for multi-database UoW
2. **Event Publishing**: Integrate with domain events
3. **Saga Pattern**: Long-running transaction coordination
4. **Read/Write Split**: Separate UoW for read vs write operations
5. **Metrics**: Transaction duration and success rate tracking

## References

- **Pattern Source**: Martin Fowler's "Patterns of Enterprise Application Architecture"
- **Implementation**: `src/app/shared/domain/unit_of_work.py`
- **Tests**: `src/tests/infrastructure/unit_of_work/`
- **Architecture Review**: `docs/evaluation/26-05-10/architecture-review.md`

---

**Created**: 2026-05-11  
**Status**: Production Ready  
**Coverage**: 23 unit tests, 11 integration tests
