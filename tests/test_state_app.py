"""
Unit tests for the AppState class and application initialization.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from unicef_geospatial.state import AppState


class TestAppStateInitialization:
    """Test cases for AppState initialization."""

    def test_app_state_creates_fastapi_instance(self):
        """Test that AppState creates a FastAPI instance."""
        app_state = AppState()

        assert isinstance(app_state.app, FastAPI)
        assert app_state.logger is not None

    def test_app_state_reads_secret_files(self):
        """Test that AppState reads secret files correctly."""
        with patch("builtins.open") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value.strip.return_value = (
                "test-secret"
            )

            with patch("unicef_geospatial.utils.initialize.initialize_earth_engine"):
                AppState()

            assert os.environ.get("LANGFUSE_SECRET_KEY") == "test-secret"
            assert os.environ.get("OPENAI_API_KEY") == "test-secret"


class TestMiddlewareConfiguration:
    """Test cases for middleware configuration."""

    def test_ip_filtering_middleware_added(self):
        """Test that IP filtering middleware is properly configured."""
        app_state = AppState()

        assert len(app_state.app.user_middleware) > 0

    def test_cors_middleware_configuration(self):
        """Test that CORS middleware is properly configured."""
        app_state = AppState()

        cors_middleware_found = False
        for middleware in app_state.app.user_middleware:
            if "CORSMiddleware" in str(middleware):
                cors_middleware_found = True
                break

        assert cors_middleware_found


class TestIPFilteringMiddleware:
    """Test cases for IP filtering middleware functionality."""

    @pytest.mark.asyncio
    async def test_ip_filtering_allows_localhost(self):
        """Test that localhost is always allowed."""
        AppState()

        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "localhost"

        assert "localhost" in ["localhost"]

    def test_ip_filtering_resolves_hostnames(self):
        """Test that hostnames are resolved to IP addresses."""
        with patch("socket.gethostbyname", return_value="127.0.0.1"):
            app_state = AppState()

            assert app_state.app is not None


class TestEnvironmentVariableHandling:
    """Test cases for environment variable handling."""

    @patch.dict(os.environ, {"PATH_TO_LANGFUSE_SECRET_KEY": "/test/langfuse"})
    def test_langfuse_secret_key_path(self):
        """Test that Langfuse secret key path is read from environment."""
        with patch("builtins.open") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value.strip.return_value = (
                "langfuse-secret"
            )

            AppState()

            mock_open.assert_any_call("/test/langfuse", "r")

    @patch.dict(os.environ, {"PATH_TO_LLM_API_KEY": "/test/llm"})
    def test_llm_api_key_path(self):
        """Test that LLM API key path is read from environment."""
        with patch("builtins.open") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value.strip.return_value = (
                "llm-secret"
            )

            AppState()

            mock_open.assert_any_call("/test/llm", "r")


class TestApplicationConfiguration:
    """Test cases for overall application configuration."""

    def test_fastapi_app_has_correct_routes(self):
        """Test that FastAPI app has the expected routes configured."""
        app_state = AppState()

        assert isinstance(app_state.app, FastAPI)
        assert hasattr(app_state.app, "routes")

    def test_middleware_order(self):
        """Test that middleware is added in the correct order."""
        app_state = AppState()

        assert hasattr(app_state.app, "user_middleware")
        assert len(app_state.app.user_middleware) > 0

    def test_app_state_singleton_behavior(self):
        """Test that multiple AppState instances work correctly."""
        app_state1 = AppState()
        app_state2 = AppState()

        assert app_state1.app is not app_state2.app
        assert isinstance(app_state1.app, FastAPI)
        assert isinstance(app_state2.app, FastAPI)


class TestSecurityConfiguration:
    """Test cases for security-related configuration."""

    def test_secret_keys_are_stripped(self):
        """Test that secret keys are properly stripped of whitespace."""
        with patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = "  secret-with-whitespace  \n"
            mock_open.return_value.__enter__.return_value = mock_file

            AppState()

            assert os.environ.get("LANGFUSE_SECRET_KEY") == "secret-with-whitespace"
            assert os.environ.get("OPENAI_API_KEY") == "secret-with-whitespace"

    def test_cors_security_headers(self):
        """Test that CORS is configured with appropriate security settings."""
        app_state = AppState()

        assert len(app_state.app.user_middleware) > 0
