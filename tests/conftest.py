"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    # Set test API key if not already set
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test-key-for-testing-only"
    
    yield
    
    # Cleanup if needed
    pass


@pytest.fixture
def temp_storage_file():
    """Create a temporary storage file for testing"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_file.close()
    yield temp_file.name
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)

