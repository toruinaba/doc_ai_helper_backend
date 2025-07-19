"""
Configuration for pytest.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "test-secret-key"

# Mock LLM provider setup is handled by individual test files
# Unit tests will explicitly override dependencies
# E2E tests will use real LLM providers from settings

# Import main app
from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.api.dependencies import get_llm_service
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService


def get_test_llm_service():
    """テスト用のモックLLMサービスを返す"""
    return MockLLMService(response_delay=0.0)


# Create test client fixture
@pytest.fixture
def client():
    """Create a test client."""
    # テスト用に依存関係をオーバーライド
    app.dependency_overrides[get_llm_service] = get_test_llm_service
    test_client = TestClient(app)
    yield test_client
    # テスト後にオーバーライドをクリア
    app.dependency_overrides.clear()
