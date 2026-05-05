# Authentication Endpoints

API endpoints for user authentication and authorization.

## Overview

The authentication system uses:
- **JWT tokens** for session management
- **bcrypt** for password hashing
- **Rate limiting** to prevent brute force attacks
- **Role-based access control** (USER, ADMIN)

## Endpoints

### POST /v1/auth/login

Authenticate a user and receive a JWT access token.

**Rate Limit:** 5 requests per 15 minutes per IP address

#### Request

```http
POST /v1/auth/login HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "YourPassword123"
}
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email address (must be valid email format) |
| password | string | Yes | User's password |

#### Response

**Success (200 OK):**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "fullname": "John Doe"
  }
}
```

**Response Body Schema:**

| Field | Type | Description |
|-------|------|-------------|
| token | string | JWT access token (expires in 24 hours) |
| user | object | User information |
| user.id | string (UUID) | User's unique identifier |
| user.email | string | User's email address |
| user.fullname | string | User's full name (first + last) |

**JWT Token Payload:**

The token contains the following claims:

```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "role": "ADMIN",
  "iat": 1714497600,
  "exp": 1714584000
}
```

| Claim | Description |
|-------|-------------|
| sub | User ID (subject) |
| email | User email |
| role | User role (USER or ADMIN) |
| iat | Issued at (Unix timestamp) |
| exp | Expiration time (Unix timestamp, iat + 24 hours) |

#### Error Responses

**Invalid Credentials (401 Unauthorized):**

```json
{
  "detail": "Invalid email or password"
}
```

**Validation Error (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "not-an-email"
    }
  ]
}
```

**Rate Limit Exceeded (429 Too Many Requests):**

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 900

{
  "error": "Rate limit exceeded: 5 per 15 minute"
}
```

#### Examples

**cURL:**

```bash
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin123!"
  }'
```

**Python:**

```python
import requests

response = requests.post(
    "http://localhost:8080/v1/auth/login",
    json={
        "email": "admin@example.com",
        "password": "Admin123!"
    }
)

if response.status_code == 200:
    data = response.json()
    token = data["token"]
    user = data["user"]
    print(f"Logged in as {user['fullname']}")
else:
    print(f"Login failed: {response.json()}")
```

**JavaScript:**

```javascript
async function login(email, password) {
  const response = await fetch('http://localhost:8080/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (response.ok) {
    const data = await response.json();
    // Store token (e.g., localStorage, cookie)
    localStorage.setItem('token', data.token);
    return data;
  } else {
    const error = await response.json();
    throw new Error(error.detail);
  }
}
```

---

## POST /v1/auth/refresh

*Not yet implemented. Planned for Phase 2.*

Refresh an access token using a refresh token.

