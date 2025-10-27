"""Tests for document upload."""
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_upload_document():
    """Test document upload."""
    # Create a test PDF file
    test_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\ntrailer\n<< /Root 1 0 R >>\nstartxref\n9\n%%EOF"

    response = client.post(
        "/upload/",
        files={"file": ("test.pdf", test_content, "application/pdf")}
    )

    assert response.status_code == 200
    assert "document_id" in response.json()
    assert "summary" in response.json()
    assert "chunk_count" in response.json()
    assert "storage_path" in response.json()


def test_upload_invalid_file():
    """Test upload with invalid file."""
    response = client.post(
        "/upload/",
        files={"file": ("test.txt", b"invalid content", "text/plain")}
    )

    # Should handle gracefully or return 400
    assert response.status_code in [200, 400]


def test_list_documents():
    """Test listing documents."""
    response = client.get("/docs/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


