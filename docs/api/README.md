# API Documentation

Complete reference for the Open Projects Hub API endpoints.

## Base URL

```
Local:      http://localhost:8080
Docker:     http://localhost:8080
Production: https://api.yourdom ain.com
```

## API Version

Current Version: **v1**

All endpoints are prefixed with `/v1` except for health check.

## Available Endpoints

### Health & Status
- `GET /health` - Health check endpoint

### Authentication (`/v1/auth`)
- `POST /v1/auth/login` - User login (rate limited: 5/15min)

### User Management (`/v1/user`)
- `POST /v1/user/register` - Create new user (requires ADMIN role)
- `GET /v1/user/{user_id}` - Get user by ID (requires authentication)

## Authentication

The API uses **JWT (JSON Web Tokens)** for authentication.

### Getting a Token

```bash
curl -X POST http://localhost:8080/v1/auth/login \
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
    "fullname": "John Doe"
  }
}
```

### Using the Token

Include the token in the `Authorization` header:

```bash
curl -X GET http://localhost:8080/v1/user/123 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Expiry

- **Access Token:** 24 hours
- **Refresh Token:** Not yet implemented (see [Phase 2](../implementation/phase2-next-steps.md))

## Rate Limiting

Rate limiting is applied per IP address.

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/v1/auth/login` | 5 requests | 15 minutes |
| All other endpoints | 100 requests | 1 minute |

**Rate Limit Response:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 900
Content-Type: application/json

{
  "error": "Rate limit exceeded"
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
| 401 | Unauthorized | Missing/invalid token, wrong credentials |
| 403 | Forbidden | Insufficient permissions (wrong role) |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Invalid request data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

See [Error Reference](./errors.md) for detailed error responses.

## Request/Response Formats

### Content Type

All requests and responses use `application/json`.

### Date/Time Format

All timestamps use **ISO 8601** format with UTC timezone:

```json
{
  "created_at": "2026-04-30T17:00:00.000Z"
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

*Not yet implemented. See [Phase 2](../implementation/phase2-next-steps.md) for planned pagination support.*

## Filtering & Sorting

*Not yet implemented. See [Phase 2](../implementation/phase2-next-steps.md).*

## Interactive Documentation

### Swagger UI

Visit `http://localhost:8080/docs` for interactive API documentation.

Features:
- Try endpoints directly from your browser
- See request/response schemas
- Authorize with JWT token
- View all available endpoints

### ReDoc

Visit `http://localhost:8080/redoc` for alternative documentation format.

## Code Examples

### Python (requests)

```python
import requests

# Login
response = requests.post(
    "http://localhost:8080/v1/auth/login",
    json={
        "email": "user@example.com",
        "password": "YourPassword123"
    }
)
data = response.json()
token = data["token"]

# Use token
response = requests.get(
    "http://localhost:8080/v1/user/123",
    headers={"Authorization": f"Bearer {token}"}
)
user = response.json()
```

### JavaScript (fetch)

```javascript
// Login
const loginResponse = await fetch('http://localhost:8080/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'YourPassword123'
  })
});
const { token } = await loginResponse.json();

// Use token
const userResponse = await fetch('http://localhost:8080/v1/user/123', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const user = await userResponse.json();
```

### cURL

```bash
# Login and extract token
TOKEN=$(curl -s -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"YourPassword123"}' \
  | jq -r '.token')

# Use token
curl -X GET http://localhost:8080/v1/user/123 \
  -H "Authorization: Bearer $TOKEN"
```

## Detailed Endpoint Documentation

- [Authentication Endpoints](./authentication.md) - Login, refresh (planned)
- [User Management Endpoints](./users.md) - Create, read, update, delete users *(planned)*
- [Error Reference](./errors.md) - All error codes and responses

## API Versioning

The API uses URL-based versioning (`/v1`, `/v2`, etc.).

**Current version:** `v1`

Breaking changes will result in a new version. Non-breaking changes (new fields, new endpoints) will be added to the current version.

## Support & Feedback

- Report issues: [GitHub Issues](https://github.com/your-org/open-projects-hub-api/issues)
- API Questions: Contact the development team
- Security Issues: See [Security Policy](../security/README.md)

---

**Last Updated:** April 30, 2026  
**API Version:** v1.0.0
