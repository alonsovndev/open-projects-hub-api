# Improvement Roadmap — 26-05-10

## Overview

This document consolidates findings from all specialised reviews into a prioritised, actionable improvement roadmap. Items are grouped by theme and ordered by impact.

---

## Priority Legend

| Priority | Definition |
|---|---|
| 🔴 Critical | Security or stability risk; should be addressed before wider user adoption |
| 🟠 High | Significant operational risk; address within the next sprint |
| 🟡 Medium | Quality or experience gap; address within the next 1–2 months |
| 🟢 Low | Improvement or best practice; schedule as capacity allows |

---

## Theme 1 — Security

| # | Priority | Finding | Action | Reference |
|---|---|---|---|---|
| S-1 | 🔴 Critical | Auth endpoints not separately rate-limited | Add per-route limits: 10 req/min for `/v1/auth/login`, 5 req/min for `/v1/auth/register` | security-review.md |
| S-2 | 🔴 Critical | No refresh token revocation | Implement a Redis-backed token blocklist, or reduce access token TTL to 15 min + single-use refresh token rotation | security-review.md |
| S-3 | 🟠 High | No account lockout on repeated failed logins | Add progressive delay or temporary lockout after 5 consecutive failures per account | security-review.md |
| S-4 | 🟡 Medium | Unbounded free-text fields | Add `max_length` to Pydantic fields: `name` ≤ 255, `description` ≤ 10 000 | api-review.md, security-review.md |
| S-5 | 🟡 Medium | Secrets management via env vars only | Integrate with AWS Secrets Manager, HashiCorp Vault, or equivalent for production | security-review.md |
| S-6 | 🟢 Low | No project ownership gate on mutations | Add a project owner/admin check equivalent to the story ownership check | security-review.md |

---

## Theme 2 — Observability

| # | Priority | Finding | Action | Reference |
|---|---|---|---|---|
| O-1 | 🔴 Critical | No request logging or correlation IDs | Add HTTP middleware that logs method, path, status, latency, and a generated `X-Request-ID` for every request | observability-review.md |
| O-2 | 🟠 High | No structured logging | Replace plain-text format with JSON (use `python-json-logger`); inject `request_id`, `user_id`, `feature` as log fields | observability-review.md |
| O-3 | 🟠 High | No metrics | Add `prometheus-fastapi-instrumentator` for auto-instrumented HTTP metrics; expose `/metrics` endpoint | observability-review.md |
| O-4 | 🟡 Medium | No distributed tracing | Integrate OpenTelemetry SDK with FastAPI and SQLAlchemy auto-instrumentation | observability-review.md |
| O-5 | 🟡 Medium | No split liveness / readiness probes | Separate `/health/live` (process alive) and `/health/ready` (DB connected) for Kubernetes compatibility | observability-review.md |
| O-6 | 🟢 Low | No alerting | Define SLO-based alerts (error rate, p99 latency) in Datadog or AlertManager once metrics are available | observability-review.md |

---

## Theme 3 — Scalability & Performance

| # | Priority | Finding | Action | Reference |
|---|---|---|---|---|
| P-1 | 🟠 High | In-process rate limiter (breaks horizontal scaling) | Configure slowapi with a Redis backend so all instances share the same counter | scalability-review.md |
| P-2 | 🟠 High | No database connection pool configuration | Set `pool_size`, `max_overflow`, and `pool_pre_ping=True` on the async engine; document recommended values | scalability-review.md |
| P-3 | 🟠 High | bcrypt hashing blocks the event loop | Wrap `PasswordHandler.hash_password` / `verify_password` in `asyncio.get_event_loop().run_in_executor(None, ...)` | scalability-review.md |
| P-4 | 🟡 Medium | No caching | Add Redis; cache dashboard stats (TTL 60 s) and user preferences (TTL 5 min) | scalability-review.md |
| P-5 | 🟡 Medium | No pagination upper bound | Enforce `max_limit` (e.g. 100) on all list endpoints | api-review.md, scalability-review.md |
| P-6 | 🟢 Low | docker-compose in production | Migrate to Kubernetes or a managed container service (ECS, Cloud Run) | scalability-review.md |

