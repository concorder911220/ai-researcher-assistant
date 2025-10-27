"""Feedback router."""
from uuid import uuid4
from fastapi import APIRouter, HTTPException

from ..db import get_db_session
from ..schemas import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackCreate) -> FeedbackResponse:
    """
    Submit feedback for a message.

    Args:
        feedback: Feedback data

    Returns:
        Created feedback
    """
    feedback_id = uuid4()

    with get_db_session() as cursor:
        cursor.execute(
            """
                INSERT INTO feedback (id, message_id, rating, note)
                VALUES (%(id)s, %(message_id)s, %(rating)s, %(note)s)
                """,
            {
                "id": str(feedback_id),
                "message_id": str(feedback.message_id),
                "rating": feedback.rating,
                "note": feedback.note,
            },
        )

        cursor.execute(
            "SELECT id, message_id, rating, note, created_at FROM feedback WHERE id = %(id)s",
            {"id": str(feedback_id)},
        )
        result = cursor.fetchone()

    return FeedbackResponse(**dict(result))


@router.get("/message/{message_id}")
async def get_feedback(message_id: str):
    """Get feedback for a message."""
    with get_db_session() as cursor:
        cursor.execute(
            """
                SELECT id, message_id, rating, note, created_at
                FROM feedback
                WHERE message_id = %(message_id)s
                """,
            {"message_id": message_id},
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Feedback not found")

    return FeedbackResponse(**dict(result))

