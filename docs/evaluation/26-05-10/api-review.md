# API Review — 26-05-10

## Overview

This document evaluates the REST API surface of the Open Projects Hub API — its structure, conventions, versioning, request/response contracts, error handling, and documentation.

---

## Endpoints Inventory

### Root & Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | None | Welcome message |
| GET | `/health` | None | Database connectivity health check |

### Authentication — `/v1/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/v1/auth/login` | None | Authenticate and issue access + refresh tokens |
| POST | `/v1/auth/register` | None | Create new user account |
| POST | `/v1/auth/refresh` | Bearer (refresh token) | Issue new access token |

### Users — `/v1/user`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/v1/user/profile` | Bearer | Retrieve own profile |
| PATCH | `/v1/user/profile` | Bearer | Update own profile |
| GET | `/v1/user/preferences` | Bearer | Retrieve own preferences |
| PATCH | `/v1/user/preferences` | Bearer | Update own preferences |
| PATCH | `/v1/user/password` | Bearer | Change own password |
| GET | `/v1/user/{user_id}` | Admin | Retrieve any user profile by ID |

### Projects — `/v1/projects`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/v1/projects` | Bearer | List projects (paginated) |
| POST | `/v1/projects` | Bearer | Create a project |
| GET | `/v1/projects/{project_id}` | Bearer | Get project by ID |
| PUT | `/v1/projects/{project_id}` | Bearer | Update a project |
| DELETE | `/v1/projects/{project_id}` | Admin | Delete a project |

### Stories — `/v1/stories`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/v1/stories` | Bearer | List stories (filterable) |
| POST | `/v1/stories` | Bearer | Create a story |
| GET | `/v1/stories/{story_id}` | Bearer | Get story by ID |
| PUT | `/v1/stories/{story_id}` | Owner or Admin | Update a story |
| DELETE | `/v1/stories/{story_id}` | Admin | Delete a story |
| PATCH | `/v1/stories/{story_id}/assign` | Bearer | Assign story to a user |
| GET | `/v1/stories/project/{project_id}` | Bearer | Get stories for a project |

### Dashboard — `/v1/dashboard`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/v1/dashboard/stats` | Bearer | Aggregate dashboard statistics |

---

## Versioning Strategy

- All resource endpoints are prefixed with `/v1`.
- The active API version is also communicated via the `X-API-Version: v1` response header, allowing clients to detect the version at runtime.
- Swagger UI and ReDoc are disabled in non-local environments, which is a good security posture but means clients must rely on this documentation or the OpenAPI schema served only in development.

### Gaps

- There is no formal version sunset or deprecation policy documented.
- No `Accept-Version` header or content-type negotiation strategy is defined for future version increments.

---

## Request Contracts

- All request bodies are validated through Pydantic v2 models.
- Email fields use `email-validator` to enforce format.
- UUIDs are typed as `uuid.UUID` (FastAPI auto-validates and returns 422 on malformed input).
- Passwords are not echoed in any response (confirmed by reviewing auth DTOs).

### Gaps

- Some write endpoints accept large free-text fields (`description`) with no maximum length constraint at the application layer; the database column is `TEXT` (unbounded).
- No file upload endpoints exist, so MIME-type concerns are not currently applicable.

---

## Response Contracts

### Success Shapes

All resource responses use consistent shapes via Pydantic response models:

```json
// Project example
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "status": "active | completed | archived",
  "created_by": "uuid",
  "start_date": "date | null",
  "end_date": "date | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Error Shapes

Each error handler returns a consistent envelope:

```json
// 404
{ "error": "Not Found", "message": "...", "resource": "...", "identifier": "..." }

// 400
{ "error": "Validation Error", "message": "..." }

// 409
{ "error": "Conflict", "message": "..." }

// 422
{ "error": "Domain Error", "message": "..." }

// 500 (production)
{ "error": "Internal Server Error", "message": "An unexpected error occurred. Please try again later." }
```

### Gaps

- Pydantic validation failures (422 Unprocessable Entity from FastAPI) return a different schema than domain errors. Clients must handle two distinct error envelope shapes.
- There is no standard pagination envelope (`total`, `page`, `per_page`, `items`) — list endpoints appear to return bare arrays.
- No `Location` header is returned after successful `POST` (resource creation), which is standard REST.

---

## HTTP Status Code Usage

| Scenario | Used Code | Correct? |
|---|---|---|
| Resource created | 201 | ✅ |
| Resource not found | 404 | ✅ |
| Invalid input | 400 | ✅ |
| Conflict (duplicate) | 409 | ✅ |
| Unauthenticated | 401 | ✅ |
| Insufficient permissions | 403 | ✅ |
| Domain rule violation | 422 | ✅ |
| Service unavailable (DB down) | 503 | ✅ |
| Unhandled exception | 500 | ✅ |

---

## Naming Conventions

A `# TODO validate best practices for endpoint naming conventions` comment remains in `app.py`. Specifically:

- `POST /v1/auth/register` and `POST /v1/auth/login` are action-style paths, which is acceptable for auth.
- `/v1/user` (singular) vs `/v1/projects` (plural) is inconsistent — RESTful conventions prefer plural resource names. The user resource should be `/v1/users`.
- `/v1/stories/project/{project_id}` places a filter as a path segment instead of a query parameter, e.g. `GET /v1/stories?project_id={id}`. This is a minor design issue.

---

## Content Negotiation

- API only produces `application/json`. No other media types are supported, which is correct for a pure API backend.
- No `Content-Type` enforcement middleware exists; FastAPI/Pydantic handles this implicitly.

---

## Rate Limiting

- Global limit: **100 requests per minute per IP** via slowapi.
- No per-endpoint or per-route limits.
- Authentication endpoints (login, register) should carry stricter limits (e.g. 10 req/min) to mitigate credential stuffing.

---

## API Documentation

- OpenAPI schema is served at `/docs` (Swagger) and `/redoc` in `local` and `container` environments.
- Both are disabled in all other environments (`docs_url = None`).
- No versioned offline API specification (e.g. `openapi.yaml`) is committed to the repository.

---

## Summary of Findings

| Finding | Severity | Recommendation |
|---|---|---|
| Singular `/v1/user` resource name | Low | Rename to `/v1/users` |
| No `Location` header on POST | Low | Return `Location: /v1/resource/{id}` after creation |
| Dual error envelopes (domain vs Pydantic) | Medium | Standardise to one envelope |
| No pagination envelope | Medium | Add `{ total, page, per_page, items }` |
| No per-endpoint rate limits on auth routes | High | Add stricter limits to `/v1/auth/login` and `/v1/auth/register` |
| Description fields unbounded | Low | Add `max_length` constraints |

---

**Audit date:** 10 May 2026  
**Audited by:** GitHub Copilot Coding Agent
