# Admin User Creation - Quick Reference

## 🎯 Two Methods

### Method 1: Seed Script (First Admin)
```bash
ADMIN_EMAIL="admin@example.com" \
ADMIN_PASSWORD="SecurePass123!" \
make seed-admin
```

Or, fully containerized:
```bash
docker compose --profile seed run --rm seed-admin
```

**When to use:** Creating your first admin user

---

### Method 2: API Endpoint (Additional Admins)
```bash
# 1. Login as admin
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "SecurePass123!"}'

# 2. Create new admin (use token from step 1)
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "newadmin@example.com",
    "password": "NewAdmin123!",
    "displayName": "New Admin",
    "role": "admin"
  }'
```

**When to use:** Creating additional admins after you have at least one

---

## 📋 User Roles

| Role | Permissions | Created By |
|------|-------------|------------|
| `member` | Full access to projects, stories and refinement | Added by the workspace Admin (`POST /v1/users`) |
| `admin` | Full access + user management | Public registration or seed script |

---

## 🔐 Endpoints

| Endpoint | Auth | Role Created | Can Specify Role? |
|----------|------|--------------|-------------------|
| `POST /v1/auth/register` | ❌ Public | `admin` (of a new workspace) | ❌ No |
| `POST /v1/users` | ✅ Admin | `member` | Only `member` is accepted |

---

## ⚡ Password Requirements

✅ Minimum 8 characters  
✅ At least one letter  
✅ At least one digit  

---

## 📚 Full Documentation

See [docs/setup/ADMIN_SETUP.md](./ADMIN_SETUP.md) for:
- Detailed examples
- Security best practices
- Troubleshooting
- Production recommendations
