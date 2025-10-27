"""SQLAlchemy models."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Float,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    name: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True)
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB)  # {language: 'en', verbosity: 'concise', ...}
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))

    chats = relationship("Chat", back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    title: Mapped[Optional[str]] = mapped_column(String)
    mime_type: Mapped[Optional[str]] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))

    chunks = relationship("DocChunk", back_populates="document", cascade="all, delete-orphan")
    chats = relationship("Chat", secondary="chat_documents", back_populates="documents")


class DocChunk(Base):
    __tablename__ = "doc_chunks"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[str]] = mapped_column(String)  # Stored as string representation

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("doc_chunks_embedding_idx", "embedding", postgresql_using="ivfflat", postgresql_with={"lists": 100}),
        Index("doc_chunks_trgm_idx", "content", postgresql_using="gin", postgresql_ops={"content": "gin_trgm_ops"}),
    )


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID, ForeignKey("users.id", ondelete="SET NULL"))
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    personality: Mapped[Optional[str]] = mapped_column(String)
    style: Mapped[Optional[dict]] = mapped_column(JSONB)
    llm_provider: Mapped[str] = mapped_column(String, default="openai")  # openai, anthropic
    llm_model: Mapped[str] = mapped_column(String, default="gpt-4-turbo-preview")
    llm_temperature: Mapped[float] = mapped_column(Float, default=0.7)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    summary = relationship("ChatSummary", back_populates="chat", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", secondary="chat_documents", back_populates="chats")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    chat_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String, CheckConstraint("role IN ('user','assistant','system','tool')"))
    content: Mapped[str] = mapped_column(Text)
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer)
    sources: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))

    chat = relationship("Chat", back_populates="messages")


class ChatSummary(Base):
    __tablename__ = "chat_summaries"

    chat_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    rolling_summary: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))

    chat = relationship("Chat", back_populates="summary")


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    chat_id: Mapped[Optional[UUID]] = mapped_column(PGUUID, ForeignKey("chats.id", ondelete="CASCADE"))
    memory_type: Mapped[str] = mapped_column(String, CheckConstraint("memory_type IN ('episodic','fact')"))
    content: Mapped[str] = mapped_column(Text)
    salience: Mapped[float] = mapped_column(Float)
    last_reinforced: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    embedding: Mapped[Optional[str]] = mapped_column(String)

    __table_args__ = (
        Index("memories_embedding_idx", "embedding", postgresql_using="ivfflat", postgresql_with={"lists": 50}),
    )


class PersonaCustom(Base):
    __tablename__ = "personas_custom"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, unique=True)
    prompt: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))


class ChatDocument(Base):
    __tablename__ = "chat_documents"

    chat_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    document_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    uploaded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, CheckConstraint("rating IN (-1,0,1)"))
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))


