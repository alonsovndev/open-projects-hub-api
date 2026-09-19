"""Shared fixtures for presentation-layer API tests."""

import pytest
from fastapi.testclient import TestClient

from src.app.app import fastapi_app


@pytest.fixture
def client():
    """Create a test client with the FastAPI lifespan properly scoped.

    Must use the context-manager form: a bare `TestClient(fastapi_app)`
    never runs `lifespan` (which calls get_engine()/close_engine()), and
    Starlette spins up a new event loop/portal per bare request. The DB
    engine singleton then ends up holding connections bound to loops that
    no longer exist by the time later tests run, and garbage-collecting
    them raises `Connection._cancel` unraisable-exception warnings —
    non-deterministic failures under this project's `filterwarnings =
    ["error", ...]`. The `with` block binds startup/shutdown and every
    request to the same loop, and close_engine() resets the singleton on
    exit, so each test gets a cleanly-scoped engine.
    """
    with TestClient(fastapi_app) as test_client:
        yield test_client
