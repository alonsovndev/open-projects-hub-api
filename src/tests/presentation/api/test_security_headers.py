"""
Tests for security headers middleware.
"""


class TestSecurityHeaders:
    """Test security headers are added to all responses."""

    def test_security_headers_present_on_root_endpoint(self, client):
        """Verify security headers are present on root endpoint."""
        response = client.get("/")

        # Verify all security headers are present
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

        assert "Content-Security-Policy" in response.headers
        assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"

        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "no-referrer"

        assert "Permissions-Policy" in response.headers
        assert response.headers["Permissions-Policy"] == "geolocation=(), microphone=(), camera=()"

    def test_security_headers_present_on_health_endpoint(self, client):
        """Verify security headers are present on health check endpoint."""
        response = client.get("/health")

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"

    def test_api_version_header_present(self, client):
        """Verify API version header is present."""
        response = client.get("/")

        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "v1"

    def test_hsts_header_not_present_in_non_production(self, client):
        """Verify HSTS header is not present in non-production environments."""
        response = client.get("/")

        # HSTS should only be present in production
        # In test/local/dev, it should not be set
        assert "Strict-Transport-Security" not in response.headers

    def test_csp_allows_swagger_ui_on_docs_endpoint(self, client):
        """Verify Content-Security-Policy allows Swagger UI resources on /docs."""
        response = client.get("/docs")

        csp = response.headers["Content-Security-Policy"]

        # Should allow Swagger UI resources
        assert "https://cdn.jsdelivr.net" in csp
        assert "'unsafe-inline'" in csp
        assert "'unsafe-eval'" in csp

    def test_csp_strict_on_api_endpoints(self, client):
        """Verify Content-Security-Policy is strict on API endpoints."""
        response = client.get("/health")

        # API endpoints should have strict CSP
        assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"
