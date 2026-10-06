# Rate Limiting Configuration and Strategy

**Last Updated:** 2026-05-11  
**Status:** ✅ Documented and Configured

## Current Implementation

### Technology Stack
- **Library:** `slowapi` (v0.1.9)
- **Storage:** In-process memory
- **Key Function:** Client IP address (`get_remote_address`)

### Rate Limits by Endpoint

| Endpoint | Rate Limit | Purpose |
|---|---|---|
| Global default | 100 req/minute | Prevent general abuse |
| `/v1/auth/login` | 10 req/minute | Mitigate brute-force attacks |
| `/v1/auth/register` | 5 req/minute | Prevent account spam |
| `/v1/auth/refresh` | 10/15 minutes | Limit token refresh attempts |
| `/v1/viewer/{access_code}` | 30 req/minute | Public Client Review route; the access code is its only credential, so cap guessing |

### Configuration

```python
# src/app/shared/infrastructure/rate_limit/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
```

### Usage Pattern

```python
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter

@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, ...):
    ...
```

---

## Scalability Analysis

### ✅ Current Setup (Single Instance)

**Works For:**
- Development environments
- Single-server deployments
- Low-to-medium traffic applications
- Vertical scaling scenarios

**Characteristics:**
- Simple implementation
- No external dependencies
- Low latency (in-memory)
- Zero operational overhead

### ⚠️ Limitations (Multi-Instance)

**Problem:**
Each application instance maintains its own rate limit counters in memory. In a horizontally scaled deployment (multiple pods/containers), a client can bypass rate limits by distributing requests across instances.

**Example:**
```
Rate limit: 10 req/minute per IP
Instances: 3 pods

Real effective limit per IP: 10 × 3 = 30 req/minute
```

**Impact:**
- Rate limits are 3× less effective with 3 instances
- No shared state across pods
- Limits are per-instance, not per-system

---

## Migration Path to Distributed Rate Limiting

### Option 1: Redis-Backed Rate Limiting (Recommended)

**When to Use:**
- Horizontal scaling (2+ instances)
- Production deployments
- Multi-region setups

**Implementation:**
```python
# Future: Redis-backed limiter
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=f"redis://{redis_client.connection_pool.connection_kwargs['host']}:"
                f"{redis_client.connection_pool.connection_kwargs['port']}"
)
```

**Benefits:**
- Shared state across all instances
- Accurate rate limiting system-wide
- TTL-based automatic cleanup
- Battle-tested solution

**Requirements:**
- Redis server/cluster
- Network latency consideration
- Additional infrastructure cost

**Migration Steps:**
1. Deploy Redis (ElastiCache, Redis Cloud, or self-hosted)
2. Update `requirements.txt` to include `redis` package
3. Add Redis connection configuration to `config_*.yml`
4. Update `rate_limiter.py` to use Redis storage
5. Test in staging environment
6. Deploy to production

---

### Option 2: API Gateway Rate Limiting

**When to Use:**
- Using AWS API Gateway, Kong, Nginx, or similar
- Want to offload rate limiting to infrastructure layer
- Need centralized policy management

**Benefits:**
- No application code changes
- Centralized configuration
- Often included in gateway service
- Lower application resource usage

**Drawbacks:**
- Less fine-grained control
- Harder to customize per-endpoint
- Requires infrastructure changes

---

### Option 3: In-Memory with Adjusted Limits (Current Interim Solution)

**When to Use:**
- Short-term solution while Redis is deferred
- Single-instance or low-scale deployments
- Development/staging environments

**Configuration:**
Current rate limits have been set conservatively to account for potential multi-instance deployments:

```python
# Adjusted for 2-3 instance deployment
# Actual limit per instance may be divided by instance count
DEFAULT_LIMIT = "100/minute"  # Effective: 200-300/min with 2-3 instances
LOGIN_LIMIT = "10/minute"     # Effective: 20-30/min with 2-3 instances  
REGISTER_LIMIT = "5/minute"   # Effective: 10-15/min with 2-3 instances
```

