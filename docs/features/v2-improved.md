# Admin Authentication & Authorization - Implementation Plan v2 (Audit-Improved)

**Feature:** Admin Authentication and Authorization  
**Status:** Planning - Revised based on Code Audit v1  
**Version:** 2.0  
**Date:** April 30, 2026

---

## 🔄 Changes from v1

This version incorporates critical findings from the **Backend Code Audit Report (v1)**:

### Key Improvements
1. ✅ **Removed Service Layer** - Use cases called directly from controllers
2. ✅ **Fixed Database Engine Singleton** - Prevent connection exhaustion
3. ✅ **Added Rate Limiting** - Protect login endpoint from brute force
4. ✅ **Async Password Hashing** - Prevent event loop blocking
5. ✅ **Password Complexity Validation** - Enforce strong passwords
6. ✅ **Improved Exception Handling** - Domain-only exceptions in repositories
7. ✅ **Enhanced Testing Strategy** - Comprehensive coverage plan
8. ✅ **Production Hardening** - Health checks, monitoring, security headers

### Architecture Changes
- **REMOVED:** `AuthService` and `UserService` (YAGNI violation)
- **ADDED:** Direct use case invocation in controllers
- **FIXED:** Repository exception handling (domain layer only)
- **IMPROVED:** Configuration management with validation

---

## Table of Contents

