"""The request log must never contain a Client Review access code."""

import pytest

from src.app.shared.infrastructure.middleware.request_logging_middleware import loggable_path


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/v1/viewer/PRJ-7K3M9XQ2", "/v1/viewer/{access_code}"),
        ("/v1/viewer/anything-a-guesser-types", "/v1/viewer/{access_code}"),
        ("/v1/projects", "/v1/projects"),
        ("/health", "/health"),
    ],
)
def test_masks_the_access_code_and_leaves_other_paths_alone(path, expected):
    assert loggable_path(path) == expected