**Limitations:**
- Not a true distributed solution
- Still vulnerable to multi-instance bypass
- Acceptable for development and staging
- **Not recommended for production at scale**

---

## Monitoring Recommendations

### Metrics to Track

1. **Rate Limit Hits:**
   - Count of requests blocked by rate limiter
   - By endpoint, status code 429
   - Alert on unusual spikes

2. **Instance Count:**
   - Track number of running instances
   - Correlate with effective rate limit thresholds

3. **Client Behavior:**
   - IPs frequently hitting rate limits
   - Potential abuse patterns
   - Legitimate users affected

### Logging

Current implementation logs rate-limited requests via slowapi's exception handler. With structured JSON logging enabled, these appear as:

```json
{
  "timestamp": 1778551531.499686,
  "level": "WARNING",
  "message": "Rate limit exceeded",
  "request_id": "...",
  "client_host": "192.168.1.1",
  "path": "/v1/auth/login",
  "status_code": 429
}
```

---

## Configuration Management

### Environment Variables

```bash
# Future: Redis configuration (when implemented)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional-password

# Rate limit configuration (optional overrides)
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_LOGIN=10/minute
RATE_LIMIT_REGISTER=5/minute
```

### Current Configuration Files

Rate limits are currently hardcoded in route decorators. For production, consider moving to configuration files:

```yaml
# config_prod.yml (future enhancement)
rate_limiting:
  enabled: true
  backend: redis  # or "memory" for development
  redis_url: ${REDIS_URL}
  limits:
    default: "100/minute"
    auth_login: "10/minute"
    auth_register: "5/minute"
    auth_refresh: "10/15minutes"
```

---

## Decision Matrix

| Scenario | Recommended Solution |
|---|---|
| Single instance deployment | Current in-memory (slowapi) ✅ |
| 2-3 instances (low traffic) | In-memory with adjusted limits ⚠️ |
| 4+ instances or high traffic | Redis-backed rate limiting 🎯 |
| Using API Gateway | Gateway-level rate limiting 🎯 |
| Development/Staging | Current in-memory ✅ |

---

## Current Status & Next Steps

### ✅ Completed (Sprint 1-2)
- Per-endpoint rate limits configured
- Auth endpoints have stricter limits
- Rate limiting tests implemented
- Documentation created

### 🔄 Deferred (Future Sprint)
- Redis-backed distributed rate limiting
- Configurable rate limits via environment/config
- Rate limit metrics/monitoring
- Custom rate limit responses

### 📋 Immediate Actions Required
**None** - Current configuration is acceptable for:
- Development environments
- Single-instance deployments
- Staging environments

### 📋 Future Actions (Before Production Scale-Out)
1. Deploy Redis infrastructure
2. Implement Redis-backed rate limiter
3. Test distributed rate limiting
4. Update deployment documentation
5. Configure monitoring/alerting

---

## Testing Rate Limits

### Manual Testing

```bash
# Test login rate limit (should return 429 after 10 requests)
for i in {1..15}; do
  curl -X POST http://localhost:8000/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}' \
    -w "\n%{http_code}\n"
done

# Test with different IPs (requires proxy or multiple clients)
curl -X POST http://localhost:8000/v1/auth/login \
  -H "X-Forwarded-For: 192.168.1.100" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrong"}'
```

### Automated Testing

See `src/tests/presentation/api/test_rate_limiting.py` for rate limit test suite.

---

## References

- **slowapi Documentation:** https://github.com/laurentS/slowapi
- **Redis Rate Limiting Pattern:** https://redis.io/docs/manual/patterns/rate-limiter/
- **OWASP Rate Limiting:** https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html

---

**Conclusion:**

The current in-memory rate limiting solution with slowapi is **production-ready for single-instance deployments** and adequate for development/staging. For horizontally scaled production deployments (2+ instances), **Redis-backed rate limiting should be implemented** as part of a future sprint.

The rate limits configured in Sprint 1 provide strong protection against brute-force and abuse attacks, with conservative values that balance security and usability.
