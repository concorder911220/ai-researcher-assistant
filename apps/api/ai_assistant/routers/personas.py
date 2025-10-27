"""Personas router."""
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException

from ..db import get_db_session
from ..schemas import PersonaCreate, PersonaResponse

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("/", response_model=PersonaResponse)
async def create_persona(persona: PersonaCreate) -> PersonaResponse:
    """
    Create a custom persona.

    Args:
        persona: Persona data

    Returns:
        Created persona
    """
    persona_id = uuid4()

    with get_db_session() as cursor:
        cursor.execute(
            """
                INSERT INTO personas_custom (id, name, prompt)
                VALUES (%(id)s, %(name)s, %(prompt)s)
                """,
            {
                "id": str(persona_id),
                "name": persona.name,
                "prompt": persona.prompt,
            },
        )

        cursor.execute(
            "SELECT id, name, prompt, created_at FROM personas_custom WHERE id = %(id)s",
            {"id": str(persona_id)},
        )
        result = cursor.fetchone()

    return PersonaResponse(**dict(result))


@router.get("/", response_model=list[PersonaResponse])
async def list_personas() -> list[PersonaResponse]:
    """List all custom personas."""
    with get_db_session() as cursor:
        cursor.execute(
            "SELECT id, name, prompt, created_at FROM personas_custom ORDER BY created_at DESC"
        )
        results = cursor.fetchall()
        return [PersonaResponse(**dict(row)) for row in results]


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: UUID) -> PersonaResponse:
    """Get a persona by ID."""
    with get_db_session() as cursor:
        cursor.execute(
            "SELECT id, name, prompt, created_at FROM personas_custom WHERE id = %(id)s",
            {"id": str(persona_id)},
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Persona not found")

    return PersonaResponse(**dict(result))


