"""Memory management service."""
import json
from datetime import datetime, timedelta

from ..config import settings
from ..db import get_db_session


async def save_chat_summary(chat_id: str, summary: str) -> None:
    """
    Save or update chat rolling summary.

    Args:
        chat_id: Chat ID
        summary: Summary text
    """
    with get_db_session() as cursor:
        cursor.execute(
            """
                INSERT INTO chat_summaries (chat_id, rolling_summary, updated_at)
                VALUES (%(chat_id)s, %(summary)s, now())
                ON CONFLICT (chat_id)
                DO UPDATE SET rolling_summary = %(summary)s, updated_at = now()
                """,
            {"chat_id": chat_id, "summary": summary},
        )


async def get_chat_summary(chat_id: str) -> str | None:
    """
    Get chat rolling summary.

    Args:
        chat_id: Chat ID

    Returns:
        Summary text or None
    """
    with get_db_session() as cursor:
        cursor.execute(
            "SELECT rolling_summary FROM chat_summaries WHERE chat_id = %(chat_id)s",
            {"chat_id": chat_id},
        )
        result = cursor.fetchone()
        return result["rolling_summary"] if result else None


async def save_memory(
    chat_id: str | None,
    memory_type: str,
    content: str,
    salience: float,
    embedding: list[float] | None = None,
) -> None:
    """
    Save a memory (episodic or fact).

    Args:
        chat_id: Chat ID (optional)
        memory_type: 'episodic' or 'fact'
        content: Memory content
        salience: Salience score (0-1)
        embedding: Memory embedding (optional)
    """
    embedding_str = json.dumps(embedding) if embedding else None

    with get_db_session() as cursor:
        cursor.execute(
            """
                INSERT INTO memories (chat_id, memory_type, content, salience, embedding, last_reinforced)
                VALUES (%(chat_id)s, %(memory_type)s, %(content)s, %(salience)s, %(embedding)s, now())
                """,
            {
                "chat_id": chat_id,
                "memory_type": memory_type,
                "content": content,
                "salience": salience,
                "embedding": embedding_str,
            },
        )


async def retrieve_memories(chat_id: str | None, embedding: list[float] | None, limit: int = 5) -> list[dict]:
    """
    Retrieve relevant memories.

    Args:
        chat_id: Chat ID (optional)
        embedding: Query embedding for semantic search
        limit: Maximum number of memories to retrieve

    Returns:
        List of relevant memories
    """
    with get_db_session() as cursor:
        if embedding:
            embedding_str = json.dumps(embedding)
            cursor.execute(
                """
                SELECT id, chat_id, memory_type, content, salience, last_reinforced
                FROM memories
                WHERE (%(chat_id)s IS NULL OR chat_id = %(chat_id)s)
                  AND embedding IS NOT NULL
                ORDER BY embedding::vector <=> %(query_embedding)s::vector
                LIMIT %(limit)s
                """,
                {"chat_id": chat_id, "query_embedding": embedding_str, "limit": limit},
            )
        else:
            cursor.execute(
                """
                    SELECT id, chat_id, memory_type, content, salience, last_reinforced
                    FROM memories
                    WHERE chat_id = %(chat_id)s
                    ORDER BY salience DESC, last_reinforced DESC
                    LIMIT %(limit)s
                    """,
                {"chat_id": chat_id, "limit": limit},
            )

        results = cursor.fetchall()
        return [
            {
                "id": str(row["id"]),
                "chat_id": str(row["chat_id"]) if row["chat_id"] else None,
                "memory_type": row["memory_type"],
                "content": row["content"],
                "salience": row["salience"],
            }
            for row in results
        ]


async def reinforce_memory(memory_id: str) -> None:
    """
    Reinforce a memory by updating last_reinforced timestamp.

    Args:
        memory_id: Memory ID
    """
    with get_db_session() as cursor:
        cursor.execute(
            "UPDATE memories SET last_reinforced = now() WHERE id = %(memory_id)s",
            {"memory_id": memory_id},
        )


async def cleanup_old_memories() -> None:
    """Remove old, low-salience memories."""
    cutoff_date = datetime.now() - timedelta(days=settings.memory_retention_days)

    with get_db_session() as cursor:
        cursor.execute(
            """
                DELETE FROM memories
                WHERE last_reinforced < %(cutoff)s
                  AND salience < 0.3
                """,
            {"cutoff": cutoff_date},
        )

