"""Public API for the logging module.

Usage:
    from src.app.shared.logging import get_logger, set_user_id, mask_email

    log = get_logger(__name__)
    log.info("Project created", extra={"project_id": pid})
"""

from src.app.shared.logging.logging import clear_context, get_logger, set_request_id, set_user_id, setup_logging
from src.app.shared.logging.utils import mask_email, redact_sensitive_fields


__all__ = [
    "clear_context",
    "get_logger",
    "mask_email",
    "redact_sensitive_fields",
    "set_request_id",
    "set_user_id",
    "setup_logging",
]
