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

# Import main app
from doc_ai_helper_backend.main import app


# Create test client fixture
@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


# Import mock services for API testing
from tests.api import mock_services
