"""Local filesystem storage helpers."""
import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from fastapi.responses import FileResponse

from .config import settings


def ensure_upload_dir() -> None:
    """Create upload directory if it doesn't exist."""
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)


def save_upload(file: UploadFile) -> str:
    """
    Save uploaded file to local filesystem.

    Args:
        file: Uploaded file object

    Returns:
        Absolute path to saved file
    """
    ensure_upload_dir()

    # Generate unique filename
    file_id = uuid4()
    safe_name = file.filename.replace(" ", "_").replace("/", "_")
    filename = f"{file_id}_{safe_name}"
    file_path = Path(settings.upload_dir) / filename

    # Save file
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return str(file_path.absolute())


def get_file_path(doc_id: str) -> str | None:
    """
    Get file path for a document.

    Args:
        doc_id: Document ID (not used, but kept for API compatibility)

    Returns:
        File path or None
    """
    # Note: This is a simplified implementation
    # In a real system, you'd query the database for storage_path
    return None


def get_file(doc_id: str):
    """
    Get file object for a document.

    Args:
        doc_id: Document ID

    Returns:
        FileResponse or None
    """
    path = get_file_path(doc_id)
    if path and os.path.exists(path):
        return FileResponse(path)
    return None


def delete_file(file_path: str) -> None:
    """
    Delete a file from storage.

    Args:
        file_path: Path to file to delete
    """
    if os.path.exists(file_path):
        os.remove(file_path)


