---
**Status:** IN PROGRESS  
**Created:** 2026-05-11  
**Last Updated:** 2026-05-11

---

# Database Integration Tests

## Overview

This document describes the database integration test suite for the Open Projects Hub API. These tests verify repository implementations, SQL queries, database constraints, and data integrity against a real PostgreSQL database.

## Test Structure

```
src/tests/integration/
├── conftest.py                              # Test fixtures and database setup
├── test_project_repository_integration.py   # Project repository tests
├── test_user_repository_integration.py      # User repository tests
└── test_story_repository_integration.py     # Story repository tests
```

## Prerequisites

### 1. PostgreSQL Database

Integration tests require a running PostgreSQL database. You have two options:

#### Option A: Docker Compose (Recommended)

```bash
# Start PostgreSQL container
docker compose up -d postgres

# Verify database is running
docker compose ps
```

#### Option B: Local PostgreSQL

Ensure PostgreSQL is running locally on port 5432 with credentials matching your test configuration.

### 2. Environment Configuration

Set up your `.env` file with test database credentials:

```bash
# Test Database Configuration
POSTGRES_PASSWORD=your_test_password
APP_ENV=test
```

### 3. Database Schema

The integration tests automatically create and drop tables for each test session using SQLAlchemy metadata.

## Running Integration Tests

### Run All Integration Tests

```bash
# Run all tests marked with @pytest.mark.e2e
pytest -m e2e -v
```

### Run Specific Test Files

```bash
# Project repository tests only
pytest src/tests/integration/test_project_repository_integration.py -v

# User repository tests only
pytest src/tests/integration/test_user_repository_integration.py -v

# Story repository tests only
pytest src/tests/integration/test_story_repository_integration.py -v
```

### Run Specific Test Cases

```bash
# Run single test method
pytest src/tests/integration/test_project_repository_integration.py::TestProjectRepositoryIntegration::test_save_creates_new_project -v

# Run all tests matching a pattern
pytest src/tests/integration/ -k "foreign_key" -v
```

### Run with Coverage

```bash
# Run integration tests with coverage report
pytest -m e2e --cov=src/app/features --cov-report=html
```

## Test Categories

### Project Repository Tests (17 tests)

Tests for `ProjectRepositoryImpl`:

- **CRUD Operations:**
  - Create, read, update, delete projects
  - Handle nonexistent records gracefully

- **Querying & Filtering:**
  - Find all with pagination (limit, offset)
  - Filter by status (active, completed, archived)
  - Count total projects with filters

- **Data Integrity:**
  - Concurrent saves maintain integrity
  - Proper ordering (most recent first)

**File:** `test_project_repository_integration.py`

### User Repository Tests (13 tests)

Tests for `UserRepositoryImpl`:

- **CRUD Operations:**
  - Create, read, update, delete users
  - Find by email address

- **Constraints:**
  - Email uniqueness enforcement
  - Case-insensitive email search

- **Password Handling:**
  - Password hash storage and retrieval
  - Hash integrity verification

**File:** `test_user_repository_integration.py`

### Story Repository Tests (15 tests)

Tests for `StoryRepositoryImpl`:

- **CRUD Operations:**
  - Create, read, update, delete stories
  - Update story assignments

- **Foreign Key Constraints:**
  - Enforce valid project_id references
  - Enforce valid assigned_to user references

- **Complex Filtering:**
  - Filter by status (todo, in_progress, done)
  - Filter by priority (low, medium, high)
  - Filter by project_id
  - Filter by assigned user
  - Combined multi-filter queries

- **Pagination:**
  - Paginate with project filter
  - Verify no data overlap between pages

**File:** `test_story_repository_integration.py`

## Test Fixtures

### Session-Scoped Fixtures

**`test_engine`**
- Creates async database engine
- Sets up database schema before tests
- Tears down schema after all tests
- Shared across all tests in session

### Function-Scoped Fixtures

**`db_session`**
- Provides fresh database session for each test
- Uses transactions for test isolation
- Automatically rolls back after test
- Recommended for most tests

**`clean_db`**
- Truncates all tables before test
- Use for tests requiring guaranteed clean state
- Slower than `db_session` but more thorough

**`test_project`** (Story tests only)
- Creates a test project for foreign key relationships
- Required for story creation

**`test_user`** (Story tests only)
- Creates a test user for foreign key relationships
- Required for story creation

## Test Isolation Strategy

### Transaction-Based Isolation (Default)

Most tests use the `db_session` fixture which wraps each test in a transaction that is rolled back after completion. This provides:

- ✅ Fast test execution
- ✅ Automatic cleanup
- ✅ No cross-test data contamination
- ⚠️ May not catch some constraint violations

### Truncation-Based Isolation