---

## Theme 4 — API Design

| # | Priority | Finding | Action | Reference |
|---|---|---|---|---|
| A-1 | 🟡 Medium | Singular `/v1/user` resource name | Rename to `/v1/users` for REST consistency (coordinate with frontend) | api-review.md |
| A-2 | 🟡 Medium | Dual error envelopes (domain vs Pydantic 422) | Override FastAPI's default `RequestValidationError` handler to use the same `{ "error": "...", "message": "..." }` shape | api-review.md |
| A-3 | 🟡 Medium | No pagination envelope on list responses | Wrap list responses in `{ "total": N, "page": N, "per_page": N, "items": [...] }` | api-review.md |
| A-4 | 🟢 Low | No `Location` header on POST | Return `Location: /v1/resource/{id}` after 201 responses | api-review.md |
| A-5 | 🟢 Low | Filter as path segment (`/stories/project/{id}`) | Prefer query parameter: `GET /v1/stories?project_id={id}` | api-review.md |
| A-6 | 🟢 Low | No versioned OpenAPI spec committed | Export and commit `openapi.yaml` to the repository on each release | api-review.md |

---

## Theme 5 — Architecture

| # | Priority | Finding | Action | Reference |
|---|---|---|---|---|
| AR-1 | 🟡 Medium | `app.py` is a god file (~280 lines) | Extract into `middleware.py`, `exception_handlers.py`, and `router_registry.py` | architecture-review.md |
| AR-2 | 🟡 Medium | No Unit-of-Work pattern | Introduce a `UnitOfWork` abstraction for multi-repository transactions | architecture-review.md |
| AR-3 | 🟢 Low | No domain events | Add a domain event publisher interface for side effects (email, audit log) | architecture-review.md |
| AR-4 | 🟢 Low | Dashboard has no domain layer | Create `dashboard/domain/` if dashboard-specific invariants emerge | architecture-review.md |

---

## Theme 6 — Testing

| # | Priority | Finding | Action | Reference |
|---|---|---|---|---|
| T-1 | 🟠 High | No database integration tests | Add a `tests/integration/` suite using testcontainers (PostgreSQL) to test repository implementations | testing-review.md |
| T-2 | 🟡 Medium | No CI coverage reporting | Add `pytest-cov` and enforce ≥ 80% line coverage in CI | testing-review.md |
| T-3 | 🟡 Medium | Duplicated `client` fixture per file | Move shared fixture to `conftest.py` | testing-review.md |
| T-4 | 🟢 Low | No contract / schema tests | Add snapshot tests for critical response shapes | testing-review.md |
| T-5 | 🟢 Low | No load tests | Add a `locust` or `k6` load test script for staging | testing-review.md |

---

## Suggested Sprint Plan

### Sprint 1 — Security Baseline (1–2 weeks)

- S-1: Per-endpoint rate limits on auth routes
- S-2: Refresh token revocation (Redis blocklist)
- O-1: Request logging middleware with correlation IDs
- O-2: Structured JSON logging

### Sprint 2 — Observability (1–2 weeks)

- O-3: Prometheus metrics endpoint
- O-4: OpenTelemetry tracing
- O-5: Liveness / readiness health check split
- P-1: Redis-backed rate limiter

### Sprint 3 — Scalability & API Polish (1–2 weeks)

- P-2: Connection pool configuration
- P-3: bcrypt async fix
- P-4: Redis caching for hot endpoints
- A-2: Unified error envelope
- A-3: Pagination envelope
- P-5: Pagination upper bound

### Sprint 4 — Architecture & Testing Hardening (2+ weeks)

- T-1: Database integration tests
- AR-1: app.py decomposition
- AR-2: Unit-of-Work pattern
- T-2: CI coverage enforcement
- S-3: Account lockout

---

**Audit date:** 10 May 2026  
**Audited by:** GitHub Copilot Coding Agent
