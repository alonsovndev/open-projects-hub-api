# Security Documentation

Comprehensive security documentation for the Open Projects Hub API.

## Overview

The API implements multiple layers of security to protect user data and prevent unauthorized access.

**Security Features:**
- JWT-based authentication
- bcrypt password hashing
- Password complexity validation
- Rate limiting (brute force protection)
- Role-based access control (RBAC)
- Secure secret validation
- SQL injection protection (SQLAlchemy parameterized queries)
- Async operations (no blocking)

## Security Layers

```
┌─────────────────────────────────────────────┐
│          Rate Limiting (slowapi)            │ ← IP-based rate limits
├─────────────────────────────────────────────┤
│      Authentication (JWT validation)        │ ← Token verification
├─────────────────────────────────────────────┤
│     Authorization (Role checking)           │ ← Permission checks
├─────────────────────────────────────────────┤
│    Input Validation (Pydantic)              │ ← Request validation
├─────────────────────────────────────────────┤
│   Business Logic (Use Cases)                │ ← Application layer
├─────────────────────────────────────────────┤
│  Data Access (SQLAlchemy parameterized)     │ ← SQL injection protection
└─────────────────────────────────────────────┘
```

## Quick Security Checklist

### Before Deployment

- [ ] Generate strong JWT secret (32+ characters)
- [ ] Update `.env` with production secrets
- [ ] Enable HTTPS (disable HTTP in production)
- [ ] Configure CORS for specific origins only
- [ ] Review and update rate limits
- [ ] Enable security headers
- [ ] Set up monitoring and alerting
- [ ] Implement log aggregation
- [ ] Review database access permissions
- [ ] Scan dependencies for vulnerabilities

### Regular Maintenance

- [ ] Rotate JWT secrets periodically
- [ ] Review access logs for anomalies
- [ ] Update dependencies monthly
- [ ] Audit user permissions quarterly
- [ ] Review rate limit effectiveness
- [ ] Test disaster recovery procedures
- [ ] Update security documentation

## Authentication

See [Authentication Security](./authentication.md) for details.

**Summary:**
- **Method:** JWT (JSON Web Tokens)
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Token Expiry:** 24 hours
- **Password Hashing:** bcrypt (12 rounds)
- **Secret Validation:** Minimum 32 characters, rejects known weak secrets

**Key Files:**
- `src/app/shared/infrastructure/security/jwt_handler.py`
- `src/app/shared/infrastructure/security/password_handler.py`

## Authorization

**Current Implementation:**
- **Roles:** USER, ADMIN
- **Method:** JWT token includes role claim
- **Enforcement:** `get_current_user` dependency checks token
- **Protected Endpoints:** Require valid JWT token

**Planned Enhancements (Phase 2):**
- SUPER_ADMIN role
- `@require_role` decorator for fine-grained control
- Resource-based authorization (users can edit own data)

