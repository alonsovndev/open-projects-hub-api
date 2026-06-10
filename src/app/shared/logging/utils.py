"""
Logging utility functions for safe and structured logging.

Provides helpers for:
- Sensitive data redaction (passwords, tokens, PII)
- Structured logging with event types
- Consistent logging patterns across features

NOTE: log_business_event and log_error_event are deprecated.
Use BusinessLogger and ApplicationLogger instead.
"""

import re
import warnings
from typing import Any


# Sensitive field patterns to redact
SENSITIVE_FIELDS = {
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "authorization",
    "auth",
    "credential",
    "credentials",
}

# Email pattern for partial masking
EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")


def redact_sensitive_fields(data: dict[str, Any]) -> dict[str, Any]:
    """
    Redact sensitive fields from a dictionary for safe logging.

    Replaces values of sensitive fields (password, token, etc.) with '***REDACTED***'.
    This is a shallow redaction - only checks top-level keys.

    Args:
        data: Dictionary that may contain sensitive fields

    Returns:
        New dictionary with sensitive values redacted

    Example:
        >>> redact_sensitive_fields({"email": "user@example.com", "password": "secret123"})
        {"email": "user@example.com", "password": "***REDACTED***"}
    """
    redacted = data.copy()

    for key in redacted:
        if key.lower() in SENSITIVE_FIELDS:
            redacted[key] = "***REDACTED***"

    return redacted


def mask_email(email: str, show_chars: int = 2) -> str:
    """
    Partially mask an email address for logging.

    Shows first N characters of local part and full domain.

    Args:
        email: Email address to mask
        show_chars: Number of characters to show from local part (default: 2)

    Returns:
        Masked email string

    Example:
        >>> mask_email("john.doe@example.com")
        "jo***@example.com"
        >>> mask_email("a@example.com")
        "a***@example.com"
    """
    match = EMAIL_PATTERN.match(email)
    if not match:
        return "***INVALID_EMAIL***"

    local_part = match.group(1)
    domain = match.group(2)

    masked_local = local_part[0] + "***" if len(local_part) <= show_chars else local_part[:show_chars] + "***"

    return f"{masked_local}@{domain}"


def log_business_event(
    logger,
    event_type: str,
    message: str,
    entity_id: str | None = None,
    user_id: str | None = None,
    additional_data: dict[str, Any] | None = None,
    level: str = "info",
) -> None:
    """
    DEPRECATED: Use BusinessLogger instead.

    Log a business event with structured fields.

    This function is deprecated and will be removed in a future version.
    Use BusinessLogger for better type safety and readability.

    Example replacement:
        log = BusinessLogger(get_logger(__name__), user_id="user-123")
        log.event("project.created", entity_id="proj-456",
                  project_name="My Project")
    """
    warnings.warn(
        "log_business_event is deprecated, use BusinessLogger instead",
        DeprecationWarning,
        stacklevel=2,
    )
    extra_data = {
        "event_type": event_type,
    }

    if entity_id:
        extra_data["entity_id"] = entity_id

    if user_id:
        extra_data["user_id"] = user_id

    if additional_data:
        # Redact sensitive fields from additional data
        safe_data = redact_sensitive_fields(additional_data)
        extra_data.update(safe_data)

    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra=extra_data)


def log_error_event(
    logger,
    error_type: str,
    message: str,
    error: Exception | None = None,
    entity_id: str | None = None,
    user_id: str | None = None,
    additional_data: dict[str, Any] | None = None,
) -> None:
    """
    DEPRECATED: Use BusinessLogger or ApplicationLogger instead.

    Log an error event with exception details.

    This function is deprecated and will be removed in a future version.
    Use BusinessLogger.failure() or ApplicationLogger.error() instead.

    Example replacement:
        log = BusinessLogger(get_logger(__name__), user_id="user-123")
        log.failure("project.create.failed", error=e,
                    project_name="My Project")
    """
    warnings.warn(
        "log_error_event is deprecated, use BusinessLogger or ApplicationLogger instead",
        DeprecationWarning,
        stacklevel=2,
    )
    extra_data = {
        "error_type": error_type,
    }

    if entity_id:
        extra_data["entity_id"] = entity_id

    if user_id:
        extra_data["user_id"] = user_id

    if additional_data:
        safe_data = redact_sensitive_fields(additional_data)
        extra_data.update(safe_data)

    if error:
        extra_data["error_class"] = type(error).__name__
        extra_data["error_message"] = str(error)
        # Use logger.exception() to automatically include traceback
        logger.exception(message, extra=extra_data)
    else:
        logger.error(message, extra=extra_data)
