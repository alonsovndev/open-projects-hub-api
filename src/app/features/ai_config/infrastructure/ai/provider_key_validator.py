"""Live verification of a provider API key, plus best-effort quota reading (FR-010-05/12)."""

from dataclasses import dataclass

import httpx

from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.domain.value_objects.provider_failure_reason import ProviderFailureReason
from src.app.shared.logging import get_logger


# Endpoints that merely list models: the cheapest call each provider offers that still
# requires a valid key, so validation costs the user's quota as little as possible.
_VALIDATION_ENDPOINTS: dict[AIProvider, str] = {
    AIProvider.GEMINI: "https://generativelanguage.googleapis.com/v1beta/models",
    AIProvider.OPENAI: "https://api.openai.com/v1/models",
    AIProvider.DEEPSEEK: "https://api.deepseek.com/v1/models",
}

# Consumption at or above this fraction triggers the low-quota banner (FR-010-12).
QUOTA_WARNING_THRESHOLD = 0.8

_VALIDATION_TIMEOUT_SECONDS = 15.0


@dataclass(frozen=True)
class KeyValidationResult:
    """Outcome of a single validation call."""

    valid: bool
    reason: ProviderFailureReason | None = None
    retry_after: str | None = None
    # Fraction of the provider quota consumed, when the provider reports it at all.
    # None means "not detectable", which FR-010-12 accepts as the normal case.
    quota_consumed_ratio: float | None = None

    @property
    def quota_warning(self) -> bool:
        """Whether the user should be warned that their provider quota is running low."""
        return self.quota_consumed_ratio is not None and self.quota_consumed_ratio >= QUOTA_WARNING_THRESHOLD


class ProviderKeyValidator:
    """
    Asks the provider whether a key works.

    Nothing here logs or returns the key: failures are reported as a
    `ProviderFailureReason`, and outbound errors surface by exception type only, because
    an httpx error string can carry request detail including headers.
    """

    def __init__(self, timeout_seconds: float = _VALIDATION_TIMEOUT_SECONDS):
        """
        Args:
            timeout_seconds: How long to wait for the provider before reporting NETWORK.
        """
        self._timeout = timeout_seconds
        self._log = get_logger(__name__)

    async def validate(self, api_key: str, provider: AIProvider) -> KeyValidationResult:
        """
        Check a key against its provider.

        Args:
            api_key: The raw provider key to test.
            provider: The provider to test it against.

        Returns:
            KeyValidationResult describing acceptance, or why the provider refused.
        """
        url = _VALIDATION_ENDPOINTS[provider]
        headers = self._auth_headers(api_key, provider)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=headers)
        except httpx.TimeoutException:
            self._log.warning(
                "Provider key validation timed out",
                extra={"event_type": "ai_config.key.validation_timeout", "provider": provider.value},
            )
            return KeyValidationResult(valid=False, reason=ProviderFailureReason.NETWORK)
        except Exception as e:
            # Type only: httpx exception messages can embed the outgoing request.
            self._log.warning(
                "Provider key validation could not reach the provider",
                extra={
                    "event_type": "ai_config.key.validation_unreachable",
                    "provider": provider.value,
                    "error_type": type(e).__name__,
                },
            )
            return KeyValidationResult(valid=False, reason=ProviderFailureReason.NETWORK)

        return self._interpret(response, provider)

    def _interpret(self, response: httpx.Response, provider: AIProvider) -> KeyValidationResult:
        if response.status_code == httpx.codes.OK:
            return KeyValidationResult(valid=True, quota_consumed_ratio=self._read_quota_ratio(response))

        self._log.info(
            "Provider refused a key during validation",
            extra={
                "event_type": "ai_config.key.validation_refused",
                "provider": provider.value,
                "status_code": response.status_code,
            },
        )

        if response.status_code in (httpx.codes.UNAUTHORIZED, httpx.codes.FORBIDDEN):
            return KeyValidationResult(valid=False, reason=ProviderFailureReason.AUTH_FAILED)

        if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
            return KeyValidationResult(
                valid=False,
                reason=ProviderFailureReason.RATE_LIMITED,
                retry_after=response.headers.get("retry-after"),
            )

        if response.status_code == httpx.codes.PAYMENT_REQUIRED:
            return KeyValidationResult(valid=False, reason=ProviderFailureReason.QUOTA_EXHAUSTED)

        return KeyValidationResult(valid=False, reason=ProviderFailureReason.NETWORK)

    def _read_quota_ratio(self, response: httpx.Response) -> float | None:
        """
        Derive quota consumption from rate-limit headers, where the provider sends them.

        OpenAI and DeepSeek expose `x-ratelimit-limit-requests` and
        `x-ratelimit-remaining-requests`; Gemini sends neither, so this returns None there.
        FR-010-12 explicitly treats the warning as best-effort for that reason.
        """
        limit = response.headers.get("x-ratelimit-limit-requests")
        remaining = response.headers.get("x-ratelimit-remaining-requests")

        if limit is None or remaining is None:
            return None

        try:
            limit_value = float(limit)
            remaining_value = float(remaining)
        except ValueError:
            return None

        if limit_value <= 0:
            return None

        return max(0.0, min(1.0, 1.0 - (remaining_value / limit_value)))

    def _auth_headers(self, api_key: str, provider: AIProvider) -> dict[str, str]:
        if provider is AIProvider.GEMINI:
            return {"x-goog-api-key": api_key}
        return {"Authorization": f"Bearer {api_key}"}