**Status:** Coming soon  
**See:** [Phase 2 Next Steps](../implementation/phase2-next-steps.md#4-add-refresh-token-support-2-hours)

**Planned Behavior:**

```http
POST /v1/auth/refresh HTTP/1.1
Content-Type: application/json

{
  "refresh_token": "..."
}
```

**Planned Response:**

```json
{
  "token": "new-access-token",
  "refresh_token": "new-refresh-token",
  "user": {
    "id": "...",
    "email": "...",
    "fullname": "..."
  }
}
```

---

## POST /v1/auth/logout

*Not yet implemented. Planned for Phase 2.*

Logout a user by invalidating their refresh token.

**Status:** Coming soon  
**See:** [Phase 2 Next Steps](../implementation/phase2-next-steps.md#4-add-refresh-token-support-2-hours)

---

## Using the Access Token

Once you have an access token, include it in the `Authorization` header for protected endpoints:

```http
GET /v1/user/123 HTTP/1.1
Host: localhost:8080
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Validation

The API validates tokens on each request:

1. **Signature verification** - Ensures token wasn't tampered with
2. **Expiration check** - Rejects expired tokens (>24 hours old)
3. **Claims validation** - Verifies required claims (sub, email, role)

**Invalid/Expired Token Response:**

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Invalid or expired token"
}
```

### Token Security

- Tokens are signed with HS256 algorithm
- Secret key is validated (minimum 32 characters)
- Tokens expire after 24 hours
- Include user role for authorization

**Best Practices:**

- Store tokens securely (httpOnly cookies recommended)
- Never share tokens between users
- Implement token refresh before expiry
- Clear tokens on logout
- Use HTTPS in production

---

## Authentication Flow

```
┌──────────┐                                     ┌──────────┐
│  Client  │                                     │   API    │
└────┬─────┘                                     └────┬─────┘
     │                                                │
     │ POST /v1/auth/login                            │
     │ { email, password }                            │
     ├───────────────────────────────────────────────>│
     │                                                │
     │                                                │ Verify credentials
     │                                                │ Generate JWT token
     │                                                │
     │ 200 OK                                         │
     │ { token, user }                                │
     │<───────────────────────────────────────────────┤
     │                                                │
     │ Store token                                    │
     │                                                │
     │ GET /v1/user/123                               │
     │ Authorization: Bearer {token}                  │
     ├───────────────────────────────────────────────>│
     │                                                │
     │                                                │ Validate token
     │                                                │ Check permissions
     │                                                │
     │ 200 OK                                         │
     │ { user data }                                  │
     │<───────────────────────────────────────────────┤
     │                                                │
```

---

## Password Requirements

When creating or updating passwords, the following rules apply:

- **Minimum length:** 8 characters
- **Uppercase:** At least one uppercase letter (A-Z)
- **Lowercase:** At least one lowercase letter (a-z)
- **Digit:** At least one digit (0-9)
- **Special characters:** Allowed but not required

**Examples:**

- ✅ `Password123` - Valid
- ✅ `MySecure1Pass` - Valid
- ✅ `Test1234!@#$` - Valid
- ❌ `password` - No uppercase, no digit
- ❌ `PASSWORD123` - No lowercase
- ❌ `Pass123` - Too short
- ❌ `Password` - No digit

See [Password Security](../security/authentication.md#password-requirements) for more details.

---

## Rate Limiting Details

Login endpoint is rate limited to prevent brute force attacks.

**Configuration:**
- **Limit:** 5 requests
- **Window:** 15 minutes
- **Key:** Client IP address

**How it works:**

1. Client makes login request
2. API checks request count for that IP in last 15 minutes
3. If count < 5: Process request, increment counter
4. If count >= 5: Return 429 error with `Retry-After` header
5. Counter resets after 15 minutes

**Testing rate limiting:**

```bash
# Make 6 login attempts (6th should fail)
for i in {1..6}; do
  echo "Attempt $i:"
  curl -X POST http://localhost:8080/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"Test123"}'
  echo -e "\n"
done
```

See [Rate Limiting](../security/rate-limiting.md) for more details.

---

## Security Considerations

### Password Hashing

- Uses **bcrypt** with default work factor (12 rounds)
- Hashing is done **asynchronously** to prevent blocking
- Passwords are never logged or stored in plain text

### JWT Security

- Tokens signed with **HS256** algorithm
- Secret key validated at startup (min 32 characters)
- Known weak secrets rejected ("secret", "changeme", etc.)
- Tokens include expiration time (24 hours)

### Brute Force Protection

- **Rate limiting:** 5 attempts per 15 minutes
- **Failed attempts:** Count toward rate limit
- **IP-based:** Rate limit per client IP address

### Best Practices

For application developers:
- Always use HTTPS in production
- Store tokens in httpOnly cookies (not localStorage)
- Implement CSRF protection for cookies
- Clear tokens on logout
- Validate token on each request
- Monitor failed auth attempts

For users:
- Use strong, unique passwords
- Don't share credentials
- Log out when done
- Report suspicious activity

---

**See Also:**
- [Security Overview](../security/README.md)
- [Rate Limiting](../security/rate-limiting.md)
- [Error Reference](./errors.md)

---

**Last Updated:** April 30, 2026
