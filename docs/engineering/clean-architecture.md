# Clean Architecture

## Overview

The Open Projects Hub API follows **Clean Architecture** (also known as Onion Architecture or Hexagonal Architecture), as described by Robert C. Martin.

This architecture enforces a **Dependency Rule**: source code dependencies only point inward. Inner layers know nothing about outer layers.

## Layer Structure

```
                    ┌─────────────────────────┐
                    │     EXTERNAL TOOLS       │
                    │  (Database, JWT, HTTP)   │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │   INFRASTRUCTURE LAYER   │
                    │  ┌─────────────────────┐ │
                    │  │ Repositories         │ │
                    │  │ JWT Handler          │ │
                    │  │ Password Handler     │ │
                    │  │ Database Engine      │ │
                    │  │ Configuration        │ │
                    │  └─────────────────────┘ │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │     DOMAIN LAYER         │
                    │  ┌─────────────────────┐ │
                    │  │ Entities             │ │
                    │  │ Value Objects        │ │
                    │  │ Repository Interfaces│ │
                    │  └─────────────────────┘ │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │   APPLICATION LAYER      │
                    │  ┌─────────────────────┐ │
                    │  │ Use Cases            │ │
                    │  │ Application DTOs     │ │
                    │  └─────────────────────┘ │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │   PRESENTATION LAYER     │
                    │  ┌─────────────────────┐ │
                    │  │ FastAPI Routes       │ │
                    │  │ Request/Response DTOs│ │
                    │  │ Dependencies         │ │
                    │  └─────────────────────┘ │
                    └─────────────────────────┘
```

## Layer Responsibilities

### 1. Domain Layer (`src/app/features/domain/`)

**Purpose:** Contains enterprise business logic and rules.

**Contains:**
- **Entities:** Business objects with identity
- **Value Objects:** Objects defined by their attributes
- **Repository Interfaces:** Contracts for data access

**Rules:**
- ✅ No dependencies on other layers
- ✅ Pure Python (no frameworks)
- ✅ Can be tested in isolation
- ✅ Should never change for external reasons

**Example:**
```python
# domain/entities/user_entity.py
@dataclass
class UserEntity:
    id: EntityId
    email: Email
    first_name: str
    last_name: str
    password_hash: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def fullname(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

**Key Files:**
- `src/app/features/user/domain/entities/user_entity.py`
- `src/app/features/user/domain/value_objects/email.py`
- `src/app/features/user/domain/value_objects/user_role.py`
- `src/app/features/user/domain/repositories/user_repository.py` (interface)

### 2. Application Layer (`src/app/features/application/`)

**Purpose:** Orchestrates business logic through use cases.

**Contains:**
- **Use Cases:** Application-specific business rules
- **Application DTOs:** Data transfer objects for application layer
- **Service Interfaces:** Contracts for external services

**Rules:**
- ✅ Depends only on domain layer
- ✅ Defines interfaces that infrastructure implements
- ✅ No framework dependencies
- ✅ Thin layer - orchestrates, doesn't implement

**Example:**
```python
# application/use_cases/create_user.py
class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, request: CreateUserRequest) -> UserResponse:
        # 1. Check if user exists
        existing = await self.user_repo.find_by_email(request.email)
        if existing:
            raise DuplicateEmailError(...)

        # 2. Hash password
        password_hash = await PasswordHandler.hash_password(request.password)

        # 3. Create entity
        user = UserEntity(...)

        # 4. Save
        created_user = await self.user_repo.save(user)

        # 5. Return response
        return UserResponse.from_entity(created_user)
```

**Key Files:**
- `src/app/features/user/application/use_cases/create_user.py`
- `src/app/features/auth/application/use_cases/login_user.py`
- `src/app/features/user/application/dtos/user_dto.py`
- `src/app/features/auth/application/dtos/auth_dto.py`

### 3. Infrastructure Layer (`src/app/features/infrastructure/`, `src/app/shared/infrastructure/`)

**Purpose:** Implements technical details and external services.

**Contains:**
- **Repository Implementations:** Database access
- **JWT Handler:** Token creation/validation
- **Password Handler:** bcrypt hashing
- **Database Engine:** SQLAlchemy async engine
- **Configuration:** YAML config loading

**Rules:**
- ✅ Depends on domain and application layers
- ✅ Implements interfaces defined by domain/application
- ✅ Framework-specific code lives here
- ✅ Can be swapped (e.g., PostgreSQL → MongoDB)

**Example:**
```python
# infrastructure/repository/user_repository_impl.py
class UserRepositoryImpl(UserRepository):  # Implements domain interface
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def find_by_email(self, email: Email) -> Optional[UserEntity]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.email == str(email))
            )
            user_model = result.scalar_one_or_none()
            return user_model.to_entity() if user_model else None

    async def save(self, user: UserEntity) -> Optional[UserEntity]:
        try:
            async with self.session_factory() as session:
                user_model = UserModel.from_entity(user)
                session.add(user_model)
                await session.commit()
                await session.refresh(user_model)
                return user_model.to_entity()
        except IntegrityError:
            return None  # Repository returns None, use case decides what to do
