"""Sentry error tracking setup (ADR-009)."""

import os
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import sentry_sdk
from sentry_sdk.types import Event, Hint

from src.app.config.app_config import AppConfig
from src.app.shared.infrastructure.middleware.request_logging_middleware import loggable_path


# pyaml_env substitutes the literal "N/A" for an !ENV var with no default that is unset.
_UNSET_DSN_VALUES = (None, "", "N/A")
_HEALTH_PATH = "/health"
_DEFAULT_TRACES_SAMPLE_RATE = 0.1


def scrub_event(event: Event, hint: Hint) -> Event:
    """Strip credentials from the request URL, the query string, headers and the transaction name.

    send_default_pii=False drops cookies and bodies and filters only well-known sensitive
    headers, while the URL is always sent and the Client Review route carries its access
    code in the path. Free-text exception and log messages are not scrubbed, so they must
    not interpolate the access code.
    """
    request = event.get("request")
    if request:
        request.pop("query_string", None)
        request.pop("headers", None)
        url = request.get("url")
        if isinstance(url, str):
            parts = urlsplit(url)
            request["url"] = urlunsplit((parts.scheme, parts.netloc, loggable_path(parts.path), "", ""))

    transaction = event.get("transaction")
    if transaction:
        event["transaction"] = loggable_path(transaction)

    return event


def build_traces_sampler(traces_sample_rate: float) -> Callable[[dict[str, Any]], float]:
    """Sample at the configured rate, except for health checks, which are polled every few seconds."""

    def traces_sampler(sampling_context: dict[str, Any]) -> float:
        path = sampling_context.get("asgi_scope", {}).get("path", "")
        if path == _HEALTH_PATH or path.startswith(f"{_HEALTH_PATH}/"):
            return 0.0
        parent_sampled = sampling_context.get("parent_sampled")
        if parent_sampled is not None:
            return float(parent_sampled)
        return traces_sample_rate

    return traces_sampler


def init_sentry(config: AppConfig) -> bool:
    """Initialise Sentry when the environment config carries a DSN; return whether it did.

    Without a configured DSN the SDK is never initialised, so a stray SENTRY_DSN in the
    process environment cannot switch on reporting in local, dev or test. The release comes
    from SENTRY_RELEASE (the deployed image tag) so each deploy is a distinct release.
    """
    dsn = config.get_config("monitoring.sentry_dsn")
    if dsn in _UNSET_DSN_VALUES:
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=config.env,
        release=os.environ.get("SENTRY_RELEASE") or config.get_config("app.version"),
        send_default_pii=False,
        include_local_variables=False,
        traces_sampler=build_traces_sampler(
            config.get_config("monitoring.sentry_traces_sample_rate", _DEFAULT_TRACES_SAMPLE_RATE)
        ),
        before_send=scrub_event,
        before_send_transaction=scrub_event,
    )
    return True
