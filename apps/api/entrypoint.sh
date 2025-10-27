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

# Create database if it doesn't exist
echo "🔧 Ensuring database exists..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -tc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1 || \
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB"
echo "✅ Database ready!"

# Run database migrations (from apps/api directory)
echo "🔄 Running database migrations..."
echo "  📂 Current directory: $(pwd)"
echo "  📄 Alembic config: $(ls -la alembic.ini 2>&1 || echo 'Not found')"
alembic -c /app/apps/api/alembic.ini upgrade head
echo "✅ Migrations completed!"

# Change to the API directory
cd /app/apps/api

# Start the application with reload for development
echo "🌟 Starting FastAPI application..."
echo "  📍 Working directory: $(pwd)"
echo "  🔑 Environment loaded from .env"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload

