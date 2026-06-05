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
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "displayName": "John Doe",
    "role": "viewer"
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

- **Access Token:** 15 minutes
- **Refresh Token:** 7 days
- **Refresh Flow:** Single-use token rotation (old refresh token is revoked after use)

### Roles

| Role | Description |
|------|-------------|
| `admin` | Full access to all resources including create/update/delete |
| `viewer` | Read access to projects, stories, clients; can create stories |

## Rate Limiting

Rate limiting is applied per IP address.

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/v1/auth/login` | 10 requests | 1 minute |
| `/v1/auth/register` | 5 requests | 1 minute |
| `/v1/auth/refresh` | 10 requests | 15 minutes |
| All other endpoints | 100 requests | 1 minute |

**Rate Limit Response:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 900
Content-Type: application/json

{
  "detail": "Rate limit exceeded"
}
```

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
| `GET /v1/projects` | `status` (active, completed, archived) |
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

## Interactive Documentation

### Swagger UI

Visit `http://localhost:8000/docs` for interactive API documentation.

Features:
- Try endpoints directly from your browser
- See request/response schemas
- Authorize with JWT token
- View all available endpoints

### ReDoc

Visit `http://localhost:8000/redoc` for alternative documentation format.

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

- [Authentication Endpoints](./authentication.md) - Login, register, refresh
- [User Management Endpoints](./users.md) - Profile, admin user creation
- [Error Reference](./errors.md) - All error codes and responses

## API Versioning

The API uses URL-based versioning (`/v1`, `/v2`, etc.).

**Current version:** `v1`

Breaking changes will result in a new version. Non-breaking changes (new fields, new endpoints) will be added to the current version.

## Architecture

For architectural decisions and design patterns, see the [ADR index](../adr/README.md):

- [ADR-001](../adr/ADR-001-cross-feature-queries-for-performance.md) - Cross-Feature Queries for Performance
- [ADR-002](../adr/ADR-002-centralized-validation-pattern.md) - Centralized Validation Pattern
- [ADR-003](../adr/ADR-003-dto-based-use-cases.md) - DTO-Based Use Cases
- [ADR-004](../adr/ADR-004-dependency-inversion-for-repositories.md) - Dependency Inversion for Repositories

## Support & Feedback

- Report issues: [GitHub Issues](https://github.com/your-org/open-projects-hub-api/issues)
- API Questions: Contact the development team
- Security Issues: See [Security Policy](../security/README.md)

---

**Last Updated:** May 21, 2026  
**API Version:** v1.1.0
