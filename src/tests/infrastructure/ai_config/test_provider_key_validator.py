"""Tests for ProviderKeyValidator's HTTP-to-reason mapping (FR-010-10, FR-010-12)."""

import logging

import httpx
import pytest

from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.domain.value_objects.provider_failure_reason import ProviderFailureReason
from src.app.features.ai_config.infrastructure.ai.provider_key_validator import ProviderKeyValidator


RAW_KEY = "sk-proj-abcdefghijklmnopqrstuv1234"


def stub_transport(monkeypatch, *, status: int = 200, headers: dict[str, str] | None = None, raises=None):
    """Replace httpx's network layer so no test ever reaches a real provider."""
    captured: dict[str, object] = {}

    async def fake_get(self, url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers", {})
        if raises is not None:
            raise raises
        return httpx.Response(status_code=status, headers=headers or {}, json={"data": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    return captured


class TestSuccessfulValidation:
    @pytest.mark.asyncio
    async def test_a_200_means_the_key_works(self, monkeypatch):
        stub_transport(monkeypatch, status=200)
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert result.valid is True
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_gemini_receives_its_key_in_the_goog_header(self, monkeypatch):
        captured = stub_transport(monkeypatch, status=200)
        await ProviderKeyValidator().validate(RAW_KEY, AIProvider.GEMINI)
        assert captured["headers"]["x-goog-api-key"] == RAW_KEY

    @pytest.mark.asyncio
    async def test_openai_receives_its_key_as_a_bearer_token(self, monkeypatch):
        captured = stub_transport(monkeypatch, status=200)
        await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert captured["headers"]["Authorization"] == f"Bearer {RAW_KEY}"

    @pytest.mark.asyncio
    async def test_the_key_never_appears_in_the_request_url(self, monkeypatch):
        """httpx puts the URL into its exception messages, so the key must stay in headers."""
        captured = stub_transport(monkeypatch, status=200)
        await ProviderKeyValidator().validate(RAW_KEY, AIProvider.GEMINI)
        assert RAW_KEY not in str(captured["url"])


class TestFailureMapping:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (401, ProviderFailureReason.AUTH_FAILED),
            (403, ProviderFailureReason.AUTH_FAILED),
            (402, ProviderFailureReason.QUOTA_EXHAUSTED),
            (429, ProviderFailureReason.RATE_LIMITED),
            (500, ProviderFailureReason.NETWORK),
            (503, ProviderFailureReason.NETWORK),
        ],
    )
    @pytest.mark.asyncio
    async def test_maps_each_status_to_its_reason(self, monkeypatch, status, expected):
        stub_transport(monkeypatch, status=status)
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert result.valid is False
        assert result.reason is expected

    @pytest.mark.asyncio
    async def test_a_rate_limit_carries_the_providers_retry_after(self, monkeypatch):
        stub_transport(monkeypatch, status=429, headers={"retry-after": "42"})
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert result.retry_after == "42"

    @pytest.mark.asyncio
    async def test_a_timeout_is_reported_as_a_network_problem(self, monkeypatch):
        stub_transport(monkeypatch, raises=httpx.TimeoutException("too slow"))
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert result.reason is ProviderFailureReason.NETWORK

    @pytest.mark.asyncio
    async def test_a_transport_error_is_reported_as_a_network_problem(self, monkeypatch):
        stub_transport(monkeypatch, raises=httpx.ConnectError("no route"))
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert result.reason is ProviderFailureReason.NETWORK

    @pytest.mark.asyncio
    async def test_a_failure_never_logs_the_key(self, monkeypatch, caplog):
        """NFR-010-02: an httpx error string can embed the request, so only types are logged."""
        stub_transport(monkeypatch, raises=httpx.ConnectError(f"failed sending {RAW_KEY}"))

        with caplog.at_level(logging.DEBUG):
            await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)

        assert RAW_KEY not in caplog.text


class TestQuotaReading:
    """FR-010-12 is best-effort: only providers that report usage can trigger the warning."""

    @pytest.mark.asyncio
    async def test_reads_consumption_from_rate_limit_headers(self, monkeypatch):
        stub_transport(
            monkeypatch,
            status=200,
            headers={"x-ratelimit-limit-requests": "100", "x-ratelimit-remaining-requests": "10"},
        )
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert result.quota_consumed_ratio == pytest.approx(0.9)
        assert result.quota_warning is True

    @pytest.mark.asyncio
    async def test_does_not_warn_well_below_the_threshold(self, monkeypatch):
        stub_transport(
            monkeypatch,
            status=200,
            headers={"x-ratelimit-limit-requests": "100", "x-ratelimit-remaining-requests": "90"},
        )
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert result.quota_warning is False

    @pytest.mark.asyncio
    async def test_reports_nothing_when_the_provider_sends_no_usage_headers(self, monkeypatch):
        stub_transport(monkeypatch, status=200)
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.GEMINI)
        assert result.quota_consumed_ratio is None
        assert result.quota_warning is False

    @pytest.mark.asyncio
    async def test_ignores_unparseable_headers(self, monkeypatch):
        stub_transport(
            monkeypatch,
            status=200,
            headers={"x-ratelimit-limit-requests": "lots", "x-ratelimit-remaining-requests": "some"},
        )
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert result.quota_consumed_ratio is None

    @pytest.mark.asyncio
    async def test_ignores_a_zero_limit(self, monkeypatch):
        stub_transport(
            monkeypatch,
            status=200,
            headers={"x-ratelimit-limit-requests": "0", "x-ratelimit-remaining-requests": "0"},
        )
        result = await ProviderKeyValidator().validate(RAW_KEY, AIProvider.OPENAI)
        assert result.quota_consumed_ratio is None
