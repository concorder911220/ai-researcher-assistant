"""Agent service for handling LLM interactions."""
import json
from typing import Any, Generator

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool

from ..config import settings
from ..services.embeddings import get_embedding_model
from ..services.retriever import calculate_retrieval_confidence
from ..services.retriever_chat import hybrid_search_for_chat
from ..services.memory import (
    get_chat_summary,
    retrieve_memories,
    save_memory,
    save_chat_summary,
)
from ..services.citations import extract_citations, format_chunk_source

# Tool: Web search using SerpAPI
def search_web(query: str) -> str:
    """
    Search the web using SerpAPI.

    Args:
        query: Search query

    Returns:
        Search results as JSON string
    """
    if not settings.serpapi_api_key:
        return json.dumps({"error": "SerpAPI key not configured"})
    
    try:
        from serpapi import GoogleSearch
        
        params = {
            "q": query,
            "api_key": settings.serpapi_api_key,
            "engine": "google",
            "num": 5
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})


async def create_agent(system_prompt: str, personality: str | None = None) -> ChatOpenAI:
    """
    Create an agent with system prompt and personality.

    Args:
        system_prompt: System prompt
        personality: Personality type (optional)

    Returns:
        ChatOpenAI agent
    """
    # Load personality prompts if specified
    if personality:
        try:
            with open(f"apps/api/ai_assistant/prompts/persona_{personality}.md") as f:
                personality_prompt = f.read()
        except FileNotFoundError:
            personality_prompt = ""
    else:
        personality_prompt = ""

    # Load base system prompt
    try:
        with open("apps/api/ai_assistant/prompts/system_base.md") as f:
            base_prompt = f.read()
    except FileNotFoundError:
        base_prompt = ""

    full_prompt = f"{base_prompt}\n\n{personality_prompt}\n\n{system_prompt}"

    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        openai_api_key=settings.openai_api_key,
    )


async def chat_with_rag(
    chat_id: str,
    message: str,
    system_prompt: str,
    personality: str | None = None,
    stream: bool = False,
):
    """
    Handle a chat message with RAG retrieval.

    Args:
        chat_id: Chat ID
        message: User message
        system_prompt: System prompt
        personality: Personality type
        stream: Whether to stream the response

    Returns:
        Response dictionary with content, sources, and citations (if not streaming)
        Generator of chunks (if streaming)
    """
    # Retrieve recent conversation history (last 10 messages)
    from ..db import get_db_session
    conversation_history = []
    try:
        with get_db_session() as cursor:
            cursor.execute(
                """
                SELECT role, content
                FROM messages
                WHERE chat_id = %(chat_id)s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                {"chat_id": chat_id}
            )
            results = cursor.fetchall()
            # Reverse to get chronological order (oldest first)
            conversation_history = [
                {"role": row["role"], "content": row["content"]} 
                for row in reversed(results)
            ]
    except Exception as e:
        pass
    
    # Get chat summary (optional)
    summary = None
    try:
        summary = await get_chat_summary(chat_id)
    except Exception:
        pass

    # Generate query embedding
    embedding_model = get_embedding_model()
    query_embedding = embedding_model.embed_query(message)

    # Retrieve relevant chunks (filtered by chat's documents)
    chunks = await hybrid_search_for_chat(
        query=message,
        query_embedding=query_embedding,
        chat_id=chat_id,
        top_k=settings.top_k_chunks,
    )

    # Check confidence
    confidence = calculate_retrieval_confidence(chunks)

    # If confidence is low, search the web
    web_results = None
    if confidence < settings.retrieval_confidence_threshold:
        # Use SerpAPI web search
        web_search_results = search_web(message)
        web_results = json.loads(web_search_results)

    # Retrieve relevant memories
    memories = await retrieve_memories(chat_id, query_embedding)

    # Format context with detailed metadata
    context_parts = []
    for i, chunk in enumerate(chunks):
        # Get metadata
        doc_name = chunk.get('title', 'Unknown Document')
        page = chunk.get('page', 'N/A')
        
        # Format chunk with metadata
        chunk_header = f"[Source {i+1}: {doc_name}"
        if page and page != 'N/A':
            chunk_header += f" - Page {page}"
        chunk_header += "]"
        
        context_parts.append(f"{chunk_header}\n{chunk['content']}")
    
    context = "\n\n---\n\n".join(context_parts)

    # Build prompt with conversation history
    prompt_parts = [("system", system_prompt)]
    
    if summary:
        prompt_parts.append(("system", f"Conversation summary: {summary}"))

    if memories:
        memory_context = "\n".join([mem["content"] for mem in memories])
        prompt_parts.append(("system", f"Relevant memories:\n{memory_context}"))
    
    # Add conversation history
    for msg in conversation_history:
        if msg["role"] == "user":
            prompt_parts.append(("human", msg["content"]))
        elif msg["role"] == "assistant":
            prompt_parts.append(("assistant", msg["content"]))
    
    # Add current message with context
    prompt_parts.append(("human", f"Context from documents:\n{context}\n\nUser: {message}"))

    prompt_template = ChatPromptTemplate.from_messages(prompt_parts)
    model = await create_agent(system_prompt, personality)

    # Generate response
    chain = prompt_template | model

    if stream:
        # Streaming response - just yield chunks
        async for chunk in chain.astream({"message": message}):
            if hasattr(chunk, 'content'):
                yield chunk
    else:
        # Non-streaming response
        result = chain.invoke({"message": message})
        response_content = result.content

        # Extract citations
        citations = extract_citations(response_content)

        # Format sources
        sources = []
        for i, chunk in enumerate(chunks):
            sources.append(
                {
                    **format_chunk_source(chunk),
                    "citation_id": i + 1,
                }
            )

        if web_results and "organic_results" in web_results:
            for i, result in enumerate(web_results["organic_results"][:3]):
                sources.append(
                    {
                        **format_web_source(result),
                        "citation_id": len(sources) + i + 1,
                    }
                )

        # For non-streaming, yield the final result
        yield {
            "content": response_content,
            "sources": sources,
            "citations": citations,
        }