```

**Key Files:**
- `src/app/features/user/infrastructure/repositories/user_repository_impl.py`
- `src/app/shared/infrastructure/security/jwt_handler.py`
- `src/app/shared/infrastructure/security/password_handler.py`
- `src/app/shared/persistence/engine_factory.py`
- `src/app/config/app_config.py`

### 4. Presentation Layer (`src/app/features/presentation/`)

**Purpose:** Handles HTTP requests and responses.

**Contains:**
- **FastAPI Routes:** API endpoints
- **Request/Response DTOs:** Pydantic models for API
- **Dependencies:** FastAPI dependency injection setup
- **Exception Handlers:** HTTP error responses

**Rules:**
- ✅ Depends on all inner layers
- ✅ Thin controllers - delegate to use cases
- ✅ HTTP-specific concerns (status codes, headers)
- ✅ Authentication/authorization middleware

**Example:**
```python
# presentation/web/routes/user_routes.py
@router.post("/register", response_model=CreateUserResponse)
async def register_user(
    payload: CreateUserRequest,
    create_user_use_case: CreateUserUseCase = Depends(get_create_user_use_case),
) -> CreateUserResponse:
    response = await create_user_use_case.execute(payload)
    return response
```

**Key Files:**
- `src/app/features/auth/presentation/auth_routes.py`
- `src/app/features/user/presentation/user_routes.py`
- `src/app/composition/` - Centralized dependency injection
- `src/app/shared/presentation/exception_handlers.py`

## Dependency Flow

```
Presentation → Application → Domain ← Infrastructure
                                      ↑
                              (implements interfaces)
```

**What this means:**
- Presentation calls Application use cases
- Application calls Domain repository interfaces
- Infrastructure implements those interfaces
- Domain knows nothing about Infrastructure

**What is NOT allowed:**
- ❌ Domain → Infrastructure (dependency inversion via interfaces)
- ❌ Application → Presentation (use cases don't know about HTTP)
- ❌ Infrastructure → Application (infrastructure doesn't know about use cases)

## Dependency Inversion in Practice

### The Problem

Without dependency inversion, the application layer would directly depend on infrastructure:

```python
# ❌ BAD - Application depends on infrastructure
from src.app.features.infrastructure.repository.user_repository_impl import UserRepositoryImpl

class CreateUserUseCase:
    def __init__(self):
        self.repo = UserRepositoryImpl()  # Direct dependency!
```

### The Solution

The domain layer defines the interface, infrastructure implements it:

```python
# ✅ GOOD - Dependency inversion
# Domain defines interface
class UserRepository(ABC):
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[UserEntity]: ...

# Application depends on interface
class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):  # Depends on abstraction
        self.user_repo = user_repo

# Infrastructure implements interface
class UserRepositoryImpl(UserRepository):  # Concrete implementation
    async def find_by_email(self, email: Email) -> Optional[UserEntity]:
        ...
```

## File Organization

```
src/app/
├── app.py                          # FastAPI app setup
├── main.py                         # ASGI entrypoint for deployment
├── composition/                     # Centralized dependency injection
│   ├── __init__.py                 # Public API (40+ exports)
│   ├── infrastructure.py           # Database, AI service
│   ├── repositories.py             # Shared repositories
│   └── features/                   # Feature-specific DI factories
│       ├── auth.py
│       ├── clients.py
│       ├── dashboard.py
│       ├── projects.py
│       ├── refinement.py
│       ├── stories.py
│       └── users.py
├── config/                         # Configuration loading
│   ├── app_config.py               # Config singleton
│   ├── config_local.yml
│   ├── config_dev.yml
│   ├── config_container.yml
│   └── config_prod.yml
├── shared/
│   ├── domain/
│   │   └── value_objects/          # Shared value objects (EntityId, etc.)
│   ├── infrastructure/
│   │   ├── database/               # Database engine, sessions
│   │   ├── models/                 # SQLAlchemy base models
│   │   ├── security/               # JWT, password hashing
│   │   └── rate_limit/             # Rate limiting
│   ├── logging/                    # Structured logging utilities
│   ├── persistence/                # Database engine factory
│   ├── presentation/               # Router registry, middleware
│   └── utils/                      # Shared utilities
└── features/                       # Feature modules (no __init__.py)
    ├── auth/                       # Authentication
    │   ├── application/            # Use cases, DTOs
    │   ├── domain/                 # Entities, value objects
    │   ├── infrastructure/         # Repositories, models
    │   └── presentation/           # Routes, dependencies
    ├── user/                       # User management
    ├── clients/                    # Client management
    ├── projects/                   # Project management
    ├── stories/                    # Story management
    ├── refinement/                 # AI refinement
    └── dashboard/                  # Dashboard stats
