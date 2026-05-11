# Scalability Review — 26-05-10

## Overview

This document evaluates the scalability characteristics of the Open Projects Hub API — how it behaves under increased load, and what changes are required to support growth in users, data, and requests.

---

## Current Architecture

```
Client → [gunicorn + uvicorn workers] → FastAPI app → PostgreSQL
```

- **Concurrency model:** Async I/O (asyncio). FastAPI routes use `async def`; database calls use SQLAlchemy 2.0 async with asyncpg.
- **Process model:** gunicorn manages multiple uvicorn worker processes. The number of workers is configurable in `gunicorn_conf.py`.
- **Deployment:** Docker container defined in `Dockerfile`; orchestration via `compose.yml` (local/dev).

---

## Horizontal Scalability

### Stateless Application Layer ✅

The API is stateless — JWT tokens carry all session state. Multiple application instances can handle requests from the same user without shared session storage.

### Shared Database ⚠️

PostgreSQL is the single shared state. Scaling the application tier is straightforward, but all instances converge on the same database. Read scalability may become a bottleneck before write scalability.

### Rate Limiter State ⚠️

The slowapi limiter uses **in-process state** by default. With multiple application instances (horizontal scaling), each instance tracks its own rate-limit counters independently. A user can bypass the 100 req/min limit by routing requests across N instances, achieving N × 100 req/min.

**Fix:** Replace in-process storage with a Redis-backed store for the rate limiter.

---

## Database Scalability

### Connection Pool

SQLAlchemy async engine uses default pool settings. No explicit `pool_size`, `max_overflow`, or `pool_pre_ping` is configured.

**Implications:**
- Default `pool_size` is 5 with `max_overflow` of 10 — a total of 15 connections per process.
- With N gunicorn workers, the database receives up to N × 15 connections.
- PostgreSQL defaults to 100 max connections. With as few as 7 workers, the default pool will be close to exhaustion.

**Fix:** Configure the pool explicitly and/or use PgBouncer as a connection proxy.

### Query Patterns

The migrations create appropriate indexes for common query patterns:

| Table | Indexed Columns |
|---|---|
| `users` | `email` (unique), `created_at`, `updated_at` |
| `projects` | `created_by`, `status`, `created_at` |
| `stories` | `project_id`, `created_by`, `assigned_to`, `status`, `priority`, `created_at` |

### Gaps

- **No pagination limits enforced.** List endpoints accept a `limit` query parameter but there is no upper bound enforced in the application layer. A client could request 10 000 records in one call.
- **No query result caching.** The dashboard stats endpoint (`GET /v1/dashboard/stats`) likely performs aggregate queries on every call with no caching.
- **No read replica support.** All queries hit the primary database, including read-heavy operations like dashboard stats.

---

## Caching

There is **no caching layer** in the current design. The `lru_cache` decorator is used for the JWT handler singleton (`get_jwt_handler`) and is limited to in-process caching only.

### High-value Caching Targets

| Endpoint | Caching Strategy | TTL Suggestion |
|---|---|---|
| `GET /v1/dashboard/stats` | Application-level (Redis) | 60 seconds |
| `GET /v1/projects` | Optional HTTP cache headers (`Cache-Control: private, max-age=30`) | 30 seconds |
| `GET /v1/user/preferences` | User-specific in-memory or Redis | 5 minutes |

---

## Async I/O Quality

All database operations use the SQLAlchemy async engine with `await` correctly. Route handlers use `async def` throughout.

One exception: `get_jwt_handler()` uses `@lru_cache` which is a synchronous construct, but this is acceptable because the function body is synchronous (it only reads configuration and constructs an object).

---

## Compute Scalability

### CPU-Bound Operations

- bcrypt password hashing is CPU-bound. For high registration rates, this will saturate a worker.
- **Fix:** Run bcrypt in a thread pool executor (`asyncio.get_event_loop().run_in_executor(...)`) to avoid blocking the event loop.

### I/O-Bound Operations

All database I/O is properly async. No blocking I/O was found in the request path.

---

## Infrastructure Considerations

| Component | Current State | Production Recommendation |
|---|---|---|
| App server | gunicorn + uvicorn | ✅ Suitable; configure worker count = 2 × CPU cores + 1 |
| Container | Docker | ✅ Ready; push to container registry |
| Orchestration | docker-compose (local only) | ❌ Migrate to Kubernetes or ECS for production |
| Database | PostgreSQL (single instance) | Add read replica for read-heavy workloads |
| Cache | None | Add Redis for rate limiter, sessions, and query cache |
| Load balancer | Not configured | Required for horizontal scaling |
| CDN/TLS termination | Not configured | Offload TLS to a load balancer or reverse proxy |

---

## Load Estimation

Based on typical project management tool usage:

| Scenario | Estimated RPS | Current Capacity | Notes |
|---|---|---|---|
| MVP / early users | < 10 RPS | ✅ Comfortable | Single instance sufficient |
| Small team (50 DAU) | 10–50 RPS | ✅ Adequate | 2–4 workers |
| Growing product (500 DAU) | 50–500 RPS | ⚠️ Needs tuning | Pool config, Redis rate limiter |
| Scale (5000+ DAU) | 500+ RPS | ❌ Requires redesign | Read replica, caching, multiple instances |

---

## Recommendations

| Priority | Finding | Recommendation |
|---|---|---|
| High | In-process rate limiter state | Replace with Redis-backed slowapi storage |
| High | No connection pool configuration | Set `pool_size`, `max_overflow`, add `pool_pre_ping=True` |
| High | bcrypt is blocking | Wrap in `run_in_executor` for async-safe execution |
| Medium | No caching | Add Redis; cache dashboard stats and user preferences |
| Medium | No pagination upper bound | Enforce `max_limit` (e.g. 100) on all list endpoints |
| Low | No read replica | Plan for a PostgreSQL read replica as DAU grows |
| Low | docker-compose in production | Migrate to Kubernetes or managed container service |

---

**Audit date:** 10 May 2026  
**Audited by:** GitHub Copilot Coding Agent
