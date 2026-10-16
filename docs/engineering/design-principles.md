# Design Principles

## Overview

This document outlines the core software design principles applied throughout the Open Projects Hub API. These principles guide architectural decisions, code structure, and implementation details.

## Applied Principles

### 1. SOLID Principles

#### S - Single Responsibility Principle (SRP)

**Rule:** Each class/module should have one reason to change.

**Applied in:**

- **Use Cases:** Each use case handles exactly one user action
  ```python
  # ✅ Good: One responsibility
  class CreateUserUseCase:      # Only creates users
  class LoginUserUseCase:       # Only handles login
  class GetUserByIdUseCase:     # Only retrieves users
  ```

- **Handlers:** Single purpose handlers
  ```python
  # ✅ Good: Each handler has one job
  class JWTHandler:             # Only handles JWT operations
  class PasswordHandler:        # Only handles password hashing
  ```

- **Routes:** Thin controllers delegate to use cases
  ```python
  # ✅ Good: Route only handles HTTP concerns
  @router.post("/register")
  async def register_user(
      payload: CreateUserRequest,
      create_user_use_case: CreateUserUseCase = Depends(...),
  ) -> CreateUserResponse:
      return await create_user_use_case.execute(payload)
  ```

**Violations we fixed:**
- Removed service layer that was just passing calls through
- Moved password validation from service to DTO (where it belongs)

---

#### O - Open/Closed Principle (OCP)

**Rule:** Open for extension, closed for modification.

**Applied in:**

- **Repository Pattern:** Add new implementations without changing interface
  ```python
  # Interface is closed for modification
  class UserRepository(ABC):
      @abstractmethod
      async def find_by_email(self, email: Email) -> Optional[UserEntity]: ...

  # But open for extension via new implementations
  class PostgreSQLUserRepository(UserRepository): ...
  class MongoDBUserRepository(UserRepository): ...     # New!
  class InMemoryUserRepository(UserRepository): ...    # New!
  ```

- **Value Objects:** Extend validation without changing base
  ```python
  # Add new value objects without modifying existing ones
  class Email: ...
  class PhoneNumber: ...      # New value object
  class Address: ...          # New value object
  ```

---

#### L - Liskov Substitution Principle (LSP)

**Rule:** Subtypes must be substitutable for their base types.

**Applied in:**

- **Repository implementations** can be swapped without affecting use cases
  ```python
  # Use case doesn't care which implementation is used
  class CreateUserUseCase:
      def __init__(self, user_repo: UserRepository):  # Works with ANY implementation
          self.user_repo = user_repo
  ```

- **Testing:** Mock repositories work the same as real ones
  ```python
  # Test with mock
  mock_repo = AsyncMock(spec=UserRepository)
  use_case = CreateUserUseCase(mock_repo)  # Works identically

  # Production with real implementation
  real_repo = PostgreSQLUserRepository(session_factory)
  use_case = CreateUserUseCase(real_repo)  # Same interface, same behavior
  ```

---

#### I - Interface Segregation Principle (ISP)

**Rule:** Don't force clients to depend on methods they don't use.

**Applied in:**

- **Focused repository interfaces**
  ```python
  # ✅ Good: Interface only has methods the use case needs
  class UserRepository(ABC):
      @abstractmethod
      async def find_by_id(self, user_id: EntityId) -> Optional[UserEntity]: ...

      @abstractmethod
      async def find_by_email(self, email: Email) -> Optional[UserEntity]: ...

      @abstractmethod
      async def save(self, user: UserEntity) -> Optional[UserEntity]: ...
  ```

- **Separated concerns**
  ```python
  # ✅ Good: Separate handlers for separate concerns
  class JWTHandler:             # Token operations only
  class PasswordHandler:        # Password operations only

  # ❌ Bad: God handler
  class SecurityHandler:        # Does JWT + Password + RBAC + ...
  ```

---

#### D - Dependency Inversion Principle (DIP)

**Rule:** Depend on abstractions, not concretions.

**Applied in:**

