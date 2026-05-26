# Engineering Documentation

Comprehensive documentation covering the architecture, design principles, patterns, and best practices used in the Open Projects Hub API.

## 📁 Directory Structure

```
docs/engineering/
├── README.md                    # This file - index
├── clean-architecture.md        # Layered architecture explanation
├── composition-root.md          # Dependency injection and composition root
├── ddd-patterns.md              # Domain-Driven Design patterns
├── design-principles.md         # SOLID, DRY, YAGNI, KISS
└── async-patterns.md            # Async/await patterns
```

## 🏗️ Architecture Overview

### Clean Architecture with DDD

The project follows **Clean Architecture** principles combined with **Domain-Driven Design (DDD)** patterns:

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│  (FastAPI routes, request/response DTOs, deps)       │
├─────────────────────────────────────────────────────┤
│                  Application Layer                   │
│  (Use cases, application DTOs, business orchestration)│
├─────────────────────────────────────────────────────┤
│                   Domain Layer                       │
│  (Entities, value objects, domain events, interfaces)│
├─────────────────────────────────────────────────────┤
│               Infrastructure Layer                   │
│  (DB repos, JWT handler, password hashing, config)   │
└─────────────────────────────────────────────────────┘
```

**Dependency Rule:** Inner layers know nothing about outer layers. Outer layers depend on inner layers.

### Key Benefits

- **Testability:** Domain and application layers are framework-independent
- **Maintainability:** Changes to infrastructure don't affect business logic
- **Flexibility:** Easy to swap implementations (e.g., database, auth provider)
- **Clarity:** Clear separation of concerns across layers

## 📚 Core Concepts

| Concept | Description | Document |
|---------|-------------|----------|
| **Clean Architecture** | Layered architecture with dependency inversion | [Clean Architecture](./clean-architecture.md) |
| **Composition Root** | Centralized dependency injection container | [Composition Root](./composition-root.md) |
| **Domain-Driven Design** | Ubiquitous language, bounded contexts, rich domain models | [DDD Patterns](./ddd-patterns.md) |
| **SOLID Principles** | Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion | [Design Principles](./design-principles.md) |
| **Async/Await** | Non-blocking I/O for high concurrency | [Async Patterns](./async-patterns.md) |

## 🎯 Design Principles

### Applied Principles

1.  **YAGNI (You Aren't Gonna Need It)**
    - Removed unnecessary service layer
    - No premature abstraction

2.  **KISS (Keep It Simple, Stupid)**
    - Direct use case injection
    - Minimal configuration overhead

3.  **DRY (Don't Repeat Yourself)**
    - Base models for common fields
    - Shared value objects
    - Reusable dependencies

4.  **Fail Fast**
    - JWT secret validation at startup
    - Configuration validation on load
    - Type checking throughout

---

## ✅ Clean Code Practices

### Use Case Design

Follow the **Command Pattern with DTOs**:
- Use case methods should accept DTOs (e.g., `CreateProjectRequest`) rather than many individual parameters.
- Keep context parameters separate (e.g., `created_by: str` from JWT token).
- Aim for a maximum of 2-3 parameters per use case method (typically: DTO + context).

**Parameter Naming Conventions:**
- Use `request` for input DTOs (matches `XxxRequest` type name).
- Use explicit ID names: `project_id`, `user_id`, `story_id` (not generic `id`).
- Use `created_by` for actor context from authentication.

**Example (Good):**
```python
async def execute(self, request: CreateProjectRequest, created_by: str) -> ProjectResponse:
    pass
```

### Route Handler Patterns

**Pass DTOs directly to use cases:**
```python
# ✅ Good - pass DTO directly
use_case.execute(request=payload, created_by=user_id)
```

### Variable Naming

- Use self-documenting names that match their type or purpose.
- Avoid generic names like `command`, `data`, `tmp`, `val`.
- Match DTO type names: `CreateProjectRequest` → `request`.
- Be explicit with IDs and context variables.

### Validation Patterns

**Use shared validators directly, not wrapper methods:**

```python
# ✅ Good - Direct call to shared validators
class ProjectEntity:
    def update_details(self, name: str):
        ProjectValidators.validate_name(name)
        self._name = name
```
**Why:** Wrappers add no value, bloat code, and obscure intent. Call validators directly.
**Reference:** See `src/app/features/projects/domain/validators/project_validators.py` for centralized validation.

---

## 🤝 API Contract Rules

- Keep endpoint versioning under `/v1` as defined by router prefixes in `src/app/shared/presentation/router_registry.py`.
- Align route updates with docs in `docs/api/README.md` when paths or auth requirements change.
- DTOs use `camelCase` for JSON (Pydantic `alias_generator=to_camel`) but Python code uses `snake_case`.
- **See also:** [API Documentation](../api/README.md) for more details on API contracts.

---

## 🔄 Refactoring Guidelines

### When Refactoring Use Cases

1.  **Check parameter count** - If > 4 parameters, refactor to use DTO.
2.  **Use existing DTOs** - Most features have `CreateXxxRequest` and `UpdateXxxRequest` DTOs.
3.  **Keep context separate** - Authentication/authorization context stays as separate parameters.
4.  **Update routes** - Change route handlers to pass DTOs directly (no unpacking).
5.  **Update tests** - Modify test fixtures to create DTOs instead of passing individual parameters.
6.  **Verify** - Run `make test-unit` to ensure no regressions.

### Repository Pattern Consistency

- All repositories use plain `ABC` with explicit methods (no `BaseRepository`).
- Return types should match domain needs (e.g., `Tuple[ProjectEntity, str]` for project + client name).
- Repository methods use domain entities, not DTOs or models directly.

### Mapper Location

- Mappers live in feature's `application/mappers/` directory (not `shared/`).
- Mappers convert between domain entities and application DTOs.
- Keep mappers close to the DTOs they work with.


