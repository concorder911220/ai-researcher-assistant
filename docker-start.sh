#!/bin/bash

echo "🐳 AI Research Assistant - Docker Setup"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "📝 Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY (Required)"
    echo "   - ANTHROPIC_API_KEY (Optional - for Claude)"
    echo "   - SERPAPI_API_KEY (Optional - for web search)"
    echo ""
    echo "Then run this script again: ./docker-start.sh"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if OPENAI_API_KEY is set
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "⚠️  OPENAI_API_KEY is not set in .env file"
    echo "   Please add your OpenAI API key to .env file"
    exit 1
fi

echo "✅ Environment variables loaded"
echo ""

# Ask user what to do
echo "What would you like to do?"
echo "1) Start services (docker-compose up)"
echo "2) Start with rebuild (docker-compose up --build)"
echo "3) Stop services (docker-compose down)"
echo "4) Stop and remove volumes - fresh start (docker-compose down -v)"
echo "5) View logs (docker-compose logs -f)"
echo ""
read -p "Enter your choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting services..."
        docker-compose up
        ;;
    2)
        echo ""
        echo "🔨 Building and starting services..."
        docker-compose up --build
        ;;
    3)
        echo ""
        echo "🛑 Stopping services..."
        docker-compose down
        echo "✅ Services stopped"
        ;;
    4)
        echo ""
        echo "🗑️  Stopping services and removing volumes..."
        docker-compose down -v
        echo "✅ Services stopped and volumes removed"
        ;;
    5)
        echo ""
        echo "📜 Viewing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