Tests requiring guaranteed isolation use the `clean_db` fixture which truncates all tables. Use when:

- Testing uniqueness constraints
- Verifying constraint violations
- Need absolute certainty of clean state

## Verifying Test Coverage

Integration tests verify:

1. **SQL Query Correctness**
   - SELECT, INSERT, UPDATE, DELETE operations
   - WHERE clauses and filtering
   - ORDER BY and pagination

2. **Database Constraints**
   - Primary keys
   - Foreign keys
   - Unique constraints
   - NOT NULL constraints

3. **Data Integrity**
   - Concurrent operations
   - Transaction handling
   - Referential integrity

4. **Repository Implementation**
   - Domain entity ↔ database model mapping
   - Error handling for database failures
   - Proper async/await patterns

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: open-projects-hub-admin
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: open-projects-hub-db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run integration tests
        env:
          POSTGRES_PASSWORD: test_password
          APP_ENV: test
        run: |
          pytest -m e2e -v --cov=src/app/features
```

## Troubleshooting

### Database Connection Errors

**Problem:** `connection refused` errors

**Solution:**
```bash
# Verify PostgreSQL is running
docker compose ps postgres

# Check logs for errors
docker compose logs postgres

# Restart if needed
docker compose restart postgres
```

### Test Isolation Issues

**Problem:** Tests fail intermittently due to leftover data

**Solution:**
```python
# Use clean_db fixture instead of db_session
async def test_with_clean_state(clean_db: AsyncSession):
    # Test code here
    pass
```

### Foreign Key Constraint Violations

**Problem:** Tests fail with foreign key errors

**Solution:**
- Ensure test fixtures create dependent entities first
- Use `test_project` and `test_user` fixtures in story tests
- Verify entity IDs match foreign key references

### Slow Test Execution

**Problem:** Integration tests take too long

**Solution:**
```bash
# Run tests in parallel (requires pytest-xdist)
pytest -m e2e -n auto -v

# Run only changed tests
pytest -m e2e --lf -v  # Last failed
pytest -m e2e --ff -v  # Failed first
```

## Best Practices

### 1. Use Transactions for Isolation

```python
@pytest.mark.e2e
async def test_something(db_session: AsyncSession):
    # Transaction automatically rolls back after test
    repository = MyRepository(db_session)
    await repository.save(entity)
    await db_session.commit()
    # Rollback happens automatically
```

### 2. Test Both Happy and Error Paths

```python
async def test_foreign_key_constraint(db_session: AsyncSession):
    # Test constraint violation
    with pytest.raises(IntegrityError):
        await repository.save(invalid_entity)
        await db_session.commit()
```

### 3. Verify Data Persistence

```python
async def test_save_and_retrieve(db_session: AsyncSession):
    # Save
    await repository.save(entity)
    await db_session.commit()

    # Retrieve and verify
    found = await repository.find_by_id(entity.id.value)
    assert found.name == entity.name
```

### 4. Test Complex Queries

```python
async def test_complex_filtering(db_session: AsyncSession):
    # Test multiple filters combined
    results = await repository.find_all(status="active", priority="high", assigned_to=user_id, limit=10)
    # Verify filtering logic
```

### 5. Keep Tests Independent

- Don't rely on execution order
- Create necessary data in fixtures or test setup
- Use unique identifiers (UUIDs) to avoid conflicts

## Performance Considerations

### Session Scope vs Function Scope

- **Session-scoped engine:** Shared across all tests (faster)
- **Function-scoped session:** Fresh per test (isolated)

### Database Setup Strategies

Current implementation creates/drops schema per session:

```python
# Session setup
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

# Session teardown
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)
```

For faster iterations during development, consider using Alembic migrations instead.

## Maintenance

### Adding New Integration Tests

1. Create test file in `src/tests/integration/`
2. Import necessary repositories and entities
3. Mark tests with `@pytest.mark.e2e` and `@pytest.mark.asyncio`
4. Use appropriate fixtures (`db_session` or `clean_db`)
5. Follow existing naming conventions

### Updating After Schema Changes

When database schema changes:

1. Update SQLAlchemy models
2. Create/update Alembic migration
3. Run integration tests to verify compatibility
4. Update test fixtures if needed

## Test Metrics

### Current Coverage

- **Project Repository:** 17 tests, ~95% coverage
- **User Repository:** 13 tests, ~90% coverage
- **Story Repository:** 15 tests, ~92% coverage
- **Total:** 45 integration tests

### Target Metrics

- Line coverage: ≥ 80%
- Repository methods: 100%
- Critical paths: 100%
- Error handling: 100%

## References

- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Next Steps:**
- Add integration tests for remaining repositories
- Implement parallel test execution
- Add performance benchmarks
- Configure CI/CD pipeline
