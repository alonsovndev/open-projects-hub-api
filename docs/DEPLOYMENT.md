# Deployment Guide

This guide covers deploying the Open Projects Hub API to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Security Checklist](#security-checklist)
- [Monitoring & Logging](#monitoring--logging)

---

## Prerequisites

### Required

- Docker 20.10+ with Docker Compose v2
- PostgreSQL 15+ (or use Docker Compose)
- Python 3.12+ (for local development)
- Git

### Recommended

- Reverse proxy (Nginx, Traefik, etc.) for HTTPS termination
- Secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.)
- Log aggregation service (ELK, CloudWatch, etc.)
- Monitoring service (Prometheus, Datadog, etc.)

---

## Docker Deployment

### 1. Clone Repository

```bash
git clone <repository-url>
cd open-projects-hub-api
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with production values:

```bash
# Application Environment — note: the bundled compose.yml sets APP_ENV=container on the
# app service, which overrides this value. To run with config_prod.yml under Compose,
# change `environment.APP_ENV` in compose.yml.
APP_ENV=prod

# Logging
LOG_LEVEL=INFO
LOG_FORMAT_JSON=true

# Database (use strong passwords!)
POSTGRES_USER=open-projects-hub-admin
POSTGRES_PASSWORD=<GENERATE_STRONG_PASSWORD>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=open-projects-hub-db

# JWT (CRITICAL: Generate strong secret, minimum 32 characters)
SECRET_KEY=<GENERATE_STRONG_SECRET_KEY>

# CORS (restrict to your frontend domains)
CORS_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com
CORS_ALLOW_CREDENTIALS=true

# Encryption of user-supplied AI provider keys (required, no default; see ADR-018 —
# losing or changing it makes every stored user key undecryptable)
API_KEY_ENCRYPTION_KEY=<GENERATE_BASE64_32_BYTES>

# Platform AI provider keys — only the one named by `ai.provider` in config_<env>.yml is used;
# without it, story refinement falls back to the mock AI service
GEMINI_API_KEY=
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
```

**Generate strong secrets:**
```bash
# JWT secret (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# API key encryption key (base64-encoded 32 bytes)
python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"

# Database password (16+ characters)
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### 3. Build and Start Services

```bash
# Build and start in detached mode (--build picks up code/dependency changes;
# without it Compose reuses the previously built image)
docker compose up --build -d

# Check logs
docker compose logs -f app

# Check health
curl http://localhost:8080/health
```

### 4. Run Database Migrations

Migrations run automatically on container startup via `scripts/start-api.sh`.

To run manually:
```bash
docker compose exec app alembic upgrade head
```

### 5. Create First Admin User

Run the one-shot `seed-admin` compose service (uses the same `.env`/`APP_ENV=container` config as the `app` service, so it always targets the running database):

```bash
docker compose --profile seed run --rm seed-admin
```

Or set custom credentials for that run:
```bash
ADMIN_EMAIL="admin@yourdomain.com" \
ADMIN_PASSWORD="SecureAdmin123!" \
ADMIN_DISPLAY_NAME="System Administrator" \
docker compose --profile seed run --rm -e ADMIN_EMAIL -e ADMIN_PASSWORD -e ADMIN_DISPLAY_NAME seed-admin
```

Running outside Docker (e.g. `APP_ENV=local` against a host-exposed Postgres):
```bash
ADMIN_EMAIL="admin@yourdomain.com" \
ADMIN_PASSWORD="SecureAdmin123!" \
ADMIN_DISPLAY_NAME="System Administrator" \
python scripts/seed_admin.py
```

---

## Environment Configuration

### Available Environments

| Environment | Purpose | API Docs | Usage |
|------------|---------|----------|-------|
| `local` | Local development with hot reload | ✅ Enabled | Development |
| `dev` | Development server | ❌ Disabled | Staging |
| `container` | Docker containerized | ✅ Enabled | Docker dev |
| `prod` | Production | ❌ Disabled | Production |
| `test` | Testing | ❌ Disabled | CI/CD |

### Configuration Files

Environment-specific YAML configs in `src/app/config/`:

- `config_local.yml` - Local development settings
- `config_dev.yml` - Development server settings
- `config_container.yml` - Docker container settings
- `config_prod.yml` - Production settings
- `config_test.yml` - Testing settings

Set `APP_ENV` environment variable to switch environments.

---

## Database Setup

### Using Docker Compose (Recommended)

The default `compose.yml` includes PostgreSQL 15 with health checks.

**Ports:**
- API: `8080` (mapped from container port `8080`)
- PostgreSQL: `5432` (mapped from container port `5432`)

### Using External PostgreSQL

Update `.env`:

```bash
POSTGRES_HOST=your-database-host.example.com
POSTGRES_PORT=5432
POSTGRES_USER=your-db-user
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=open-projects-hub-db
```

Then remove the `postgres` service from `compose.yml` or use:

```bash
docker compose up app -d
```

### Backup & Restore

**Backup:**
```bash
docker compose exec postgres pg_dump -U open-projects-hub-admin open-projects-hub-db > backup.sql
```

**Restore:**
```bash
docker compose exec -T postgres psql -U open-projects-hub-admin open-projects-hub-db < backup.sql
```

---

## Security Checklist

### Before Production Deployment

- [ ] **Generate strong JWT secret** (minimum 32 characters, not default value)
- [ ] **Use strong database password** (16+ characters, random)
- [ ] **Configure CORS** for specific domains only (not `*`)
- [ ] **Enable HTTPS** via reverse proxy (Nginx, Traefik, etc.)
- [ ] **Disable HTTP** in production (redirect to HTTPS)
- [ ] **Set `APP_ENV=prod`** to disable API docs (`/docs`, `/redoc`)
- [ ] **Review rate limits** in `src/app/shared/infrastructure/rate_limit/rate_limiter.py`
- [ ] **Enable structured JSON logging** (`LOG_FORMAT_JSON=true`)
- [ ] **Set `LOG_LEVEL=INFO`** (not DEBUG in production)
- [ ] **Use secrets management** (not `.env` files in production)
- [ ] **Restrict database access** (firewall rules, VPC)
- [ ] **Run security scan** (`make security`)
- [ ] **Update dependencies** regularly
- [ ] **Set up monitoring** and alerting
- [ ] **Configure log aggregation**
- [ ] **Test backup/restore** procedures

### Security Headers (Recommended)

Add via reverse proxy (Nginx example):

```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

---

## Monitoring & Logging

### Health Check Endpoint

```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Open Projects Hub API",
  "version": "1.0.0"
}
```

### Structured Logging

The API uses structured JSON logging when `LOG_FORMAT_JSON=true`.

**Log fields:**
- `timestamp` - ISO 8601 timestamp
- `level` - Log level (INFO, WARNING, ERROR, etc.)
- `message` - Log message
- `request_id` - Unique request identifier
- `user_id` - Authenticated user ID (if applicable)
- `event_type` - Business event type (e.g., `story.created`)
- Additional context fields

**Example log entry:**
```json
{
  "timestamp": "2026-06-11T10:30:00.123Z",
  "level": "INFO",
  "message": "Story created successfully",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "event_type": "story.created",
  "entity_id": "770e8400-e29b-41d4-a716-446655440002",
  "title": "Implement user authentication"
}
```

### Docker Logs

```bash
# View all logs
docker compose logs

# Follow logs (real-time)
docker compose logs -f

# View specific service logs
docker compose logs -f app
docker compose logs -f postgres

# Last 100 lines
docker compose logs --tail=100 app
```

### Log Aggregation (Recommended)

For production, use log aggregation services:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **AWS CloudWatch Logs**
- **Google Cloud Logging**
- **Datadog**
- **Splunk**

---

## Reverse Proxy Setup

### Nginx Example

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Traefik Example

```yaml
# docker-compose.yml
services:
  app:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
      - "traefik.http.services.api.loadbalancer.server.port=8080"
```

---

## Troubleshooting

### API Not Starting

**Check logs:**
```bash
docker compose logs app
```

**Common issues:**
- Database not ready → Wait for postgres healthcheck
- Migrations failed → Check database connection
- Port conflict → Change port mapping in `compose.yml`

### Database Connection Errors

**Verify database is running:**
```bash
docker compose ps postgres
```

**Check database logs:**
```bash
docker compose logs postgres
```

**Test connection:**
```bash
docker compose exec postgres psql -U open-projects-hub-admin -d open-projects-hub-db -c "SELECT 1;"
```

### JWT Errors

**Symptoms:**
- `JWTSecretError: Secret too short`
- `JWTSecretError: Known weak/default secret`

**Solution:**
Generate a strong secret (32+ characters):
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update `SECRET_KEY` in `.env` and restart:
```bash
docker compose restart app
```

---

## Scaling & Performance

### Horizontal Scaling

Run multiple app containers behind a load balancer:

```yaml
services:
  app:
    deploy:
      replicas: 3
```

### Database Connection Pooling

SQLAlchemy async engine uses connection pooling by default.

Configure pool size in `src/app/shared/persistence/engine_factory.py`.

### Caching (Future)

Consider adding Redis for:
- Session storage
- Rate limiting state
- Query result caching

---

## Support & Maintenance

### Regular Tasks

- **Weekly:** Review logs for errors and security events
- **Monthly:** Update dependencies, security patches
- **Quarterly:** Review and rotate secrets, audit user permissions

### Monitoring Metrics

Track these metrics:

- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database connection pool usage
- Memory/CPU usage
- Disk space

### Alerting

Set up alerts for:

- Error rate spike (> 5%)
- Response time degradation (p95 > 1s)
- Database connection failures
- Disk space low (< 20% free)
- Rate limit violations spike

---

## See Also

- [API Documentation](./api/README.md)
- [Security Overview](./security/README.md)
- [Admin Setup Guide](./setup/ADMIN_SETUP.md)
- [Code Quality Guide](./CODE_QUALITY.md)

---

**Last Updated:** June 11, 2026  
**Deployment Version:** 1.0.0
