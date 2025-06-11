"""
Test health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get(f"{settings.api_prefix}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "version" in response.json()


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()
