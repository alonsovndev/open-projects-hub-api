from collections.abc import Callable
from typing import cast

import backoff

from src.app.shared.logging import get_logger


log = get_logger(__name__)

# Transient exceptions worth retrying (network, timeouts, temporary failures)
RETRIABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    ConnectionRefusedError,
    ConnectionResetError,
    OSError,  # covers BrokenPipeError, socket errors
)


def retry_on_exception(max_tries: int = 3) -> Callable:
    """
    Reusable decorator for retrying a function with exponential backoff on transient exceptions.

    Only retries on network/timeout errors — not on logic errors like FileNotFoundError
    or TypeError. Use this for I/O-bound operations that may fail temporarily
    (external API calls, database connection acquisition).

    Args:
        max_tries: Maximum number of attempts before giving up (default 3).

    Returns:
        A decorator function wrapping the retry logic.
    """
    return cast(
        "Callable[..., object]",
        backoff.on_exception(
            backoff.expo,
            RETRIABLE_EXCEPTIONS,
            max_tries=max_tries,
            on_backoff=lambda details: log.warning(f"Retrying due to: {details['exception']}"),
            on_giveup=lambda details: log.error(f"Giving up after {details['tries']} attempts."),
        ),
    )
