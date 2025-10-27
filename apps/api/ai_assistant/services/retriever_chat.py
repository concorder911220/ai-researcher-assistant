"""Enhanced retriever with chat-document filtering."""
import json
from typing import List, Dict, Any, Optional

from ..db import get_db_session
from .retriever import hybrid_search as base_hybrid_search


async def hybrid_search_for_chat(
    query: str,
    query_embedding: List[float],
    chat_id: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search limited to documents in a specific chat.

    Args:
        query: Search query string
        query_embedding: Query embedding vector
        chat_id: Chat ID to filter documents
        top_k: Number of results to return

    Returns:
        List of matching chunks with scores, filtered by chat's documents
    """
    embedding_str = json.dumps(query_embedding)

    with get_db_session() as cursor:
        # Vector similarity search (filtered by chat's documents)
        cursor.execute(
            """
            SELECT dc.id, dc.document_id, dc.chunk_index, dc.content,
                   1 - (dc.embedding::vector <=> %(query_embedding)s::vector) AS vector_score
            FROM doc_chunks dc
            INNER JOIN chat_documents cd ON dc.document_id = cd.document_id
            WHERE cd.chat_id = %(chat_id)s
              AND dc.embedding IS NOT NULL
            ORDER BY dc.embedding::vector <=> %(query_embedding)s::vector
            LIMIT %(top_k)s
            """,
            {"query_embedding": embedding_str, "chat_id": chat_id, "top_k": top_k},
        )

        vector_results = cursor.fetchall()

        # Keyword search using pg_trgm (filtered by chat's documents)
        cursor.execute(
            """
            SELECT dc.id, dc.document_id, dc.chunk_index, dc.content,
                   similarity(dc.content, %(query)s) AS keyword_score
            FROM doc_chunks dc
            INNER JOIN chat_documents cd ON dc.document_id = cd.document_id
            WHERE cd.chat_id = %(chat_id)s
              AND dc.content %% %(query)s
            ORDER BY similarity(dc.content, %(query)s) DESC
            LIMIT %(top_k)s
            """,
            {"query": query, "chat_id": chat_id, "top_k": top_k},
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

    # Calculate hybrid score
    for item in combined_results.values():
        item["hybrid_score"] = (0.7 * item["vector_score"]) + (0.3 * item["keyword_score"])

    # Sort by hybrid score
    sorted_results = sorted(
        combined_results.values(),
        key=lambda x: x["hybrid_score"],
        reverse=True
    )

    return sorted_results[:top_k]

