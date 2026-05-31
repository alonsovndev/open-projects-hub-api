# Domain-Driven Design (DDD) Patterns

## Overview

The Open Projects Hub API applies **Domain-Driven Design (DDD)** patterns to model business concepts accurately and maintain a ubiquitous language between developers and domain experts.

DDD focuses on:
- **Domain Model:** Accurate representation of business concepts
- **Ubiquitous Language:** Shared vocabulary between team members
- **Bounded Contexts:** Clear boundaries between different domains
- **Rich Domain Models:** Entities with behavior, not just data

## Core DDD Building Blocks

### 1. Entities

Entities are objects with a **unique identity** that persists through their lifecycle.

**Characteristics:**
- Has a unique identifier (`EntityId`)
- Has a lifecycle (created, updated, deleted)
- Identity matters more than attributes
- Can be mutable

**Implementation:**

```python
# src/app/features/domain/entities/user_entity.py
@dataclass
class UserEntity:
    id: EntityId                    # Unique identity
    email: Email                    # Value object
    first_name: str
    last_name: str
    password_hash: str
    role: UserRole                  # Value object
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Domain behavior
    @property
    def fullname(self) -> str:
        """Computed property - domain logic."""
        return f"{self.first_name} {self.last_name}"

    def deactivate(self) -> None:
        """Domain method - changes entity state."""
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
```

**Key Files:**
- `src/app/features/domain/entities/user_entity.py`

### 2. Value Objects

Value Objects are objects **defined by their attributes**, not identity. They are immutable and interchangeable.

**Characteristics:**
- No identity - equality based on attributes
- Immutable - cannot be changed after creation
- Self-validating - validates itself on creation
- Side-effect free - operations return new instances

**Implementation Pattern:**

```python
# src/app/features/domain/value_objects/email.py
class Email:
    def __init__(self, value: str):
        self._validate(value)
        self._value = value.lower().strip()

    def _validate(self, value: str) -> None:
        if not value or not isinstance(value, str):
            raise ValueError("Email must be a non-empty string")
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError(f"Invalid email format: {value}")

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other) -> bool:
        if isinstance(other, Email):
            return self._value == other._value
        return False

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return self._value
```

**Value Objects in the Project:**

| Value Object | Purpose | Validation |
|--------------|---------|------------|
| `Email` | Email addresses | Format validation |
| `UserRole` | User roles (USER, ADMIN) | Enum validation |
| `EntityId` | Unique identifiers | UUID validation |

**Key Files:**
- `src/app/features/domain/value_objects/email.py`
- `src/app/features/domain/value_objects/user_role.py`
- `src/app/shared/domain/value_objects/entity_id.py`

### 3. Repository Interfaces

Repository interfaces define **contracts** for data access, implemented by the infrastructure layer.

**Purpose:**
- Abstract data access from business logic
- Define what data operations are needed
- Allow different implementations (PostgreSQL, MongoDB, in-memory)

**Implementation:**

```python
# src/app/features/domain/repositories/user_repository.py
class UserRepository(ABC):
    """
    Repository interface for User persistence.

    Defines the contract for user data access.
    Implementations live in the infrastructure layer.
    """

    @abstractmethod
    async def find_by_id(self, user_id: EntityId) -> Optional[UserEntity]:
        """Find a user by their unique identifier."""
        pass

    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[UserEntity]:
        """Find a user by their email address."""
        pass

    @abstractmethod
    async def save(self, user: UserEntity) -> Optional[UserEntity]:
        """
        Create or update a user.

        Returns the saved user entity, or None if save failed
        (e.g., duplicate email constraint violation).
        """
        pass
```

**Key Files:**
- `src/app/features/domain/repositories/user_repository.py`

### 4. Use Cases (Application Services)

Use Cases represent **application-specific business rules**. They orchestrate entities, repositories, and other services.

**Characteristics:**
- One use case = one user action
- Thin orchestration layer
- Depends on repository interfaces (not implementations)
- Returns application DTOs (not entities)

**Implementation:**

