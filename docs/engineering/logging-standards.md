# Logging Standards

**Status:** Adopted  
**Last Updated:** 2026-05-26  
**Authors:** Open Projects Hub Team

## Purpose

This document defines the logging standards for Open Projects Hub API. These standards ensure:
- Consistent structured logging across all features
- Secure handling of PII and sensitive data
- Effective audit trail for business operations
- Easy searchability and troubleshooting
- Request traceability with correlation IDs

## Core Components

### 1. Correlation Context

Every request is tracked with:
- **Request ID**: Unique identifier for each HTTP request
- **User ID**: Authenticated user UUID (when authenticated)

Both IDs are automatically injected into all log records via `CorrelationIdFilter`.

**Log Format:**
```
[timestamp] [level] [request:request_id] [user:user_id] logger_name:module.py:line_number message
```

**Implementation:**
```python
from src.app.shared.logging.correlation import set_correlation_id, set_user_context

# In middleware (automatic)
set_correlation_id(request_id)

# In auth dependency (automatic)
set_user_context(user_id)
```

### 2. Structured Event Logging

Use structured events with `event_type` for filtering and searching.

#### Event Type Naming Convention

```
<feature>.<entity>.<action>[.<detail>]
```

**Examples:**
- `story.created`
- `story.updated`
- `story.assigned`
- `auth.login.invalid_credentials`
- `refinement.stories.generated`
- `dashboard.stats.retrieved`

#### Business Events

```python
from src.app.shared.logging import log_business_event

log_business_event(
    logger=log,
    event_type="story.created",
    message="Story created successfully",
    entity_id=str(story_id),
    user_id=created_by,
    additional_data={
        "title": story.title,
        "status": story.status.value,
    },
)
```

#### Error Events

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

### 3. PII and Sensitive Data Protection

**Auto-Redacted Fields:**
- `password`
- `token`, `access_token`, `refresh_token`
- `secret`, `api_key`
- `authorization`, `credential`

**Email Masking:**
```python
from src.app.shared.logging import mask_email

masked = mask_email("john.doe@example.com")
# Output: "jo***@example.com"
```

**Usage:**
```python
log_business_event(
    logger=log,
    event_type="auth.login.success",
    message="User logged in successfully",
    additional_data={
        "email": mask_email(user_email),  # Always mask emails
    },
)
```

**Never Log:**
- Plain passwords
- JWT tokens
- Raw API keys
- Complete credit card numbers
- Unmasked emails in business events

### 4. Logging Utilities

#### Redact Sensitive Fields

```python
from src.app.shared.logging import redact_sensitive_fields

safe_data = redact_sensitive_fields({
    "username": "john",
    "password": "secret123",
    "api_key": "abc123",
})
# Output: {"username": "john", "password": "***REDACTED***", "api_key": "***REDACTED***"}
```

## Feature-Specific Patterns

### Authentication

```python
# Success
log_business_event(
    logger=log,
    event_type="auth.login.success",
    message="User logged in successfully",
    user_id=user_id,
    additional_data={"email": mask_email(email)},
)

# Failure
log.warning(
    "Login failed due to invalid credentials",
    extra={
        "email": mask_email(email),
        "event_type": "auth.login.invalid_credentials",
    },
)
```

### CRUD Operations

```python
# Create
log_business_event(
    logger=log,
    event_type="story.created",
    message="Story created successfully",
    entity_id=str(story_id),
    user_id=created_by,
    additional_data={"title": story.title},
)

# Update with change tracking
changes = {}
if new_title != old_title:
    changes["title"] = {"old": old_title, "new": new_title}

log_business_event(
    logger=log,
    event_type="story.updated",
    message="Story updated successfully",
    entity_id=str(story_id),
    user_id=updated_by,
    additional_data={"changes": changes},
)

# Delete
log_business_event(
    logger=log,
    event_type="story.deleted",
    message="Story deleted successfully",
    entity_id=str(story_id),
    user_id=deleted_by,
)
```

### AI Operations

```python
# Start
log.info(
    "Starting AI story generation from notes",
    extra={
        "project_id": project_id,
        "notes_length": len(raw_notes),
        "event_type": "refinement.generate.started",
    },
)

# Success
log_business_event(
    logger=log,
    event_type="refinement.stories.generated",
    message="Stories generated from notes successfully",
    entity_id=project_id,
    user_id=created_by,
    additional_data={
        "story_count": len(stories),
        "notes_length": len(raw_notes),
    },
)
```

### Database Operations

```python
# Repository logging
log_error_event(
    logger=log,
    error_type="dashboard.database.aggregation_failed",
    message="Failed to retrieve dashboard stats",
    error=exception,
)
```

## Log Levels

