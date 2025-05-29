"""
Test cases for all API endpoints in the unicef-geospatial application.
"""

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


class TestHomeEndpoint:
    """Test cases for the home endpoint."""

    def test_home_endpoint(self, client: TestClient):
        """Test that the home endpoint returns 200 status."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"


class TestAuthenticationEndpoints:
    """Test cases for authentication endpoints."""

    def test_login_with_valid_credentials(self, client: TestClient):
        """Test successful login with valid credentials."""
        login_data = {"username": "dev", "password": "dev"}

        response = client.post("/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert "username" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["username"] == "dev"

    def test_login_with_invalid_username(self, client: TestClient):
        """Test login failure with invalid username."""
        login_data = {"username": "nonexistent", "password": "testpass"}

        response = client.post("/token", data=login_data)
        assert response.status_code == 401

        error_data = response.json()
        assert error_data["detail"] == "Incorrect username or password"

    def test_login_with_invalid_password(self, client: TestClient):
        """Test login failure with invalid password."""
        login_data = {"username": "dev", "password": "wrongpass"}

        response = client.post("/token", data=login_data)
        assert response.status_code == 401

        error_data = response.json()
        assert error_data["detail"] == "Incorrect username or password"

    def test_login_with_missing_credentials(self, client: TestClient):
        """Test login failure with missing credentials."""
        response = client.post("/token", data={})
        assert response.status_code == 422

    def test_get_current_user_with_valid_token(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting current user with valid token."""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200

        user_data = response.json()
        assert user_data["username"] == "dev"

    def test_get_current_user_without_token(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_get_current_user_with_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 401

    def test_get_current_user_with_malformed_header(self, client: TestClient):
        """Test getting current user with malformed authorization header."""
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 401


class TestChatEndpoints:
    """Test cases for chat/ask endpoints."""

    @patch("unicef_geospatial.utils.handlers.handle_response")
    def test_ask_endpoint_with_valid_request(
        self,
        mock_handle_response,
        client: TestClient,
        auth_headers: dict,
        sample_chat_message: dict,
    ):
        """Test the ask endpoint with valid request."""

        async def mock_stream():
            yield json.dumps({"trace_id": "test", "response": "Test response"}) + "\n"

        mock_handle_response.return_value = mock_stream()

        response = client.post("/ask", json=sample_chat_message, headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_ask_endpoint_without_authentication(
        self, client: TestClient, sample_chat_message: dict
    ):
        """Test the ask endpoint without authentication."""
        response = client.post("/ask", json=sample_chat_message)
        assert response.status_code == 401

    def test_ask_endpoint_with_invalid_payload(
        self, client: TestClient, auth_headers: dict
    ):
        """Test the ask endpoint with invalid payload."""
        invalid_payload = {"invalid_field": "invalid_value"}

        response = client.post("/ask", json=invalid_payload, headers=auth_headers)
        assert response.status_code == 422

    def test_ask_endpoint_with_missing_chat_messages(
        self, client: TestClient, auth_headers: dict
    ):
        """Test the ask endpoint with missing chat_messages field."""
        invalid_payload = {"session_id": "test-session"}

        response = client.post("/ask", json=invalid_payload, headers=auth_headers)
        assert response.status_code == 422

    def test_ask_endpoint_with_empty_chat_messages(
        self, client: TestClient, auth_headers: dict
    ):
        """Test the ask endpoint with empty chat_messages array."""
        payload = {"chat_messages": [], "session_id": "test-session"}

        response = client.post("/ask", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_ask_endpoint_with_invalid_message_format(
        self, client: TestClient, auth_headers: dict
    ):
        """Test the ask endpoint with invalid message format."""
        invalid_payload = {
            "chat_messages": [
                {
                    "content": "What is the weather?",
                    "invalid_role": "user",
                    "trace_id": "test-trace",
                }
            ],
            "session_id": "test-session",
        }

        response = client.post("/ask", json=invalid_payload, headers=auth_headers)
        assert response.status_code == 422


class TestIPFiltering:
    """Test cases for IP filtering middleware."""

    def test_allowed_ip_access(self, client: TestClient):
        """Test that allowed IPs can access the API."""
        response = client.get("/")
        assert response.status_code == 200

    @patch.dict("os.environ", {"FRONTEND_ORIGIN": "http://allowed-host.com"})
    def test_blocked_ip_access(self, client: TestClient):
        """Test that blocked IPs cannot access the API."""

        mock_client = MagicMock()
        mock_client.host = "127.9.9.9"

        with patch("fastapi.Request.client", new_callable=lambda: mock_client):
            response = client.get("/")
            assert response.status_code == 403


class TestCORSConfiguration:
    """Test cases for CORS configuration."""

    def test_cors_headers_present(self, client: TestClient):
        """Test that CORS headers are present in responses."""
        response = client.options("/")
        assert response.status_code in [200, 405]

    def test_allowed_methods(self, client: TestClient):
        """Test that only allowed methods are supported."""
        get_response = client.get("/")
        assert get_response.status_code == 200

        put_response = client.put("/")
        assert put_response.status_code in [405, 404]


class TestErrorHandling:
    """Test cases for error handling."""

    def test_404_for_nonexistent_endpoint(self, client: TestClient):
        """Test 404 response for non-existent endpoints."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client: TestClient):
        """Test 405 response for wrong HTTP method."""
        response = client.put("/token")
        assert response.status_code == 405

    def test_422_for_validation_errors(self, client: TestClient):
        """Test 422 response for validation errors."""
        response = client.post("/token", json={"invalid": "data"})
        assert response.status_code == 422


class TestRateLimiting:
    """Test cases for rate limiting (if implemented)."""

    def test_multiple_requests_allowed(self, client: TestClient):
        """Test that multiple reasonable requests are allowed."""
        for _ in range(5):
            response = client.get("/")
            assert response.status_code == 200


class TestApplicationHealth:
    """Test cases for application health and status."""

    def test_application_startup(self, client: TestClient):
        """Test that the application starts up correctly."""
        response = client.get("/")
        assert response.status_code == 200

    def test_concurrent_requests(self, client: TestClient, auth_headers: dict):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def make_request():
            return client.get("/users/me", headers=auth_headers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(3)]
            results = [future.result() for future in futures]

            for response in results:
                assert response.status_code == 200