```python
# src/app/features/application/use_cases/create_user.py
class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, request: CreateUserRequest) -> UserResponse:
        """
        Execute the create user use case.

        Steps:
        1. Check if user with email already exists
        2. Hash password asynchronously
        3. Create new user entity
        4. Save to repository
        5. Return response DTO
        """
        # 1. Check for existing user
        existing_user = await self.user_repo.find_by_email(request.email)
        if existing_user:
            raise DuplicateEmailError(
                f"User with email {request.email} already exists"
            )

        # 2. Hash password (async to avoid blocking)
        password_hash = await PasswordHandler.hash_password(request.password)

        # 3. Create entity
        user = UserEntity(
            id=EntityId.generate(),
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password_hash=password_hash,
            role=request.role,
        )

        # 4. Save
        created_user = await self.user_repo.save(user)
        if created_user is None:
            raise DuplicateEmailError(
                f"Failed to create user with email {request.email}"
            )

        # 5. Return response
        return UserResponse.from_entity(created_user)
```

**Key Files:**
- `src/app/features/application/use_cases/create_user.py`
- `src/app/features/application/use_cases/login_user.py`

## Ubiquitous Language

### Shared Vocabulary

| Term | Definition | Used In |
|------|------------|---------|
| **User** | A person who can authenticate and use the system | Domain, Application |
| **Admin** | A user with administrative privileges | Domain, Application |
| **Authentication** | Process of verifying user identity | Application, Infrastructure |
| **Authorization** | Process of verifying user permissions | Application, Presentation |
| **Token** | JWT used for authentication | Infrastructure, Presentation |
| **Session** | Not used (stateless JWT) | N/A |
| **Role** | User's permission level (USER, ADMIN) | Domain |

### Naming Conventions

- **Entities:** `{Noun}Entity` (e.g., `UserEntity`)
- **Value Objects:** `{Noun}` (e.g., `Email`, `UserRole`)
- **Repositories:** `{Noun}Repository` (interface), `{Noun}RepositoryImpl` (implementation)
- **Use Cases:** `{Verb}{Noun}UseCase` (e.g., `CreateUserUseCase`, `LoginUserUseCase`)
- **DTOs:** `{Noun}Request`, `{Noun}Response` (presentation), `{Noun}DTO` (application)

## Bounded Contexts

### Current Context: User Management

The entire project currently exists within a single bounded context: **User Management**.

**Context:**
- Handles user registration, authentication, and profile management
- Owns the User aggregate
- Defines authentication boundaries

**Future Contexts (planned):**
- **Project Management:** Projects, tasks, milestones
- **Team Management:** Teams, memberships, invitations
- **Notification:** Email, in-app notifications

### Context Mapping

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  User Context    │────>│ Project Context  │────>│ Notification Ctx │
│  (Current)       │     │  (Planned)       │     │  (Planned)       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

## Aggregates

### User Aggregate

The **User** is currently the only aggregate root.

**Aggregate Root:** `UserEntity`

**Boundaries:**
- User entity owns its data
- All changes go through the entity or use cases
- Repository only accepts aggregate roots

```python
# User entity owns its password hash - external code doesn't manipulate it directly
@dataclass
class UserEntity:
    id: EntityId
    email: Email
    password_hash: str        # Managed by domain/application layer
    role: UserRole            # Controlled through domain logic
    # ...
```

## Domain Events (Future)

Domain events represent **something that happened** in the domain that other parts of the system might care about.

**Planned Events:**

```python
# Future implementation
@dataclass
class UserCreatedEvent:
    user_id: EntityId
    email: Email
    created_at: datetime

@dataclass
class UserAuthenticatedEvent:
    user_id: EntityId
    authenticated_at: datetime

@dataclass
class UserDeactivatedEvent:
    user_id: EntityId
    deactivated_by: EntityId
    deactivated_at: datetime
```

**Usage:**

```python
# In use case
class CreateUserUseCase:
    async def execute(self, request: CreateUserRequest) -> UserResponse:
        # ... create user ...

        # Publish domain event
        event = UserCreatedEvent(
            user_id=created_user.id,
            email=created_user.email,
            created_at=created_user.created_at,
        )
        await self.event_publisher.publish(event)

        return UserResponse.from_entity(created_user)
```

## Value Object vs Entity Decision Guide

| Question | Answer | Pattern |
|----------|--------|---------|
| Does it have a unique identity? | Yes | Entity |
| Can two instances with same attributes be different? | Yes | Entity |
| Is it immutable? | Yes | Value Object |
| Does equality depend on all attributes? | Yes | Value Object |
| Does it have a lifecycle? | Yes | Entity |
| Is it just data with validation? | Yes | Value Object |

**Examples:**

- `UserEntity` → Entity (has ID, lifecycle, mutable state)
- `Email` → Value Object (immutable, equality by value)
- `UserRole` → Value Object (enum, immutable)
- `EntityId` → Value Object (UUID wrapper, immutable)

