"""Logging utilities: sensitive data redaction and PII masking."""

import re
from typing import Any


SENSITIVE_FIELDS = frozenset(
    {
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
)

EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")


def redact_sensitive_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy of *data* with sensitive field values replaced by '***REDACTED***'.

    Recognised sensitive keys (case-insensitive): password, token, secret, api_key,
    apikey, access_token, refresh_token, authorization, auth, credential, credentials.
    """
    redacted = data.copy()
    for key in redacted:
        if key.lower() in SENSITIVE_FIELDS:
            redacted[key] = "***REDACTED***"
    return redacted


def mask_email(email: str, show_chars: int = 2) -> str:
    """Partially mask an email address for safe logging.

    Shows the first *show_chars* characters of the local part followed by
    ``***`` and the full domain.  Returns ``"***INVALID_EMAIL***"`` when the
    input does not look like an email.
    """
    match = EMAIL_PATTERN.match(email)
    if not match:
        return "***INVALID_EMAIL***"

    local_part = match.group(1)
    domain = match.group(2)
    masked_local = local_part[0] + "***" if len(local_part) <= show_chars else local_part[:show_chars] + "***"
    return f"{masked_local}@{domain}"
