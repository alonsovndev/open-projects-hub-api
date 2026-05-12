# Testing Review — 26-05-10

## Overview

This document evaluates the test suite of the Open Projects Hub API — its coverage, quality, structure, and gaps.

---

## Test Infrastructure

| Component | Tool | Notes |
|---|---|---|
| Test framework | pytest 8.3.4 | Configured in `pytest.ini` |
| Async support | pytest-asyncio 0.25.3 | Required for async test functions |
| HTTP test client | FastAPI `TestClient` (via httpx) | Synchronous requests against the real FastAPI app |
| Fixtures | Per-file `@pytest.fixture` | Consistent pattern across all test files |
| Test database | None | All tests use mocked/in-memory repositories |

---

## Test Structure

```
src/tests/
├── conftest.py
├── application/                     # Use case unit tests
├── domain/                          # Domain entity / value object tests
├── infrastructure/                  # Repository / adapter tests
└── presentation/
    └── api/
        ├── test_auth_login.py
        ├── test_auth_protected_routes.py
        ├── test_auth_register.py
        ├── test_health_check.py
        ├── test_preferences.py
        ├── test_rate_limiting.py
        ├── test_security_headers.py
        ├── test_user_password.py
        ├── test_user_profile.py
        ├── dashboard/
        │   └── test_dashboard_stats.py
        ├── projects/
        │   └── test_projects.py
        └── stories/
            └── test_stories.py
```

---

## Test Coverage by Feature

### Authentication ✅

**Files:** `test_auth_login.py`, `test_auth_register.py`, `test_auth_protected_routes.py`

| Scenario | Covered? |
|---|---|
| Successful login returns 200 with token, email, displayName, loggedInAt | ✅ |
| Login with unknown email returns 401 | ✅ |
| Login with wrong password returns 401 | ✅ |
| Login response contains access and refresh tokens | ✅ |
| Register with valid data returns 201 | ✅ |
| Register with duplicate email returns 409 | ✅ |
| Register with invalid email returns 422 | ✅ |
| Protected routes return 401 without token | ✅ |
| Protected routes return 401 with expired/invalid token | ✅ |
| Admin-only routes return 403 for non-admin users | ✅ |

### Security Headers ✅

**File:** `test_security_headers.py`

All 7 security headers are tested on the root endpoint and health endpoint. HSTS absence in non-production is also verified.

### Rate Limiting ✅

**File:** `test_rate_limiting.py`

Rate limit threshold triggering is covered.

### Health Check ✅

**File:** `test_health_check.py`

Health endpoint 200 response and DB-disconnected 503 response are covered.

### User Profile ✅

**File:** `test_user_profile.py`

Get and update profile scenarios are covered.

### User Preferences ✅

**File:** `test_preferences.py`

Get and update preference scenarios are covered.

### Password Change ✅

**File:** `test_user_password.py`

Correct current password, incorrect current password, and new password validation are covered.

### Projects ✅

**File:** `projects/test_projects.py`

CRUD scenarios (create, list, get by ID, update, delete) with both success and error paths are covered.

### Stories ✅

**File:** `stories/test_stories.py`

CRUD scenarios and story assignment are covered.

### Dashboard ✅

**File:** `dashboard/test_dashboard_stats.py`

Dashboard stats retrieval is covered.

---

## Test Quality Assessment

### Strengths

1. **Consistent fixture pattern.** Every test file creates a `TestClient` via a `@pytest.fixture`. This is clean and avoids shared state between test classes.

2. **One assertion theme per test.** Tests are focused — each test function validates a single scenario, making failures easy to diagnose.

3. **Both status code and payload shape are verified.** Tests check `response.status_code` and key fields in `response.json()`.

4. **Negative paths are covered.** Invalid credentials, missing tokens, permission failures, and conflict errors all have dedicated tests.

5. **Security-specific test file.** Having `test_security_headers.py` and `test_rate_limiting.py` as separate, dedicated files signals that security is treated as a first-class concern.

### Weaknesses

1. **No database integration tests.** All tests operate on mocked repositories. The actual SQL queries, foreign key constraints, and index behaviour are never exercised in the test suite. A migration or schema change could silently break production without test failures.

2. **Test isolation relies on application-level mocking, not test transactions.** Without a real database, tests cannot verify that concurrent writes are handled correctly or that cascading deletes work as expected.

3. **No performance/load tests.** There are no benchmarks or load tests to verify that the async implementation holds up under concurrent requests.

4. **No contract tests.** There are no consumer-driven contract tests to verify the API response shapes match what frontend clients expect.

5. **No mutation tests.** The test suite has not been run through a mutation testing tool (e.g. `mutmut`) to verify that tests are actually capable of catching bugs.

6. **`conftest.py` not explored.** If shared fixtures exist in `conftest.py`, they are not consistently referenced in feature tests. Each file redeclares its own `client` fixture.

---

## Test Run Instructions

```bash
# Full test suite
python3 -m pytest

# Quiet output
python3 -m pytest -q

# Single file
python3 -m pytest src/tests/presentation/api/test_auth_login.py -q

# Single test function
python3 -m pytest src/tests/presentation/api/test_auth_login.py::test_login_success_returns_frontend_shape -q
```

---

## Recommendations

| Priority | Finding | Recommendation |
|---|---|---|
| High | No database integration tests | Add a test suite that runs against a real PostgreSQL instance (use testcontainers or a dedicated test DB in CI) |
| Medium | No CI coverage reporting | Integrate `pytest-cov` and enforce a minimum coverage threshold (e.g. 80%) in CI |
| Medium | Duplicated `client` fixture | Move the shared `TestClient` fixture to `conftest.py` |
| Low | No contract tests | Add snapshot or schema-validation tests for critical response shapes |
| Low | No mutation testing | Run `mutmut` periodically to verify test effectiveness |
| Low | No performance tests | Add a `locust` or `k6` script for basic load testing against a staging environment |

---

**Audit date:** 10 May 2026  
**Audited by:** GitHub Copilot Coding Agent
