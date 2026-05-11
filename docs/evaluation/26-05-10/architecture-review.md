# Architecture Review — 26-05-10

## Overview

This document assesses the architectural quality of the Open Projects Hub API, examining layer boundaries, dependency direction, module organisation, and adherence to the stated Clean Architecture / DDD design.

---

## Stated Architecture

The codebase follows **Clean Architecture** (Robert C. Martin) with four explicit layers:

```
Presentation → Application → Domain ← Infrastructure
```

Dependencies point inward. Outer layers depend on inner layers; inner layers expose interfaces that outer layers implement.

---

## Directory Structure

```
src/
├── main.py                          # Entry point (imports fastApiApp)
└── app/
    ├── app.py                       # FastAPI bootstrap, middleware, routers
    ├── config/                      # YAML-backed AppConfig singleton
    ├── shared/
    │   ├── domain/                  # Shared value objects (EntityId)
    │   ├── infrastructure/          # Database engine, JWT, password, rate limiter
    │   ├── presentation/            # Shared base handler, shared DI
    │   └── utils/                   # Logging, date, UUID helpers
    └── features/
        ├── user/
        │   ├── domain/              # UserEntity, Email VO, UserRole VO, repository interface
        │   ├── application/         # Use cases (login, register, create, update, password…)
        │   ├── infrastructure/      # UserRepositoryImpl, UserPrefsRepositoryImpl
        │   └── presentation/        # Auth routes, user routes, auth_dependencies, DI
        ├── projects/
        │   ├── domain/              # ProjectEntity, value objects, repository interface
        │   ├── application/         # CRUD use cases, DTOs
        │   ├── infrastructure/      # ProjectRepositoryImpl
        │   └── presentation/        # Project routes, DI
        ├── stories/
        │   ├── domain/              # StoryEntity, value objects, repository interface
        │   ├── application/         # CRUD + assign use cases, DTOs
        │   ├── infrastructure/      # StoryRepositoryImpl
        │   └── presentation/        # Story routes, DI
        └── dashboard/
            ├── application/         # GetDashboardStatsUseCase, DTO
            ├── infrastructure/      # DashboardRepositoryImpl
            └── presentation/        # Dashboard routes, DI
```

---

## Layer Compliance Assessment

### Domain Layer ✅

- Entities (`UserEntity`, `ProjectEntity`, `StoryEntity`) are pure Python dataclasses.
- Value objects (`Email`, `UserRole`, `EntityId`, `ProjectStatus`, `StoryStatus`, `StoryPriority`) encapsulate invariant validation.
- Repository interfaces are abstract base classes defined in the domain — infrastructure implements them.
- No FastAPI, Pydantic, or SQLAlchemy imports in domain code.

### Application Layer ✅

- Use cases are single-responsibility classes with an `execute()` method.
- DTOs are Pydantic models used only at the application boundary — they do not leak into the domain.
- Use cases receive repository interfaces via constructor injection (dependency inversion).
- No HTTP-specific concerns (status codes, headers) are present.

### Infrastructure Layer ✅

- `UserRepositoryImpl` et al. implement the domain repository interfaces.
- SQLAlchemy ORM models (`UserModel`, `ProjectModel`, `StoryModel`) live here and are mapped back to domain entities via `to_entity()` / `from_entity()` methods.
- JWT, bcrypt, and rate-limiting concerns are contained here.
- The `AppConfig` singleton reads from `settings.yml` and environment variables.

### Presentation Layer ✅ (with minor notes)

- FastAPI routers are thin controllers that delegate immediately to use cases.
- Auth dependencies (`get_current_user`, `require_admin`) are defined here and injected via `Depends()`.
- Exception handlers in `app.py` translate domain errors to HTTP responses.
- **Minor:** `app.py` directly constructs domain-level exception handler functions using domain exception types; the mapping is clear but the file has grown to ~280 lines and could be split.

---

## Dependency Inversion in Practice

The infrastructure modules are wired into the presentation layer through per-feature `dependencies.py` files:

```python
# projects/presentation/dependencies.py
def get_create_project_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> CreateProjectUseCase:
    repo = ProjectRepositoryImpl(session)
    return CreateProjectUseCase(repo)
```

This pattern is consistent across all features. Use cases receive concrete repository implementations at the boundary, keeping the application layer free of infrastructure references.

---

## Cross-Cutting Concerns

| Concern | Location | Approach |
|---|---|---|
| Logging | `shared/utils/log_util.py` | Singleton logger, stdlib `logging` |
| Configuration | `shared/infrastructure/config/` (via `AppConfig`) | YAML + env var overlay |
| Database engine | `shared/infrastructure/config/` | SQLAlchemy async engine, lazy init |
| Rate limiting | `shared/infrastructure/rate_limit/` | slowapi limiter singleton |
| JWT | `shared/infrastructure/security/jwt_handler.py` | Stateless HS256 tokens |
| Password hashing | `shared/infrastructure/security/password_handler.py` | bcrypt |
| Security headers | `app.py` middleware | Applied globally |
| CORS | `app.py` middleware | Configurable per environment |

---

## Identified Architectural Issues

### 1. Missing Domain Events

There is no event/notification mechanism. Actions like "user registered" or "story assigned" are handled inline by use cases with no hook for side effects (e.g. email notifications). Adding event dispatching later will require non-trivial refactoring.

### 2. No Unit-of-Work Pattern

Each use case receives a single repository. For write operations that span multiple repositories (e.g. creating a project and initialising default stories atomically), there is no transaction boundary abstraction. This will become important when multi-aggregate operations are required.

### 3. Dashboard Has No Domain Layer

The `dashboard` feature contains only `application/` and `infrastructure/` layers. Dashboard statistics are likely derived from existing domain data, but there is no `dashboard/domain/` directory. If the dashboard ever has its own invariants, it will need a domain layer.

### 4. `app.py` Is a God File

`app.py` bootstraps the app, registers all exception handlers, configures middleware, defines CORS helpers, and registers all routers. As the number of features grows this file will become a maintenance burden. Consider splitting registration into focused modules.

### 5. Feature-Level `presentation/dependencies.py` Duplication

Each feature duplicates the same pattern of getting a database session and constructing use cases. A shared factory pattern or feature-level composition root could reduce this boilerplate.

---

## Positive Patterns

- **Consistent use of `@dataclass` for domain entities** makes entities lightweight and easy to test.
- **`EntityId` value object** wraps UUIDs, preventing primitive obsession across the domain.
- **`BaseRouteHandler`** in shared presentation provides a reusable pattern for route logic.
- **Feature-based module organisation** means a new developer can find all code related to a feature in one place.

---

## Recommendations

| Priority | Recommendation |
|---|---|
| Medium | Extract app.py bootstrapping into focused modules (middleware.py, exception_handlers.py, router_registry.py) |
| Medium | Add a Unit-of-Work abstraction for multi-repository transactions |
| Low | Add domain events / publisher interface for side effects |
| Low | Add a dashboard domain layer as a future-proofing measure |

---

**Audit date:** 10 May 2026  
**Audited by:** GitHub Copilot Coding Agent
