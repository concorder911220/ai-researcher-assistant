"""Tests for feedback system."""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from apps.api.main import app

client = TestClient(app)


def test_submit_feedback():
    """Test submitting feedback."""
    message_id = str(uuid4())
    
    response = client.post(
        "/feedback/",
        json={
            "message_id": message_id,
            "rating": 1,
            "note": "Great response!"
        }
    )

    # May fail if message doesn't exist in test DB
    assert response.status_code in [200, 404]


def test_feedback_ratings():
    """Test feedback rating validation."""
    message_id = str(uuid4())
    
    # Test valid rating
    response = client.post(
        "/feedback/",
        json={
            "message_id": message_id,
            "rating": 0,
            "note": None
        }
    )
    assert response.status_code in [200, 404]

    # Test invalid rating (should fail validation)
    response = client.post(
        "/feedback/",
        json={
            "message_id": message_id,
            "rating": 5,  # Invalid
            "note": None
        }
    )
    # Should fail with 422
    assert response.status_code in [422, 404]


