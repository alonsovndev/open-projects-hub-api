from unittest.mock import MagicMock, patch

import pytest
import sentry_sdk
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sentry_sdk.transport import Transport

from src.app.shared.domain.exceptions.domain_exceptions import DomainError
from src.app.shared.infrastructure.observability.sentry import build_traces_sampler, init_sentry, scrub_event
from src.app.shared.logging.middleware import RequestContextMiddleware
from src.app.shared.presentation.exception_handlers import register_exception_handlers


def _config_with(dsn, traces_sample_rate=0.25) -> MagicMock:
    config = MagicMock()
    config.env = "prod"
    config.get_config.side_effect = lambda key, default=None: {
        "monitoring.sentry_dsn": dsn,
        "monitoring.sentry_traces_sample_rate": traces_sample_rate,
        "app.version": "1.0.0",
    }.get(key, default)
    return config


class _RecordingTransport(Transport):
    events: list[dict] = []

    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.type == "event":
                self.events.append(item.payload.json)


def test_scrub_event_masks_the_access_code_and_drops_the_query_string():
    event = {
        "request": {
            "url": "https://api.example.com/v1/viewer/PRJ-7K3M9XQ2?token=abc",
            "query_string": "token=abc",
            "headers": {"x-api-token": "secret"},
        },
        "transaction": "/v1/viewer/PRJ-7K3M9XQ2",
    }

    scrubbed = scrub_event(event, {})

    assert scrubbed["request"] == {"url": "https://api.example.com/v1/viewer/{access_code}"}
    assert scrubbed["transaction"] == "/v1/viewer/{access_code}"


def test_scrub_event_tolerates_events_without_request_data():
    assert scrub_event({"message": "startup"}, {}) == {"message": "startup"}


@pytest.mark.parametrize(
    ("sampling_context", "expected"),
    [
        ({"asgi_scope": {"path": "/health/live"}}, 0.0),
        ({"asgi_scope": {"path": "/health/ready"}}, 0.0),
        ({"asgi_scope": {"path": "/health"}}, 0.0),
        ({"asgi_scope": {"path": "/healthcheck-report"}}, 0.25),
        ({"asgi_scope": {"path": "/v1/projects"}}, 0.25),
        ({"asgi_scope": {"path": "/v1/projects"}, "parent_sampled": True}, 1.0),
        ({}, 0.25),
    ],
)
def test_traces_sampler_skips_health_checks_and_honours_the_parent(sampling_context, expected):
    assert build_traces_sampler(0.25)(sampling_context) == expected


@pytest.mark.parametrize("unset_dsn", [None, "", "N/A"])
def test_init_sentry_stays_off_without_a_configured_dsn(unset_dsn, monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")

    with patch("src.app.shared.infrastructure.observability.sentry.sentry_sdk.init") as init:
        assert init_sentry(_config_with(unset_dsn)) is False

    init.assert_not_called()


def test_init_sentry_uses_the_deployed_image_tag_as_release(monkeypatch):
    monkeypatch.setenv("SENTRY_RELEASE", "v0.2.0")

    with patch("src.app.shared.infrastructure.observability.sentry.sentry_sdk.init") as init:
        assert init_sentry(_config_with("https://key@o0.ingest.sentry.io/1")) is True

    options = init.call_args.kwargs
    assert options["release"] == "v0.2.0"
    assert options["environment"] == "prod"
    assert options["send_default_pii"] is False
    assert options["include_local_variables"] is False


def test_init_sentry_falls_back_to_the_app_version_without_a_release_tag(monkeypatch):
    monkeypatch.delenv("SENTRY_RELEASE", raising=False)

    with patch("src.app.shared.infrastructure.observability.sentry.sentry_sdk.init") as init:
        init_sentry(_config_with("https://key@o0.ingest.sentry.io/1"))

    assert init.call_args.kwargs["release"] == "1.0.0"


def _events_for(app: FastAPI, path: str) -> tuple[int, list[dict]]:
    _RecordingTransport.events = []
    sentry_sdk.init(
        dsn="https://key@o0.ingest.sentry.io/1",
        transport=_RecordingTransport,
        include_local_variables=False,
        before_send=scrub_event,
    )
    try:
        response = TestClient(app, raise_server_exceptions=False).get(path, headers={"X-Request-ID": "req-123"})
        sentry_sdk.flush()
    finally:
        sentry_sdk.init()
    return response.status_code, list(_RecordingTransport.events)


def test_an_unhandled_exception_reaches_sentry_once_and_scrubbed():
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    @app.get("/v1/viewer/{access_code}")
    def explode(access_code: str):
        raise RuntimeError("boom")

    status_code, events = _events_for(app, "/v1/viewer/PRJ-7K3M9XQ2?token=abc")

    assert status_code == 500
    assert len(events) == 1
    event = events[0]
    assert event["exception"]["values"][-1]["value"] == "boom"
    assert event["tags"]["request_id"] == "req-123"
    assert event["request"]["url"] == "http://testserver/v1/viewer/{access_code}"
    assert event["transaction"] == "/v1/viewer/{access_code}"
    assert "headers" not in event["request"]
    assert "query_string" not in event["request"]
    frames = event["exception"]["values"][-1]["stacktrace"]["frames"]
    assert all("vars" not in frame for frame in frames)


def test_a_handled_domain_error_does_not_reach_sentry():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/rule")
    def break_rule():
        raise DomainError("rule broken")

    status_code, events = _events_for(app, "/rule")

    assert status_code == 422
    assert events == []