```

**Note:** Feature folders use **implicit namespace packages** (no `__init__.py` files). Always use explicit file-path imports:

```python
# ✅ Correct
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase

# ❌ Wrong - will fail due to no __init__.py
from src.app.features.projects.application.use_cases import CreateProjectUseCase
```

## Benefits of Clean Architecture

### 1. Testability

Each layer can be tested in isolation:

```python
# Test domain without database
def test_user_entity_fullname():
    user = UserEntity(first_name="John", last_name="Doe", ...)
    assert user.fullname == "John Doe"

# Test use case with mock repository
@pytest.mark.asyncio
async def test_create_user_use_case():
    mock_repo = AsyncMock()
    mock_repo.find_by_email.return_value = None
    use_case = CreateUserUseCase(mock_repo)
    result = await use_case.execute(request)
    assert result.email == "test@example.com"
```

### 2. Maintainability

Changes to infrastructure don't affect business logic:

```python
# Want to switch from PostgreSQL to MongoDB?
# Just create a new repository implementation:

class MongoDBUserRepository(UserRepository):
    async def find_by_email(self, email: Email) -> Optional[UserEntity]:
        # MongoDB implementation
        ...

# Domain and application layers remain unchanged!
```

### 3. Flexibility

Multiple implementations can coexist:

```python
# Use different repositories for different environments
if config.environment == "test":
    repo = InMemoryUserRepository()
elif config.environment == "production":
    repo = PostgreSQLUserRepository()
```

### 4. Clear Boundaries

New developers can quickly understand where to put code:

- Business rules → Domain/Application
- Database access → Infrastructure
- HTTP endpoints → Presentation
- Shared utilities → Shared

## What We Removed (and Why)

### Service Layer (Removed)

**Before:**
```
Presentation → Services → Use Cases → Domain ← Infrastructure
```

**After:**
```
Presentation → Use Cases → Domain ← Infrastructure
```

**Why removed:**
- Service layer was just passing calls through (YAGNI violation)
- Added unnecessary abstraction
- Made code harder to follow
- Use cases already encapsulate business logic

**See:** [Design Principles - YAGNI](./design-principles.md#yagni-you-arent-gonna-need-it)

## Migration Guide

### Adding a New Feature

1. **Domain Layer:**
   - Create entities, value objects, repository interfaces

2. **Application Layer:**
   - Create use cases and application DTOs

3. **Infrastructure Layer:**
   - Implement repository interfaces
   - Create SQLAlchemy models

4. **Presentation Layer:**
   - Create routes and request/response DTOs
   - Wire up dependencies

### Modifying Existing Code

- **Change business rule?** → Application/Domain layer
- **Change database query?** → Infrastructure layer
- **Change API response format?** → Presentation layer
- **Add new endpoint?** → Presentation layer

## Anti-Patterns to Avoid

### ❌ Leaky Abstractions

```python
# BAD - Domain knows about SQLAlchemy
class UserEntity:
    def save(self, session: Session):  # ❌ Domain depends on infrastructure
        session.add(self)
```

### ❌ Fat Controllers

```python
# BAD - Route contains business logic
@router.post("/register")
async def register(payload: CreateUserRequest):
    # ❌ Business logic in presentation layer
    if await user_repo.find_by_email(payload.email):
        raise HTTPException(...)

    password_hash = await PasswordHandler.hash_password(payload.password)
    user = UserEntity(...)
    await user_repo.save(user)
    return user
```

### ❌ Circular Dependencies

```python
# BAD - A imports B, B imports A
# domain/entities/user.py → application/dtos/user_dto.py
# application/dtos/user_dto.py → domain/entities/user.py
```

**Solution:** Use separate conversion methods in DTOs:

```python
# DTO depends on entity (one direction)
@dataclass
class UserResponse:
    @classmethod
    def from_entity(cls, entity: UserEntity) -> "UserResponse":
        return cls(id=str(entity.id), email=str(entity.email), ...)
```

## References

- [The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Robert C. Martin
- [Clean Code](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882) - Robert C. Martin
- [Domain-Driven Design](https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215) - Eric Evans
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) - Alistair Cockburn

---

**See Also:**
- [DDD Patterns](./ddd-patterns.md)
- [Design Principles](./design-principles.md)
- [Composition Root](./composition-root.md)

---

**Last Updated:** June 11, 2026
