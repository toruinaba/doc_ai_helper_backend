"""
Configuration for pytest.
"""

import os
import sys

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "test-secret-key"
