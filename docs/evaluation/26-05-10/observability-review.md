# Observability Review — 26-05-10

## Overview

This document assesses the observability posture of the Open Projects Hub API across the three pillars: **logs**, **metrics**, and **traces**.

---

## Current State Summary

| Pillar | Status | Detail |
|---|---|---|
| Logs | ⚠️ Partial | Plain-text stdlib logging; consistent usage; no structured format |
| Metrics | ❌ Missing | No metrics endpoint; no collection agent configured |
| Traces | ❌ Missing | No distributed tracing; no correlation/request IDs |

---

## Logs

### Implementation

Logging is implemented in `src/app/shared/utils/log_util.py`:

```python
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
```

- A single named logger (`log`) is imported and used throughout the codebase.
- Log level is configurable via `LOG_LEVEL` environment variable.
- The comment in `log_util.py` states the format is *"compatible with Datadog log ingestion"*, indicating future Datadog integration is planned.

### Log Usage Audit

| Location | Log Level | Message Quality |
|---|---|---|
| `login_user.py` | WARNING on failed login (by email), WARNING on bad password (by user ID only) | Good — no PII leakage of password |
| `jwt_handler.py` | WARNING on expired/invalid tokens, INFO on creation | Good |
| `app.py` exception handlers | WARNING (404, 400, 409), ERROR (422, 500) | Good level mapping |
| `app.py` health check | ERROR on DB failure | Good |
| `password_handler.py` | Not reviewed — assumed via use cases | N/A |

### Gaps

1. **No structured / JSON logging.** Plain-text logs cannot be reliably parsed by log aggregation tools (Datadog, CloudWatch, Loki) without a log parsing pipeline. Every field that is not part of the fixed format (e.g. resource type, user ID) must be extracted via regex.

2. **No request-level logging.** There is no middleware that logs each incoming request (method, path, status code, latency). Operations teams cannot query "how many 4xx responses did `/v1/auth/login` return in the last hour?" without a dedicated middleware.

3. **No correlation / request ID.** Requests have no unique identifier. When a user reports a failure, there is no token to trace that specific request across log lines.

4. **Log format inconsistency.** Free-form f-string messages are used throughout. The structure of logged data is not enforced, making log-based alerting brittle.

5. **No log sampling for high-volume paths.** All requests log at equal verbosity. Under load, INFO-level logs from hot paths (health check polling, dashboard stats) will dominate.

---

## Metrics

### Current State

No metrics collection exists. There is no:
- Prometheus `/metrics` endpoint
- StatsD client
- Application performance monitoring (APM) agent

### Recommended Metrics

A production API should at minimum expose:

| Metric | Type | Description |
|---|---|---|
| `http_requests_total` | Counter | Total requests by method, path, status code |
| `http_request_duration_seconds` | Histogram | Request latency by method and path |
| `http_requests_in_progress` | Gauge | In-flight request count |
| `db_query_duration_seconds` | Histogram | Database query latency |
| `login_attempts_total` | Counter | Login attempts by outcome (success/failure) |
| `token_validations_total` | Counter | JWT validations by outcome |
| `rate_limit_hits_total` | Counter | Rate-limited requests |

### Quick Win

FastAPI integrates with `prometheus-fastapi-instrumentator`, which auto-instruments all routes with request count and latency metrics with a single line:

```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(fastApiApp).expose(fastApiApp)
```

---

## Traces

### Current State

No distributed tracing is configured. There is no:
- OpenTelemetry SDK
- Jaeger / Zipkin / Tempo integration
- Trace/span propagation headers

### Why Traces Matter

Without traces, when a slow request is reported:
1. Logs must be searched manually with no request ID to filter on.
2. It is impossible to know whether latency came from the database, a network call, or Python computation.
3. N+1 query patterns are invisible.

### Recommended Approach

Integrate OpenTelemetry with auto-instrumentation for FastAPI and SQLAlchemy:

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

FastAPIInstrumentor.instrument_app(fastApiApp)
SQLAlchemyInstrumentor().instrument()
```

Traces can be exported to any OTLP-compatible backend (Jaeger, Grafana Tempo, Datadog APM).

---

## Health Check

A `/health` endpoint exists and checks database connectivity:

```
GET /health → 200 { "status": "healthy", "database": "connected" }
             → 503 { "status": "unhealthy", "error": "database_unreachable" }
```

**Assessment: Good baseline.** This is sufficient for a simple liveness + readiness check.

**Gaps:**
- The health check does not distinguish between **liveness** (the process is alive) and **readiness** (the service can handle traffic). Kubernetes requires both.
- The health check does not report version or last-deployed-at, making it harder to confirm a deployment succeeded.

---

## Alerting

No alerting configuration exists (no Alertmanager rules, no Datadog monitors, no CloudWatch alarms). This is expected at the current maturity level but must be addressed before production.

---

## Recommendations

| Priority | Finding | Recommendation |
|---|---|---|
| High | No structured logging | Switch to JSON log format (e.g. `python-json-logger`) |
| High | No request logging middleware | Add middleware logging method, path, status, latency, request ID |
| High | No request correlation ID | Generate and propagate `X-Request-ID` header; include in all log messages |
| High | No metrics | Add `prometheus-fastapi-instrumentator` for auto-instrumented HTTP metrics |
| Medium | No distributed tracing | Integrate OpenTelemetry with FastAPI and SQLAlchemy instrumentation |
| Medium | No separate liveness/readiness probes | Split `/health/live` (process alive) and `/health/ready` (DB connected) |
| Low | No log sampling | Add sampling for high-volume, low-value log paths (e.g. health check polling) |
| Low | No alerting | Define SLO-based alerts (error rate, p99 latency) once metrics are in place |

---

**Audit date:** 10 May 2026  
**Audited by:** GitHub Copilot Coding Agent