See [Phase 2 Next Steps](../implementation/phase2-next-steps.md#5-add-super_admin-role-30-minutes)

## Rate Limiting

See [Rate Limiting](./rate-limiting.md) for details.

**Summary:**
- **Library:** slowapi
- **Key:** Client IP address
- **Login Endpoint:** 5 requests per 15 minutes
- **Other Endpoints:** 100 requests per minute
- **Response:** HTTP 429 with `Retry-After` header

**Configuration:**
```python
# src/app/shared/infrastructure/rate_limit/rate_limiter.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)

# src/app/features/presentation/web/routes/auth_routes.py
@router.post("/login")
@limiter.limit("5/15minutes")
async def login(...):
    ...
```

## Password Security

### Requirements

- **Minimum length:** 8 characters
- **Uppercase:** At least one (A-Z)
- **Lowercase:** At least one (a-z)
- **Digit:** At least one (0-9)
- **Special characters:** Allowed but not required

### Hashing

- **Algorithm:** bcrypt
- **Work factor:** 12 rounds (default)
- **Execution:** Asynchronous (using `asyncio.to_thread`)
- **Verification:** Constant-time comparison

**Implementation:**
```python
# src/app/shared/infrastructure/security/password_handler.py
class PasswordHandler:
    @staticmethod
    async def hash_password(plain_password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = await asyncio.to_thread(
            bcrypt.hashpw,
            plain_password.encode("utf-8"),
            salt
        )
        return hashed.decode("utf-8")
    
    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        result = await asyncio.to_thread(
            bcrypt.checkpw,
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
        return result
```

### Validation

Enforced at API boundary using Pydantic validators:

```python
# src/app/features/application/dtos/user_dto.py
@field_validator("password")
@classmethod
def validate_password(cls, value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain digit")
    return value
```

## JWT Token Security

### Token Structure

```
Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "sub": "user-id",
  "email": "user@example.com",
  "role": "ADMIN",
  "iat": 1714497600,
  "exp": 1714584000
}

Signature:
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret_key
)
```

### Secret Key Validation

```python
# src/app/shared/infrastructure/security/jwt_handler.py
WEAK_SECRETS = {
    "secret", "your-secret-key-here", "changeme",
    "default", "test", "password", "12345", "supersecret"
}

@classmethod
def validate_secret_key(cls, secret_key: str) -> None:
    # Check length
    if len(secret_key) < 32:
        raise JWTSecretError("Secret too short (min 32 chars)")
    
    # Check against known weak secrets (case-insensitive)
    if secret_key.lower() in cls.WEAK_SECRETS:
        raise JWTSecretError("Known weak/default secret")
```

### Token Expiry

- **Access Token:** 24 hours (configurable)
- **Refresh Token:** Not yet implemented (planned: 30 days)

### Token Validation

Every protected endpoint validates:
1. Token signature (HMAC-SHA256)
2. Token expiration (`exp` claim)
3. Required claims present (`sub`, `email`, `role`)

## SQL Injection Protection

**Protection Method:** SQLAlchemy parameterized queries

All database queries use SQLAlchemy ORM or parameterized raw SQL:

```python
# ✅ SAFE - Parameterized query
result = await session.execute(
    select(UserModel).where(UserModel.email == email)
)

# ✅ SAFE - ORM methods
user = await session.get(UserModel, user_id)

# ❌ UNSAFE - String concatenation (NOT USED)
# query = f"SELECT * FROM users WHERE email = '{email}'"
```

## CORS Configuration

**Current:** Permissive (for development)

```python
# src/app/app.py
fastApiApp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Recommendation:**

```python
fastApiApp.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.yourdomain.com",
        "https://admin.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## Security Headers

**Recommended additions for production:**

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Trust only specific hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.yourdomain.com"]
)

# Add security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Secrets Management

### Development

Secrets stored in `.env` file (not committed to git):

```bash
# .env
SECRET_KEY=your-secret-key-here-at-least-32-characters-long
POSTGRES_PASSWORD=your-database-password
```

### Production

**Recommended approaches:**

1. **Environment variables** (Docker, Kubernetes)
   ```bash
   docker run -e SECRET_KEY=... -e POSTGRES_PASSWORD=... app
   ```

2. **Secrets management service** (AWS Secrets Manager, HashiCorp Vault)
   ```python
   import boto3
   secrets = boto3.client('secretsmanager')
   secret = secrets.get_secret_value(SecretId='prod/api/jwt-secret')
   ```

3. **Kubernetes secrets**
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: api-secrets
   data:
     SECRET_KEY: base64-encoded-value
   ```

### Generating Strong Secrets

```bash
# JWT secret (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Database password (16+ characters)
python -c "import secrets; print(secrets.token_urlsafe(16))"

# Or use openssl
openssl rand -base64 32
```

## Logging & Monitoring

### Security Events Logged

```python
# Authentication events
log.info("login_success", email=email, ip=ip_address)
log.warning("login_failed", email=email, ip=ip_address, reason=reason)

# Authorization events
log.warning("permission_denied", user_id=user_id, endpoint=endpoint, role=role)

# Rate limiting
log.warning("rate_limit_exceeded", ip=ip_address, endpoint=endpoint)

