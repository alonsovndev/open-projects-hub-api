# Logging Implementation Guide

**Status:** ✅ Production Ready  
**Last Updated:** 2026-05-26

## Overview

This document describes the structured logging implementation across the Open Projects Hub API, completed in two phases.

## Architecture

### Core Components

1. **Correlation Context** (`src/app/shared/logging/correlation.py`)
   - Thread-safe request tracking with `request_id` and `user_id`
   - Automatic injection via `CorrelationIdFilter`

2. **Logging Utilities** (`src/app/shared/logging/utils.py`)
   - `log_business_event()` - Structured business operation logging
   - `log_error_event()` - Error logging with context
   - `mask_email()` - PII protection for email addresses
   - `redact_sensitive_fields()` - Auto-redaction of sensitive data

3. **Log Format**
   ```
   [timestamp] [level] [request:request_id] [user:user_id] logger:module message
   ```

## Phase 1: Foundation (Complete)

### Implemented

✅ Correlation context with request and user tracking  
✅ Logging utilities for structured events  
✅ PII protection (email masking, sensitive field redaction)  
✅ Enhanced authentication logging  
✅ Request/response middleware logging  
✅ 31 unit tests for logging utilities  

### Key Files Created

- `src/app/shared/logging/correlation.py` - Context management
- `src/app/shared/logging/utils.py` - Logging utilities
- `src/app/shared/logging/formatters.py` - Log formatters
- `src/tests/unit/shared/logging/` - Test suite

## Phase 2: Feature Enhancement (Complete)

### Features Enhanced

| Feature | Use Cases | Event Types | Tests |
|---------|-----------|-------------|-------|
| Dashboard | 1 | 2 | 6/6 ✅ |
| Stories | 4 | 8 | 25/25 ✅ |
| User | 2 | 6 | 11/11 ✅ |
| Clients | 3 | 6 | 16/16 ✅ |
| Refinement | 2 | 6 | 12/12 ✅ |

**Total:** 12 use cases, 28 event types, 70 tests passing

### Event Type Examples

```
story.created
story.updated
story.deleted
story.assigned
user.password.changed
user.profile.updated
client.created
client.updated
refinement.stories.generated
refinement.draft.approved
dashboard.stats.retrieved
```

## Usage Patterns

### Business Operations

```python
from src.app.shared.logging import get_logger, log_business_event

log = get_logger(__name__)

log_business_event(
    logger=log,
    event_type="story.created",
    message="Story created successfully",
    entity_id=str(story_id),
    user_id=created_by,
    additional_data={"title": story.title},
)
```

### Error Handling

```python
from src.app.shared.logging import log_error_event

log_error_event(
    logger=log,
    error_type="story.create.validation_failed",
    message="Story validation failed",
    error=exception,
    additional_data={"user_id": created_by},
)
```

### PII Protection

```python
from src.app.shared.logging import mask_email

log_business_event(
    logger=log,
    event_type="user.profile.updated",
    message="Profile updated",
    additional_data={
        "email": mask_email(user.email),  # jo***@example.com
    },
)
```

### Change Tracking

```python
changes = {}
if new_title != old_title:
    changes["title"] = {"old": old_title, "new": new_title}

log_business_event(
    logger=log,
    event_type="story.updated",
    message="Story updated",
    entity_id=str(story_id),
    additional_data={"changes": changes},
)
```

## Use Case Template

Every use case should follow this pattern:

```python
from src.app.shared.logging import get_logger, log_business_event, log_error_event

log = get_logger(__name__)

class CreateStoryUseCase:
    async def execute(self, request: CreateStoryRequest, created_by: str) -> StoryResponse:
        try:
            # 1. Log validation failures (WARNING)
            if not request.title:
                log.warning(
                    "Validation failed",
                    extra={
                        "event_type": "story.create.validation_failed",
                        "user_id": created_by,
                    },
                )
                raise ValueError("Title required")

            # 2. Perform operation
            story = await self.repository.save(...)

            # 3. Log success (INFO)
            log_business_event(
                logger=log,
                event_type="story.created",
                message="Story created successfully",
                entity_id=str(story.id.value),
                user_id=created_by,
            )

            return response

        except ValueError:
            raise  # Already logged
        except Exception as e:
            # Log unexpected errors (ERROR)
            log_error_event(
                logger=log,
                error_type="story.create.unexpected_error",
                message="Unexpected error",
                error=e,
            )
            raise
```

