# API Documentation

Complete reference for the Open Projects Hub API endpoints.

## Base URL

```
Local:      http://localhost:8000
Docker:     http://localhost:8080
Production: https://api.yourdomain.com
```

## API Version

Current Version: **v1.1.0**

All endpoints are prefixed with `/v1` except for health check.

## API Contract

For a consolidated list of API endpoints and their details, refer to the [API Contract](./api-contract.md).
## JSON Convention

All request and response bodies use **camelCase** for JSON field names. This is enforced via Pydantic's `alias_generator=to_camel` on all DTOs.

```json
{
  "displayName": "John Doe",
  "createdAt": "2026-05-21T12:00:00.000Z"
}
```

Python code uses `snake_case` internally; the alias generator handles the conversion automatically.

## Authentication

The API uses **JWT (JSON Web Tokens)** for authentication.

### Getting a Token

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "YourPassword123"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "email": "user@example.com",
  "displayName": "John Doe",
  "role": "admin",
  "loggedInAt": "2026-05-21T12:00:00.000Z",
  "user": {
    "email": "user@example.com",
    "displayName": "John Doe",
    "role": "admin",
    "workspace": { "id": "9b2f0c1e-6d0a-4c47-9d8e-1f2a3b4c5d6e", "name": "Jane's Studio" }
  }
}
```

### Using the Token

Include the token in the `Authorization` header:

```bash
curl -X GET http://localhost:8000/v1/users/me/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Expiry

Token expiry is configurable via the application configuration. Refresh tokens use single-use rotation (the old refresh token is revoked after use).

### Workspaces and Roles

Every account belongs to one **workspace**, and clients, projects and stories belong
to a workspace. Each sign-up creates a new workspace; its Admin adds teammates
with `POST /v1/users`. The workspace always comes from the token (`wid` claim), never from
the path or body, and a record of another workspace answers **404**, exactly like one that
does not exist.

| Role | Description |
|------|-------------|
| `admin` | Everything a member can do, plus adding members (`POST /v1/users`), switching them active/inactive (`PATCH /v1/users/{id}/status`) and deleting them (`DELETE /v1/users/{id}`) |
| `member` | Full create/update/delete on clients, projects, stories and refinement; own AI keys; lists the team (`GET /v1/users`) |

`PATCH /v1/workspaces/me` (Admin only) renames the caller's workspace. Body: `{ "name": "..." }`
(trimmed, 1-100 characters, otherwise 422). Returns `{ "id": "...", "name": "..." }`.

