"""Search router."""
from uuid import UUID

from fastapi import APIRouter

from ..db import get_db_session
from ..services import embeddings, retriever

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/")
async def search_documents(query: str, limit: int = 5):
    """
    Search documents using hybrid retrieval.

    Args:
        query: Search query
        limit: Maximum number of results

    Returns:
        Search results
    """
    # Generate query embedding
    embedding_model = embeddings.get_embedding_model()
    query_embedding = embedding_model.embed_query(query)

    # Perform hybrid search
    results = await retriever.hybrid_search(
        query,
        query_embedding,
        top_k=limit,
        alpha=0.7,
    )

    # Get additional metadata for each result
    doc_ids = [result["document_id"] for result in results]
    with get_db_session() as cursor:
        cursor.execute(
            """
                SELECT id, title, summary
                FROM documents
                WHERE id IN %(doc_ids)s
                """,
            {"doc_ids": tuple(doc_ids)},
        )
        doc_metadata = {str(row["id"]): row for row in cursor.fetchall()}

    # Enrich results with metadata
    for result in results:
        doc_id = result["document_id"]
        if doc_id in doc_metadata:
            result["document_title"] = doc_metadata[doc_id]["title"]
            result["document_summary"] = doc_metadata[doc_id]["summary"]

    return {"query": query, "results": results}


