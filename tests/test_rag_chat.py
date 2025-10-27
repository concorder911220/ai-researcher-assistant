"""Tests for RAG chat functionality."""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from apps.api.main import app

client = TestClient(app)


def test_create_chat():
    """Test chat creation."""
    response = client.post(
        "/chat/",
        json={
            "system_prompt": "You are a helpful assistant.",
            "personality": "friendly"
        }
    )

    assert response.status_code == 200
    assert "id" in response.json()
    assert "system_prompt" in response.json()


def test_send_message():
    """Test sending a message."""
    # Create a chat first
    chat_response = client.post(
        "/chat/",
        json={
            "system_prompt": "You are a helpful assistant.",
            "personality": None
        }
    )
    chat_id = chat_response.json()["id"]

    # Send a message
    response = client.post(
        "/chat/message",
        json={
            "message": "Hello!",
            "chat_id": chat_id,
            "stream": False
        }
    )

    assert response.status_code == 200
    assert "content" in response.json()
    assert "sources" in response.json()
    assert "citations" in response.json()


def test_search_documents():
    """Test document search."""
    response = client.post(
        "/search/",
        json={
            "query": "test query",
            "limit": 5
        }
    )

    assert response.status_code == 200
    assert "query" in response.json()
    assert "results" in response.json()


