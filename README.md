# Personal AI Research Assistant with Memory

A full-stack AI research assistant with RAG (Retrieval-Augmented Generation), memory, multi-LLM support, and advanced tool integration.

## 🌟 Features

- **Document Upload & Processing**: Upload PDFs, Word docs, Excel, and other formats with automatic parsing, chunking, and vectorization
- **RAG Chat**: Chat with your documents using hybrid retrieval (vector + keyword search)
- **Multi-LLM Support**: Choose between OpenAI GPT-4 and Anthropic Claude on a per-message basis
- **LangChain Agent**: Intelligent tool orchestration with web search, calculator, and news search
- **Memory System**: 
  - Short-term: Rolling conversation summaries
  - Long-term: Episodic and factual memories with vector search
- **Web Search Integration**: Automatic web search via SerpAPI when RAG confidence is low
- **Personas**: Built-in (friendly, factual, humorous) and custom personas
- **User Profiles**: Per-user settings and preferences
- **Citations**: Automatic source citation with document titles, page numbers, and relevance scores
- **Feedback System**: Thumbs up/down to tune chat behavior
- **Streaming**: SSE support for real-time responses
- **Next.js Frontend**: Modern GPT-style UI with sidebar, file upload, and chat history

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI with Python 3.13
- **LLMs**: 
  - OpenAI GPT-4 Turbo
  - Anthropic Claude Sonnet 4
- **Agent Framework**: LangChain with OpenAI function calling
- **Embeddings**: OpenAI text-embedding-3-small
- **Document Processing**: Unstructured + LibreOffice + Tesseract OCR + Poppler
- **Database**: PostgreSQL 16 with pgvector and pg_trgm extensions
- **Storage**: Docker volumes (persistent)
- **Migrations**: Alembic
- **Package Manager**: pip with requirements.txt
- **Testing**: pytest

### Frontend
- **Framework**: Next.js 14 with React
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI**: Modern GPT-style interface with dynamic routing

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Automated database setup and migrations
- **Environment**: Separate configs for Docker and local development

## 📁 Project Structure

```
home_task/
├── apps/api/                          # Backend API
│   ├── main.py                        # FastAPI application entry
│   ├── alembic/                       # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── alembic.ini                    # Alembic configuration
│   ├── entrypoint.sh                  # Docker entrypoint script
│   └── ai_assistant/
│       ├── config.py                  # Environment configuration
│       ├── db.py                      # Database connection
│       ├── models.py                  # SQLAlchemy models
│       ├── schemas.py                 # Pydantic schemas
│       ├── routers/                   # API route handlers
│       │   ├── upload.py              # Document upload
│       │   ├── docs.py                # Document management
│       │   ├── chat.py                # Chat & RAG
│       │   ├── search.py              # Hybrid search
│       │   ├── feedback.py            # Feedback system
│       │   └── personas.py            # Persona management
│       ├── services/                  # Business logic
│       │   ├── parsing.py             # Document parsing
│       │   ├── chunking.py            # Text chunking
│       │   ├── embeddings.py          # Vector embeddings
│       │   ├── summarizer.py          # Document summarization
│       │   ├── retriever.py           # Hybrid retrieval
│       │   ├── retriever_chat.py      # Chat-scoped retrieval
│       │   ├── agent_new.py           # LangChain agent
│       │   ├── memory.py              # Memory management
│       │   └── citations.py           # Source citations
│       ├── prompts/                   # Prompt templates
│       │   ├── system_base.md
│       │   ├── persona_factual.md
│       │   ├── persona_friendly.md
│       │   └── persona_humorous.md
│       └── telemetry/
│           └── logging.py             # Logging utilities
├── frontend/                          # Next.js frontend
│   ├── app/                           # App router pages
│   │   ├── page.tsx                   # Home/upload page
│   │   └── chat/[id]/page.tsx         # Individual chat pages
│   └── components/                    # React components
│       ├── ChatSidebar.tsx            # Sidebar with chat history
│       ├── ChatMessages.tsx           # Message display with sources
│       ├── ChatInput.tsx              # Message input with LLM selector
│       ├── DocumentUpload.tsx         # Document upload component
│       └── NewChatModal.tsx           # New chat creation modal
├── requirements.txt                   # Python dependencies (root)
├── docker-compose.yml                 # Docker orchestration
├── Dockerfile                         # API container definition
├── .dockerignore                      # Docker build exclusions
├── env.example                        # Environment template (Docker)
├── .env.local                         # Environment template (Local)
└── README.md
```

