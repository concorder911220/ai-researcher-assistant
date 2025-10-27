"""Application configuration."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

# Find project root (where .env is located)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings."""

    # API Keys (optional for migrations)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    serpapi_api_key: Optional[str] = None

    # Database
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "ai_assistant"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    # Storage
    upload_dir: str = "./uploads"  # Local development default

    # OpenAI
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # LLM
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7

    # Retrieval
    hybrid_search_alpha: float = 0.7  # 0=keyword, 1=vector
    top_k_chunks: int = 5
    retrieval_confidence_threshold: float = 0.7

    # Memory
    memory_retention_days: int = 30
    memory_reinforcement_window: int = 7

    # Agent
    agent_max_iterations: int = 5
    agent_verbose: bool = True
    enable_web_search: bool = True
    enable_calculator: bool = True

    class Config:
        # Use absolute path to .env file in project root
        env_file = str(ENV_FILE)
        case_sensitive = False
        extra = "ignore"


settings = Settings()


