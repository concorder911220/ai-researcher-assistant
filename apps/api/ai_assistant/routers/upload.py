"""Document upload router."""
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile, HTTPException, Form

from ..config import settings
from ..db import get_db_session
from ..schemas import DocumentUploadResponse
from ..storage import save_upload
from ..services import parsing, chunking, embeddings, summarizer

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Upload and process a document.
    Document will be available for linking when creating a chat.

    Args:
        file: Uploaded file

    Returns:
        Document info with summary and chunk count
    """
    # Save file
    storage_path = save_upload(file)

    # Parse and chunk
    try:
        text_chunks = parsing.parse_and_chunk(storage_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse document: {str(e)}")

    # Generate summary
    first_chunk = text_chunks[0] if text_chunks else ""
    summary = await summarizer.summarize_document("\n\n".join(text_chunks[:5]))

    # Generate embeddings
    chunk_embeddings = await embeddings.embed_texts(text_chunks)

    # Save to database
    doc_id = uuid4()

    with get_db_session() as cursor:
        # Insert document
        cursor.execute(
            """
            INSERT INTO documents (id, title, mime_type, storage_path, summary)
            VALUES (%(id)s, %(title)s, %(mime_type)s, %(storage_path)s, %(summary)s)
            """,
            {
                "id": str(doc_id),
                "title": file.filename,
                "mime_type": file.content_type,
                "storage_path": storage_path,
                "summary": summary,
            },
        )

        # Insert chunks
        for i, (chunk, embedding) in enumerate(zip(text_chunks, chunk_embeddings)):
            cursor.execute(
                """
                INSERT INTO doc_chunks (id, document_id, chunk_index, content, embedding)
                VALUES (%(id)s, %(document_id)s, %(chunk_index)s, %(content)s, %(embedding)s)
                """,
                {
                    "id": str(uuid4()),
                    "document_id": str(doc_id),
                    "chunk_index": i,
                    "content": chunk,
                    "embedding": embedding,
                },
            )

    return DocumentUploadResponse(
        document_id=doc_id,
        summary=summary,
        chunk_count=len(text_chunks),
        storage_path=storage_path,
    )