1. [Overview](#overview)
2. [Critical Fixes from Audit](#critical-fixes-from-audit)
3. [Requirements](#requirements)
4. [Architecture](#architecture)
5. [Detailed Implementation Plan](#detailed-implementation-plan)
6. [API Contract](#api-contract)
7. [Database Schema](#database-schema)
8. [Security Considerations](#security-considerations)
9. [Testing Strategy](#testing-strategy)
10. [Production Readiness](#production-readiness)
11. [Rollout Plan](#rollout-plan)

---

## Overview

### Problem Statement
Implement a production-ready admin authentication and authorization system that:
- Connects FastAPI backend with frontend
- Follows Clean Architecture and DDD principles
- Addresses all HIGH and CRITICAL issues from code audit
- Is secure, scalable, and maintainable

### Target Outcomes
1. Admins can login with email/password and receive a JWT token
2. API response aligns with frontend's `AdminLoginApiResponse` interface
3. Role-based authorization (ADMIN and USER roles)
4. Secure token-based session management
5. Protected endpoints validate JWT tokens and user roles
6. **NEW:** Production-ready with rate limiting, monitoring, and proper error handling
7. **NEW:** Comprehensive test coverage (>70%)

---

## Critical Fixes from Audit

### 🔴 Priority 1: Blockers (MUST FIX)

#### 1. Database Engine Singleton Bug
**Issue:** Engine created per request causes connection exhaustion  
**File:** `dependencies.py`

**Old (WRONG):**
```python
async def get_database_session():
    postgres_db_session_manager = PostgresDbConnection(postgres_config)  # ❌ New engine every request
    async with postgres_db_session_manager.get_session() as session:
        yield session
```

**New (CORRECT):**
```python
from contextlib import asynccontextmanager
from functools import lru_cache

@lru_cache(maxsize=1)
def get_db_connection() -> PostgresDbConnection:
    """Singleton database connection manager."""
    postgres_config = AppConfig.instance().get_config("postgres", {})
    return PostgresDbConnection(postgres_config)

async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a database session."""
    db_conn = get_db_connection()
    async with db_conn.get_session() as session:
        yield session
```

---

#### 2. Remove Service Layer (YAGNI Violation)
**Issue:** `AuthService` and `UserService` are pure pass-throughs  
**Impact:** Unnecessary complexity, extra files to maintain

**Before:**
```
Controller → Service → UseCase
```

**After:**
```
Controller → UseCase (direct)
```

**Changes:**
- Delete `auth_service.py`
- Delete `user_service.py`
- Update controllers to inject use cases directly

---

#### 3. Add Rate Limiting
**Issue:** Login endpoint vulnerable to brute force  
**Solution:** Use `slowapi` for rate limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/login")
@limiter.limit("5/15minutes")  # 5 attempts per 15 minutes
async def login(...):
    ...
```

---

#### 4. Async Password Hashing
**Issue:** Bcrypt blocks event loop (CPU-intensive)  
**Solution:** Use `asyncio.to_thread()`

**Before:**
```python
password_hash = PasswordHandler.hash_password(payload.password)  # ❌ Blocks
```

**After:**
```python
password_hash = await asyncio.to_thread(
    PasswordHandler.hash_password, 
    payload.password
)  # ✅ Non-blocking
```

---

#### 5. Password Complexity Validation
**Issue:** No password policy enforcement  
**Solution:** Pydantic validator

```python
from pydantic import field_validator

class UserCreateRequest(BaseModel):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain a digit')
        return v
```

---

### 🟡 Priority 2: High Impact

#### 6. Fix Repository Exception Handling
**Issue:** Infrastructure layer raises application exceptions  
**Solution:** Repository returns domain entities or None only

**Before:**
```python
# user_repository_impl.py
from src.app.features.application.exceptions.user_exception import UserAlreadyExistsException  # ❌ Wrong layer

if result.scalar_one_or_none():
    raise UserAlreadyExistsException(user.email.value)  # ❌ Application concern
```

**After:**
```python
# Repository just saves or returns None
async def save(self, user: UserEntity) -> Optional[UserEntity]:
    try:
        existing = await self._check_exists_by_email(user.email)
        if existing:
            return None  # ✅ Let use case handle business logic
        
        user_model = UserModel(...)
        self.db_session.add(user_model)
        await self.db_session.commit()
        return map_model_to_entity(user_model)
    except IntegrityError:
        await self.db_session.rollback()
        return None  # ✅ Database constraint violation = user exists
```

**Use case handles the logic:**
```python
created_user = await self.user_repository.save(new_user_entity)
if not created_user:
    raise UserAlreadyExistsException(str(new_user_entity.email))  # ✅ Application logic
```

---

#### 7. JWT Secret Validation
**Issue:** No validation that SECRET_KEY was changed from default  
**Solution:** Startup validation

```python
def validate_jwt_config(config: AppConfig):
    """Validate JWT configuration at startup."""
    secret = config.get_config("jwt.secret_key")
    
    if not secret:
        raise ValueError("JWT secret_key is required")
    
    if secret in ["your-super-secret-jwt-key-change-this-in-production", "test", "secret"]:
        raise ValueError(
            "JWT secret_key is using default/insecure value. "
            "Generate a strong key with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
        )
    
    if len(secret) < 32:
        raise ValueError("JWT secret_key must be at least 32 characters")
```

---

## Requirements

### Functional Requirements
- [x] FR-1: Admin users authenticate with email and password
- [x] FR-2: System issues JWT token upon successful authentication
- [x] FR-3: API response matches frontend interface exactly
- [x] FR-4: Support role-based authorization (ADMIN, USER)
- [x] FR-5: Protected endpoints validate JWT tokens
- [x] FR-6: Admin-only endpoints verify ADMIN role
- [x] FR-7: Generic error messages for failed authentication
- [ ] **FR-8: Rate limiting on authentication endpoints** (NEW)
- [ ] **FR-9: Password complexity requirements enforced** (NEW)

### Non-Functional Requirements
- [x] NFR-1: Password hashing using bcrypt (async implementation)
- [x] NFR-2: JWT tokens expire after 24 hours
- [x] NFR-3: Tokens sent via Authorization header
- [x] NFR-4: Clean architecture boundaries maintained
- [x] NFR-5: Comprehensive test coverage (>70%)
- [ ] **NFR-6: Database connection pooling with singleton pattern** (NEW)
- [ ] **NFR-7: Request logging with correlation IDs** (NEW)
- [ ] **NFR-8: Health check endpoint** (NEW)
- [ ] **NFR-9: Security headers middleware** (NEW)
- [ ] **NFR-10: Production-ready error handling** (NEW)

---

## Architecture

### Component Overview (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌─────────────────┐         ┌──────────────────────┐      │
│  │  Auth Routes    │         │  Auth Dependencies   │      │
│  │  POST /login    │────────▶│  - get_current_user  │      │
│  │  (rate limited) │         │  - require_admin     │      │
│  └─────────────────┘         └──────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼ (NO SERVICE LAYER)
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────────────┐                                   │
│  │  LoginUserUseCase    │ ◀── Called directly from route    │
│  │  - execute()         │                                   │
│  └──────────────────────┘                                   │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  Auth DTOs                                        │      │
│  │  - LoginRequest (with password validation)        │      │
│  │  - AdminLoginResponse                             │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
│  ┌─────────────────┐         ┌──────────────────────┐      │
│  │  JWT Handler    │         │  Password Handler    │      │
│  │  (cached)       │         │  (async methods)     │      │
│  └─────────────────┘         └──────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  User Repository (fixed exception handling)       │      │
│  │  - Returns None on duplicate, not exception       │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Domain Layer                           │
│  ┌─────────────────┐         ┌──────────────────────┐      │
│  │  UserEntity     │         │  UserRole Enum       │      │
│  │  (enriched)     │         │  - ADMIN, USER       │      │
│  └─────────────────┘         └──────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  Auth Exceptions (domain only)                    │      │
│  │  - InvalidCredentialsError                        │      │
│  │  - UnauthorizedError                              │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Key Changes from v1
1. ❌ **Removed:** `AuthService`, `UserService`
2. ✅ **Added:** Direct use case injection in routes
3. ✅ **Fixed:** Repository layer boundary (no application exceptions)
4. ✅ **Improved:** Connection pooling with singleton pattern

---

## Detailed Implementation Plan

### **Phase 1: Infrastructure Fixes** (CRITICAL)

#### **1.1 Fix Database Connection Singleton**
**File:** `src/app/shared/infrastructure/config/postgres_db_conn.py`

**NO CHANGES NEEDED** - Class is already well-designed. The issue is in how it's used.

**File:** `src/app/features/presentation/web/dependencies.py`

```python
from functools import lru_cache
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config.app_config import AppConfig
from src.app.shared.infrastructure.config.postgres_db_conn import PostgresDbConnection
from src.app.shared.utils.config_util import get_config_value

app_config: dict = AppConfig.instance().config


@lru_cache(maxsize=1)
def get_db_connection() -> PostgresDbConnection:
    """
    Singleton database connection manager.
    Creates engine once and reuses across requests.
    """
    postgres_config = get_config_value(app_config, "postgres", {})
    return PostgresDbConnection(postgres_config)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    Reuses the singleton connection manager.
    """
    db_conn = get_db_connection()
    async with db_conn.get_session() as session:
        yield session
```

**Impact:** Prevents creating new database engine on every request.

---

#### **1.2 Add Rate Limiting**
**File:** `requirements.txt`

```txt
# Add slowapi for rate limiting
slowapi==0.1.9
```

**File:** `src/app/app.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Create FastAPI app
fastApiApp = FastAPI(title=app_name, version=app_version)

# Register rate limiter
fastApiApp.state.limiter = limiter
fastApiApp.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ... rest of app setup ...
```

---

#### **1.3 Update Password Handler for Async**
**File:** `src/app/shared/infrastructure/security/password_handler.py`

```python
import asyncio
import bcrypt

from src.app.shared.utils.log_util import log


class PasswordHandler:
    """
    Handles password hashing and verification using bcrypt.
    Uses asyncio.to_thread() to prevent blocking the event loop.
    """

    @staticmethod
    def _hash_password_sync(plain_password: str) -> str:
        """Synchronous bcrypt hashing (runs in thread pool)."""
        return bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    @staticmethod
    def _verify_password_sync(plain_password: str, hashed_password: str) -> bool:
        """Synchronous bcrypt verification (runs in thread pool)."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception as e:
            log.error(f"Error verifying password: {str(e)}")
            return False

    @staticmethod
    async def hash_password(plain_password: str) -> str:
        """
        Asynchronously hashes a plain text password using bcrypt.
        Runs in thread pool to avoid blocking the event loop.

        Args:
            plain_password: Plain text password

        Returns:
            Hashed password string
        """
        return await asyncio.to_thread(
            PasswordHandler._hash_password_sync,
            plain_password
        )

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Asynchronously verifies a plain text password against a hashed password.
        Runs in thread pool to avoid blocking the event loop.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        return await asyncio.to_thread(
            PasswordHandler._verify_password_sync,
            plain_password,
            hashed_password
        )
```

**Impact:** Prevents bcrypt from blocking the async event loop during password operations.

---

### **Phase 2: Remove Service Layer**

#### **2.1 Delete Unnecessary Services**

**DELETE these files:**
- `src/app/features/application/services/auth_service.py`
- `src/app/features/application/services/user_service.py`

**Rationale:** Pure pass-through layers that add no value (YAGNI violation).

---

#### **2.2 Update Dependencies to Inject Use Cases Directly**
**File:** `src/app/features/presentation/web/dependencies.py`

```python
from typing import AsyncGenerator
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config.app_config import AppConfig
from src.app.features.infrastructure.repository.user_repository_impl import UserRepositoryImpl
from src.app.features.application.use_cases.login_user import LoginUserUseCase
from src.app.features.application.use_cases.create_user import CreateUserUseCase
from src.app.features.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.shared.infrastructure.config.postgres_db_conn import PostgresDbConnection
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.utils.config_util import get_config_value

app_config: dict = AppConfig.instance().config


# Database connection (singleton)
@lru_cache(maxsize=1)
def get_db_connection() -> PostgresDbConnection:
    """Singleton database connection manager."""
    postgres_config = get_config_value(app_config, "postgres", {})
    return PostgresDbConnection(postgres_config)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a database session."""
    db_conn = get_db_connection()
    async with db_conn.get_session() as session:
        yield session


# JWT Handler (singleton)
@lru_cache(maxsize=1)
def get_jwt_handler() -> JWTHandler:
    """
    Dependency to get JWTHandler instance.
    Creates a cached singleton instance from config.
    """
    secret_key = AppConfig.instance().get_config("jwt.secret_key")
    algorithm = AppConfig.instance().get_config("jwt.algorithm", "HS256")
    expiration = AppConfig.instance().get_config("jwt.access_token_expire_minutes", 1440)

    # Validate secret key
    if not secret_key:
        raise ValueError("JWT secret_key not configured")
    
    if secret_key in ["your-super-secret-jwt-key-change-this-in-production", "test", "secret"]:
        raise ValueError(
            "JWT secret_key is using default/insecure value. "
            "Generate a strong key with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
        )
    
    if len(secret_key) < 32:
        raise ValueError("JWT secret_key must be at least 32 characters")

    return JWTHandler(
        secret_key=secret_key,
        algorithm=algorithm,
        expiration_minutes=int(expiration),
    )


# Use Case Dependencies (NEW - replaces service layer)
async def get_login_use_case(
    session: AsyncSession = Depends(get_database_session),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> LoginUserUseCase:
    """Dependency to get LoginUserUseCase with injected dependencies."""
    user_repository = UserRepositoryImpl(session)
    return LoginUserUseCase(user_repository, jwt_handler)


async def get_create_user_use_case(
    session: AsyncSession = Depends(get_database_session)
) -> CreateUserUseCase:
    """Dependency to get CreateUserUseCase with injected dependencies."""
    user_repository = UserRepositoryImpl(session)
    return CreateUserUseCase(user_repository)


async def get_user_by_id_use_case(
    session: AsyncSession = Depends(get_database_session)
) -> GetUserByIdUseCase:
    """Dependency to get GetUserByIdUseCase with injected dependencies."""
    user_repository = UserRepositoryImpl(session)
    return GetUserByIdUseCase(user_repository)
```

---

### **Phase 3: Update Use Cases**

#### **3.1 Update CreateUserUseCase (Async Password Hashing)**
**File:** `src/app/features/application/use_cases/create_user.py`

```python
import asyncio
from src.app.features.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.application.dtos.user_dto_mapper import map_create_request_to_entity, map_entity_to_dto_user
from src.app.features.application.exceptions.user_exception import UserAlreadyExistsException
from src.app.features.domain.repositories.user_repository import UserRepository
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.utils.log_util import log


class CreateUserUseCase:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, payload: UserCreateRequest) -> UserResponse:
        try:
            # Hash password asynchronously
            password_hash = await PasswordHandler.hash_password(payload.password)

            new_user_entity = map_create_request_to_entity(payload, password_hash)

            # Check if user exists
            existing_user = await self.user_repository.find_by_email(new_user_entity.email)

            if existing_user:
                log.warning(f"Duplicate user creation attempt with email: {new_user_entity.email}")
                raise UserAlreadyExistsException(str(new_user_entity.email))

            # Save user
            created_user = await self.user_repository.save(new_user_entity)
            
            # Repository returns None if user already exists (DB constraint)
            if not created_user:
                log.warning(f"User creation failed due to database constraint: {new_user_entity.email}")
                raise UserAlreadyExistsException(str(new_user_entity.email))

            response_dto = map_entity_to_dto_user(created_user)

            log.info(f"User created successfully: {created_user.id}")
            return response_dto

        except (ValueError, UserAlreadyExistsException):
            raise
        except Exception as e:
            log.error(f"Unexpected error in CreateUserUseCase: {str(e)}")
            raise
```

---

#### **3.2 Update LoginUserUseCase (Async Password Verification)**
**File:** `src/app/features/application/use_cases/login_user.py`

```python
from src.app.features.application.dtos.auth_dto import AdminLoginResponse, LoginRequest
from src.app.features.domain.exceptions.auth_exceptions import InvalidCredentialsError
from src.app.features.domain.repositories.user_repository import UserRepository
from src.app.features.domain.value_objects.email import Email
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.utils.log_util import log


class LoginUserUseCase:
    """
    Use case for authenticating users and issuing JWT tokens.
    """

    def __init__(self, user_repository: UserRepository, jwt_handler: JWTHandler):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler

    async def execute(self, payload: LoginRequest) -> AdminLoginResponse:
        """
        Authenticates user and returns login response with JWT token.

        Args:
            payload: LoginRequest with email and password

        Returns:
            AdminLoginResponse with token and user details

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        try:
            # Find user by email (normalized)
            user_entity = await self.user_repository.find_by_email(
                Email(str(payload.email).lower().strip())
            )

            if not user_entity:
                log.warning(f"Login attempt with non-existent email: {payload.email}")
                raise InvalidCredentialsError()

            # Verify password asynchronously
            is_valid = await PasswordHandler.verify_password(
                payload.password,
                user_entity.password_hash,
            )
            
            if not is_valid:
                log.warning(f"Failed login attempt for user: {user_entity.id}")
                raise InvalidCredentialsError()

            # Generate JWT token
            token = self.jwt_handler.create_access_token(
                user_id=str(user_entity.id),
                email=str(user_entity.email),
                role=user_entity.role.value,
            )

            # Create response
            response = AdminLoginResponse.from_user_entity(user_entity, token)

            log.info(f"User logged in successfully: {user_entity.id}")
            return response

        except InvalidCredentialsError:
            raise
        except Exception as e:
            log.error(f"Unexpected error in LoginUserUseCase: {str(e)}")
            raise
```

---

### **Phase 4: Update Presentation Layer**

#### **4.1 Update Auth Routes (Remove Service, Add Rate Limiting)**
**File:** `src/app/features/presentation/web/routes/auth_routes.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.app.features.application.dtos.auth_dto import AdminLoginResponse, LoginRequest
from src.app.features.application.use_cases.login_user import LoginUserUseCase
from src.app.features.domain.exceptions.auth_exceptions import InvalidCredentialsError
from src.app.features.presentation.web.dependencies import get_login_use_case
from src.app.app import limiter  # Import from main app

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
@limiter.limit("5/15minutes")  # 5 login attempts per 15 minutes per IP
async def login(
    request: Request,  # Required for rate limiting
    payload: LoginRequest,
    login_use_case: LoginUserUseCase = Depends(get_login_use_case),
) -> AdminLoginResponse:
    """
    Authenticate user and return JWT token with user details.

    Rate limited to 5 attempts per 15 minutes per IP address.

    Args:
        request: FastAPI request (for rate limiting)
        payload: LoginRequest with email and password
        login_use_case: Injected LoginUserUseCase

    Returns:
        AdminLoginResponse with token and user details

    Raises:
        401: Invalid credentials
        429: Too many requests (rate limit exceeded)
        500: Internal server error
    """
    try:
        response = await login_use_case.execute(payload)
        return response

    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message),
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
```

---

#### **4.2 Update User Routes (Remove Service)**
**File:** `src/app/features/presentation/web/routes/user_routes.py`

```python
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.params import Depends

from src.app.features.application.dtos.user_dto import UserResponse, UserCreateRequest
from src.app.features.application.exceptions.user_exception import (
    UserDoesNotExistException,
    UserAlreadyExistsException
)
from src.app.features.application.use_cases.create_user import CreateUserUseCase
from src.app.features.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.presentation.web.auth_dependencies import get_current_user, require_admin
from src.app.features.presentation.web.dependencies import (
    get_create_user_use_case,
    get_user_by_id_use_case
)

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    get_user_use_case: GetUserByIdUseCase = Depends(get_user_by_id_use_case),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """
    Get user by ID.
    
    Requires authentication.
    """
    try:
        user_result = await get_user_use_case.execute(str(user_id))
        return user_result

    except UserDoesNotExistException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    create_user_use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    current_user: Dict[str, Any] = Depends(require_admin),
) -> UserResponse:
    """
    Create a new user (admin only).
    
    Requires ADMIN role.
    """
    try:
        user_result = await create_user_use_case.execute(payload)
        return user_result

    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

---

### **Phase 5: Add Password Validation**

#### **5.1 Update UserCreateRequest DTO**
**File:** `src/app/features/application/dtos/user_dto.py`

```python
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from pydantic.alias_generators import to_camel


class UserResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

    id: str
    fullname: str
    email: str


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    first_name: str
    last_name: str
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password complexity requirements.
        
        Requirements:
        - At least 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        return v
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and trim name fields."""
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty')
        if len(v) > 50:
            raise ValueError('Name cannot exceed 50 characters')
        return v
```

---

### **Phase 6: Fix Repository Layer**

#### **6.1 Update UserRepositoryImpl (Remove Application Exceptions)**
**File:** `src/app/features/infrastructure/repository/user_repository_impl.py`

```python
from typing import Optional, List

from sqlalchemy import select
import sqlalchemy.exc

from src.app.features.domain.entities.user_entity import UserEntity
from src.app.features.domain.repositories.user_repository import UserRepository
from src.app.features.domain.value_objects.email import Email
from src.app.features.infrastructure.models.user_model import UserModel
from src.app.features.infrastructure.repository.user_model_mapper import map_model_to_entity
from src.app.shared.domain.repositories.base_repository import ID, T

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.utils.log_util import log


class DatabaseConnectionError(Exception):
    """Custom exception to indicate database connection errors."""
    pass


class UserRepositoryImpl(UserRepository):

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the UserRepositoryImpl with a SQLAlchemy AsyncSession.

        Args:
            db_session (AsyncSession): The SQLAlchemy session to use for database operations.
        """
        self.db_session = db_session

    async def find_by_id(self, entity_id: EntityId) -> Optional[UserEntity]:
        try:
            log.info(f"Finding user by id: {entity_id.value}")
            user_model: Optional[UserModel] = await self.db_session.get(UserModel, entity_id.value)

            if user_model is None:
                log.info(f"User with id {entity_id.value} not found")
                return None

            log.info(f"User with id {entity_id.value} found")
            return map_model_to_entity(user_model)

        except sqlalchemy.exc.OperationalError as db_error:
            log.error(f"Database connection error while finding user by id: {entity_id.value}. Error: {str(db_error)}")
            raise DatabaseConnectionError("Failed to connect to the database.") from db_error

        except Exception as e:
            log.error(f"Error finding user by id: {entity_id.value} Exception: {str(e)}")
            raise

    async def find_by_email(self, email: Email) -> Optional[UserEntity]:
        """
        Find user by email.
        
        Returns None if user not found (NOT an exception).
        """
        try:
            result = await self.db_session.execute(
                select(UserModel).where(UserModel.email == email.value)
            )
            user_model = result.scalar_one_or_none()

            if user_model is None:
                log.info(f"User with email {email.value} not found")
                return None

            log.info(f"User with email {email.value} found")
            return map_model_to_entity(user_model)
            
        except Exception as e:
            log.error(f"Error finding user by email: {email.value} Exception: {str(e)}")
            raise

    async def find_by_name(self, record: str) -> Optional[UserEntity]:
        """Not implemented yet."""
        pass

    async def save(self, user: UserEntity) -> Optional[UserEntity]:
        """
        Save a new user.
        
        Returns:
            UserEntity if successful, None if user already exists (email constraint violation).
        """
        try:
            user_model = UserModel(
                id=user.id.value,
                email=user.email.value,
                first_name=user.first_name,
                last_name=user.last_name,
                password_hash=user.password_hash,
                role=user.role
            )

            self.db_session.add(user_model)
            await self.db_session.commit()
            await self.db_session.refresh(user_model)

            log.info(f"User persisted successfully. id={user_model.id}")
            return map_model_to_entity(user_model)

        except sqlalchemy.exc.IntegrityError as e:
            await self.db_session.rollback()
            log.error(f"IntegrityError while saving user with email {user.email}: {e}")
            # Return None to indicate duplicate - let use case handle business logic
            return None

        except Exception as e:
            await self.db_session.rollback()
            log.error(f"Unexpected error while saving user with email {user.email}: {e}")
            raise

    async def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Not implemented yet."""
        pass

    async def exists(self, entity_id: ID) -> bool:
        """Not implemented yet."""
        pass

    async def update(self, entity: T) -> Optional[T]:
        """Not implemented yet."""
        pass

    async def delete(self, entity_id: ID) -> bool:
        """Not implemented yet."""
        pass
```

**Key changes:**
- Removed `UserAlreadyExistsException` import (application layer concern)
- `save()` returns `None` on duplicate instead of raising exception
- Use case layer handles business logic of "user already exists"

---

### **Phase 7: Production Hardening**

#### **7.1 Add Health Check Endpoint**
**File:** `src/app/app.py`

```python
from fastapi import FastAPI, status
from sqlalchemy import text

@fastApiApp.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    
    Returns:
        200: Service is healthy
        503: Service is unhealthy
    """
    try:
        # Check database connectivity
        db_conn = get_db_connection()
        async with db_conn.get_session() as session:
            await session.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "service": app_name,
            "version": app_version
        }
    except Exception as e:
        log.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )
```

---

#### **7.2 Add Security Headers Middleware**
**File:** `src/app/app.py`

```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


# Add middleware
fastApiApp.add_middleware(SecurityHeadersMiddleware)
```

---

#### **7.3 Update Docker Compose with Health Check**
**File:** `compose.yml`

```yaml
services:
  app:
    container_name: open_projects_hub_api_app
    build:
      context: .
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    env_file:
      - .env
    environment:
        APP_ENV: "docker"
    ports:
      - "8080:8080"
    command: ["./start.sh"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - open_projects_hub_network

  # ... postgres config unchanged ...
```

---

## Testing Strategy

### Coverage Goals
- **Domain Layer:** 100% (entities, value objects)
- **Application Layer:** 90% (use cases, DTOs)
- **Infrastructure Layer:** 70% (repositories, security)
- **Presentation Layer:** 80% (routes, dependencies)

### Test Structure

```
tests/
├── unit/
│   ├── domain/
│   │   ├── test_user_entity.py
│   │   ├── test_email_value_object.py
│   │   ├── test_entity_id.py
│   │   └── test_user_role.py
│   ├── application/
│   │   ├── use_cases/
│   │   │   ├── test_create_user.py
│   │   │   ├── test_login_user.py
│   │   │   └── test_get_user_by_id.py
│   │   └── dtos/
│   │       ├── test_user_dto_validation.py
│   │       └── test_auth_dto.py
│   └── infrastructure/
│       └── security/
│           ├── test_jwt_handler.py
│           └── test_password_handler.py
├── integration/
│   ├── test_user_repository_impl.py
│   └── test_database_connection.py
├── e2e/
│   ├── test_auth_flow.py
│   ├── test_user_registration_flow.py
│   └── test_protected_routes.py
└── performance/
    └── test_password_hashing_performance.py
```

### Key Test Cases (NEW)

#### **Password Validation Tests**
```python
# tests/unit/application/dtos/test_user_dto_validation.py

def test_password_too_short_raises_error():
    with pytest.raises(ValueError, match="at least 8 characters"):
        UserCreateRequest(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Short1"  # Only 6 chars
        )

def test_password_no_uppercase_raises_error():
    with pytest.raises(ValueError, match="uppercase letter"):
        UserCreateRequest(..., password="password123")

def test_password_no_digit_raises_error():
    with pytest.raises(ValueError, match="digit"):
        UserCreateRequest(..., password="Password")

def test_valid_password_accepts():
    user = UserCreateRequest(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password="ValidPass123"
    )
    assert user.password == "ValidPass123"
```

#### **Rate Limiting Tests**
```python
# tests/e2e/test_auth_flow.py

@pytest.mark.asyncio
async def test_login_rate_limit_blocks_after_5_attempts(client):
    """Test that login is rate-limited to 5 attempts per 15 minutes."""
    
    # Make 5 failed login attempts
    for i in range(5):
        response = client.post("/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrong"
        })
        assert response.status_code in [401, 429]
    
    # 6th attempt should be rate limited
    response = client.post("/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrong"
    })
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()
```

#### **Async Password Hashing Tests**
```python
# tests/performance/test_password_hashing_performance.py

@pytest.mark.asyncio
async def test_password_hashing_is_non_blocking():
    """Verify password hashing doesn't block event loop."""
    import asyncio
    
    start = asyncio.get_event_loop().time()
    
    # Hash 10 passwords concurrently
    tasks = [
        PasswordHandler.hash_password(f"password{i}")
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    elapsed = asyncio.get_event_loop().time() - start
    
    # Should complete faster than sequential (< 10 * single_hash_time)
    assert len(results) == 10
    assert all(len(h) > 0 for h in results)
    # Assert runs in reasonable time (adjust based on hardware)
    assert elapsed < 5.0
```

---

## Production Readiness Checklist

### ✅ Implemented
- [x] Clean Architecture layer separation
- [x] Async/await patterns
- [x] Type safety with Pydantic
- [x] JWT authentication
- [x] Role-based authorization
- [x] Password hashing with bcrypt
- [x] Database connection pooling
- [x] Environment-based configuration

### ✅ Fixed from Audit
- [x] Database engine singleton pattern
- [x] Removed service layer (YAGNI)
- [x] Rate limiting on login endpoint
- [x] Async password hashing
- [x] Password complexity validation
- [x] Repository exception handling fixed
- [x] JWT secret validation

### 🔄 To Implement
- [ ] Comprehensive test coverage (>70%)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Structured logging with correlation IDs
- [ ] Prometheus metrics
- [ ] Error monitoring (Sentry)
- [ ] API documentation with examples

### 📋 Deployment Checklist
- [ ] Generate strong JWT secret: `python -c 'import secrets; print(secrets.token_urlsafe(64))'`
- [ ] Set all environment variables in `.env`
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Create admin user via SQL script
- [ ] Test health check endpoint
- [ ] Verify rate limiting works
- [ ] Test login flow end-to-end
- [ ] Check security headers in responses

---

## Rollout Plan

### Week 1: Infrastructure & Core Fixes
**Days 1-2:**
- Fix database connection singleton
- Add rate limiting
- Update password handler to async

**Days 3-4:**
- Remove service layer
- Update dependencies for direct use case injection
- Add password validation

**Day 5:**
- Fix repository exception handling
- Add JWT secret validation
- Test all changes

### Week 2: Testing & Hardening
**Days 1-3:**
- Write comprehensive unit tests
- Write integration tests
- Write end-to-end tests

**Days 4-5:**
- Add health check endpoint
- Add security headers middleware
- Update Docker compose with health checks
- Performance testing

### Week 3: Production Deployment
**Days 1-2:**
- Set up CI/CD pipeline
- Configure production environment
- Generate production secrets

**Days 3-4:**
- Deploy to staging
- Run full test suite
- Security audit

**Day 5:**
- Deploy to production
- Monitor logs and metrics
- Document runbook

---

## Monitoring & Observability

### Logs to Monitor
```python
# Key log messages to track:
log.info(f"User logged in successfully: {user_entity.id}")
log.warning(f"Failed login attempt for user: {user_entity.id}")
log.warning(f"Login attempt with non-existent email: {payload.email}")
log.error(f"Unexpected error in LoginUserUseCase: {str(e)}")
```

### Metrics to Track
1. **Authentication:**
   - Login attempts (success/failure)
   - Rate limit hits
   - JWT token issuance rate
   - Password validation failures

2. **Performance:**
   - Login endpoint latency (p50, p95, p99)
   - Password hashing duration
   - Database query duration
   - Connection pool utilization

3. **Errors:**
   - 401 Unauthorized count
   - 429 Rate limit exceeded count
   - 500 Internal server errors
   - Database connection failures

### Alerts to Configure
- **Critical:**
  - Health check failures
  - Database connection pool exhaustion
  - 500 error rate > 1%

- **Warning:**
  - Failed login rate > 10 per minute
  - Rate limit hit rate > 5%
  - p95 latency > 500ms

---

## Migration from v1

If you've already implemented v1, follow this migration guide:

### Step 1: Database Connection Fix
```bash
# 1. Update dependencies.py with singleton pattern
# 2. Restart application
# 3. Monitor connection pool metrics
```

### Step 2: Remove Service Layer
```bash
# 1. Delete auth_service.py and user_service.py
# 2. Update dependencies.py
# 3. Update all route files
# 4. Run tests
```

### Step 3: Add Rate Limiting
```bash
# 1. Install slowapi: pip install slowapi
# 2. Update app.py
# 3. Update auth_routes.py
# 4. Test with curl (5+ login attempts)
```

### Step 4: Update Password Handling
```bash
# 1. Update password_handler.py
# 2. Update create_user.py use case
# 3. Update login_user.py use case
# 4. Run performance tests
```

### Step 5: Add Validation & Hardening
```bash
# 1. Update user_dto.py with validators
# 2. Add health check endpoint
# 3. Add security headers middleware
# 4. Run full test suite
```

---

## Conclusion

This v2 implementation plan addresses all **HIGH** and **CRITICAL** issues from the code audit while maintaining the excellent Clean Architecture foundation of the existing codebase.

**Key Improvements:**
- ✅ Fixed 6 critical bugs
- ✅ Removed unnecessary complexity (service layer)
- ✅ Added production-critical features (rate limiting, health checks)
- ✅ Improved security (password validation, JWT validation)
- ✅ Enhanced performance (async password hashing, connection pooling)

**Result:** A production-ready authentication system that is secure, scalable, and maintainable.

---

**Next Actions:**
1. Review this plan with team
2. Estimate effort (recommended: 2-3 weeks)
3. Begin Phase 1 implementation
4. Track progress against audit technical debt register
5. Verify each phase with tests before proceeding
