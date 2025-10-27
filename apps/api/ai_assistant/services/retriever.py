"""Hybrid retrieval service."""
import json
from typing import Any

from ..config import settings
from ..db import get_db_session


async def hybrid_search(
    query: str,
    query_embedding: list[float],
    top_k: int = 5,
    alpha: float = 0.7,
) -> list[dict[str, Any]]:
    """
    Perform hybrid search (vector + keyword) on document chunks.

    Args:
        query: Search query
        query_embedding: Query embedding vector
        top_k: Number of results to return
        alpha: Weight for vector search (1.0 = pure vector, 0.0 = pure keyword)

    Returns:
        List of matching chunks with scores
    """
    embedding_str = json.dumps(query_embedding)

    with get_db_session() as cursor:
        # Vector similarity search
        cursor.execute(
            """
            SELECT id, document_id, chunk_index, content,
                   1 - (embedding::vector <=> %(query_embedding)s::vector) AS vector_score
            FROM doc_chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding::vector <=> %(query_embedding)s::vector
            LIMIT %(top_k)s
            """,
            {"query_embedding": embedding_str, "top_k": top_k},
        )

        vector_results = cursor.fetchall()

        # Keyword search using pg_trgm
        cursor.execute(
            """
            SELECT id, document_id, chunk_index, content,
                   similarity(content, %(query)s) AS keyword_score
            FROM doc_chunks
            WHERE content %% %(query)s
            ORDER BY similarity(content, %(query)s) DESC
            LIMIT %(top_k)s
            """,
            {"query": query, "top_k": top_k},
        )

        keyword_results = cursor.fetchall()

    # Combine results with hybrid scoring
    combined_results = {}
    for result in vector_results:
        doc_id = result["id"]
        combined_results[doc_id] = {
            "id": str(result["id"]),
            "document_id": str(result["document_id"]),
            "chunk_index": result["chunk_index"],
            "content": result["content"],
            "vector_score": float(result["vector_score"]),
            "keyword_score": 0.0,
            "hybrid_score": 0.0,
        }

    for result in keyword_results:
        doc_id = result["id"]
        if doc_id in combined_results:
            combined_results[doc_id]["keyword_score"] = float(result["keyword_score"])
        else:
            combined_results[doc_id] = {
                "id": str(result["id"]),
                "document_id": str(result["document_id"]),
                "chunk_index": result["chunk_index"],
                "content": result["content"],
                "vector_score": 0.0,
                "keyword_score": float(result["keyword_score"]),
                "hybrid_score": 0.0,
            }

    # Calculate hybrid scores
    for item in combined_results.values():
        item["hybrid_score"] = alpha * item["vector_score"] + (1 - alpha) * item["keyword_score"]

    # Sort by hybrid score and return top_k
    sorted_results = sorted(combined_results.values(), key=lambda x: x["hybrid_score"], reverse=True)

    return sorted_results[:top_k]


def calculate_retrieval_confidence(chunks: list[dict]) -> float:
    """
    Calculate confidence score for retrieval results.

    Args:
        chunks: Retrieved chunks

    Returns:
        Confidence score between 0 and 1
    """
    if not chunks:
        return 0.0

    # Simple confidence based on highest hybrid score
    max_score = max(chunk.get("hybrid_score", 0.0) for chunk in chunks)
    return max_score