## Security & Compliance

### PII Protection

✅ **Auto-redacted fields:** password, token, secret, api_key, access_token, refresh_token, authorization, credential  
✅ **Email masking:** `john.doe@example.com` → `jo***@example.com`  
✅ **No sensitive data in logs:** Passwords, JWT tokens, and credentials never logged  

### Audit Trail

✅ **WHO**: `user_id` in all business events  
✅ **WHAT**: `event_type` describes action  
✅ **WHEN**: ISO 8601 timestamp in every log record  
✅ **WHERE**: `entity_id` for affected resources  
✅ **CHANGES**: Old/new values tracked in updates  

## Configuration

Environment-specific settings in `src/app/config/config_<env>.yml`:

```yaml
logging:
  level: "INFO"          # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "text"         # "text" for local, "json" for production
```

## Search & Filter Examples

### By Event Type

```bash
# Text format (local)
grep "event_type.*story.created" logs/app.log

# JSON format (production)
jq 'select(.event_type == "story.created")' logs/app.json
```

### By User

```bash
# Text format
grep "user:550e8400-e29b-41d4-a716-446655440000" logs/app.log

# JSON format
jq 'select(.user_id == "550e8400-e29b-41d4-a716-446655440000")' logs/app.json
```

### By Request

```bash
# Trace entire request lifecycle
grep "request:abc123def456" logs/app.log
```

### Audit Security Operations

```bash
# Password changes
grep "event_type.*user.password.changed" logs/app.log

# Failed login attempts
grep "event_type.*auth.login.invalid_credentials" logs/app.log
```

## Test Coverage

### Logging Utilities
- 31 unit tests in `src/tests/unit/shared/logging/`
- Tests for correlation context, redaction, masking, event logging

### Feature Use Cases
- 70 tests for enhanced use cases across 5 features
- All tests verify logging doesn't break functionality

**Total:** 101 tests passing ✅

## Migration Checklist

When adding logging to existing code:

- [ ] Import utilities: `get_logger`, `log_business_event`, `log_error_event`, `mask_email`
- [ ] Initialize logger: `log = get_logger(__name__)`
- [ ] Replace f-string logs with structured logging
- [ ] Add event types: `<feature>.<entity>.<action>`
- [ ] Mask emails in logs
- [ ] Track field changes in updates
- [ ] Log validation failures at WARNING level
- [ ] Log unexpected errors with `log_error_event`
- [ ] Log business events with `log_business_event`
- [ ] Verify tests pass

## References

- **Standards:** [Logging Standards](./logging-standards.md) - Complete patterns and conventions
- **Source Code:** `src/app/shared/logging/` - Implementation
- **Tests:** `src/tests/unit/shared/logging/` - Test suite
- **Configuration:** `src/app/config/config_*.yml` - Environment settings

## Implementation Statistics

- **Features Enhanced:** 5 (Dashboard, Stories, User, Clients, Refinement)
- **Use Cases Enhanced:** 12
- **Event Types Added:** 28
- **Tests Created/Updated:** 101
- **Lines of Documentation:** 1,500+
- **Code Quality:** ✅ All linting passed, zero regressions

## Next Steps

**Production Readiness:**
✅ Code complete and tested  
✅ Documentation complete  
✅ Standards documented  
✅ Zero regressions  

**Future Enhancements:**
- Set up log aggregation (ELK, Datadog, CloudWatch)
- Create monitoring dashboards
- Implement audit report generators
- Add performance timing metrics

---

**Status:** Production Ready  
**Approved:** 2026-05-26  
**Version:** 1.0
