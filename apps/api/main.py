"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ai_assistant.config import settings
from ai_assistant.routers import upload, docs, chat, search, feedback, personas

app = FastAPI(
    title="Personal AI Research Assistant",
    description="Backend API with RAG, memory, and tool integration",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(docs.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(feedback.router)
app.include_router(personas.router)

# Mount static file serving for uploads
try:
    app.mount("/files", StaticFiles(directory=settings.upload_dir), name="files")
except RuntimeError:
    # Directory doesn't exist yet, will be created on first upload
    pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Personal AI Research Assistant API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


