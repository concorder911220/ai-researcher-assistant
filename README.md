# Personal AI Research Assistant with Memory

A backend API for a personal AI research assistant with RAG (Retrieval-Augmented Generation), memory, and tool integration.

## Features

- **Document Upload & Processing**: Upload PDFs, Word docs, and other formats. Automatic parsing, chunking, and vectorization.
- **RAG Chat**: Chat with your documents using hybrid retrieval (vector + keyword search).
- **Memory System**: Short-term rolling summaries and long-term episodic/factual memories.
- **Web Search Integration**: Automatic web search via SerpAPI when confidence is low.
- **Personas**: Built-in and custom personas for different interaction styles.
- **Citations**: Automatic source citation for all responses.
- **Feedback System**: Thumbs up/down to tune chat behavior.
- **Streaming**: SSE support for real-time responses.

## Tech Stack

- **Framework**: FastAPI
- **LLM**: OpenAI GPT-4
- **Embeddings**: OpenAI text-embedding-3-small
- **Document Processing**: Unstructured
- **Database**: PostgreSQL with pgvector
- **Storage**: Local filesystem (Docker volume)
- **Package Manager**: Poetry or pip (requirements.txt)
- **Testing**: pytest

## Project Structure

```
home_task/
├── apps/api/
│   ├── pyproject.toml
│   ├── main.py
│   └── ai_assistant/
│       ├── __init__.py
│       ├── config.py
│       ├── db.py
│       ├── models.py
│       ├── schemas.py
│       ├── storage.py
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── upload.py
│       │   ├── docs.py
│       │   ├── chat.py
│       │   ├── search.py
│       │   ├── feedback.py
│       │   └── personas.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── parsing.py
│       │   ├── chunking.py
│       │   ├── embeddings.py
│       │   ├── summarizer.py
│       │   ├── retriever.py
│       │   ├── agent.py
│       │   ├── memory.py
│       │   └── citations.py
│       ├── prompts/
│       │   ├── system_base.md
│       │   ├── persona_factual.md
│       │   ├── persona_friendly.md
│       │   └── persona_humorous.md
│       └── telemetry/
│           ├── __init__.py
│           └── logging.py
├── tests/
├── infra/
│   └── init_db.sql
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Setup

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- SerpAPI key
- Python 3.11+ (for local development)

### Installation (Docker)

1. Clone the repository and navigate to the project directory.

2. Copy the environment file:
   ```bash
   cp env.example .env
   ```

3. Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_key_here
   SERPAPI_API_KEY=your_key_here
   ```

4. Start the services:
   ```bash
   docker-compose up -d
   ```

5. The API will be available at `http://localhost:8000`

   **Note**: Database migrations run automatically on startup via Alembic.

### Installation (Local Development)

#### Option 1: Using Poetry (Recommended)

```bash
cd apps/api
poetry install
poetry run uvicorn main:app --reload
```

#### Option 2: Using pip

```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload
```

For production deployment:
```bash
pip install -r requirements-prod.txt
```

## API Endpoints

### Documents

- `POST /upload/` - Upload and process a document
- `GET /docs/` - List all documents
- `GET /docs/{doc_id}` - Get a document by ID
- `GET /docs/{doc_id}/chunks` - Get chunks for a document
- `DELETE /docs/{doc_id}` - Delete a document

### Chat

- `POST /chat/` - Create a new chat
- `GET /chat/` - List all chats
- `GET /chat/{chat_id}` - Get a chat by ID
- `POST /chat/message` - Send a message (with RAG)

### Search

- `POST /search/` - Search documents using hybrid retrieval

### Feedback

- `POST /feedback/` - Submit feedback for a message
- `GET /feedback/message/{message_id}` - Get feedback for a message

### Personas

- `POST /personas/` - Create a custom persona
- `GET /personas/` - List all personas
- `GET /personas/{persona_id}` - Get a persona by ID

### Health

- `GET /` - Root endpoint
- `GET /health` - Health check

## Usage

### Upload a Document

```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@document.pdf"
```

### Chat with Documents

```bash
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the main topic of my documents?",
    "chat_id": "your-chat-id",
    "stream": false
  }'
```

### Search Documents

```bash
curl -X POST "http://localhost:8000/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search query",
    "limit": 5
  }'
```

## Development

### Running Tests

Using Poetry:
```bash
cd apps/api
poetry install
poetry run pytest
```

Using pip:
```bash
cd apps/api
pip install -r requirements.txt
pytest
```

### Local Development

Using Poetry:
```bash
cd apps/api
poetry install
poetry run uvicorn main:app --reload
```

Using pip:
```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload
```

## Database Schema

The system uses PostgreSQL with pgvector and is managed via **Alembic migrations**.

### Main Tables

- **documents**: Document metadata and summaries
- **doc_chunks**: Document chunks with embeddings (VECTOR type)
- **chats**: Chat sessions
- **messages**: Chat messages
- **chat_summaries**: Rolling chat summaries
- **memories**: Long-term memories with embeddings (episodic/factual)
- **personas_custom**: Custom personas
- **feedback**: User feedback

### Migrations

Migrations are automatically run on container startup. For manual migration management:

```bash
cd apps/api

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Configuration

Configuration is managed through environment variables:

- `OPENAI_API_KEY`: OpenAI API key
- `SERPAPI_API_KEY`: SerpAPI key
- `POSTGRES_*`: Database connection settings
- `UPLOAD_DIR`: Directory for uploaded files
- `LLM_MODEL`: LLM model name (default: gpt-4-turbo-preview)
- `EMBEDDING_MODEL`: Embedding model (default: text-embedding-3-small)
- `HYBRID_SEARCH_ALPHA`: Weight for hybrid search (default: 0.7)
- `TOP_K_CHUNKS`: Number of chunks to retrieve (default: 5)

## License

MIT