## Anti-Corruption Layer

When integrating with external systems, use an **Anti-Corruption Layer** to translate between external and internal models.

**Example (Future OAuth Integration):**

```python
# External model (OAuth provider)
class OAuthUserProfile:
    def __init__(self, external_id: str, provider_email: str, ...):
        self.external_id = external_id
        self.provider_email = provider_email

# Anti-corruption layer
class OAuthAdapter:
    def to_user_entity(self, oauth_profile: OAuthUserProfile) -> UserEntity:
        """Translate external model to internal domain model."""
        return UserEntity(
            id=EntityId.generate(),
            email=Email(oauth_profile.provider_email),
            first_name=oauth_profile.first_name,
            last_name=oauth_profile.last_name,
            password_hash="",  # OAuth users don't have passwords
            role=UserRole.USER,
        )
```

## DDD vs CRUD: Why DDD?

### CRUD Approach (What we avoided)

```python
# ❌ Anemic domain model
class User:
    id: int
    email: str
    password_hash: str
    role: str

# Business logic scattered everywhere
def create_user(db, email, password, role):
    # Validation here
    # Password hashing here
    # Database save here
    pass

def login_user(db, email, password):
    # Database query here
    # Password verification here
    # Token generation here
    pass
```

### DDD Approach (What we use)

```python
# ✅ Rich domain model
@dataclass
class UserEntity:
    id: EntityId
    email: Email              # Self-validating
    password_hash: str        # Managed by domain
    role: UserRole            # Type-safe enum

    @property
    def fullname(self) -> str:
        return f"{self.first_name} {self.last_name}"

# Business logic in use cases
class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, request: CreateUserRequest) -> UserResponse:
        # Clear, single responsibility
        ...

class LoginUserUseCase:
    def __init__(self, user_repo: UserRepository, jwt_handler: JWTHandler):
        self.user_repo = user_repo
        self.jwt_handler = jwt_handler

    async def execute(self, request: LoginRequest) -> LoginResponse:
        # Clear, single responsibility
        ...
```

## Benefits of DDD in This Project

1. **Clear Business Logic:** Rules live in domain/use cases, not scattered
2. **Type Safety:** Value objects prevent invalid states
3. **Testability:** Domain layer is framework-independent
4. **Maintainability:** Changes to one layer don't affect others
5. **Communication:** Ubiquitous language aligns team understanding
6. **Flexibility:** Easy to add new features or change implementations

## Common DDD Mistakes to Avoid

### ❌ Anemic Domain Model

```python
# BAD - Entity is just a data container
@dataclass
class UserEntity:
    id: str
    email: str
    password_hash: str
```

**Fix:** Use value objects and domain behavior:

```python
# GOOD - Entity has behavior and validation
@dataclass
class UserEntity:
    id: EntityId
    email: Email              # Self-validating value object
    password_hash: str

    @property
    def fullname(self) -> str:
        ...
```

### ❌ Leaky Domain Model

```python
# BAD - Domain knows about SQLAlchemy
class UserEntity:
    def save(self, session: Session):  # ❌ Infrastructure dependency
        session.add(self)
```

**Fix:** Use repository pattern:

```python
# GOOD - Domain is persistence-agnostic
class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: UserEntity) -> UserEntity:
        ...
```

### ❌ God Use Case

```python
# BAD - Use case does everything
class UserManagementUseCase:
    async def execute(self, action: str, data: dict):
        if action == "create": ...
        elif action == "update": ...
        elif action == "delete": ...
        elif action == "login": ...
```

**Fix:** Single responsibility per use case:

```python
# GOOD - One use case per action
class CreateUserUseCase: ...
class UpdateUserUseCase: ...
class DeleteUserUseCase: ...
class LoginUserUseCase: ...
```

## References

- [Domain-Driven Design](https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215) - Eric Evans
- [Implementing Domain-Driven Design](https://www.amazon.com/Implementing-Domain-Driven-Design-Vaughn-Vernon/dp/0321834577) - Vaughn Vernon
- [Domain-Driven Design Distilled](https://www.amazon.com/Domain-Driven-Design-Distilled-Vaughn-Vernon/dp/0134434420) - Vaughn Vernon
- [Martin Fowler - DDD](https://martinfowler.com/tags/domain%20driven%20design.html)

---

**See Also:**
- [Clean Architecture](./clean-architecture.md)
- [Repository Pattern](./repository-pattern.md)
- [Design Principles](./design-principles.md)

---

**Last Updated:** April 30, 2026
