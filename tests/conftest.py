"""
Test configuration and fixtures for unicef-geospatial API tests.
"""

import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add the unicef_geospatial directory to Python path for imports
project_root = Path(__file__).parent.parent
unicef_geospatial_path = project_root / "unicef_geospatial"
if str(unicef_geospatial_path) not in sys.path:
    sys.path.insert(0, str(unicef_geospatial_path))


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI application."""
    from unicef_geospatial.app import app

    return app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Get authentication headers for testing protected endpoints."""
    # Login to get a token
    login_data = {"username": "dev", "password": "dev"}
    response = client.post("/token", data=login_data)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    else:
        # Return a mock header if authentication fails in tests
        return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_chat_message() -> dict:
    """Sample chat message for testing chat endpoints."""
    return {
        "chat_messages": [
            {
                "content": "What is the weather like today?",
                "role": "user",
                "trace_id": "test-trace-id",
            }
        ],
        "session_id": "test-session-id",
    }
