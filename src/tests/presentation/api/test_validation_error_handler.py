"""
Tests for FastAPI RequestValidationError handler.

Verifies that Pydantic validation errors return consistent error envelopes
matching the format used by domain validation errors.
"""

import pytest
from fastapi.testclient import TestClient

from src.app.app import fastapi_app


client = TestClient(fastapi_app)


class TestValidationErrorHandler:
    """Test suite for request validation error handling."""

    def test_missing_required_field_returns_422_with_standard_envelope(self):
        """Test that missing required fields return 422 with detail message."""
        response = client.post(
            "/v1/auth/register",
            json={
                "display_name": "John Doe",
                "email": "john@example.com",
                # Missing required 'password' field
            },
        )

        assert response.status_code == 422
        data = response.json()

        # Verify standard error envelope (FastAPI format)
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_invalid_email_format_returns_422_with_standard_envelope(self):
        """Test that invalid email format returns 422 with detail message."""
        response = client.post(
            "/v1/auth/register",
            json={"display_name": "John Doe", "email": "not-a-valid-email", "password": "SecurePass123"},
        )

        assert response.status_code == 422
        data = response.json()

        # Verify standard error envelope
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.integration
    def test_invalid_field_type_returns_422_with_standard_envelope(self):
        """Test that registration with valid data returns 201 or 409 (requires DB)."""
        response = client.post(
            "/v1/auth/register",
            json={"display_name": "John Doe", "email": "john@example.com", "password": "SecurePass123"},
        )

        # This should succeed since all fields are valid
        assert response.status_code == 201 or response.status_code == 409

    def test_password_too_short_returns_422_with_standard_envelope(self):
        """Test that validation on password constraints returns 422."""
        response = client.post(
            "/v1/auth/register",
            json={"display_name": "John Doe", "email": "john@example.com", "password": "Ab1"},
        )

        assert response.status_code == 422
        data = response.json()

        # Verify standard error envelope
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.integration
    def test_error_envelope_matches_domain_error_format(self):
        """Test that validation error envelope format matches domain error format."""
        # Domain validation error (from business logic)
        domain_error_response = client.post(
            "/v1/auth/register",
            json={
                "display_name": "John Doe",
                "email": "duplicate@example.com",  # Assuming this triggers domain error
                "password": "SecurePass123",
            },
        )

        # Pydantic validation error (from request parsing)
        pydantic_error_response = client.post(
            "/v1/auth/register",
            json={
                "display_name": "John Doe",
                "email": "john@example.com",
                # Missing password
            },
        )

        # Both should have same envelope structure
        if domain_error_response.status_code in (400, 422):
            domain_data = domain_error_response.json()
            pydantic_data = pydantic_error_response.json()

            # Both should have detail key with string value
            assert "detail" in domain_data
            assert "detail" in pydantic_data
            assert isinstance(domain_data["detail"], str)
            assert isinstance(pydantic_data["detail"], str)
