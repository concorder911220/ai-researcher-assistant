FROM python:3.13-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file from root
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project structure
COPY . .

# Create upload directory
RUN mkdir -p /data/uploads

# Set working directory to apps/api
WORKDIR /app/apps/api

# Make entrypoint executable
RUN chmod +x entrypoint.sh && \
    ls -la entrypoint.sh && \
    head -1 entrypoint.sh

# Expose port
EXPOSE 8000

# Run migrations and start application
CMD ["/bin/bash", "/app/apps/api/entrypoint.sh"]

