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

**Rate Limit:** 10 requests per 1 minute per IP address

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
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "email": "user@example.com",
  "displayName": "John Doe",
  "role": "viewer",
  "loggedInAt": "2026-04-30T17:00:00.000Z",
  "user": {
    "email": "user@example.com",
    "displayName": "John Doe",
    "role": "viewer"
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| token | string | JWT access token |
| accessToken | string | JWT access token (same value as token) |
| refreshToken | string | JWT refresh token (single-use rotation) |
| email | string | User's email address |
| displayName | string | User's display name |
| role | string | User role (admin or viewer) |
| loggedInAt | string | ISO 8601 timestamp when login occurred |
| user | object | Nested user detail object (email, displayName, name, role) |

**JWT Token Payload:**

The token contains the following claims:

```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "role": "admin",
  "iat": 1714497600,
  "exp": 1714584000
}
```

| Claim | Description |
|-------|-------------|
| sub | User ID (subject) |
| email | User email |
| role | User role (admin or viewer) |
| iat | Issued at (Unix timestamp) |
| exp | Expiration time (Unix timestamp) |

#### Error Responses

**Invalid Credentials (401 Unauthorized):**

```json
{
  "detail": "Invalid email or password"
}
```

**Email Not Verified (403 Forbidden):** returned only when the password is correct, so it
never reveals an account's state to someone guessing at emails. The web app keys off `code`
to send the user to email verification.

```json
{
  "detail": "Please verify your email before signing in.",
  "code": "EMAIL_NOT_VERIFIED"
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
  "detail": "Rate limit exceeded: 10 per 1 minute"
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

Refresh an access token using a refresh token.

**Rate Limit:** 10 requests per 15 minutes per IP address

```http
POST /v1/auth/refresh HTTP/1.1
Content-Type: application/json

{
  "refreshToken": "..."
}
```

**Response:**

```json
{
  "token": "new-access-token",
  "accessToken": "new-access-token",
  "refreshToken": "new-refresh-token",
  "tokenType": "Bearer"
}
```

Refresh tokens use single-use rotation: the old refresh token is revoked after use, and a new one is issued.

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

## POST /v1/auth/register

Bootstraps the instance's first account: open only while the instance has no accounts
(403 afterwards). The account is always an **Admin**, is created **unverified** with no AI
credits, and is emailed a verification code. No tokens are returned: the account can sign
in only after `POST /v1/auth/verify-email` succeeds.

**Request:** `{"displayName": "Jane Doe", "email": "jane@example.com", "password": "SecurePass1"}`

**Response (201 Created):**

```json
{
  "email": "ja***@example.com",
  "verificationRequired": true,
  "nextStep": "verify-email",
  "codeExpiresAt": "2026-09-28T20:35:00+00:00"
}
```

**Errors:** 403 registration closed · 409 email already registered · 422 invalid body
(including a `role` field).

**Recovering a stuck instance:** the first registration closes registration even while it is
unverified. If its code can never be delivered (mistyped email, SMTP failure, or Resend's
`onboarding@resend.dev` sender, which only reaches the Resend account owner), run
`make seed-admin` (`scripts/seed_admin.py`) to create a verified admin.

The code is 6 characters from `23456789ABCDEFGHJKLMNPQRSTUVWXYZ`, stored only as a bcrypt
hash, and expires after 5 minutes. It is sent through the SMTP relay configured in
`SMTP_*` (Resend in dev); a delivery failure is logged and the user can resend.

---

## POST /v1/auth/verify-email

**Request:** `{"email": "jane@example.com", "code": "ABC234"}` (case-insensitive)

**Response (200 OK):** `{"verified": true}`. The account is verified and granted its free
AI credits (F-010 FR-010-01).

**Errors:**
- 400 `Invalid or expired verification code`: the same response for a wrong, expired or
  superseded code, an unknown email, or an already-verified account.
- 429 `Too many attempts. Please request a new code.`: after 5 wrong attempts against one code.

---

## POST /v1/auth/resend-verification

**Request:** `{"email": "jane@example.com"}`

**Response (200 OK):** `{"message": "If this email is awaiting verification, a new code has been sent."}`.
It is the same for unknown and already-verified emails, and in those cases no email is sent.
A new code invalidates the previous one.

**Errors:** 429 once 4 codes (the one sent at registration plus 3 resends) have been issued
to the email within 15 minutes.

---

## POST /v1/auth/logout

A dedicated logout endpoint does not exist. Since refresh tokens use single-use rotation, clients should discard their tokens to effectively log out.

---

## Using the Access Token

Once you have an access token, include it in the `Authorization` header for protected endpoints:

```http
GET /v1/users/123 HTTP/1.1
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
- Access tokens have a configurable expiration
- Refresh tokens use single-use rotation
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
     │ GET /v1/users/123                               │
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
- **Limit:** 10 requests
- **Window:** 1 minute
- **Key:** Client IP address

**How it works:**

1. Client makes login request
2. API checks request count for that IP in last 1 minute
3. If count < 10: Process request, increment counter
4. If count >= 10: Return 429 error with `Retry-After` header
5. Counter resets after 1 minute

**Testing rate limiting:**

```bash
# Make 11 login attempts (11th should fail)
for i in {1..11}; do
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

- **Rate limiting:** 10 attempts per 1 minute
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
