# Async/await Patterns
## Overview
The Open Projects Hub API uses async/await throughout for high concurrency without blocking the event loop.
## Key Pattern: `asyncio.to_thread()`
CPU-intensive operations (like bcrypt) run in a thread pool:
```python
async def hash_password(password: str) -> str:
    salt = bcrypt. gensalt()
    hashed = await asyncio.to_thread(bcrypt.hashpw, password.encode(), salt)
    return hashed.decode()
```
Direct await for database (SQLAlchemy async is native async):
```python
async with db.session() as session:
    result = await session.execute(select(UserModel))
```
## When to Use `to_thread()`
| Operation | Pattern | Why |
|----------|---------|-----|
| bcrypt | `to_thread()` | CPU-intensive |
| Database | Direct await | Native async |
| HTTP requests | `httpx.AsyncClient` | Built-in async |
## Anti-Patterns
❌ `time.sleep()` blocks event loop  
✅ `asyncio.sleep()` yields control
## Testing Async
```python
@pytest.mark.asyncio
async def test_hash_password():
    hashed = await PasswordHandler.hash_password("password123")
    assert hashed.startswith("$2b$")
```
## Key Files
- `src/ app/shared/infrastructure/security/password_handler.psy`