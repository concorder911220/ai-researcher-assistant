"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Document schemas
class DocumentResponse(BaseModel):
    id: UUID
    title: Optional[str] = None
    mime_type: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    summary: str
    chunk_count: int
    storage_path: str


# Chunk schemas
class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str

    class Config:
        from_attributes = True


# Chat schemas
class ChatCreate(BaseModel):
    user_id: Optional[UUID] = None
    system_prompt: Optional[str] = None
    personality: Optional[str] = None
    llm_provider: Optional[str] = "openai"  # openai, anthropic
    llm_model: Optional[str] = "gpt-4-turbo-preview"
    llm_temperature: Optional[float] = 0.7
    document_ids: list[str] = []  # Documents to link with this chat


class ChatResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    system_prompt: Optional[str] = None
    personality: Optional[str] = None
    style: Optional[dict] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    created_at: datetime

    class Config:
        from_attributes = True


# Message schemas
class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    role: str
    content: str
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    sources: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[UUID] = None
    stream: bool = False
    # Per-message LLM selection
    llm_provider: Optional[str] = "openai"
    llm_model: Optional[str] = "gpt-4-turbo-preview"
    llm_temperature: Optional[float] = 0.7


class ChatResponseMessage(BaseModel):
    content: str
    sources: Optional[list[dict]] = None
    citations: Optional[list[str]] = None
    tool_calls: Optional[int] = 0  # Number of tools used


# Persona schemas
class PersonaCreate(BaseModel):
    name: str
    prompt: str


class PersonaResponse(BaseModel):
    id: UUID
    name: str
    prompt: str
    created_at: datetime

    class Config:
        from_attributes = True


# Feedback schemas
class FeedbackCreate(BaseModel):
    message_id: UUID
    rating: int = Field(..., ge=-1, le=1)
    note: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: UUID
    message_id: UUID
    rating: int
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Memory schemas
class MemoryResponse(BaseModel):
    id: UUID
    chat_id: Optional[UUID] = None
    memory_type: str
    content: str
    salience: float
    last_reinforced: Optional[datetime] = None

    class Config:
        from_attributes = True