`POST /v1/users` accepts `role` `member` (the default and only value); `admin` and anything else are rejected (422).
Clients have no account: see [Client Review](#client-review-public).
Added accounts are created unverified. The invitee is emailed a 24-hour code and link, chooses a password when submitting it to `POST /v1/auth/verify-email`, and is granted free AI credits on verification (subject to the workspace's 25-credit lifetime ceiling).

User responses include `isActive`. `PATCH /v1/users/{id}/status` (Admin only) takes
`{ "active": false }` or `{ "active": true }` and returns the updated user. An inactive account
stays in `GET /v1/users` but cannot sign in or refresh a session and cannot be assigned
stories; its data is untouched, and an access token already issued works until it expires.
Switching it back on lets the person sign in again with their existing password.

`DELETE /v1/users/{id}` (Admin only) permanently deletes a teammate and answers **204**. The
projects and stories they created, and the stories assigned to them, move to the Admin making
the call, and their stored AI keys are erased. The email becomes free to add again. This cannot
be undone.

Both endpoints answer 400 when the target is the workspace Admin, 403 for non-admins, and 404
for an unknown or other-workspace user.

### Client Review (public)

Clients (a freelancer's customers) have no account. A stakeholder reviews a project at
`/viewer` on the web app by typing its **access code**, and the web app calls the one public
read route:

`GET /v1/viewer/{access_code}` — no token. Returns `{ projectName, phase, total, stories[] }`
where each story has `id`, `title`, `description`, `acceptanceCriteria[]`, `status`,
`priority`, `points`, `createdAt` and `updatedAt`. Approved stories only (drafts never reach
the database), ordered highest priority first, then oldest first. Query: `limit` (default
100, max 100), `offset`. It identifies no user, client record or workspace.

The code is `projects.access_code` (`accessCode` on project responses, `PRJ-` plus 8
characters, e.g. `PRJ-7K3M9XQ2`), unique across all workspaces and generated by the server;
it is not the freelancer-chosen `code`. An unknown or malformed code answers **404**
`Project not found` in both cases. The route is limited to 30 requests per minute per IP
(**429**). `POST /v1/projects/{id}/access-code/regenerate` (Admin or Member) replaces the code and
invalidates the old one immediately.

## Rate Limiting

Rate limiting is applied per IP address.

Limits are per client IP and per endpoint. Endpoints not listed here have no request-rate limit.

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/v1/auth/login` | 10 requests | 1 minute |
| `/v1/auth/register` | 5 requests | 1 minute |
| `/v1/auth/verify-email` | 10 requests | 15 minutes |
| `/v1/auth/resend-verification` | 5 requests | 15 minutes |
| `/v1/auth/refresh` | 10 requests | 15 minutes |
| `/v1/auth/forgot-password` | 5 requests | 15 minutes |
| `/v1/auth/resend-reset-code` | 5 requests | 15 minutes |
| `/v1/auth/reset-password` | 10 requests | 15 minutes |
| `/v1/viewer/{accessCode}` | 30 requests | 1 minute |

Separately, login has a per-account progressive lockout, and API key validation is limited to 5 attempts per user per hour.

**Rate Limit Response:**
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": "Rate limit exceeded: 10 per 1 minute"
}
```

Counters are kept in memory per worker process (see Known Limitations in the repository README).

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Meaning | When You'll See It |
|------|---------|-------------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created (POST) |
| 204 | No Content | Resource deleted successfully |
| 400 | Bad Request | Validation failed, invalid input |
| 401 | Unauthorized | Missing/invalid token, wrong credentials |
| 403 | Forbidden | Insufficient permissions (wrong role) |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists (e.g., duplicate email) |
| 422 | Validation Error | Invalid request data (Pydantic validation) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | AI service error (refinement endpoints) |

See [Error Reference](./errors.md) for detailed error responses.

## Request/Response Formats

### Content Type

All requests and responses use `application/json`.

### Date/Time Format

All timestamps use **ISO 8601** format with UTC timezone:

```json
{
  "createdAt": "2026-04-30T17:00:00.000Z"
}
```

### UUIDs

All entity IDs use **UUID v4** format:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000"
}
```

## Pagination

List endpoints support offset-based pagination with `limit` and `offset` query parameters.

### Request Parameters

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `limit` | int | 20 | 1-100 | Maximum number of results |
| `offset` | int | 0 | >= 0 | Number of results to skip |

### Response Format

```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "items": [
    { "id": "...", "name": "Project Alpha" },
    { "id": "...", "name": "Project Beta" }
  ]
}
```

### Paginated Endpoints

| Endpoint | Additional Filters |
|----------|-------------------|
| `GET /v1/clients` | None |
| `GET /v1/projects` | `status`, `clientId`, `createdFrom`, `createdTo`, `updatedFrom`, `updatedTo`, `search` |
| `GET /v1/stories` | `project_id`, `status`, `priority`, `assigned_to` |
| `GET /v1/stories/by-project/{project_id}` | None |

## Filtering & Sorting

### Stories Filters

The `GET /v1/stories` endpoint supports the following query parameters:

| Filter | Values |
|--------|--------|
| `project_id` | UUID string |
| `status` | `todo`, `in_progress`, `done` |
| `priority` | `low`, `medium`, `high` |
| `assigned_to` | UUID string |

### Projects Filters

The `GET /v1/projects` endpoint supports:

| Filter | Values |
|--------|--------|
| `status` | `active`, `completed`, `archived` |
| `clientId` | UUID string |
| `createdFrom` | ISO 8601 datetime (inclusive lower bound on `createdAt`) |
| `createdTo` | ISO 8601 datetime (inclusive upper bound on `createdAt`) |
| `updatedFrom` | ISO 8601 datetime (inclusive lower bound on `updatedAt`) |
| `updatedTo` | ISO 8601 datetime (inclusive upper bound on `updatedAt`) |
| `search` | Case-insensitive substring match on project `name` or `code` |

Example:

```
GET /v1/projects?status=active&clientId=550e8400-e29b-41d4-a716-446655440003&search=payroll
```

## Interactive Documentation

### Swagger UI

Visit `http://localhost:8000/docs` for interactive API documentation (available in `local` and `container` environments only).

Features:
- Try endpoints directly from your browser
- See request/response schemas
- Authorize with JWT token
- View all available endpoints

**Note:** API documentation is disabled in non-local/container environments for security. Set `APP_ENV=local` or `APP_ENV=container` to enable.

### ReDoc

Visit `http://localhost:8000/redoc` for alternative documentation format (also disabled in production environments).

## Code Examples

### Python (requests)

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/v1/auth/login",
    json={
        "email": "user@example.com",
        "password": "YourPassword123"
    }
)
data = response.json()
token = data["token"]

# Use token
response = requests.get(
    "http://localhost:8000/v1/users/me/profile",
    headers={"Authorization": f"Bearer {token}"}
)
user = response.json()
```

### JavaScript (fetch)

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'YourPassword123'
  })
});
const { token } = await loginResponse.json();

// Use token
const userResponse = await fetch('http://localhost:8000/v1/users/me/profile', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const user = await userResponse.json();
```

### cURL

```bash
# Login and extract token
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"YourPassword123"}' \
  | jq -r '.token')

# Use token
curl -X GET http://localhost:8000/v1/users/me/profile \
  -H "Authorization: Bearer $TOKEN"
```

## Detailed Endpoint Documentation

- [API Contract](./api-contract.md) - Complete endpoint reference
- [Authentication Guide](./authentication.md) - Login, register, email verification, refresh flows
- [Error Reference](./errors.md) - All error codes and responses

## API Versioning

The API uses URL-based versioning (`/v1`, `/v2`, etc.).

**Current version:** `v1`

Breaking changes will result in a new version. Non-breaking changes (new fields, new endpoints) will be added to the current version.

## Architecture

For architectural decisions and design patterns, see:

- [Clean Architecture](../engineering/clean-architecture.md) - Layered architecture and dependency rules
- [Composition Root](../engineering/composition-root.md) - Centralized dependency injection
- [DDD Patterns](../engineering/ddd-patterns.md) - Domain-driven design implementation
- [Design Principles](../engineering/design-principles.md) - SOLID and other principles

## Support & Feedback

- Report issues: [GitHub Issues](https://github.com/alonsovndev/open-projects-hub-api/issues)
- API Questions: Contact the development team
- Security Issues: See [Security Policy](../security/README.md)

---

**Last Updated:** October 7, 2026  
**API Version:** v1.0.0