- **Application layer depends on domain interfaces**
  ```python
  # ✅ Good: Use case depends on interface
  class CreateUserUseCase:
      def __init__(self, user_repo: UserRepository):  # Interface
          self.user_repo = user_repo

  # ❌ Bad: Direct dependency on implementation
  class CreateUserUseCase:
      def __init__(self):
          self.user_repo = PostgreSQLUserRepository()  # Concrete!
  ```

- **Infrastructure implements domain interfaces**
  ```python
  # Domain defines the contract
  class UserRepository(ABC): ...

  # Infrastructure fulfills it
  class UserRepositoryImpl(UserRepository): ...
  ```

---

### 2. DRY (Don't Repeat Yourself)

**Rule:** Every piece of knowledge must have a single, unambiguous, authoritative representation.

**Applied in:**

- **Base Model:** Common fields defined once
  ```python
  # src/app/shared/infrastructure/models/base_model.py
  class BaseModel:
      id: Mapped[str] = mapped_column(primary_key=True)
      created_at: Mapped[datetime]
      updated_at: Mapped[datetime]
  ```

- **Base DTO:** Common validation patterns
  ```python
  # Email validation in one place
  class EmailField(str):
      @classmethod
      def __get_pydantic_core_schema__(cls, source_type, handler):
          return core_str_schema & core_str_validator(
              lambda v: Email(v)
          )
  ```

- **Dependencies:** Centralized dependency injection in `src/app/composition/`

**When we allow duplication:**
- Different domains with genuinely different rules
- When abstraction would be more complex than duplication
- Test fixtures that serve different purposes

---

### 3. YAGNI (You Aren't Gonna Need It)

**Rule:** Don't add functionality until it's necessary.

**Applied in:**

- **Removed Service Layer:** Was just passing calls through
  ```python
  # ❌ Before: Unnecessary abstraction
  Presentation → Service → Use Case → Domain

  # ✅ After: Direct and clear
  Presentation → Use Case → Domain
  ```

- **No premature pagination:** Not needed yet
  ```python
  # ❌ Not implementing: Complex pagination for single-item queries
  # ✅ Will add when: We have list endpoints with >100 items
  ```

- **Simple error handling:** No complex error hierarchy yet
  ```python
  # ✅ Current: Simple exceptions
  raise DuplicateEmailError("...")
  raise AuthenticationError("...")

  # ❌ Not implementing: Full error hierarchy with error codes, messages, etc.
  # ✅ Will add when: We need i18n, detailed error tracking, etc.
  ```

---

### 4. KISS (Keep It Simple, Stupid)

**Rule:** Simplicity should be a key goal.

**Applied in:**

- **Direct dependency injection**
  ```python
  # ✅ Simple: Direct injection
  @router.post("/register")
  async def register(
      payload: CreateUserRequest,
      use_case: CreateUserUseCase = Depends(get_create_user_use_case),
  ):
      return await use_case.execute(payload)
  ```

- **Simple password validation**
  ```python
  # ✅ Simple: Regex and length check
  @field_validator("password")
  def validate_password(cls, value: str) -> str:
      if len(value) < 8:
          raise ValueError("Password must be at least 8 characters")
      if not re.search(r"[A-Z]", value):
          raise ValueError("Password must contain uppercase letter")
      if not re.search(r"[a-z]", value):
          raise ValueError("Password must contain lowercase letter")
      if not re.search(r"\d", value):
          raise ValueError("Password must contain digit")
      return value
  ```

- **Flat project structure**
  ```
  # ✅ Simple: Clear folder structure
  src/app/
  ├── shared/           # Cross-cutting concerns
  └── features/         # Feature-specific code
      ├── domain/       # Business rules
      ├── application/  # Use cases
      ├── infrastructure/ # Technical details
      └── presentation/ # HTTP endpoints
  ```

---

### 5. Fail Fast

**Rule:** Detect and report errors as early as possible.

**Applied in:**

- **JWT secret validation at startup**
  ```python
  # App won't start with weak secret
  class JWTHandler:
      def __init__(self, secret_key: str, validate_secret: bool = True):
          if validate_secret:
              self._validate_secret_key(secret_key)  # Fails fast!
          self.secret_key = secret_key

  def _validate_secret_key(cls, secret_key: str) -> None:
      if len(secret_key) < 32:
          raise JWTSecretError("JWT secret key is too short (min 32 chars)")
      if secret_key.lower() in cls.WEAK_SECRETS:
          raise JWTSecretError("Known weak/default secret")
  ```

