#!/bin/bash
set -e

echo "🚀 Starting AI Assistant API..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# Run database migrations (from apps/api directory)
echo "🔄 Running database migrations..."
alembic upgrade head
echo "✅ Migrations completed!"

# Start the application with reload for development
echo "🌟 Starting FastAPI application..."
echo "  📍 Working directory: $(pwd)"
echo "  🔑 Environment loaded from .env"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload

