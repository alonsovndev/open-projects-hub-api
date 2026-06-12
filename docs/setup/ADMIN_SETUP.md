# Admin User Setup Guide

This guide explains how to create admin users in the Open Projects Hub API.

## Table of Contents

- [Overview](#overview)
- [Method 1: Database Seed Script (First Admin)](#method-1-database-seed-script-first-admin)
- [Method 2: API Endpoint (Subsequent Admins)](#method-2-api-endpoint-subsequent-admins)
- [Security Best Practices](#security-best-practices)

---

## Overview

The system supports two types of users:
- **`viewer`** - Can view projects and stories (default role for public registration)
- **`admin`** - Full access including user management, project/story creation, and deletion

### User Creation Endpoints

| Endpoint | Auth Required | Default Role | Can Specify Role? |
|----------|---------------|--------------|-------------------|
| `POST /v1/auth/register` | ❌ No (public) | `viewer` | ❌ No |
| `POST /v1/users` | ✅ Yes (admin only) | `viewer` | ✅ Yes |

---

## Method 1: Database Seed Script (First Admin)

**Use this method to create your first admin user.**

### Quick Start

```bash
# Using environment variables
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname" \
ADMIN_EMAIL="admin@mycompany.com" \
ADMIN_PASSWORD="SecurePass123!" \
ADMIN_DISPLAY_NAME="Main Admin" \
make seed-admin
```

Or using the script directly:

```bash
# Using the script directly
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"
export ADMIN_EMAIL="admin@mycompany.com"
export ADMIN_PASSWORD="SecurePass123!"
export ADMIN_DISPLAY_NAME="Main Admin"

python3 scripts/seed_admin.py
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | - | PostgreSQL connection string with asyncpg driver |
| `ADMIN_EMAIL` | No | `admin@example.com` | Email for the admin user |
| `ADMIN_PASSWORD` | No | `Admin123!@#` | Password (min 8 chars) |
| `ADMIN_DISPLAY_NAME` | No | `System Administrator` | Display name |

### Example Output

```
============================================================
🌱 Admin User Seed Script
============================================================
Database: localhost:5432/open_projects_hub
Admin Email: admin@mycompany.com
Admin Name: Main Admin
------------------------------------------------------------
✅ Admin user created successfully!
   User ID: 550e8400-e29b-41d4-a716-446655440000
   Email: admin@mycompany.com
   Display Name: Main Admin
   Role: admin
   Created At: 2026-05-18 10:30:00
============================================================
🎉 You can now login with these credentials:
   Email: admin@mycompany.com
   Password: SecurePass123!
============================================================
```

### Docker Compose Example

If using Docker Compose with the default `compose.yml`:

```bash
# Get DATABASE_URL from compose.yml environment variables
# Default username: open-projects-hub-admin, database: open-projects-hub-db
DATABASE_URL="postgresql+asyncpg://open-projects-hub-admin:YOUR_POSTGRES_PASSWORD@localhost:5432/open-projects-hub-db" \
ADMIN_EMAIL="admin@mycompany.com" \
ADMIN_PASSWORD="SecureAdmin123!" \
make seed-admin
```

**Note:** Replace `YOUR_POSTGRES_PASSWORD` with the `POSTGRES_PASSWORD` value from your `.env` file.

### Idempotent Behavior

The script is **safe to run multiple times**. If the admin user already exists, it will report:

```
⚠️  Admin user already exists: admin@mycompany.com
   User ID: 550e8400-e29b-41d4-a716-446655440000
   Role: admin
   Created: 2026-05-18 10:30:00
------------------------------------------------------------
✅ No action needed - admin user already exists
```

---

## Method 2: API Endpoint (Subsequent Admins)

**Use this method to create additional admin users after you have at least one admin.**

### Prerequisites

1. You must have an existing admin account
2. Obtain an access token by logging in

### Step 1: Login as Admin

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@mycompany.com",
    "password": "SecureAdmin123!"
  }'
```

**Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@mycompany.com",
    "displayName": "Main Admin",
    "role": "admin"
  }
}
```

### Step 2: Create New Admin User

```bash
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "newadmin@mycompany.com",
    "password": "AnotherSecurePass123!",
    "displayName": "Secondary Admin",
    "role": "admin"
  }'
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "email": "newadmin@mycompany.com",
  "displayName": "Secondary Admin",
  "role": "admin"
}
```

### Creating Viewer Users

To create a viewer user (or omit `role` to default to viewer):

```bash
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "viewer@mycompany.com",
    "password": "ViewerPass123!",
    "displayName": "John Viewer",
    "role": "viewer"
  }'
```

---

## Security Best Practices

### Password Requirements

All passwords must meet these requirements:
- ✅ Minimum 8 characters
- ✅ At least one letter (a-z, A-Z)
- ✅ At least one digit (0-9)

**Strong password examples:**
- `SecureAdmin123!`
- `MyP@ssw0rd2024`
- `Adm1nStr0ng!`

### Production Recommendations

1. **Change Default Credentials Immediately**
   ```bash
   # Never use the default password in production
   ADMIN_PASSWORD="YourVeryStrongPassword123!" make seed-admin
   ```

2. **Use Environment Variables**
   - Never hardcode credentials in code
   - Use `.env` files (excluded from git)
   - Use secrets management in production (AWS Secrets Manager, Vault, etc.)

3. **Restrict Seed Script Access**
   ```bash
   # Make seed script executable only by owner
   chmod 700 scripts/seed_admin.py
   ```

4. **Disable Seed Script in Production**
   - Run seed script only during initial setup
   - Consider removing or protecting the script in production deployments

5. **Audit Admin Creation**
   - Monitor admin user creation via API logs
   - Implement additional validation or approval workflows if needed

6. **Use Rate Limiting**
   - The `POST /v1/users` endpoint inherits standard rate limiting
   - Consider additional restrictions for admin user creation

### Environment-Specific Setup

#### Development
```bash
# .env.development
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dev_db
ADMIN_EMAIL=admin@dev.local
ADMIN_PASSWORD=DevAdmin123!
```

#### Production
```bash
# Use secrets management, not .env files
# Example: AWS Secrets Manager, HashiCorp Vault, etc.
aws secretsmanager get-secret-value --secret-id prod/admin/credentials
```

---

## Troubleshooting

### Error: "DATABASE_URL environment variable is required"

**Solution:** Ensure `DATABASE_URL` is set with the correct format:
```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"
```

### Error: "Admin password must be at least 8 characters long"

**Solution:** Use a password with at least 8 characters:
```bash
export ADMIN_PASSWORD="MySecurePass123!"
```

### Error: "type 'userrole' does not exist"

**Solution:** Run database migrations:
```bash
alembic upgrade head
```

### Error: "Permission denied: scripts/seed_admin.py"

**Solution:** Make the script executable:
```bash
chmod +x scripts/seed_admin.py
```

---

## Summary

| Task | Method | Command |
|------|--------|---------|
| Create first admin | Seed script | `DATABASE_URL=... ADMIN_EMAIL=... make seed-admin` |
| Create additional admins | API | `POST /v1/users` with `role: "admin"` |
| Public registration | API | `POST /v1/auth/register` (always creates viewers) |

For questions or issues, refer to the [main documentation](../README.md) or open an issue.
