# API Error Reference

Complete reference for all API error responses.

## Error Response Format

All errors follow a consistent JSON format:

```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (422), the format includes more detail:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "invalid-input"
    }
  ]
}
```

## HTTP Status Codes

### 2xx Success

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |

### 4xx Client Errors

| Code | Name | When It Occurs |
|------|------|----------------|
| 400 | Bad Request | Invalid request format or data |
| 401 | Unauthorized | Missing, invalid, or expired authentication |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Requested resource doesn't exist |
| 422 | Unprocessable Entity | Request validation failed |
| 429 | Too Many Requests | Rate limit exceeded |

### 5xx Server Errors

| Code | Name | When It Occurs |
|------|------|----------------|
| 500 | Internal Server Error | Unexpected server-side error |
| 503 | Service Unavailable | Service temporarily unavailable (e.g., database down) |

## Common Errors

### Authentication Errors (401)

#### Invalid Credentials

```http
POST /v1/auth/login
```

```json
{
  "detail": "Invalid email or password"
}
```

**Cause:** Email doesn't exist or password is incorrect  
**Solution:** Verify credentials and try again

#### Missing Token

```http
GET /v1/users/123
Authorization: (missing)
```

```json
{
  "detail": "Not authenticated"
}
```

**Cause:** No `Authorization` header provided  
**Solution:** Include `Authorization: Bearer {token}` header

#### Invalid Token

```http
GET /v1/users/123
Authorization: Bearer invalid-token
```

```json
{
  "detail": "Invalid or expired token"
}
```

**Causes:**
- Token signature invalid (tampered/wrong secret)
- Token malformed
- Token expired (>24 hours old)

**Solution:** Login again to get a new token

#### Expired Token

```http
GET /v1/users/123
Authorization: Bearer eyJ... (expired)
```

```json
{
  "detail": "Token has expired"
}
```

**Cause:** Token has expired  
**Solution:** Login again or use refresh token

### Authorization Errors (403)

#### Insufficient Permissions

```http
POST /v1/users/register
Authorization: Bearer {user-role-token}
```

```json
{
  "detail": "Insufficient permissions"
}
```

**Cause:** User doesn't have required role (e.g., USER trying to access ADMIN endpoint)  
**Solution:** Request access from an administrator

### Validation Errors (422)

#### Invalid Email Format

```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "not-an-email",
  "password": "Password123"
}
```

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "not-an-email",
      "url": "https://errors.pydantic.dev/2.5/v/value_error"
    }
  ]
}
```

**Cause:** Email field doesn't contain a valid email address  
**Solution:** Provide a valid email format (e.g., `user@example.com`)

#### Weak Password

```http
POST /v1/users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "weak",
  "first_name": "John",
  "last_name": "Doe"
}
```

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "Password must be at least 8 characters long and contain uppercase, lowercase, and a digit",
      "input": "weak"
    }
  ]
}
```

**Cause:** Password doesn't meet complexity requirements  
**Solution:** Use a password with:
- At least 8 characters
- One uppercase letter
- One lowercase letter
- One digit

#### Missing Required Fields

```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com"
}
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "password"],
      "msg": "Field required",
      "input": {"email": "user@example.com"}
    }
  ]
}
```

**Cause:** Required field `password` is missing  
**Solution:** Include all required fields

### Rate Limit Errors (429)

#### Rate Limit Exceeded

```http
POST /v1/auth/login
(11th request within 1 minute)
```

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": "Rate limit exceeded: 10 per 1 minute"
}
```

**Cause:** Too many requests from the same IP address  
**Solution:** Wait for the window in the message to pass (the API does not send a `Retry-After` header)

**Rate Limits:**
- Login: 10 requests per 1 minute
- General: 100 requests per 1 minute

### Not Found Errors (404)

#### User Not Found

```http
GET /v1/users/nonexistent-id
Authorization: Bearer {valid-token}
```

```json
{
  "detail": "User not found"
}
```

**Cause:** User with that ID doesn't exist  
**Solution:** Verify the user ID is correct

#### Endpoint Not Found

```http
GET /v1/nonexistent
```

```json
{
  "detail": "Not Found"
}
```

**Cause:** Endpoint doesn't exist  
**Solution:** Check API documentation for correct endpoint

### Server Errors (500)

#### Internal Server Error

```http
GET /v1/users/123
```

```json
{
  "detail": "Internal server error"
}
```

**Cause:** Unexpected server-side error  
**Solution:**
- Retry the request
- Check server logs
- Contact support if persists

#### Database Connection Error

```http
GET /health
```

```http
HTTP/1.1 503 Service Unavailable