| Level | Usage |
|-------|-------|
| **DEBUG** | Development-only details (disabled in production) |
| **INFO** | Normal business operations, successful events |
| **WARNING** | Expected errors (validation failures, not found, auth failures) |
| **ERROR** | Unexpected errors, infrastructure failures, unhandled exceptions |
| **CRITICAL** | System-level failures requiring immediate attention |

## Use Case Logging Pattern

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
                    "Story title validation failed",
                    extra={
                        "event_type": "story.create.validation_failed",
                        "user_id": created_by,
                    },
                )
                raise ValueError("Title is required")

            # 2. Perform operation
            story = StoryEntity.create(...)
            saved_story = await self.repository.save(story)

            # 3. Log success (INFO)
            log_business_event(
                logger=log,
                event_type="story.created",
                message="Story created successfully",
                entity_id=str(saved_story.id.value),
                user_id=created_by,
                additional_data={"title": saved_story.title},
            )

            return to_story_response(saved_story)

        except ValueError:
            # Re-raise expected errors (already logged above)
            raise
        except Exception as e:
            # Log unexpected errors (ERROR)
            log_error_event(
                logger=log,
                error_type="story.create.unexpected_error",
                message="Unexpected error during story creation",
                error=e,
                additional_data={"user_id": created_by},
            )
            raise
```

## Testing Logging

When testing, verify log records include expected fields:

```python
def test_logs_business_event(caplog):
    # Arrange
    use_case = CreateStoryUseCase(mock_repository)

    # Act
    with caplog.at_level(logging.INFO):
        result = await use_case.execute(request, user_id)

    # Assert
    assert any(
        record.event_type == "story.created"
        and record.entity_id == str(story_id)
        for record in caplog.records
    )
```

## Configuration

### Environment-Specific Levels

- **Local/Development**: DEBUG
- **Staging**: INFO
- **Production**: INFO

Configured in `src/app/config/config_<env>.yml`:

```yaml
logging:
  level: "INFO"
  format: "text"  # or "json" for production
```

### JSON Format for Production

JSON format enables:
- Easy parsing by log aggregation tools (ELK, Datadog, CloudWatch)
- Structured field extraction
- Efficient searching and filtering

Text format is preferred for local development (human-readable).

## Migration Checklist

When adding logging to existing code:

- [ ] Import logging utilities: `get_logger`, `log_business_event`, `log_error_event`, `mask_email`
- [ ] Add logger initialization: `log = get_logger(__name__)`
- [ ] Replace f-string logs with structured event logging
- [ ] Add event types following naming convention
- [ ] Mask all email addresses in logs
- [ ] Track field changes in update operations
- [ ] Log validation failures at WARNING level
- [ ] Log unexpected errors with `log_error_event`
- [ ] Log successful business events with `log_business_event`
- [ ] Verify tests still pass

## Examples by Feature

### Auth
- ✅ `login_user.py` - Complete example with masked emails and structured events

### Stories
- ✅ `create_story.py` - Creation with validation logging
- ✅ `update_story.py` - Change tracking in updates
- ✅ `delete_story.py` - Deletion event logging
- ✅ `assign_story.py` - Assignment with previous assignee tracking

### Projects
- ✅ `create_project.py` - Business event logging pattern

### Dashboard
- ✅ `get_dashboard_stats.py` - Stats retrieval logging
- ✅ `dashboard_repository.py` - Database error logging

### User
- ✅ `change_password.py` - Security operation logging
- ✅ `update_user_profile.py` - Profile update with change tracking

### Clients
- ✅ `create_client.py` - Client creation with email masking
- ✅ `update_client.py` - Client update with change tracking
- ✅ `delete_client.py` - Client deletion logging

### Refinement
- ✅ `generate_stories_from_notes.py` - AI operation logging
- ✅ `approve_draft.py` - Draft approval workflow logging

## Tools and Scripts

### View Logs by Event Type

```bash
# Local development
grep "event_type.*story.created" logs/app.log

# Production (JSON format)
jq 'select(.event_type == "story.created")' logs/app.json
```

### Filter by User

```bash
# Text format
grep "user:550e8400-e29b-41d4-a716-446655440000" logs/app.log

# JSON format
jq 'select(.user_id == "550e8400-e29b-41d4-a716-446655440000")' logs/app.json
```

### Trace Request

```bash
# Text format
grep "request:abc123def456" logs/app.log

# JSON format
jq 'select(.request_id == "abc123def456")' logs/app.json
```

## References

- Implementation: `src/app/shared/logging/`
- Phase 1 Summary: `specs/phase-1-logging-implementation-summary.md`
- Configuration: `src/app/config/config_*.yml`
- Tests: `src/tests/unit/shared/logging/`

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-05-26 | 1.0 | Initial adoption - Phase 1 and Phase 2 complete |