- **Configuration validation**
  ```python
  # Config fails if required values missing
  class AppConfig:
      @classmethod
      def load(cls) -> "AppConfig":
          config = cls._load_yaml()
          cls._validate_required(config)  # Fails fast!
          return cls(config)
  ```

- **Value object validation**
  ```python
  # Invalid email throws immediately
  email = Email("invalid")  # Raises ValueError
  email = Email("valid@example.com")  # OK
  ```

---

### 6. Principle of Least Astonishment

**Rule:** Code should behave in a way that least surprises users (developers).

**Applied in:**

- **Repository returns None on failure**
  ```python
  # ✅ Expected: None means "not found" or "failed"
  user = await repo.find_by_email(email)
  if user is None:
      # Handle not found
  ```

- **Use cases raise exceptions for business errors**
  ```python
  # ✅ Expected: Exception means "business rule violated"
  try:
      await use_case.execute(request)
  except DuplicateEmailError:
      # Handle duplicate
  ```

- **DTOs validate input**
  ```python
  # ✅ Expected: Invalid data rejected immediately
  CreateUserRequest(email="invalid", ...)  # Raises ValidationError
  ```

---

## Anti-Patterns We Avoid

### 1. ❌ God Objects

```python
# BAD: One class does everything
class UserManager:
    def create_user(self): ...
    def delete_user(self): ...
    def login_user(self): ...
    def send_email(self): ...
    def generate_report(self): ...
```

**Why avoided:** Violates SRP, hard to test, hard to maintain.

**Our approach:** Separate use cases per action.

---

### 2. ❌ Anemic Domain Model

```python
# BAD: Entity is just a data container
@dataclass
class User:
    id: str
    email: str
    name: str
```

**Why avoided:** No behavior, validation scattered, business logic leaks.

**Our approach:** Rich entities with value objects and behavior.

---

### 3. ❌ Smart UI / Fat Controller

```python
# BAD: Route contains all logic
@router.post("/register")
async def register(payload: dict):
    # Database query
    # Password hashing
    # Email validation
    # User creation
    # Token generation
    # Response formatting
    ...
```

**Why avoided:** All concerns mixed, impossible to test, duplicate code.

**Our approach:** Thin routes delegate to use cases.

---

### 4. ❌ Shotgun Surgery

```python
# BAD: One change requires edits in many places
# Add new user field → edit entity, DTO, model, repository, route, test, ...
```

**Our approach:** Clear layer boundaries minimize change propagation.

---

### 5. ❌ Feature Envy

```python
# BAD: Method uses other class's data more than its own
class UserService:
    def get_full_name(self, user: UserEntity) -> str:
        return f"{user.first_name} {user.last_name}"  # Should be on UserEntity!
```

**Our approach:** Move behavior to the entity that owns the data.

---

## Decision Framework

When making design decisions, we ask:

1. **SOLID:** Does it follow SOLID principles?
2. **DRY:** Is there duplication? Can it be extracted?
3. **YAGNI:** Do we need this now? Or are we guessing?
4. **KISS:** Is this the simplest solution that works?
5. **Testability:** Can I test this in isolation?
6. **Maintainability:** Will this be easy to change later?
7. **Performance:** Does it meet performance requirements?

If all answers are positive, proceed. If any are negative, reconsider.

## Code Review Checklist

When reviewing code, check:

- [ ] Single responsibility (one class = one purpose)
- [ ] Depends on abstractions, not concretions
- [ ] No unnecessary abstractions (YAGNI)
- [ ] Simple and readable (KISS)
- [ ] Fails fast on invalid input
- [ ] No duplicate logic (DRY)
- [ ] Layer boundaries respected
- [ ] Value objects for validated data
- [ ] Use cases orchestrate, don't implement
- [ ] Routes delegate to use cases

---

**See Also:**
- [Clean Architecture](./clean-architecture.md)
- [DDD Patterns](./ddd-patterns.md)

---

**Last Updated:** April 30, 2026
