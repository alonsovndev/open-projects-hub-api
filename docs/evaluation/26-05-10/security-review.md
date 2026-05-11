# Security Review — 26-05-10

## Overview

This document assesses the security posture of the Open Projects Hub API, covering authentication, authorisation, input validation, transport security, secrets management, and known gaps.

---

## Authentication

### Mechanism

JWT (JSON Web Tokens) using the HS256 (HMAC-SHA256) algorithm, implemented via `PyJWT 2.10.1`.

### Token Types

| Token | Expiry | Purpose |
|---|---|---|
| Access token | 24 hours (1440 min, configurable) | API authorisation on protected routes |
| Refresh token | 7 days (10080 min, configurable) | Obtaining new access tokens without re-login |

### Claims and Validation

Access tokens carry:
- `sub` (user UUID)
- `email`
- `role`
- `iat` (issued-at)
- `exp` (expiry)
- `aud` (`open-projects-hub-api`)
- `iss` (`open-projects-hub-api`)

On decode, the following are enforced:
- `exp`, `iat`, `sub`, `aud`, `iss` presence is required
- Expiry is verified
- Audience and issuer are verified

The refresh token additionally carries a `"type": "refresh"` claim that is verified before it is accepted as a refresh token.

**Assessment: Strong.** Both token types are validated with full claim verification.

### Secret Key Strength Enforcement

`JWTHandler._validate_secret_key()` enforces:
- Minimum 32 characters
- Rejection of a blocklist of known weak secrets (`secret`, `changeme`, `password`, etc.)
- Case-insensitive comparison

**Assessment: Good.** This prevents accidental use of development placeholders in production.

### Gaps

- **No token revocation.** There is no blocklist, Redis-backed invalidation, or token rotation on refresh. A stolen access token is valid for up to 24 hours; a stolen refresh token is valid for 7 days with no way to invalidate it.
- **Access token expiry is 24 hours.** Many APIs use 15-minute access tokens with refresh. A 24-hour window is large.
- **Refresh token is stateless.** If a user changes their password or is deactivated, outstanding refresh tokens remain valid until natural expiry.

---

## Authorisation

### Role-Based Access Control (RBAC)

Two roles exist: `ADMIN` and `USER` (viewer).

- `get_current_user` — validates the JWT; returns the claims dict. Required on all authenticated routes.
- `require_admin` — calls `get_current_user`, then asserts `role == ADMIN`. Returns 403 if not admin.
- `create_story_owner_or_admin_dependency(story_id)` — factory that checks the requesting user is either the story creator or an admin.

**Assessment: Appropriate for current scope.** The story ownership check performs a live database query to verify the creator, which is correct.

### Gaps

- **No project ownership check.** Projects have a `created_by` field but project update/delete do not verify the requesting user is the creator (beyond admin). Currently only admins can delete projects.
- **No resource-level permissions.** There is no concept of project membership — any authenticated user can view and create stories in any project.

---

## Input Validation

- All HTTP request bodies are validated by Pydantic v2 models before reaching use cases.
- Email addresses are validated by `email-validator`.
- UUIDs are validated by Python's `uuid.UUID` type (FastAPI converts and rejects invalid values with 422).
- Password validation rules are enforced in the change-password and register flows.

### Gaps

- Free-text fields (`description`, `name`) have no maximum length constraints at the application layer. The database columns are `VARCHAR(255)` for name and `TEXT` (unbounded) for description. An attacker could send large payloads.
- No explicit XSS sanitisation — this is an API, so this is lower risk, but stored text is returned verbatim.

---

## Transport Security

### Security Response Headers

Applied globally by `add_security_headers` middleware to every response:

| Header | Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` | Restrict resource loading |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Referrer-Policy` | `no-referrer` | No referrer header leak |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | Disable unused browser APIs |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HTTPS enforcement (production only) |

**Assessment: Strong.** All OWASP-recommended headers are present.

### CORS

CORS origins, methods, headers, and credential policy are all configurable via `settings.yml`. A runtime check prevents wildcard origins being used with `allow_credentials=True`:

```python
if allow_credentials and ("*" in origins or any("*" in origin for origin in origins)):
    raise ValueError("CORS misconfiguration: ...")
```

**Assessment: Good.** The configuration guard prevents a common misconfiguration.

---

## Secrets Management

- The JWT secret key is loaded from `settings.yml` / environment variable (`jwt.secret_key`).
- The `.env.example` file exists to guide developers on required variables without exposing real secrets.
- `settings.yml` should not be committed with real secrets; the `.gitignore` should exclude it in production deployment pipelines.

### Gaps

- No secrets rotation mechanism is documented.
- There is no integration with a secrets manager (e.g. AWS Secrets Manager, Vault). All secrets are delivered via environment variables, which is acceptable for small-scale deployments but lacks audit trails.

---

## Rate Limiting

Global rate limit: **100 requests per minute per IP** (slowapi).

### Gaps

- **Authentication endpoints are not separately limited.** Login and register should have much lower limits (e.g. 5–10 req/min) to mitigate brute-force and credential-stuffing attacks.
- **No account lockout.** Failed login attempts are logged but do not trigger any delay or lockout.
- **IP-based limiting only.** Proxied requests may bypass rate limiting if the real client IP is not forwarded correctly (`X-Forwarded-For` handling depends on proxy configuration).

---

## Password Security

- Passwords are hashed using bcrypt via `PasswordHandler`.
- Passwords are never returned in any response.
- Password change requires knowledge of the current password (verified before hashing the new value).

**Assessment: Correct.**

---

## API Documentation Exposure

- Swagger UI (`/docs`) and ReDoc (`/redoc`) are disabled in all non-local environments (`fastApiApp.docs_url = None`).
- The OpenAPI JSON schema (`/openapi.json`) is also disabled in production.

**Assessment: Good security hygiene.**

---

## Dependency Vulnerabilities

| Package | Version | Known CVEs at audit date |
|---|---|---|
| fastapi | 0.115.11 | None known |
| pyjwt | 2.10.1 | None known |
| bcrypt | 5.0.0 | None known |
| sqlalchemy | 2.0.39 | None known |
| asyncpg | 0.30.0 | None known |
| slowapi | 0.1.9 | None known |

*Note: Dependency vulnerability scanning should be integrated into CI (e.g. `pip-audit` or Dependabot).*

---

## Risk Matrix

| Risk | Likelihood | Impact | Priority |
|---|---|---|---|
| Stolen refresh token (no revocation) | Medium | High | High |
| Brute-force login (no per-endpoint rate limit) | Medium | High | High |
| Large payload DoS (no max_length) | Low | Medium | Medium |
| Secrets in environment only (no manager) | Low | High | Medium |
| No project ownership checks | Low | Medium | Low |

---

## Recommendations

| Priority | Finding | Recommendation |
|---|---|---|
| High | No refresh token revocation | Implement a token blocklist (Redis) or short-lived access tokens (15 min) with single-use refresh rotation |
| High | Auth endpoints not rate-limited separately | Add per-route limits: 10 req/min for `/v1/auth/login`, 5 req/min for `/v1/auth/register` |
| Medium | No account lockout | Add progressive delay or temporary lockout after N consecutive failed logins |
| Medium | Unbounded text fields | Add `max_length` to Pydantic fields for `name` (255) and `description` (10 000) |
| Medium | No secrets manager | Integrate with a secrets manager for production deployments |
| Low | No project ownership gate | Add a project owner/admin check on project mutation endpoints |

---

**Audit date:** 10 May 2026  
**Audited by:** GitHub Copilot Coding Agent