# Token validation
log.warning("invalid_token", ip=ip_address, reason=reason)
```

### What NOT to Log

- ❌ Passwords (plain text or hashed)
- ❌ JWT tokens (full token)
- ❌ API keys or secrets
- ❌ Personal identifiable information (PII) without need
- ❌ Credit card numbers or sensitive financial data

### Recommended Monitoring

1. **Failed authentication attempts** - Alert on >10/minute from same IP
2. **Rate limit hits** - Track which IPs are being rate limited
3. **Token validation failures** - Spike may indicate attack
4. **Unusual access patterns** - Access outside normal hours
5. **Database errors** - May indicate SQL injection attempts
6. **Permission denied errors** - Privilege escalation attempts

## Vulnerability Prevention

### Implemented

- ✅ SQL Injection → Parameterized queries
- ✅ Brute Force → Rate limiting
- ✅ Weak Passwords → Complexity requirements
- ✅ Token Tampering → HMAC signature validation
- ✅ Replay Attacks → Token expiration
- ✅ Timing Attacks → Constant-time password comparison (bcrypt)
- ✅ DoS → Rate limiting

### Planned/Recommended

- ⏸️ XSS → Content Security Policy headers
- ⏸️ CSRF → CSRF tokens (if using cookies)
- ⏸️ Clickjacking → X-Frame-Options header
- ⏸️ Man-in-the-Middle → HTTPS only, HSTS header
- ⏸️ Session Fixation → Token refresh/rotation

## Incident Response

### If Security Issue Detected

1. **Identify** - Determine scope and impact
2. **Contain** - Disable affected accounts/features
3. **Eradicate** - Remove threat, patch vulnerability
4. **Recover** - Restore normal operations
5. **Learn** - Post-mortem, update procedures

### Reporting Security Issues

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead:
- Email: security@yourdomain.com
- Include: Description, steps to reproduce, impact assessment
- Response time: Within 48 hours

## Compliance

### GDPR Considerations

- **Data minimization** - Only collect necessary data
- **Right to erasure** - Implement user deletion
- **Data portability** - Export user data functionality
- **Consent** - Track user consent for data processing
- **Breach notification** - Process for notifying users

### OWASP Top 10 Coverage

| Risk | Status | Mitigation |
|------|--------|------------|
| Broken Access Control | ✅ Addressed | JWT + role-based authorization |
| Cryptographic Failures | ✅ Addressed | bcrypt hashing, JWT signatures |
| Injection | ✅ Addressed | Parameterized queries |
| Insecure Design | ✅ Addressed | Clean Architecture, security by design |
| Security Misconfiguration | ⚠️ Partial | Need to harden production config |
| Vulnerable Components | ⚠️ Ongoing | Regular dependency updates needed |
| Authentication Failures | ✅ Addressed | Strong passwords, rate limiting |
| Data Integrity Failures | ✅ Addressed | JWT signature validation |
| Logging Failures | ⚠️ Partial | Need centralized logging |
| SSRF | ✅ N/A | No external requests from user input |

## Security Testing

### Automated Tests

```bash
# Run security-focused tests
pytest src/tests/infrastructure/security/ -v
pytest src/tests/presentation/api/test_rate_limiting.py -v
pytest src/tests/application/dtos/test_user_dto_validation.py -v
```

### Manual Testing

```bash
# Test rate limiting
for i in {1..6}; do curl -X POST .../login ...; done

# Test invalid tokens
curl -H "Authorization: Bearer fake-token" .../user/123

# Test weak passwords
curl -d '{"password":"weak"}' .../register

# Test SQL injection (should fail safely)
curl -d '{"email":"admin@example.com' OR '1'='1"}' .../login
```

### Penetration Testing

Recommended tools:
- **OWASP ZAP** - Web application scanner
- **Burp Suite** - Security testing platform
- **SQLMap** - SQL injection tester (should find nothing)
- **JWTTool** - JWT manipulation/testing

## Security Best Practices

### For Developers

See [Security Best Practices](./best-practices.md) for detailed guidelines.

**Summary:**
1. Never log sensitive data
2. Validate all inputs at API boundary
3. Use parameterized queries only
4. Hash passwords asynchronously
5. Validate JWT secrets at startup
6. Implement rate limiting on sensitive endpoints
7. Keep dependencies updated
8. Review security implications of changes
9. Write security tests
10. Follow principle of least privilege

### For Deployment

1. Use HTTPS in production (disable HTTP)
2. Generate strong random secrets (32+ chars)
3. Configure CORS for specific origins only
4. Enable security headers
5. Set up monitoring and alerting
6. Use secrets management service
7. Implement log aggregation
8. Regular security updates
9. Backup regularly
10. Test disaster recovery

### For Users

1. Use strong, unique passwords
2. Don't share credentials
3. Log out when done
4. Report suspicious activity
5. Enable 2FA when available (future)

## Security Roadmap

### Phase 2 (Planned)
- Refresh token implementation
- Token revocation/blacklist
- Enhanced health checks with security status
- Role-based authorization decorator

### Phase 3 (Future)
- Two-factor authentication (2FA)
- OAuth2/OpenID Connect integration
- API key authentication (for service accounts)
- Audit logging (who did what when)
- Password reset flow with email verification
- Account lockout after failed attempts

### Phase 4 (Future)
- Web Application Firewall (WAF) integration
- DDoS protection
- Advanced threat detection
- Security dashboards
- Automated vulnerability scanning
- Compliance reporting

---

**See Also:**
- [Authentication Security](./authentication.md)
- [Rate Limiting](./rate-limiting.md)
- [Security Best Practices](./best-practices.md)
- [API Documentation](../api/README.md)

---

**Last Updated:** April 30, 2026  
**Security Version:** 1.0.0
