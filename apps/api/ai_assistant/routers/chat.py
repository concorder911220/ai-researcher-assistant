"""Chat router."""
import json
from uuid import UUID, uuid4
from typing import Generator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..db import get_db_session
from ..schemas import ChatCreate, ChatResponse, ChatRequest, ChatResponseMessage
from ..services.agent_new import chat_with_rag_agent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate) -> ChatResponse:
    """
    Create a new chat.

    Args:
        chat_data: Chat creation data

    Returns:
        Created chat
    """
    chat_id = uuid4()

    with get_db_session() as cursor:
        cursor.execute(
            """
                INSERT INTO chats (id, user_id, system_prompt, personality, style, llm_provider, llm_model, llm_temperature)
                VALUES (%(id)s, %(user_id)s, %(system_prompt)s, %(personality)s, %(style)s, %(llm_provider)s, %(llm_model)s, %(llm_temperature)s)
                """,
            {
                "id": str(chat_id),
                "user_id": str(chat_data.user_id) if chat_data.user_id else None,
                "system_prompt": chat_data.system_prompt,
                "personality": chat_data.personality,
                "style": json.dumps({}),
                "llm_provider": chat_data.llm_provider or "openai",
                "llm_model": chat_data.llm_model or "gpt-4-turbo-preview",
                "llm_temperature": chat_data.llm_temperature or 0.7,
            },
        )
        
        # Link selected documents to this chat
        if chat_data.document_ids:
            for doc_id in chat_data.document_ids:
                cursor.execute(
                    """
                    INSERT INTO chat_documents (chat_id, document_id)
                    VALUES (%(chat_id)s, %(document_id)s)
                    ON CONFLICT (chat_id, document_id) DO NOTHING
                    """,
                    {"chat_id": str(chat_id), "document_id": doc_id}
                )

        cursor.execute(
            "SELECT id, user_id, system_prompt, personality, style, llm_provider, llm_model, llm_temperature, created_at FROM chats WHERE id = %(id)s",
            {"id": str(chat_id)},
        )
        result = cursor.fetchone()

    return ChatResponse(**dict(result))


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: UUID) -> ChatResponse:
    """Get a chat by ID."""
    with get_db_session() as cursor:
        cursor.execute(
            "SELECT id, user_id, system_prompt, personality, style, llm_provider, llm_model, llm_temperature, created_at FROM chats WHERE id = %(chat_id)s",
            {"chat_id": str(chat_id)},
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Chat not found")

    return ChatResponse(**dict(result))


@router.get("/", response_model=list[ChatResponse])
async def list_chats() -> list[ChatResponse]:
    """List all chats."""
    with get_db_session() as cursor:
        cursor.execute("SELECT id, system_prompt, personality, style, created_at FROM chats ORDER BY created_at DESC")
        results = cursor.fetchall()
        return [ChatResponse(**dict(row)) for row in results]


@router.get("/{chat_id}/messages")
async def get_chat_messages(chat_id: UUID):
    """Get all messages for a chat."""
    with get_db_session() as cursor:
        cursor.execute(
            """
            SELECT id, chat_id, role, content, sources, created_at
            FROM messages
            WHERE chat_id = %(chat_id)s
            ORDER BY created_at ASC
            """,
            {"chat_id": str(chat_id)},
        )
        results = cursor.fetchall()
        return [
            {
                "id": str(row["id"]),
                "chat_id": str(row["chat_id"]),
                "role": row["role"],
                "content": row["content"],
                "sources": row["sources"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in results
        ]


@router.post("/message")
async def send_message(request: ChatRequest):
    """
    Send a message in a chat with RAG.

    Args:
        request: Chat request

    Returns:
        Chat response
    """
    # Get or create chat
    if request.chat_id:
        chat_id = request.chat_id
    else:
        # Create new chat
        chat_id = uuid4()
        with get_db_session() as cursor:
            cursor.execute(
                """
                    INSERT INTO chats (id, system_prompt, personality, style)
                    VALUES (%(id)s, %(system_prompt)s, %(personality)s, %(style)s)
                    """,
                {
                    "id": str(chat_id),
                    "system_prompt": "You are a helpful AI assistant.",
                    "personality": None,
                    "style": {},
                },
            )

    # Get chat info (system prompt and personality)
    with get_db_session() as cursor:
        cursor.execute(
            "SELECT system_prompt, personality FROM chats WHERE id = %(chat_id)s",
            {"chat_id": str(chat_id)},
        )
        chat_info = cursor.fetchone()

        if not chat_info:
            raise HTTPException(status_code=404, detail="Chat not found")

    system_prompt = chat_info["system_prompt"] or "You are a helpful AI assistant."
    personality = chat_info["personality"]

    # Log LLM selection
    llm_provider = request.llm_provider or "openai"
    llm_model = request.llm_model or "gpt-4-turbo-preview"
    llm_temperature = request.llm_temperature if request.llm_temperature is not None else 0.7
    
    print(f"\n{'='*60}")
    print(f"🤖 LLM Selection for Message")
    print(f"{'='*60}")
    print(f"  Chat ID: {chat_id}")
    print(f"  Provider: {llm_provider.upper()}")
    print(f"  Model: {llm_model}")
    print(f"  Temperature: {llm_temperature}")
    print(f"  Message: {request.message[:50]}{'...' if len(request.message) > 50 else ''}")
    print(f"{'='*60}\n")

    # Save user message
    user_msg_id = uuid4()
    with get_db_session() as cursor:
        cursor.execute(
            """
                INSERT INTO messages (id, chat_id, role, content)
                VALUES (%(id)s, %(chat_id)s, 'user', %(content)s)
                """,
            {
                "id": str(user_msg_id),
                "chat_id": str(chat_id),
                "content": request.message,
            },
        )

    # Stream response if requested
    if request.stream:
        return StreamingResponse(
            _stream_chat_response(
                str(chat_id), 
                request.message, 
                system_prompt, 
                personality,
                llm_provider=llm_provider,
                llm_model=llm_model,
                llm_temperature=llm_temperature,
            ),
            media_type="text/event-stream",
        )

    # Generate response using agent with tools - per-message LLM selection
    response_gen = chat_with_rag_agent(
        str(chat_id), 
        request.message, 
        system_prompt, 
        personality,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        stream=False
    )
    
    response = None
    async for result in response_gen:
        response = result
        break  # Get the first (and only) result for non-streaming

    if not response:
        raise HTTPException(status_code=500, detail="Failed to generate response")

    # Save assistant message
    assistant_msg_id = uuid4()
    with get_db_session() as cursor:
        cursor.execute(
            """
                INSERT INTO messages (id, chat_id, role, content, sources)
                VALUES (%(id)s, %(chat_id)s, 'assistant', %(content)s, %(sources)s)
                """,
            {
                "id": str(assistant_msg_id),
                "chat_id": str(chat_id),
                "content": response["content"],
                "sources": json.dumps({"sources": response["sources"], "citations": response["citations"]}),
            },
        )

    return ChatResponseMessage(
        content=response["content"],
        sources=response["sources"],
        citations=response["citations"],
        tool_calls=response.get("tool_calls", 0),  # NEW: Include tool call count
    )


async def _stream_chat_response(
    chat_id: str,
    message: str,
    system_prompt: str,
    personality: str | None,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4-turbo-preview",
    llm_temperature: float = 0.7,
) -> Generator[str, None, None]:
    """Stream chat response."""
    response_content = ""
    # Generate response using agent - per-message LLM selection
    response_iter = chat_with_rag_agent(
        chat_id, message, system_prompt, personality,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        stream=True
    )
    
    async for chunk in response_iter:
        if hasattr(chunk, 'content'):
            response_content += chunk.content
            yield f"data: {chunk.content}\n\n"

    # Save complete message after streaming
    assistant_msg_id = uuid4()
    with get_db_session() as cursor:
        cursor.execute(
            """
                INSERT INTO messages (id, chat_id, role, content)
                VALUES (%(id)s, %(chat_id)s, 'assistant', %(content)s)
                """,
            {
                "id": str(assistant_msg_id),
                "chat_id": chat_id,
                "content": response_content,
            },
        )

