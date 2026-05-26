# ADR-004: Dependency Inversion for Repositories

**Status**: Accepted  
**Date**: 2026-05-21  
**Decision Makers**: Solo developer  
**Affected Components**: `src/app/features/*/presentation/dependencies.py`, `src/app/features/*/infrastructure/repositories/`

---

## Context

Dependency injection functions were returning concrete implementations instead of interfaces:

```python
# Returning concrete implementation
async def get_project_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ProjectRepositoryImpl:  # Concrete type
    return ProjectRepositoryImpl(session)
```

This led to:
- Tight coupling between use cases and specific implementations
- Difficulty mocking repositories in tests (must mock concrete class)
- Violation of the Dependency Inversion Principle (SOLID)
- Inability to swap implementations (e.g., for caching, different databases)

---

## Decision

**All dependency injection functions return interfaces (ABC) not concrete implementations.**

Specifically:
- Repository interfaces are defined as `ABC` classes in the domain layer
- Dependency functions return the interface type
- Use cases accept the interface type in their constructors
- Concrete implementations are created inside the dependency function

### Implementation

```python
# Interface defined in domain layer
class ProjectRepository(ABC):
    @abstractmethod
    async def create(self, entity: ProjectEntity) -> ProjectEntity:
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: EntityId) -> Optional[ProjectEntity]:
        pass

# Dependency function returns interface
async def get_project_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ProjectRepository:  # Interface type
    return ProjectRepositoryImpl(session)

# Use case accepts interface
class CreateProjectUseCase:
    def __init__(self, repository: ProjectRepository):  # Interface, not impl
        self.repository = repository
```

---

## Consequences

### Positive

✅ **SOLID compliance**: Follows Dependency Inversion Principle  
✅ **Easier testing**: Mock interfaces instead of concrete classes  
✅ **Implementation swapping**: Can swap implementations without changing use cases  
✅ **Clear contracts**: Interface defines the expected behavior  
✅ **Decoupled layers**: Application layer depends on abstractions  

### Negative

⚠️ **Boilerplate**: Must maintain both interface and implementation  
⚠️ **Indirection**: One more layer to navigate when debugging  

### Accepted Trade-offs

- **Boilerplate** → **Testability and flexibility**
- **Indirection** → **Clean architecture boundaries**

---

## Alternatives Considered

### Option A: Concrete Returns (PREVIOUS)
- **Effort**: Already existed
- **Testability**: Poor (must mock concrete class)
- **Best for**: Prototypes, single-implementation systems

### Option B: Factory Pattern
- **Effort**: 2-3 hours
- **Testability**: Good
- **Best for**: Multiple implementations selected at runtime

### Option C: Protocol Classes (Python typing.Protocol)
- **Effort**: 1-2 hours
- **Testability**: Good
- **Best for**: Structural subtyping without inheritance

### Option D: ABC Interfaces (CHOSEN)
- **Effort**: Already implemented
- **Testability**: Excellent (clear contracts)
- **Best for**: Explicit contracts with enforced method signatures

---

## When to Revisit

Reconsider this decision if:

1. **Single implementation forever**: Feature will never have alternative implementations
2. **Performance critical**: Interface dispatch overhead becomes measurable (unlikely in Python)
3. **Simple CRUD**: Feature has trivial persistence needs

---

## References

- SOLID Principles: Dependency Inversion Principle (DIP)
- Clean Architecture: Dependencies point inward toward domain
- Python ABC: `abc.ABC` and `@abstractmethod`
- Related code: `src/app/features/*/domain/repositories/` (interfaces)
- Related code: `src/app/features/*/infrastructure/repositories/` (implementations)

---

## Notes

This pattern ensures:
- **Testability**: Easy to mock with `MagicMock(spec=ProjectRepository)`
- **Flexibility**: Can add caching, logging, or alternative storage
- **Clarity**: Interface documents the contract explicitly
- **Safety**: ABC enforces implementation of all abstract methods
