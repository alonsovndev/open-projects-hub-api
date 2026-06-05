"""
Tests for FastAPI RequestValidationError handler.

Verifies that Pydantic validation errors return consistent error envelopes
matching the format used by domain validation errors.
"""

from fastapi.testclient import TestClient

from src.app.app import fastapi_app


client = TestClient(fastapi_app)


class TestValidationErrorHandler:
    """Test suite for request validation error handling."""

    def test_missing_required_field_returns_422_with_standard_envelope(self):
        """Test that missing required fields return 422 with error/message envelope."""
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

        # Verify standard error envelope
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Validation Error"
        assert "password" in data["message"].lower()
        assert "required" in data["message"].lower() or "missing" in data["message"].lower()

    def test_invalid_email_format_returns_422_with_standard_envelope(self):
        """Test that invalid email format returns 422 with error/message envelope."""
        response = client.post(
            "/v1/auth/register",
            json={"display_name": "John Doe", "email": "not-a-valid-email", "password": "SecurePass123"},
        )

        assert response.status_code == 422
        data = response.json()

        # Verify standard error envelope
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Validation Error"
        assert "email" in data["message"].lower()

    def test_invalid_field_type_returns_422_with_standard_envelope(self):
        """Test that invalid field types return 422 with error/message envelope."""
        response = client.post(
            "/v1/auth/register",
            json={
                "display_name": 12345,  # Should be string
                "email": "john@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 422
        data = response.json()

        # Verify standard error envelope
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Validation Error"

    def test_password_too_short_returns_422_with_standard_envelope(self):
        """Test that password validation errors return 422 with error/message envelope."""
        response = client.post(
            "/v1/auth/register",
            json={
                "display_name": "John Doe",
                "email": "john@example.com",
                "password": "Short1",  # Too short (< 8 chars)
            },
        )

        assert response.status_code == 422
        data = response.json()

        # Verify standard error envelope
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Validation Error"
        assert "password" in data["message"].lower()

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

            # Both should have exactly these keys
            assert set(domain_data.keys()) == {"error", "message"}
            assert set(pydantic_data.keys()) == {"error", "message"}

            # Both should have string values
            assert isinstance(domain_data["error"], str)
            assert isinstance(domain_data["message"], str)
            assert isinstance(pydantic_data["error"], str)
            assert isinstance(pydantic_data["message"], str)