## 🚀 Quick Start (Docker)

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Anthropic API key (optional, [Get one here](https://console.anthropic.com/))
- SerpAPI key (optional, [Get one here](https://serpapi.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/concorder911220/ai-researcher-assistant.git
   cd home_task
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   ```

3. **Add your API keys to `.env`**
   ```env
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...  # Optional
   SERPAPI_API_KEY=...            # Optional
   
   # Docker settings (default)
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   POSTGRES_DB=ai_assistant
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   UPLOAD_DIR=/data/uploads
   ```

4. **Build and start the containers**
   ```bash
   docker-compose up -d --build
   ```

5. **Check the logs**
   ```bash
   docker-compose logs -f api
   ```

6. **Access the API**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - Frontend (if deployed): http://localhost:3000

### What Happens on Startup

The `entrypoint.sh` script automatically:
1. ✅ Waits for PostgreSQL to be ready
2. ✅ Creates the `ai_assistant` database if it doesn't exist
3. ✅ Enables `pgvector` and `pg_trgm` PostgreSQL extensions
4. ✅ Runs Alembic migrations to create all tables and indexes
5. ✅ Starts the FastAPI application with auto-reload

## 💻 Local Development

### Prerequisites

- Python 3.13+
- PostgreSQL 16+ with pgvector installed
- System dependencies (for document processing):
  ```bash
  # Ubuntu/Debian
  sudo apt-get install -y \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    poppler-utils tesseract-ocr libreoffice
  
  # macOS
  brew install poppler tesseract libreoffice
  ```

### Setup

1. **Set up environment**
   ```bash
   cp .env.local .env
   ```

2. **Edit `.env` for local development**
   ```env
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   SERPAPI_API_KEY=...
   
   # Local settings
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=ai_assistant
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   UPLOAD_DIR=./uploads
   ```

3. **Create a virtual environment**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up the database**
   ```bash
   # Create database
   createdb ai_assistant
   
   # Enable extensions
   psql ai_assistant -c "CREATE EXTENSION IF NOT EXISTS vector;"
   psql ai_assistant -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
   ```

6. **Run migrations**
   ```bash
   cd apps/api
   alembic upgrade head
   ```

7. **Start the development server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0
   ```

## 📡 API Endpoints

### Documents
- `POST /upload/` - Upload and process a document
- `GET /docs/` - List all documents
- `GET /docs/{doc_id}` - Get document by ID
- `GET /docs/{doc_id}/chunks` - Get document chunks
- `DELETE /docs/{doc_id}` - Delete a document

### Chat
- `POST /chat/` - Create a new chat (with document selection and LLM config)
- `GET /chat/` - List all chats
- `GET /chat/{chat_id}` - Get chat by ID
- `GET /chat/{chat_id}/messages` - Get chat messages
- `POST /chat/message` - Send a message (RAG + agent + memory)

### Search
- `POST /search/` - Hybrid search across documents

### Feedback
- `POST /feedback/` - Submit feedback for a message
- `GET /feedback/message/{message_id}` - Get message feedback

### Personas
- `POST /personas/` - Create custom persona
- `GET /personas/` - List all personas
- `GET /personas/{persona_id}` - Get persona by ID

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check

## 🔧 Usage Examples

### Upload a Document

```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@document.pdf"
```

Response:
```json
{
  "id": "uuid",
  "filename": "document.pdf",
  "size": 12345,
  "summary": "Document summary...",
  "chunk_count": 15
}
```

### Create a Chat with Documents

```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Research Chat",
    "document_ids": ["doc-uuid-1", "doc-uuid-2"],
    "llm_provider": "openai",
    "llm_model": "gpt-4-turbo-preview",
    "llm_temperature": 0.7,
    "personality": "friendly"
  }'
```

### Send a Message

```bash
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key findings?",
    "chat_id": "chat-uuid",
    "llm_provider": "anthropic",
    "llm_model": "claude-sonnet-4-20250514",
    "llm_temperature": 0.7,
    "stream": false
  }'
```

Response:
```json
{
  "response": "Based on the documents...",
  "sources": [
    {
      "title": "Research Paper",
      "document_name": "paper.pdf",
      "page": 5,
      "chunk_index": 12,
      "score": 0.89,
      "content": "Relevant excerpt..."
    }
  ],
  "tool_calls": 0
}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_assistant --cov-report=html

# Run specific test file
pytest tests/test_retriever.py
```

## 🗄️ Database Schema

The system uses PostgreSQL 16 with the following extensions:
- **pgvector**: Vector similarity search for embeddings
- **pg_trgm**: Trigram-based full-text search

### Main Tables

- **users**: User profiles with preferences
- **documents**: Document metadata and summaries
- **doc_chunks**: Text chunks with vector embeddings (1536-dim)
- **chats**: Chat sessions with LLM configuration
- **chat_documents**: Many-to-many relationship (chat ↔ documents)
- **messages**: Chat messages with sources
- **chat_summaries**: Rolling conversation summaries
- **memories**: Long-term memories (episodic/factual) with embeddings
- **personas_custom**: Custom user-created personas
- **feedback**: User feedback (thumbs up/down)

### Migrations

Migrations are managed with Alembic and run automatically on Docker startup.

**Manual migration commands:**

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

# View current version
alembic current
```

## ⚙️ Configuration

All configuration is managed through environment variables. See `env.example` for Docker deployment and `.env.local` for local development.

### Core Settings

- `OPENAI_API_KEY`: OpenAI API key (required)
- `ANTHROPIC_API_KEY`: Anthropic API key (optional)
- `SERPAPI_API_KEY`: SerpAPI key (optional, for web search)

### Database Settings

- `POSTGRES_HOST`: Database host (`db` for Docker, `localhost` for local)
- `POSTGRES_PORT`: Database port (default: 5432)
- `POSTGRES_DB`: Database name (default: ai_assistant)
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password

### Storage Settings

- `UPLOAD_DIR`: Upload directory (`/data/uploads` for Docker, `./uploads` for local)

### LLM Settings

- `LLM_MODEL`: Default LLM model (default: gpt-4-turbo-preview)
- `LLM_TEMPERATURE`: Default temperature (default: 0.7)
- `EMBEDDING_MODEL`: Embedding model (default: text-embedding-3-small)
- `EMBEDDING_DIMENSIONS`: Embedding dimensions (default: 1536)

### Retrieval Settings

- `HYBRID_SEARCH_ALPHA`: Vector/keyword search weight (default: 0.7, range: 0-1)
- `TOP_K_CHUNKS`: Number of chunks to retrieve (default: 5)
- `MEMORY_TOP_K`: Number of memories to retrieve (default: 3)

### Agent Settings

- `AGENT_MAX_ITERATIONS`: Max agent iterations (default: 5)
- `AGENT_VERBOSE`: Enable verbose logging (default: true)
- `ENABLE_WEB_SEARCH`: Enable SerpAPI web search (default: true)
- `ENABLE_CALCULATOR`: Enable calculator tool (default: true)

## 🐳 Docker Commands

### Basic Operations

```bash
# Build and start
docker-compose up -d --build

# Stop services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# View logs
docker-compose logs -f api
docker-compose logs -f db

# Restart a service
docker-compose restart api

# Enter API container
docker exec -it ai_assistant_api bash

# Enter database
docker exec -it ai_assistant_db psql -U postgres -d ai_assistant
```

### Debugging

```bash
# Check container status
docker-compose ps

# Check environment variables
docker exec ai_assistant_api env | grep POSTGRES

# Check upload directory
docker exec ai_assistant_api ls -la /data/uploads

# View database tables
docker exec -it ai_assistant_db psql -U postgres -d ai_assistant -c "\dt"

# Check pgvector extension
docker exec -it ai_assistant_db psql -U postgres -d ai_assistant -c "\dx"
```

## 🌐 Deployment

### VPS/Cloud Deployment

The application has been successfully deployed to production. Example deployment:

```bash
# On your server
git clone <repository-url>
cd home_task

# Configure environment
cp env.example .env
nano .env  # Add your API keys

# Build and deploy
docker-compose up -d --build

# Check status
docker-compose ps
docker-compose logs -f api
```

**Production considerations:**
- Use strong database passwords
- Enable HTTPS with a reverse proxy (Nginx/Traefik)
- Set up log rotation
- Configure backup for PostgreSQL data
- Use Docker secrets for sensitive data
- Monitor resource usage

### Environment Differences

| Setting | Docker | Local |
|---------|--------|-------|
| `POSTGRES_HOST` | `db` | `localhost` |
| `UPLOAD_DIR` | `/data/uploads` | `./uploads` |
| Database | In container | On host machine |
| Dependencies | In image | System-wide |



## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- LangChain for agent orchestration
- OpenAI and Anthropic for LLM APIs
- pgvector for vector similarity search
- Unstructured for document parsing

---