{
  "status": "unhealthy",
  "checks": {
    "database": "unhealthy: connection refused"
  }
}
```

**Cause:** Database is unreachable  
**Solution:** Check database service status

## Error Response Headers

### Retry-After

Not sent by this API: rate-limited responses (`429`) state the limit in the body instead, for example `{"error": "Rate limit exceeded: 10 per 1 minute"}`.

### WWW-Authenticate

Indicates authentication scheme required.

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer
```

## Handling Errors

### Client-Side Best Practices

**Always check status code:**

```javascript
const response = await fetch('/v1/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email, password }),
  headers: { 'Content-Type': 'application/json' }
});

if (!response.ok) {
  const error = await response.json();

  switch (response.status) {
    case 401:
      // Handle authentication error
      showLoginError(error.detail);
      break;
    case 422:
      // Handle validation errors
      showValidationErrors(error.detail);
      break;
    case 429:
      // Handle rate limit
      // 429 bodies use `error`, not `detail`, and carry no Retry-After header
      showRateLimitError(error.error);
      break;
    case 500:
      // Handle server error
      showServerError();
      break;
    default:
      showGenericError(error.detail);
  }
}
```

**Implement retry logic for 5xx errors:**

```javascript
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);

      if (response.ok || response.status < 500) {
        return response;
      }

      // Wait before retry (exponential backoff)
      await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
    } catch (error) {
      if (i === maxRetries - 1) throw error;
    }
  }
}
```

**Handle token expiration:**

```javascript
async function apiCall(url, options = {}) {
  const token = getStoredToken();

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });

  if (response.status === 401) {
    // Token expired, redirect to login
    clearStoredToken();
    redirectToLogin();
    return null;
  }

  return response;
}
```

### Server-Side Logging

Errors are logged server-side with relevant context:

```python
# In application logs
ERROR 2026-04-30 17:00:00 - Authentication failed
  email: user@example.com
  ip: 192.168.1.100
  reason: invalid_password

WARNING 2026-04-30 17:01:00 - Rate limit exceeded
  endpoint: /v1/auth/login
  ip: 192.168.1.100
  limit: 5/15minutes
```

## Testing Error Scenarios

### Test Invalid Credentials

```bash
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"wrong@example.com","password":"wrong"}'
```

### Test Missing Token

```bash
curl -X GET http://localhost:8080/v1/users/123
```

### Test Invalid Token

```bash
curl -X GET http://localhost:8080/v1/users/123 \
  -H "Authorization: Bearer invalid-token"
```

### Test Rate Limiting

```bash
for i in {1..6}; do
  curl -X POST http://localhost:8080/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"Test123"}'
  echo ""
done
```

### Test Validation Errors

```bash
# Invalid email
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"not-an-email","password":"Test123"}'

# Weak password
curl -X POST http://localhost:8080/v1/users/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"email":"user@example.com","password":"weak","first_name":"John","last_name":"Doe"}'
```

## Debugging Tips

1. **Check response status code** - Indicates error category
2. **Read error detail** - Contains specific error message
3. **Check request format** - Verify Content-Type, body format
4. **Verify authentication** - Check token is valid and not expired
5. **Check rate limits** - Wait if hitting rate limits
6. **Review server logs** - For 500 errors, check server logs
7. **Test with cURL** - Isolate issues from client code
8. **Use Swagger UI** - Test endpoints interactively at `/docs`

## FAQ

**Q: Why am I getting 401 when my credentials are correct?**  
A: Check for extra whitespace in email/password, ensure password meets complexity requirements, verify account exists.

**Q: How do I know when my token expires?**  
A: Decode the JWT (don't verify signature) and check the `exp` claim. Token expiry is configurable.

**Q: Can I retry after a 429 error?**  
A: Yes. The message states the limit window (for example `10 per 1 minute`); wait for it to pass, then retry.

**Q: What should I do for 500 errors?**  
A: These are server-side errors. Implement retry logic with exponential backoff. If persists, contact support.

**Q: How do I handle validation errors (422)?**  
A: Parse the `detail` array, extract field-specific errors, and display them to the user.

---

**See Also:**
- [API Overview](./README.md)
- [Authentication](./authentication.md)
- [Security](../security/README.md)

---

**Last Updated:** April 30, 2026
