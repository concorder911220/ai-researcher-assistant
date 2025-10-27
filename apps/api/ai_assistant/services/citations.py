"""Citation management service."""
import re
from typing import Any


def extract_citations(text: str) -> list[str]:
    """
    Extract citations from text (e.g., [1], [2], etc.).

    Args:
        text: Text with citations

    Returns:
        List of citation references
    """
    pattern = r"\[(\d+)\]"
    citations = re.findall(pattern, text)
    return citations


def format_chunk_source(chunk: dict[str, Any]) -> dict[str, Any]:
    """
    Format a chunk as a citation source with rich metadata.

    Args:
        chunk: Retrieved chunk

    Returns:
        Formatted source dictionary with title, page, etc.
    """
    return {
        "id": chunk.get("id"),
        "document_id": chunk.get("document_id"),
        "title": chunk.get("title") or chunk.get("document_name") or "Document",
        "document_name": chunk.get("document_name") or chunk.get("title") or "Document",
        "page": chunk.get("page"),
        "chunk_index": chunk.get("chunk_index"),
        "content": chunk.get("content"),
        "score": chunk.get("hybrid_score", chunk.get("score", 0.0)),
        "type": "document",
    }


def format_web_source(source: dict[str, Any]) -> dict[str, Any]:
    """
    Format a web search result as a citation source.

    Args:
        source: Web search result

    Returns:
        Formatted source dictionary
    """
    return {
        "url": source.get("url", ""),
        "title": source.get("title", ""),
        "snippet": source.get("snippet", ""),
        "source_type": "web",
    }


