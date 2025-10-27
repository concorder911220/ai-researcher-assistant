"""Pytest configuration and fixtures."""
import pytest


@pytest.fixture
def app():
    """Provide app instance."""
    from apps.api.main import app
    return app


@pytest.fixture
def client(app):
    """Provide test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


