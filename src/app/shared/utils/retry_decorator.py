import logging

import backoff

log = logging.getLogger(__name__)


def retry_on_exception(max_tries=3):
    """
    Reusable decorator for retrying a function with backoff on exceptions.

    Args:
        max_tries (int): Maximum number of attempts before giving up.

    Returns:
        callable: A decorator function wrapping the retry logic.
    """
    return backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=max_tries,
        on_backoff=lambda details: log.warning(f"Retrying due to: {details['exception']}"),
        on_giveup=lambda details: log.error(f"Giving up after {details['tries']} attempts."),
    )
