"""Document retrieval router."""
from uuid import UUID

from fastapi import APIRouter, HTTPException

from ..db import get_db_session
from ..schemas import DocumentResponse, ChunkResponse

router = APIRouter(prefix="/docs", tags=["documents"])


@router.get("/", response_model=list[DocumentResponse])
async def list_documents():
    """List all documents."""
    with get_db_session() as cursor:
        cursor.execute("SELECT id, title, mime_type, summary, created_at FROM documents ORDER BY created_at DESC")
        results = cursor.fetchall()
        return [DocumentResponse(**dict(row)) for row in results]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: UUID):
    """Get a document by ID."""
    with get_db_session() as cursor:
        cursor.execute(
            "SELECT id, title, mime_type, summary, created_at FROM documents WHERE id = %(doc_id)s",
            {"doc_id": str(doc_id)},
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentResponse(**dict(result))


@router.get("/{doc_id}/chunks", response_model=list[ChunkResponse])
async def get_document_chunks(doc_id: UUID):
    """Get chunks for a document."""
    with get_db_session() as cursor:
        cursor.execute(
            """
                SELECT id, document_id, chunk_index, content
                FROM doc_chunks
                WHERE document_id = %(doc_id)s
                ORDER BY chunk_index
                """,
            {"doc_id": str(doc_id)},
        )
        results = cursor.fetchall()
        return [ChunkResponse(**dict(row)) for row in results]


@router.delete("/{doc_id}")
async def delete_document(doc_id: UUID):
    """Delete a document and its chunks."""
    with get_db_session() as cursor:
        cursor.execute("DELETE FROM documents WHERE id = %(doc_id)s", {"doc_id": str(doc_id)})

    return {"message": "Document deleted"}


