"""Embedding service."""
import json

import numpy as np
from langchain_openai import OpenAIEmbeddings

from ..config import settings


def get_embedding_model() -> OpenAIEmbeddings:
    """Get the embedding model."""
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )


async def embed_text(text: str) -> str:
    """
    Generate embedding for text.

    Args:
        text: Text to embed

    Returns:
        Embedding as JSON string for pgvector
    """
    model = get_embedding_model()
    embedding = model.embed_query(text)

    # Convert to JSON string for pgvector
    return json.dumps(embedding)


async def embed_texts(texts: list[str]) -> list[str]:
    """
    Generate embeddings for multiple texts.

    Args:
        texts: List of texts to embed

    Returns:
        List of embeddings as JSON strings
    """
    model = get_embedding_model()
    embeddings = model.embed_documents(texts)

    # Convert to JSON strings for pgvector
    return [json.dumps(emb) for emb in embeddings]


def cosine_similarity(embedding1: list[float], embedding2: list[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.

    Args:
        embedding1: First embedding
        embedding2: Second embedding

    Returns:
        Cosine similarity score
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


